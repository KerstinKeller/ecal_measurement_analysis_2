# Measurement Inspector Implementation Plan

This plan captures the architecture and phased scope used by this repository.

## 1) Recommended tooling

- Python 3.11+
- `eclipse-ecal>=6.1` as measurement ingestion layer
- `pandas` + `numpy` for canonical processing and derived metrics
- `Panel` + `HoloViews/hvPlot` for local interactive dashboards
- Optional scaling: Datashader/hvPlot resampling and Parquet cache

## 2) Product shape

Single-command local workflow:

```bash
measure-inspect /path/to/measurement
```

Expected flow:

1. Read measurement via eCAL adapter.
2. Build canonical base table.
3. Compute derived metrics and summaries.
4. Serve local Panel dashboard.

## 3) Layered architecture

- **Layer A: Measurement adapter** (`io/ecal_reader.py`)
  - Isolate eCAL specifics and normalize records.
- **Layer B: Canonical transform** (`model/derived_metrics.py`)
  - Build base table and per-row computed metrics.
- **Layer C: Summary engine** (`model/summaries.py`, `model/anomalies.py`)
  - Build stream/time/loss/anomaly tables.
- **Layer D: View-model / selection engine** (`state/*`)
  - Shared selection/filter state.
- **Layer E: Panel UI** (`views/*`, `app.py`)
  - Overview, detail diagnostics, and raw table inspection.

## 4) Canonical data model

Base table contains observed-message rows with:

- Identity: `stream_id`, `topic`
- Raw fields: `send_ts`, `recv_ts`, `counter`, `size_bytes`
- Derived timing/loss/rate fields:
  - `latency_s`, `send_dt_s`, `recv_dt_s`
  - `counter_delta_raw`, `counter_delta_norm`, `lost_msgs`, `is_gap`
  - `send_freq_hz`, `recv_freq_hz`
  - `send_period_error_s`, `recv_period_error_s`
  - `send_bitrate_bps`, `recv_bitrate_bps`
  - `latency_diff_s`
- Stability/anomaly flags:
  - `is_counter_nonmonotonic`, `is_send_time_nonmonotonic`, `is_recv_time_nonmonotonic`
  - `is_latency_anomaly`, `is_send_period_anomaly`, `is_recv_period_anomaly`

## 5) Counter semantics config

`AnalysisConfig` controls:

- `counter_bits`, `counter_wrap`, `counter_modulus`
- `expected_freq_hz` / `expected_period_s`
- thresholds for latency and period anomalies
- default time axis and bucket size

## 6) First usable scope (implemented)

- Inputs: path, stream/topic filters, expected rate/period, counter settings
- Derived columns: latency, periods, frequencies, loss, anomalies
- Outputs: stream summary, time-bucket summary, loss events
- UI pages: overview, stream detail, raw events

## 7) Next phases

- Full eCAL reader API wiring and payload decoders
- Linked brushing and richer cross-filtering
- Datashaded timelines for large datasets
- Optional parquet caching and export actions
