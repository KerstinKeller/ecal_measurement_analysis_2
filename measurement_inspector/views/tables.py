from __future__ import annotations

import panel as pn


def build_event_table(base):
    columns = [
        "recv_ts",
        "send_ts",
        "counter",
        "counter_delta_norm",
        "lost_msgs",
        "latency_s",
        "send_dt_s",
        "recv_dt_s",
        "size_bytes",
        "is_latency_anomaly",
        "is_send_period_anomaly",
        "is_recv_period_anomaly",
    ]
    available_cols = [c for c in columns if c in base.columns]
    return pn.Column(
        "## Raw event table",
        pn.widgets.Tabulator(base[available_cols], pagination="local", page_size=20, sizing_mode="stretch_both"),
        sizing_mode="stretch_both",
    )
