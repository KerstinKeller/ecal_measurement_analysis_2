from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class AnalysisConfig(BaseModel):
    counter_bits: int = Field(default=16, ge=1)
    counter_wrap: bool = True
    counter_modulus: int | None = Field(default=None, ge=2)
    expected_freq_hz: float | None = Field(default=None, gt=0)
    expected_period_s: float | None = Field(default=None, gt=0)
    latency_warn_s: float = Field(default=0.05, ge=0)
    period_error_warn_s: float = Field(default=0.01, ge=0)
    bucket_size_s: int = Field(default=1, ge=1)
    max_raw_points_before_rasterize: int = Field(default=200_000, ge=1000)
    default_time_axis: Literal["recv_ts", "send_ts"] = "recv_ts"

    @model_validator(mode="after")
    def _normalize_period_freq(self) -> "AnalysisConfig":
        if self.counter_modulus is None:
            self.counter_modulus = 2**self.counter_bits
        if self.expected_period_s is None and self.expected_freq_hz is not None:
            self.expected_period_s = 1.0 / self.expected_freq_hz
        if self.expected_freq_hz is None and self.expected_period_s is not None:
            self.expected_freq_hz = 1.0 / self.expected_period_s
        return self
