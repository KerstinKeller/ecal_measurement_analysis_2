from __future__ import annotations

import numpy as np
import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.model.counter_logic import compute_counter_metrics


CANONICAL_ORDER = [
    "stream_id",
    "topic",
    "send_ts",
    "recv_ts",
    "counter",
    "size_bytes",
    "latency_s",
    "send_dt_s",
    "recv_dt_s",
    "counter_delta_raw",
    "counter_delta_norm",
    "lost_msgs",
    "is_gap",
    "send_freq_hz",
    "recv_freq_hz",
    "send_period_error_s",
    "recv_period_error_s",
    "send_bitrate_bps",
    "recv_bitrate_bps",
    "latency_diff_s",
    "is_counter_nonmonotonic",
    "is_send_time_nonmonotonic",
    "is_recv_time_nonmonotonic",
    "is_latency_anomaly",
    "is_send_period_anomaly",
    "is_recv_period_anomaly",
]


def build_base_table(raw_df: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=CANONICAL_ORDER)

    df = raw_df.copy()
    df["stream_id"] = df["stream_id"].astype("category")
    df["topic"] = df["topic"].astype("category")

    parts: list[pd.DataFrame] = []
    for _, group in df.groupby("stream_id", observed=True, sort=False):
        g = group.sort_values("recv_ts").reset_index(drop=True)
        c = compute_counter_metrics(
            g["counter"],
            modulus=config.counter_modulus or 2**config.counter_bits,
            wrap=config.counter_wrap,
        )
        g = pd.concat([g, c], axis=1)
        g["latency_s"] = g["recv_ts"] - g["send_ts"]
        g["send_dt_s"] = g["send_ts"].diff()
        g["recv_dt_s"] = g["recv_ts"].diff()
        g["send_freq_hz"] = 1.0 / g["send_dt_s"].replace(0, np.nan)
        g["recv_freq_hz"] = 1.0 / g["recv_dt_s"].replace(0, np.nan)
        expected = config.expected_period_s
        if expected is None:
            g["send_period_error_s"] = np.nan
            g["recv_period_error_s"] = np.nan
        else:
            g["send_period_error_s"] = g["send_dt_s"] - expected
            g["recv_period_error_s"] = g["recv_dt_s"] - expected
        g["send_bitrate_bps"] = (g["size_bytes"] * 8.0) / g["send_dt_s"].replace(0, np.nan)
        g["recv_bitrate_bps"] = (g["size_bytes"] * 8.0) / g["recv_dt_s"].replace(0, np.nan)
        g["latency_diff_s"] = g["latency_s"].diff()
        g["is_counter_nonmonotonic"] = g["counter_delta_raw"].lt(0)
        g["is_send_time_nonmonotonic"] = g["send_dt_s"].lt(0)
        g["is_recv_time_nonmonotonic"] = g["recv_dt_s"].lt(0)
        g["is_latency_anomaly"] = g["latency_s"].gt(config.latency_warn_s)
        g["is_send_period_anomaly"] = g["send_period_error_s"].abs().gt(config.period_error_warn_s)
        g["is_recv_period_anomaly"] = g["recv_period_error_s"].abs().gt(config.period_error_warn_s)
        parts.append(g)

    base = pd.concat(parts, ignore_index=True)
    for col in CANONICAL_ORDER:
        if col not in base.columns:
            base[col] = np.nan
    return base[CANONICAL_ORDER]
