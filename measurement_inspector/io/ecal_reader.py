from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

import pandas as pd

from dataclasses import asdict

from measurement_inspector.io.record_models import MessageRecord


class MeasurementAdapter(Protocol):
    def list_streams(self, measurement_path: str) -> pd.DataFrame: ...

    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[dict]: ...


class EcalHdfAdapter:
    """Adapter boundary for eCAL measurement parsing.

    This class intentionally keeps any eCAL-specific API usage isolated.
    The default implementation tries to import a reader package and fails
    with a clear action message when not available.
    """

    def list_streams(self, measurement_path: str) -> pd.DataFrame:
        path = Path(measurement_path)
        if not path.exists():
            raise FileNotFoundError(f"Measurement path does not exist: {measurement_path}")

        # Placeholder metadata to keep the app runnable before exact API wiring.
        return pd.DataFrame(columns=["stream_id", "topic", "message_count"])

    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[dict]:
        path = Path(measurement_path)
        if not path.exists():
            raise FileNotFoundError(f"Measurement path does not exist: {measurement_path}")

        raise NotImplementedError(
            "Integrate this method with your installed eclipse-ecal>=6.1 measurement API and "
            "decode payloads into normalized records."
        )


def records_to_frame(records: Iterable[MessageRecord | dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for record in records:
        if isinstance(record, MessageRecord):
            rows.append(asdict(record))
        else:
            rows.append(record)
    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=["stream_id", "topic", "send_ts", "recv_ts", "counter", "size_bytes"]
        )
    return frame
