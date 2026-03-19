import pandas as pd

from measurement_inspector.model.counter_logic import compute_counter_metrics


def test_counter_no_loss_and_single_loss():
    counters = pd.Series([1, 2, 4])
    out = compute_counter_metrics(counters, modulus=256, wrap=True)
    assert out.loc[1, "lost_msgs"] == 0
    assert out.loc[2, "lost_msgs"] == 1
    assert bool(out.loc[2, "is_gap"])


def test_counter_wraparound():
    counters = pd.Series([254, 255, 0, 1])
    out = compute_counter_metrics(counters, modulus=256, wrap=True)
    assert out.loc[2, "counter_delta_norm"] == 1
    assert out.loc[2, "lost_msgs"] == 0


def test_counter_backward_when_no_wrap():
    counters = pd.Series([10, 7])
    out = compute_counter_metrics(counters, modulus=256, wrap=False)
    assert bool(out.loc[1, "is_counter_backward"])
