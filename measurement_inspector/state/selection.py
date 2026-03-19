from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SelectionState:
    selected_streams: list[str] = field(default_factory=list)
    selected_topics: list[str] = field(default_factory=list)
    time_range: tuple[float, float] | None = None
    anomaly_types: list[str] = field(default_factory=list)
