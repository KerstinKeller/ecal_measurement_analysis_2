from __future__ import annotations

import hvplot.pandas  # noqa: F401
import panel as pn


def build_stream_detail(base):
    if base.empty:
        return pn.pane.Markdown("## Stream detail\nNo data for current selection.")

    latency = base.hvplot.line(x="recv_ts", y="latency_s", by="stream_id", title="Latency over time")
    recv_dt = base.hvplot.line(x="recv_ts", y="recv_dt_s", by="stream_id", title="Receive period")
    lost = base.loc[base["lost_msgs"] > 0].hvplot.scatter(
        x="recv_ts", y="lost_msgs", by="stream_id", title="Counter-gap events", marker="triangle"
    )
    size = base.hvplot.scatter(x="recv_ts", y="size_bytes", by="stream_id", title="Payload size")
    return pn.Column("## Stream detail", latency, recv_dt, lost, size, sizing_mode="stretch_both")
