# Geofence Crossing Workflow

**Version 0.2.1** · Works on Ecoscope Desktop (Windows and macOS) and Ecoscope Web

Detects when tracked subject trajectories cross a geofence boundary and displays the crossing events on an interactive map and table, coloured by direction (green = inward, red = outward).

## Install

1. Open **Ecoscope Desktop** → **Workflow Templates** → **+ Add Template**
2. Paste the URL and press Enter:
   ```
   https://github.com/ericgitonga/geofence-crossing
   ```

## What it produces

- **Geofence Crossings Map** — crossing points coloured by direction with tooltips, overlaid on the ROI boundary
- **Geofence Crossings Table** — per-subject table of crossing time, direction, and coordinates

## Documentation

For full configuration reference, methodology, and troubleshooting see the [Technical Guide](docs/geofence_crossing_technical_guide.pdf).

## Development

```bash
# Recompile workflow from spec.yaml
./dev/recompile.sh

# Run tests
./dev/pytest-cli.sh geofence_crossing --case base --local --quiet
```
