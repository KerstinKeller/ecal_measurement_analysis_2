from __future__ import annotations

import panel as pn

from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.model.anomalies import anomaly_events
from measurement_inspector.model.summaries import loss_events, stream_summary, time_bucket_summary
from measurement_inspector.state.filters import apply_selection
from measurement_inspector.state.selection import SelectionState
from measurement_inspector.views.overview import build_overview
from measurement_inspector.views.stream_detail import build_stream_detail
from measurement_inspector.views.tables import build_event_table

pn.extension("tabulator")


def build_dashboard(base, config: AnalysisConfig):
    streams = sorted(str(s) for s in base["stream_id"].dropna().unique().tolist()) if not base.empty else []
    topics = sorted(str(t) for t in base["topic"].dropna().unique().tolist()) if not base.empty else []

    stream_widget = pn.widgets.MultiChoice(name="Streams", options=streams)
    topic_widget = pn.widgets.MultiChoice(name="Topics", options=topics)

    state = SelectionState()

    def _selected():
        state.selected_streams = stream_widget.value
        state.selected_topics = topic_widget.value
        filtered = apply_selection(base, state, time_axis=config.default_time_axis)
        ssum = stream_summary(filtered)
        bsum = time_bucket_summary(filtered, config)
        _ = loss_events(filtered)
        _ = anomaly_events(filtered)
        return pn.Tabs(
            ("Overview", build_overview(ssum, bsum)),
            ("Stream detail", build_stream_detail(filtered)),
            ("Events", build_event_table(filtered)),
            dynamic=True,
        )

    controls = pn.WidgetBox("# Filters", stream_widget, topic_widget)
    body = pn.bind(_selected)
    return pn.Row(controls, body, sizing_mode="stretch_both")
