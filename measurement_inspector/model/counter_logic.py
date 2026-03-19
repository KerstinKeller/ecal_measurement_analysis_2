from __future__ import annotations

import numpy as np
import pandas as pd


def compute_counter_metrics(
    counters: pd.Series,
    *,
    modulus: int,
    wrap: bool,
) -> pd.DataFrame:
    prev = counters.shift(1)
    raw = counters - prev
    norm = raw.copy()
    if wrap:
        norm = ((counters - prev) % modulus).astype("float64")
        norm.iloc[0] = np.nan

    lost = (norm - 1).clip(lower=0)
    lost = lost.fillna(0).astype("int64")

    is_duplicate = norm.eq(0)
    is_backward = raw.lt(0) & (~wrap)
    is_gap = lost.gt(0)
    is_ambiguous_jump = raw.lt(0) & wrap & norm.gt(1)

    return pd.DataFrame(
        {
            "counter_delta_raw": raw,
            "counter_delta_norm": norm,
            "lost_msgs": lost,
            "is_gap": is_gap,
            "is_counter_duplicate": is_duplicate,
            "is_counter_backward": is_backward,
            "is_counter_ambiguous_jump": is_ambiguous_jump,
        }
    )
