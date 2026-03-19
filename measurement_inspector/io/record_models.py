from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MessageRecord:
    stream_id: str
    topic: str
    send_ts: float
    recv_ts: float
    counter: int
    size_bytes: int
