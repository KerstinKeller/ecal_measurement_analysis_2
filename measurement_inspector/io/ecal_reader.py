from __future__ import annotations

import importlib
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
        rows = list(self.iter_messages(measurement_path))
        if not rows:
            return pd.DataFrame(columns=["stream_id", "topic", "message_count"])
        frame = pd.DataFrame(rows)
        return (
            frame.groupby(["stream_id", "topic"], dropna=False)
            .size()
            .reset_index(name="message_count")
            .sort_values(["stream_id", "topic"], kind="stable")
            .reset_index(drop=True)
        )

    def iter_messages(
        self,
        measurement_path: str,
        stream_ids: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> Iterable[dict]:
        path = Path(measurement_path)
        if not path.exists():
            raise FileNotFoundError(f"Measurement path does not exist: {measurement_path}")

        stream_filter = set(stream_ids) if stream_ids else None
        topic_filter = set(topics) if topics else None

        meas = self._open_measurement(path)
        channel_counter = 0
        try:
            for channel_name in self._iter_channel_names(meas):
                if stream_filter and channel_name not in stream_filter:
                    continue
                if topic_filter and channel_name not in topic_filter:
                    continue
                for row in self._iter_channel_messages(meas, channel_name, channel_counter):
                    channel_counter += 1
                    yield row
        finally:
            close = getattr(meas, "close", None)
            if callable(close):
                close()

    def _open_measurement(self, path: Path):
        try:
            module = importlib.import_module("ecal.measurement.hdf5")
        except ImportError as exc:
            raise NotImplementedError(
                "eclipse-ecal measurement API is not installed. Install package 'eclipse-ecal>=6.1'."
            ) from exc

        meas_cls = getattr(module, "Meas", None)
        if meas_cls is None:
            raise NotImplementedError("ecal.measurement.hdf5.Meas is not available in the installed eclipse-ecal package.")

        measurement = self._build_measurement_instance(meas_cls, path)
        is_ok = getattr(measurement, "is_ok", None)
        if callable(is_ok) and not bool(is_ok()):
            raise RuntimeError(f"Failed to open eCAL measurement at {path}")
        return measurement

    @staticmethod
    def _build_measurement_instance(meas_cls, path: Path):
        try:
            return meas_cls(str(path), 0)
        except TypeError:
            measurement = meas_cls()
            open_fn = getattr(measurement, "open", None)
            if not callable(open_fn):
                return measurement
            open_result = open_fn(str(path), 0)
            if isinstance(open_result, bool) and not open_result:
                raise RuntimeError(f"Failed to open eCAL measurement at {path}")
            return measurement

    @staticmethod
    def _iter_channel_names(measurement) -> Iterable[str]:
        channel_names = measurement.get_channel_names()
        for channel_name in channel_names or []:
            yield str(channel_name)

    def _iter_channel_messages(self, measurement, channel_name: str, base_counter: int) -> Iterable[dict]:
        entry_infos = measurement.get_entries_info(channel_name)
        entries = self._normalize_entries_info(entry_infos)
        next_counter = base_counter
        for entry in entries:
            parsed = self._parse_entry_info(entry)
            entry_id = parsed["entry_id"]
            snd_ts = parsed["snd_timestamp"]
            rcv_ts = parsed["rcv_timestamp"]
            counter_value = parsed["counter"] if parsed["counter"] is not None else next_counter
            size_bytes = self._fetch_entry_size(measurement, entry_id)
            next_counter += 1

            yield {
                "stream_id": channel_name,
                "topic": channel_name,
                "send_ts": float(self._coerce_scalar(snd_ts)),
                "recv_ts": float(self._coerce_scalar(rcv_ts)),
                "counter": int(self._coerce_scalar(counter_value)),
                "size_bytes": int(size_bytes),
            }

    @staticmethod
    def _normalize_entries_info(entry_infos: object) -> list[object]:
        if isinstance(entry_infos, tuple) and len(entry_infos) == 2 and isinstance(entry_infos[0], bool):
            ok, entries = entry_infos
            return list(entries) if ok and entries is not None else []
        if entry_infos is None:
            return []
        return list(entry_infos)

    def _extract_entry_field(self, entry: object, *names: str, default: object | None = None) -> object:
        if isinstance(entry, dict):
            lowered = {k.lower(): v for k, v in entry.items()}
            for name in names:
                if name in entry:
                    return entry[name]
                if name.lower() in lowered:
                    return lowered[name.lower()]
        else:
            for name in names:
                value = getattr(entry, name, None)
                if value is not None:
                    return value
        if isinstance(entry, (tuple, list)):
            if "entry_id" in names or "id" in names:
                return entry[0] if len(entry) > 0 else default
            if "snd_timestamp" in names or "send_timestamp" in names or "snd_ts" in names:
                return entry[1] if len(entry) > 1 else default
            if "rcv_timestamp" in names or "recv_timestamp" in names or "rcv_ts" in names:
                return entry[2] if len(entry) > 2 else default
            if "counter" in names or "clock" in names:
                return entry[3] if len(entry) > 3 else default
        if default is not None:
            return default
        requested = ", ".join(names)
        raise ValueError(f"Could not extract any of [{requested}] from measurement entry info: {entry!r}")

    def _parse_entry_info(self, entry: object) -> dict[str, object]:
        """Parse eCAL entry-info records into a stable structure.

        Preferred sources are mapping/object attributes. Tuple/list extraction is
        only used as a compatibility fallback for bindings that expose positional
        entry records in `(entry_id, snd_timestamp, rcv_timestamp, counter?)`.
        """
        if isinstance(entry, (tuple, list)):
            if len(entry) < 3:
                raise ValueError(f"Tuple/list entry-info must contain at least 3 values, got: {entry!r}")
            return {
                "entry_id": entry[0],
                "snd_timestamp": entry[1],
                "rcv_timestamp": entry[2],
                "counter": entry[3] if len(entry) > 3 else None,
            }

        return {
            "entry_id": self._extract_entry_field(entry, "entry_id", "id"),
            "snd_timestamp": self._extract_entry_field(entry, "snd_timestamp", "send_timestamp", "snd_ts"),
            "rcv_timestamp": self._extract_entry_field(entry, "rcv_timestamp", "recv_timestamp", "rcv_ts"),
            "counter": self._extract_entry_field(entry, "counter", "clock", default=None),
        }

    def _fetch_entry_size(self, measurement, entry_id: object) -> int:
        size = measurement.get_entry_data_size(entry_id)
        if isinstance(size, tuple) and len(size) == 2 and isinstance(size[0], bool):
            ok, value = size
            if not ok:
                return 0
            return int(self._coerce_scalar(value))
        return int(self._coerce_scalar(size))

    @staticmethod
    def _coerce_scalar(value: object) -> object:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if hasattr(value, "item"):
            try:
                return value.item()
            except ValueError:
                return value
        return value


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
