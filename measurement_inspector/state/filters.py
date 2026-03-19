from __future__ import annotations

import pandas as pd

from measurement_inspector.state.selection import SelectionState


def apply_selection(base: pd.DataFrame, state: SelectionState, time_axis: str = "recv_ts") -> pd.DataFrame:
    df = base
    if state.selected_streams:
        df = df[df["stream_id"].isin(state.selected_streams)]
    if state.selected_topics:
        df = df[df["topic"].isin(state.selected_topics)]
    if state.time_range is not None:
        start, end = state.time_range
        df = df[df[time_axis].between(start, end)]
    return df
