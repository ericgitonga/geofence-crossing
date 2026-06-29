from __future__ import annotations

import logging
import os
import uuid
from typing import Annotated, Any, List, Literal, Optional, Union, cast

import geopandas as gpd
import pandas as pd
from ecoscope_workflows_core.annotations import AnyGeoDataFrame
from ecoscope_workflows_ext_ecoscope.schemas import EmptyDataFrame, RegionsGDF
from ecoscope_workflows_ext_ecoscope.tasks.io._spatial_features import (
    EarthRangerSpatialFeatures,
    LocalFileSpatialFeatures,
    RemoteFileSpatialFeatures,
    SpatialFeaturesConfig,
)
from ecoscope_workflows_ext_ecoscope.tasks.results._ecomap import (
    LayerDefinition,
    TextLayerStyle,
)
from pydantic import Field
from wt_registry import register

logger = logging.getLogger(__name__)

GEOPARQUET_EXTENSIONS = (".parquet", ".geoparquet")
GEOPACKAGE_EXTENSIONS = (".gpkg",)
VALID_EXTENSIONS = GEOPARQUET_EXTENSIONS + GEOPACKAGE_EXTENSIONS


def _validate_regions(regions_gdf: gpd.GeoDataFrame) -> None:
    duplicated = regions_gdf["name"][regions_gdf["name"].duplicated()]
    if not duplicated.empty:
        raise ValueError(
            f"Region names must be unique. Duplicates: {sorted(duplicated.unique())}"
        )


