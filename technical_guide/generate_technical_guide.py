"""
Generate the Geofence Crossing Workflow Technical Guide as a PDF using ReportLab.
Run with: conda run -n ds python technical_guide/generate_technical_guide.py
Output: technical_guide/geofence_crossing_technical_guide.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from datetime import date

import os
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "geofence_crossing_technical_guide.pdf")

# ── Colour palette ────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#115631")
GREEN_MID   = colors.HexColor("#2d6a4f")
AMBER       = colors.HexColor("#e7a553")
SLATE       = colors.HexColor("#3d3d3d")
LIGHT_GREY  = colors.HexColor("#f5f5f5")
MID_GREY    = colors.HexColor("#cccccc")
WHITE       = colors.white

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

def _style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=styles[parent], **kw)
    styles.add(s)
    return s

TITLE    = _style("DocTitle",    fontSize=24, leading=30, textColor=GREEN_DARK,
                  spaceAfter=6,  alignment=TA_CENTER, fontName="Helvetica-Bold")
SUBTITLE = _style("DocSubtitle", fontSize=12, leading=16, textColor=SLATE,
                  spaceAfter=4,  alignment=TA_CENTER)
META     = _style("Meta",        fontSize=9,  leading=13, textColor=colors.grey,
                  alignment=TA_CENTER, spaceAfter=2)
H1       = _style("H1", fontSize=14, leading=18, textColor=GREEN_DARK,
                  spaceBefore=16, spaceAfter=5, fontName="Helvetica-Bold")
H2       = _style("H2", fontSize=11, leading=15, textColor=GREEN_MID,
                  spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold")
H3       = _style("H3", fontSize=9.5, leading=13, textColor=SLATE,
                  spaceBefore=7, spaceAfter=3, fontName="Helvetica-Bold")
BODY     = _style("Body", fontSize=9, leading=14, textColor=SLATE,
                  spaceAfter=5, alignment=TA_JUSTIFY)
BULLET   = _style("BulletItem", fontSize=9, leading=13, textColor=SLATE,
                  spaceAfter=2, leftIndent=14, firstLineIndent=-10)
CELL     = _style("Cell", fontSize=8.5, leading=12, textColor=SLATE,
                  spaceAfter=0, spaceBefore=0)
NOTE     = _style("Note", fontSize=8.5, leading=13,
                  textColor=colors.HexColor("#555555"),
                  backColor=colors.HexColor("#fff8e1"),
                  leftIndent=10, rightIndent=10, spaceAfter=6, borderPad=4)


def hr():
    return HRFlowable(width="100%", thickness=1, color=MID_GREY, spaceAfter=6)

def p(text, style=BODY):       return Paragraph(text, style)
def h1(text):                  return Paragraph(text, H1)
def h2(text):                  return Paragraph(text, H2)
def h3(text):                  return Paragraph(text, H3)
def sp(n=6):                   return Spacer(1, n)
def bullet(text):              return Paragraph(f"• {text}", BULLET)
def note(text):                return Paragraph(f"<b>Note:</b> {text}", NOTE)
def c(text):                   return Paragraph(text, CELL)


def make_table(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0),  GREEN_DARK),
        ("TEXTCOLOR",      (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",       (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("GRID",           (0, 0), (-1, -1), 0.4, MID_GREY),
        ("VALIGN",         (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
    ]))
    return t


# ── Page template ─────────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(GREEN_DARK)
    canvas.rect(0, 0, w, 22, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 7, "Geofence Crossing Workflow — Technical Guide")
    canvas.drawRightString(w - 1.5*cm, 7, f"Page {doc.page}")
    canvas.setFillColor(AMBER)
    canvas.rect(0, h - 4, w, 4, fill=1, stroke=0)
    canvas.restoreState()


# ── Build story ───────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title="Geofence Crossing Workflow — Technical Guide",
        author="Ecoscope",
    )

    story = []

    # ── Cover ─────────────────────────────────────────────────────────────────
    story += [
        sp(60),
        p("Geofence Crossing Workflow", TITLE),
        p("Technical Guide", SUBTITLE),
        sp(8),
        hr(),
        p("Boundary Crossing Detection — Methodology &amp; Calculation Reference", META),
        p(f"Version 0.1.0  ·  Generated {date.today().strftime('%B %d, %Y')}", META),
        hr(),
        PageBreak(),
    ]

    # ── 1. Overview ───────────────────────────────────────────────────────────
    story += [
        h1("1. Overview"), hr(),
        p(
            "The <b>Geofence Crossing Workflow</b> detects and visualises the moments "
            "when tracked subjects cross the boundary of a user-defined region of interest "
            "(ROI). It ingests subject telemetry from <b>EarthRanger</b>, converts it to "
            "trajectories, intersects those trajectories with the ROI boundary, and delivers "
            "an interactive map and a per-subject table showing each crossing event with its "
            "time, direction, and coordinates."
        ),
        p(
            "The workflow is designed for any species or asset tracked via EarthRanger. "
            "The region of interest can be loaded from a local file, a remote URL, or "
            "directly from EarthRanger spatial features."
        ),
        note(
            "Subject names are used throughout — the grouper defaults to "
            "<code>extra__subject__name</code>, which is populated automatically from "
            "EarthRanger subject details on every observation fetch."
        ),
    ]

    # ── 2. Dependencies ───────────────────────────────────────────────────────
    story += [
        sp(4), h1("2. Dependencies &amp; Prerequisites"), hr(),

        h2("2.1 EarthRanger Connection"),
        p(
            "All telemetry is fetched from an <b>EarthRanger</b> instance via "
            "<code>set_er_connection</code>. Subject group observations are retrieved "
            "with <code>get_subjectgroup_observations</code> over the configured time "
            "range. <code>raise_on_empty: false</code> allows the workflow to continue "
            "gracefully when no observations exist for the selected period."
        ),

        sp(4), h2("2.2 Groupers"),
        p(
            "One grouper field is configured by default via <code>set_groupers</code>:"
        ),
        make_table(
            [
                [c("Grouper field"),          c("EarthRanger source"),  c("Typical use")],
                [c("extra__subject__name"),   c("subject.name"),        c("One table section per individual subject (default)")],
            ],
            [4.5*cm, 4*cm, 8*cm],
        ),
        sp(4),
        p(
            "Additional groupers (sex, subtype, or any other subject attribute) can be "
            "added in the workflow configuration form. The grouper drives the "
            "<code>split_groups</code> step that partitions crossings into per-subject "
            "table views."
        ),

        sp(4), h2("2.3 Region of Interest"),
        p(
            "<code>load_spatial_features_group</code> accepts three source types, "
            "selectable at runtime:"
        ),
        make_table(
            [
                [c("Source type"),                 c("Description")],
                [c("LocalFileSpatialFeatures"),    c("GeoJSON, GeoPackage, or Shapefile from a local path")],
                [c("RemoteFileSpatialFeatures"),   c("GeoJSON or GeoPackage downloaded from a URL")],
                [c("EarthRangerSpatialFeatures"),  c("Spatial features fetched directly from the connected EarthRanger instance")],
            ],
            [4.5*cm, 12*cm],
        ),
        sp(4),
        p(
            "The ROI must contain <b>Polygon</b> geometries defining the geofence "
            "boundary. All geometries are used; multi-polygon ROIs are supported."
        ),

        sp(4), h2("2.4 Base Map Tile Layers"),
        p(
            "Base maps are configured via <code>set_base_maps</code> and composited "
            "beneath the data layers in the output ecomap."
        ),
    ]

    # ── 3. Data Ingestion ─────────────────────────────────────────────────────
    story += [
        sp(4), h1("3. Data Ingestion Pipeline"), hr(),

        h2("3.1 Observations → Trajectories"),
        p(
            "<code>relocations_to_trajectory</code> connects consecutive GPS fixes per "
            "subject into LineString segments. All <code>extra__</code>-prefixed subject "
            "detail columns (including <code>extra__subject__name</code>) are preserved "
            "on the trajectory GeoDataFrame and carried through to the crossing output."
        ),
        p("Key columns on the resulting trajectory GeoDataFrame:"),
        make_table(
            [
                [c("Column"),                  c("Description")],
                [c("geometry"),                c("LineString connecting two consecutive fixes")],
                [c("groupby_col"),             c("Subject identifier used for grouping")],
                [c("segment_start"),           c("UTC datetime of the first fix in the segment")],
                [c("segment_end"),             c("UTC datetime of the second fix in the segment")],
                [c("extra__subject__name"),    c("Subject display name (from EarthRanger subject details)")],
            ],
            [4.5*cm, 12*cm],
        ),

        sp(4), h2("3.2 Timezone Handling"),
        p(
            "<code>get_timezone_from_time_range</code> extracts the IANA timezone from "
            "the configured time range. After crossing detection, "
            "<code>convert_values_to_timezone</code> converts the "
            "<code>crossing_time</code> column from UTC to local time. The time range "
            "display format is <code>%d %b %Y %H:%M:%S %Z</code>."
        ),
    ]

    # ── 4. Crossing Detection ─────────────────────────────────────────────────
    story += [
        sp(4), h1("4. Geofence Crossing Detection"), hr(),

        h2("4.1 Algorithm"),
        p(
            "<code>detect_geofence_crossings</code> iterates over every trajectory "
            "segment and tests for intersection with the ROI boundary. For each "
            "intersecting segment:"
        ),
        bullet(
            "The <b>crossing point geometry</b> is computed as the intersection of the "
            "segment LineString with the ROI boundary."
        ),
        bullet(
            "The <b>crossing time</b> is interpolated linearly along the segment "
            "between <code>segment_start</code> and <code>segment_end</code>, "
            "proportional to the distance from the segment start to the crossing point."
        ),
        bullet(
            "The <b>direction</b> is determined by whether the segment endpoint lies "
            "inside or outside the ROI polygon."
        ),
        bullet(
            "All <code>extra__</code>-prefixed columns (e.g. "
            "<code>extra__subject__name</code>) are carried through to the crossing "
            "record."
        ),

        sp(4), h2("4.2 Direction Classification"),
        make_table(
            [
                [c("Direction value"), c("Meaning"),                         c("Map colour")],
                [c("Inward"),          c("Subject enters the ROI"),           c("#008000  (green)")],
                [c("Outward"),         c("Subject exits the ROI"),            c("#CC0000  (red)")],
            ],
            [3.5*cm, 7*cm, 6*cm],
        ),
        sp(4),
        p(
            "<code>apply_color_map</code> maps the <code>direction</code> column to "
            "the two-colour palette above, storing the result in "
            "<code>direction_colormap</code>. This column drives the point layer fill "
            "colour on the map."
        ),

        sp(4), h2("4.3 Crossing Output Columns"),
        make_table(
            [
                [c("Column"),                c("Type"),     c("Description")],
                [c("geometry"),              c("Point"),    c("WGS 84 coordinate of the boundary crossing")],
                [c("crossing_time"),         c("datetime"), c("Interpolated local time of the crossing (after timezone conversion)")],
                [c("direction"),             c("str"),      c('"Inward" or "Outward"')],
                [c("longitude"),             c("float"),    c("Crossing point longitude, rounded to 6 decimal places")],
                [c("latitude"),              c("float"),    c("Crossing point latitude, rounded to 6 decimal places")],
                [c("direction_colormap"),    c("str"),      c("Hex colour string derived from direction")],
                [c("extra__subject__name"),  c("str"),      c("Subject display name, carried from the trajectory")],
                [c("groupby_col"),           c("str"),      c("Subject identifier, carried from the trajectory")],
            ],
            [4*cm, 2*cm, 10.5*cm],
        ),
    ]

    # ── 5. Map Output ─────────────────────────────────────────────────────────
    story += [
        sp(4), h1("5. Map Output"), hr(),
        p(
            "A single combined ecomap is produced showing the ROI boundary and all "
            "crossing events across all subjects. The map is interactive (pan, zoom, "
            "click tooltips) and saved as an HTML file."
        ),

        h2("5.1 ROI Boundary Layer"),
        make_table(
            [
                [c("Property"),        c("Value")],
                [c("Geometry"),        c("Polygon outline (not filled)")],
                [c("Stroke colour"),   c("RGB(30, 30, 200, 200) — blue at 78 % opacity")],
                [c("Line width"),      c("2 px")],
                [c("Legend title"),    c("Region of Interest")],
                [c("Legend label"),    c("Boundary")],
                [c("Auto-zoom"),       c("Yes — map view fits to the ROI extent on load")],
            ],
            [4.5*cm, 12*cm],
        ),

        sp(4), h2("5.2 Crossing Points Layer"),
        make_table(
            [
                [c("Property"),           c("Value")],
                [c("Fill colour"),        c("From direction_colormap column (green = Inward, red = Outward)")],
                [c("Point radius"),       c("8 px")],
                [c("Legend"),             c("Derived from Direction column and direction_colormap")],
                [c("Tooltip columns"),    c("Crossing Time, Direction, Subject")],
            ],
            [4.5*cm, 12*cm],
        ),

        sp(4), h2("5.3 Ecomap Settings"),
        make_table(
            [
                [c("Property"),         c("Value")],
                [c("North arrow"),      c("Top-left placement")],
                [c("Legend"),           c("Title: \"Crossings\", bottom-right placement")],
                [c("Interactive"),      c("Yes (static: false)")],
                [c("Max zoom"),         c("20")],
                [c("Layer order"),      c("Base tiles → ROI boundary → crossing points")],
            ],
            [4.5*cm, 12*cm],
        ),
        sp(4),
        p(
            "The map HTML is persisted to <code>$ECOSCOPE_WORKFLOWS_RESULTS</code> "
            "and referenced by the map widget in the dashboard."
        ),
    ]

    # ── 6. Table Output ───────────────────────────────────────────────────────
    story += [
        sp(4), h1("6. Table Output"), hr(),
        p(
            "Per-subject crossing tables are produced by splitting the full crossings "
            "GeoDataFrame on the configured groupers, renaming columns for readability, "
            "then rendering each partition as an HTML table."
        ),

        h2("6.1 Column Renaming"),
        make_table(
            [
                [c("Original column"),       c("Display name")],
                [c("crossing_time"),         c("Crossing Time")],
                [c("direction"),             c("Direction")],
                [c("extra__subject__name"),  c("Subject")],
                [c("longitude"),             c("Longitude")],
                [c("latitude"),              c("Latitude")],
            ],
            [5*cm, 11.5*cm],
        ),
        sp(4),
        p(
            "Columns are renamed via <code>map_columns</code> with "
            "<code>raise_if_not_found: false</code> — missing columns are silently "
            "skipped rather than raising an error."
        ),

        sp(4), h2("6.2 Table Widget"),
        p(
            "Each per-subject partition is rendered by <code>draw_table</code> with "
            "column order: <b>Crossing Time, Direction, Subject, Longitude, Latitude</b>. "
            "Each rendered HTML table is persisted, then wrapped in a "
            "<code>create_table_widget_single_view</code> titled "
            "<i>Geofence Crossings Table</i>. All per-subject views are merged into a "
            "single grouped table widget via <code>merge_widget_views</code>."
        ),
        note(
            "Table widget tasks use <code>skipif: [never]</code> to ensure the "
            "dashboard always assembles, even when some subjects have no crossings."
        ),
    ]

    # ── 7. Interactive Dashboard ───────────────────────────────────────────────
    story += [
        sp(4), h1("7. Interactive Dashboard"), hr(),
        p(
            "<code>gather_dashboard</code> assembles the final dashboard from two "
            "widget groups, bound to the configured groupers and time range:"
        ),
        make_table(
            [
                [c("Widget"),                   c("Type"),  c("Source")],
                [c("Geofence Crossings Map"),   c("Map"),   c("ecomap_html_url → map_widget → merged_map_widget")],
                [c("Geofence Crossings Table"), c("Table"), c("crossings_table_html_url → table_widget → merged_table_widget")],
            ],
            [5.5*cm, 2*cm, 9*cm],
        ),
        sp(4),
        p(
            "The map widget presents all crossing events together on one combined view. "
            "The table widget presents per-subject views grouped by the active grouper, "
            "allowing users to navigate between subjects using the widget controls."
        ),
    ]

    # ── 8. Output Files ───────────────────────────────────────────────────────
    story += [
        sp(4), h1("8. Output Files"), hr(),
        p(
            "All files are written to <code>$ECOSCOPE_WORKFLOWS_RESULTS</code>."
        ),
        make_table(
            [
                [c("File / pattern"),            c("Format"), c("Content")],
                [c("crossings_map.html"),         c("HTML"),   c("Interactive combined map — ROI boundary and all crossing points")],
                [c("<group>_crossings.html"),     c("HTML"),   c("Per-subject crossing table (one file per subject group)")],
            ],
            [5*cm, 2*cm, 9.5*cm],
        ),
    ]

    # ── 9. Workflow Execution Logic ───────────────────────────────────────────
    story += [
        sp(4), h1("9. Workflow Execution Logic"), hr(),

        h2("9.1 Skip Conditions"),
        p(
            "Two default skip conditions apply to every task "
            "(<code>task-instance-defaults</code>):"
        ),
        bullet(
            "<b>any_is_empty_df</b> — skips the task (and all dependants) when any "
            "input DataFrame is empty. This handles subjects with no observations, or "
            "trajectories that never cross the ROI boundary."
        ),
        bullet(
            "<b>any_dependency_skipped</b> — propagates skips downstream automatically."
        ),
        p(
            "The <code>detect_geofence_crossings</code> task has an explicit additional "
            "skip condition to short-circuit cleanly when either the trajectory or the "
            "ROI is empty. Map and table widget tasks override defaults with "
            "<code>skipif: [never]</code> to ensure the dashboard always assembles."
        ),

        sp(4), h2("9.2 Data Flow Summary"),
        make_table(
            [
                [c("Stage"),                 c("Tasks")],
                [c("Setup"),                 c("EarthRanger connection, time range, timezone extraction, groupers, base maps")],
                [c("ROI loading"),           c("load_spatial_features_group")],
                [c("Telemetry ingest"),      c("get_subjectgroup_observations → relocations_to_trajectory")],
                [c("Crossing detection"),    c("detect_geofence_crossings → convert_values_to_timezone → apply_color_map")],
                [c("Grouping"),              c("add_temporal_index → split_groups")],
                [c("Map branch"),            c("map_columns (rename) → create_polygon_layer + create_point_layer → draw_ecomap → persist → widget")],
                [c("Table branch"),          c("map_columns (rename, per group) → draw_table → persist → widget (per group)")],
                [c("Dashboard"),             c("gather_dashboard combines map widget and table widget")],
            ],
            [4*cm, 12.5*cm],
        ),
    ]

    # ── 10. Software Versions ─────────────────────────────────────────────────
    story += [
        sp(4), h1("10. Software Versions"), hr(),
        make_table(
            [
                [c("Package"),                          c("Version"),        c("Role")],
                [c("ecoscope-workflows-core"),          c("0.22.18.*"),      c("Core task library and workflow engine")],
                [c("ecoscope-workflows-ext-ecoscope"),  c("0.22.18.*"),      c("Spatial analysis tasks (relocations, trajectories, maps, widgets)")],
                [c("ecoscope-workflows-ext-custom"),    c(">=0.0.46,<0.1.0"), c("Custom tasks: geofence crossing detection, spatial feature loading")],
            ],
            [6*cm, 3*cm, 7.5*cm],
        ),
        sp(4),
        p(
            "The core and ecoscope-ext packages are distributed via the "
            "<code>prefix.dev/ecoscope-workflows</code> conda channel. "
            "The custom package is built and distributed locally via a rattler-build "
            "artifacts channel. The runtime environment is managed by <b>pixi</b>."
        ),
    ]

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF written → {OUTPUT_FILE}")


if __name__ == "__main__":
    build()
