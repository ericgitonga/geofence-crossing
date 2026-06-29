from __future__ import annotations

import logging
from typing import Annotated, Any, List, Optional, Union

import geopandas as gpd
import pandas as pd
from ecoscope.platform.annotations import AnyGeoDataFrame
from ecoscope.platform.tasks.results._ecomap import LayerDefinition, TextLayerStyle
from pydantic import Field
from wt_registry import register

logger = logging.getLogger(__name__)


@register(description="Detect points where tracked subject trajectories cross a geofence boundary, returning a GeoDataFrame of crossing events with direction (Inward/Outward) and timestamp.")
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
    from typing import cast

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

    from typing import cast

    result = gpd.GeoDataFrame(crossings, geometry="geometry", crs=trajectory.crs)
    result = result.sort_values("crossing_time").reset_index(drop=True)
    return cast(AnyGeoDataFrame, result)


@register(description="Combine a static ROI boundary layer with per-subject crossing point layers, placing text labels last for correct rendering order.")
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
