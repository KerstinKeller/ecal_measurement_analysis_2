import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.model.derived_metrics import build_base_table


def test_derived_metrics_basic_columns_and_period_error():
    raw = pd.DataFrame(
        {
            "stream_id": ["s1", "s1", "s1"],
            "topic": ["t", "t", "t"],
            "send_ts": [0.0, 1.0, 2.0],
            "recv_ts": [0.1, 1.1, 2.3],
            "counter": [1, 2, 4],
            "size_bytes": [100, 100, 100],
        }
    )
    cfg = AnalysisConfig(expected_freq_hz=1.0)
    base = build_base_table(raw, cfg)

    assert set(["latency_s", "send_dt_s", "recv_dt_s", "lost_msgs"]).issubset(base.columns)
    assert base.loc[2, "lost_msgs"] == 1
    assert base.loc[1, "send_period_error_s"] == 0.0
    assert base.loc[2, "recv_period_error_s"] > 0.0
