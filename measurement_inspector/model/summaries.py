from __future__ import annotations

import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig


def stream_summary(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame()

    grp = base.groupby(["stream_id", "topic"], observed=True)
    out = grp.agg(
        msg_count=("counter", "count"),
        first_recv_ts=("recv_ts", "min"),
        last_recv_ts=("recv_ts", "max"),
        total_lost_msgs=("lost_msgs", "sum"),
        gap_count=("is_gap", "sum"),
        latency_p50_s=("latency_s", lambda s: s.quantile(0.50)),
        latency_p95_s=("latency_s", lambda s: s.quantile(0.95)),
        latency_p99_s=("latency_s", lambda s: s.quantile(0.99)),
        max_latency_s=("latency_s", "max"),
        mean_send_period_s=("send_dt_s", "mean"),
        mean_recv_period_s=("recv_dt_s", "mean"),
        send_period_std_s=("send_dt_s", "std"),
        recv_period_std_s=("recv_dt_s", "std"),
        max_recv_period_error_s=("recv_period_error_s", lambda s: s.abs().max()),
        size_mean_bytes=("size_bytes", "mean"),
        size_p95_bytes=("size_bytes", lambda s: s.quantile(0.95)),
    ).reset_index()
    out["duration_s"] = out["last_recv_ts"] - out["first_recv_ts"]
    out["loss_rate_est"] = out["total_lost_msgs"] / (out["total_lost_msgs"] + out["msg_count"]).clip(lower=1)
    return out


def time_bucket_summary(base: pd.DataFrame, config: AnalysisConfig) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame()

    df = base.copy()
    axis = config.default_time_axis
    bucket = (df[axis] // config.bucket_size_s) * config.bucket_size_s
    df["bucket_start"] = bucket
    grp = df.groupby(["bucket_start", "stream_id", "topic"], observed=True)
    out = grp.agg(
        msg_count=("counter", "count"),
        lost_msgs_sum=("lost_msgs", "sum"),
        latency_mean_s=("latency_s", "mean"),
        latency_p95_s=("latency_s", lambda s: s.quantile(0.95)),
        recv_period_mean_s=("recv_dt_s", "mean"),
        recv_period_std_s=("recv_dt_s", "std"),
        bitrate_sum_bps=("recv_bitrate_bps", "sum"),
        anomaly_count=("is_latency_anomaly", "sum"),
    ).reset_index()
    return out


def loss_events(base: pd.DataFrame) -> pd.DataFrame:
    if base.empty:
        return pd.DataFrame()

    events = base.loc[base["lost_msgs"] > 0].copy()
    events["prev_recv_ts"] = events.groupby("stream_id", observed=True)["recv_ts"].shift(1)
    events["curr_recv_ts"] = events["recv_ts"]
    events["prev_counter"] = events.groupby("stream_id", observed=True)["counter"].shift(1)
    events["curr_counter"] = events["counter"]
    events["recv_gap_s"] = events["recv_dt_s"]
    events["send_gap_s"] = events["send_dt_s"]
    events["latency_before_s"] = events.groupby("stream_id", observed=True)["latency_s"].shift(1)
    events["latency_after_s"] = events["latency_s"]
    return events[
        [
            "stream_id",
            "topic",
            "prev_recv_ts",
            "curr_recv_ts",
            "prev_counter",
            "curr_counter",
            "lost_msgs",
            "recv_gap_s",
            "send_gap_s",
            "latency_before_s",
            "latency_after_s",
        ]
    ]