def _normalize_crs(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError(
            "GeoDataFrame has no CRS information. "
            "Cannot safely convert to EPSG:4326 without knowing the source CRS."
        )
    return gdf.to_crs(4326)


def _load_spatial_regions_from_file(
    file_path: str,
    layer: str | None,
    name_column: str,
    display_name: str,
) -> RegionsGDF | EmptyDataFrame:
    if file_path.lower().endswith(GEOPACKAGE_EXTENSIONS):
        gdf = gpd.read_file(file_path, layer=layer)
    else:
        gdf = gpd.read_parquet(file_path)

    if name_column not in gdf.columns:
        raise ValueError(
            f"Column '{name_column}' not found in file. Available: {list(gdf.columns)}"
        )
    if "geometry" not in gdf.columns:
        raise ValueError("File must have a 'geometry' column")

    gdf = _normalize_crs(gdf)

    polygon_mask = gdf.geometry.geom_type.isin({"Polygon", "MultiPolygon"})
    gdf = gdf[polygon_mask].reset_index(drop=True)

    if gdf.empty:
        raise ValueError("No Polygon or MultiPolygon geometries found in the file")

    uuids = [str(uuid.uuid4()) for _ in range(len(gdf))]

    regions_gdf = gpd.GeoDataFrame(
        {
            "pk": uuids,
            "name": gdf[name_column].astype(str),
            "short_name": gdf[name_column].astype(str),
            "feature_type": "polygon",
            "geometry": gdf.geometry,
            "metadata": [{"id": uid, "display_name": display_name} for uid in uuids],
        },
        crs=4326,
    )

    _validate_regions(regions_gdf)
    return cast(RegionsGDF, regions_gdf)


@register(
    title="Load Spatial Features Group",
    description=(
        "Load a spatial feature group from a local file, remote URL, or EarthRanger. "
        "Supports geoparquet and geopackage files. All geometries are converted to "
        "CRS 4326 and filtered to polygons only."
    ),
)
def load_spatial_features_group(
    config: Annotated[
        SpatialFeaturesConfig,
        Field(title="Spatial Feature Data Source"),
    ],
) -> RegionsGDF | EmptyDataFrame:
    from ecoscope_workflows_ext_ecoscope.connections import EarthRangerConnection
    from ecoscope_workflows_ext_ecoscope.tasks.io._earthranger import (
        get_spatial_features_group,
    )

    if isinstance(config, EarthRangerSpatialFeatures):
        client = EarthRangerConnection.client_from_named_connection(config.data_source)
        regions_gdf = get_spatial_features_group(
            client=client,
            spatial_features_group_name=config.spatial_features_group_name,
        )

        polygon_mask = regions_gdf.geometry.geom_type.isin({"Polygon", "MultiPolygon"})
        regions_gdf = regions_gdf[polygon_mask].reset_index(drop=True)

        if regions_gdf.empty:
            raise ValueError("No Polygon or MultiPolygon geometries found")

        _validate_regions(regions_gdf)
        return cast(RegionsGDF, regions_gdf)

    elif isinstance(config, RemoteFileSpatialFeatures):
        import tempfile

        from ecoscope.io import download_file  # type: ignore[import-untyped]

        display_name = (
            config.url.split("/")[-1]
            .rsplit(".", 1)[0]
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

        tmp_dir = tempfile.mkdtemp()
        download_file(config.url, tmp_dir)

        downloaded = os.listdir(tmp_dir)
        if not downloaded:
            raise ValueError(f"No file downloaded from {config.url}")
        temp_path = os.path.join(tmp_dir, downloaded[0])

        return _load_spatial_regions_from_file(
            file_path=temp_path,
            layer=config.layer,
            name_column=config.name_column,
            display_name=display_name,
        )

    else:  # LocalFileSpatialFeatures
        display_name = (
            os.path.basename(config.file_path)
            .rsplit(".", 1)[0]
            .replace("-", " ")
            .replace("_", " ")
            .title()
        )

        return _load_spatial_regions_from_file(
            file_path=config.file_path,
            layer=config.layer,
            name_column=config.name_column,
            display_name=display_name,
        )


@register(
    title="Detect Geofence Crossings",
    description=(
        "Detect where trajectory segments cross the boundary of a region of interest. "
        "Returns crossing points with geometry, interpolated crossing time, "
        "direction (Inward/Outward), subject identifier, coordinates, and any extra__ "
        "subject metadata columns carried from the trajectory."
    ),
)
def detect_geofence_crossings(
    trajectory: Annotated[
        AnyGeoDataFrame,
        Field(
            description=(
                "Trajectory GeoDataFrame with LineString geometries. "
                "Must have 'groupby_col', 'segment_start', and 'segment_end' columns."
            ),
            exclude=True,
        ),
    ],
    region_of_interest: Annotated[
        AnyGeoDataFrame,
        Field(
            description="Region of interest GeoDataFrame with Polygon geometries defining the geofence boundary.",
            exclude=True,
        ),
    ],
) -> AnyGeoDataFrame:
    from shapely.geometry import LineString, Point
    from shapely.ops import unary_union

    extra_col_names = [c for c in trajectory.columns if c.startswith("extra__")]

    _empty = cast(
        AnyGeoDataFrame,
        gpd.GeoDataFrame(
            columns=["geometry", "crossing_time", "direction", "groupby_col", "longitude", "latitude"] + extra_col_names,
            geometry="geometry",
            crs=trajectory.crs,
        ),
    )

    if trajectory.empty:
        return _empty

    roi = region_of_interest
    if (
        roi.crs is not None
        and trajectory.crs is not None
        and not roi.crs.equals(trajectory.crs)
    ):
        logger.info("Reprojecting ROI from %s to %s.", roi.crs, trajectory.crs)
        roi = cast(AnyGeoDataFrame, cast(gpd.GeoDataFrame, roi).to_crs(trajectory.crs))

    roi_union = unary_union(list(roi.geometry))
    roi_boundary = roi_union.boundary

    crossings = []

    for _, row in trajectory.iterrows():
        segment = row.geometry
        if not isinstance(segment, LineString):
            continue
        if not segment.intersects(roi_boundary):
            continue

        intersection = segment.intersection(roi_boundary)
        geom_type = intersection.geom_type

        pts = []
        if geom_type == "Point":
            pts = [intersection]
        elif geom_type == "MultiPoint":
            pts = list(intersection.geoms)
        elif geom_type == "GeometryCollection":
            pts = [g for g in intersection.geoms if g.geom_type == "Point"]

        if not pts:
            continue

        pts_with_t = sorted(
            [(segment.project(pt, normalized=True), pt) for pt in pts],
            key=lambda x: x[0],
        )

        start_inside = Point(segment.coords[0]).within(roi_union)

        seg_start = row.get("segment_start")
        seg_end = row.get("segment_end")
        if pd.isnull(seg_start) or pd.isnull(seg_end):
            continue

        duration_seconds = (seg_end - seg_start).total_seconds()

        for i, (t, pt) in enumerate(pts_with_t):
            position_before_inside = start_inside ^ (i % 2 == 1)
            direction = "Outward" if position_before_inside else "Inward"
            crossing_time = seg_start + pd.Timedelta(seconds=duration_seconds * t)

            crossings.append(
                {
                    "geometry": pt,
                    "crossing_time": crossing_time,
                    "direction": direction,
                    "groupby_col": row.get("groupby_col"),
                    "longitude": round(pt.x, 6),
                    "latitude": round(pt.y, 6),
                    **{c: row.get(c) for c in extra_col_names},
                }
            )

    if not crossings:
        logger.warning("No geofence crossings detected in the trajectory data.")
        return _empty

    result = gpd.GeoDataFrame(crossings, geometry="geometry", crs=trajectory.crs)
    result = result.sort_values("crossing_time").reset_index(drop=True)
    return cast(AnyGeoDataFrame, result)


@register(
    title="Combine Map Layers",
    description=(
        "Combine static and grouped map layers into a single ordered list for rendering. "
        "Flattens nested lists and ensures text layers are placed last."
    ),
)
def combine_map_layers(
    static_layers: Annotated[
        Optional[
            Union[LayerDefinition, List[Union[LayerDefinition, List[LayerDefinition]]]]
        ],
        Field(description="Static layers from local files or base maps."),
    ] = None,
    grouped_layers: Annotated[
        Optional[
            Union[LayerDefinition, List[Union[LayerDefinition, List[LayerDefinition]]]]
        ],
        Field(description="Grouped layers generated from split/grouped data."),
    ] = None,
) -> List[LayerDefinition]:
    def flatten_layers(layers: Any) -> List[LayerDefinition]:
        if not isinstance(layers, list):
            return [layers]
        flattened: List[LayerDefinition] = []
        for item in layers:
            if isinstance(item, list):
                flattened.extend(flatten_layers(item))
            else:
                flattened.append(item)
        return flattened

    flat_static = flatten_layers(static_layers) if static_layers else []
    flat_grouped = flatten_layers(grouped_layers) if grouped_layers else []

    all_layers = flat_static + flat_grouped
    text_layers: List[LayerDefinition] = []
    other_layers: List[LayerDefinition] = []

    for layer in all_layers:
        if isinstance(layer.layer_style, TextLayerStyle):
            text_layers.append(layer)
        else:
            other_layers.append(layer)

    return other_layers + text_layers
