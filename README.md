# Measurement Inspector

Local, layered analysis tooling for eCAL HDF measurements with a Panel dashboard.

## What this project does

`measurement_inspector` ingests measurement message records, computes canonical per-message metrics, and serves an interactive local dashboard for triage and deep inspection.

Core capabilities currently implemented:

- Canonical base table with per-message derived fields.
- Wrap-aware counter semantics and inferred loss metrics.
- Stream summary and time-bucket summary tables.
- Loss-event extraction table.
- Local Panel app with overview, stream detail, and raw event-table tabs.
- CLI entrypoint: `measure-inspect`.

## Installation

```bash
python -m pip install -e .
```

## Dependencies

Primary runtime dependencies are defined in `pyproject.toml`, including:

- `numpy`, `pandas`
- `panel`, `holoviews`, `hvplot`
- `typer`, `pydantic`
- `eclipse-ecal>=6.1` (reader dependency boundary)

## Quickstart

```bash
measure-inspect /path/to/measurement \
  --topic camera/* \
  --stream-id 42 \
  --counter-bits 16 \
  --expected-rate-hz 100
```

### Current adapter status

`measurement_inspector/io/ecal_reader.py` is the dedicated integration boundary for eCAL HDF APIs. The adapter uses `ecal.measurement.hdf5.Meas` to enumerate channels and read entry metadata (send/receive timestamps, counters, and payload sizes) into the canonical message schema used by analysis and UI layers, preserving raw microsecond timestamps from eCAL.

If no readable HDF5 message table is found, CLI falls back to `<measurement_path>/messages.csv` for preview mode.

## Testing

Run tests with:

```bash
pytest -q
```

If dependencies are unavailable in your environment, run a syntax check fallback:

```bash
python -m compileall measurement_inspector tests
```

## Project structure

See [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) for the layered architecture and phased execution plan used for implementation.
