import pandas as pd

from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.model.derived_metrics import build_base_table
from measurement_inspector.model.summaries import loss_events, stream_summary, time_bucket_summary


def _base():
    raw = pd.DataFrame(
        {
            "stream_id": ["s1", "s1", "s1", "s2", "s2"],
            "topic": ["a", "a", "a", "b", "b"],
            "send_ts": [0.0, 1.0, 2.0, 0.0, 1.0],
            "recv_ts": [0.1, 1.1, 2.2, 0.2, 1.2],
            "counter": [1, 2, 4, 5, 6],
            "size_bytes": [10, 10, 10, 20, 20],
        }
    )
    return build_base_table(raw, AnalysisConfig(expected_freq_hz=1.0, bucket_size_s=1))


def test_stream_summary_and_loss_events():
    base = _base()
    s = stream_summary(base)
    assert len(s) == 2
    s1 = s[s["stream_id"] == "s1"].iloc[0]
    assert s1["total_lost_msgs"] == 1

    events = loss_events(base)
    assert len(events) == 1
    assert events.iloc[0]["lost_msgs"] == 1


def test_time_bucket_summary():
    base = _base()
    b = time_bucket_summary(base, AnalysisConfig(expected_freq_hz=1.0, bucket_size_s=1))
    assert {"bucket_start", "msg_count", "lost_msgs_sum"}.issubset(b.columns)
