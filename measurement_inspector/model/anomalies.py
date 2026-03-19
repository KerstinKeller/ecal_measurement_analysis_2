from __future__ import annotations

import pandas as pd


def anomaly_events(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame()

    rows: list[pd.DataFrame] = []
    mappings = [
        ("is_latency_anomaly", "latency", "latency_s"),
        ("is_send_period_anomaly", "send_period", "send_period_error_s"),
        ("is_recv_period_anomaly", "recv_period", "recv_period_error_s"),
    ]
    for flag, anomaly_type, value_col in mappings:
        subset = base.loc[base[flag]].copy()
        if subset.empty:
            continue
        subset["anomaly_type"] = anomaly_type
        subset["severity"] = subset[value_col].abs()
        subset["value"] = subset[value_col]
        subset["threshold"] = None
        subset["row_index"] = subset.index
        rows.append(subset[["stream_id", "topic", "recv_ts", "anomaly_type", "severity", "value", "threshold", "row_index"]])

    if not rows:
        return pd.DataFrame(columns=["stream_id", "topic", "recv_ts", "anomaly_type", "severity", "value", "threshold", "row_index"])
    return pd.concat(rows, ignore_index=True)
