from __future__ import annotations

import hvplot.pandas  # noqa: F401
import panel as pn


def build_overview(stream_summary_df, bucket_df):
    kpi = pn.Row(
        pn.indicators.Number(name="Streams", value=int(stream_summary_df["stream_id"].nunique() if not stream_summary_df.empty else 0)),
        pn.indicators.Number(name="Messages", value=int(stream_summary_df["msg_count"].sum() if not stream_summary_df.empty else 0)),
        pn.indicators.Number(name="Inferred losses", value=int(stream_summary_df["total_lost_msgs"].sum() if not stream_summary_df.empty else 0)),
    )

    summary_table = pn.widgets.Tabulator(stream_summary_df, pagination="local", page_size=12, sizing_mode="stretch_width")

    plots = pn.Column()
    if not stream_summary_df.empty:
        top_loss = stream_summary_df.sort_values("total_lost_msgs", ascending=False).head(10)
        plots.append(top_loss.hvplot.bar(x="stream_id", y="total_lost_msgs", title="Top streams by inferred loss"))
        top_lat = stream_summary_df.sort_values("latency_p95_s", ascending=False).head(10)
        plots.append(top_lat.hvplot.bar(x="stream_id", y="latency_p95_s", title="Top streams by latency p95"))
    if not bucket_df.empty:
        heat = bucket_df.hvplot.heatmap(x="bucket_start", y="stream_id", C="anomaly_count", title="Anomaly density")
        plots.append(heat)

    return pn.Column("## Overview", kpi, summary_table, plots, sizing_mode="stretch_both")
