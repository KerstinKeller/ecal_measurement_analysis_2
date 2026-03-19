from __future__ import annotations

from types import SimpleNamespace

from measurement_inspector.io.ecal_reader import EcalHdfAdapter


class FakeMeas:
    def __init__(self, path: str, access: int):
        self.path = path
        self.access = access
        self.closed = False
        self._entries = {
            "camera/front": [
                {"id": 1, "snd_timestamp": 1_000_000, "rcv_timestamp": 1_020_000, "counter": 10},
                (2, 1_100_000, 1_120_000, 11),
            ],
            "imu/main": [
                {"id": 3, "snd_timestamp": 2_000_000, "rcv_timestamp": 2_010_000, "counter": 20},
            ],
        }
        self._sizes = {1: 1024, 2: 2048, 3: 256}

    def is_ok(self) -> bool:
        return True

    def get_channel_names(self):
        return list(self._entries.keys())

    def get_entries_info(self, channel_name: str):
        return self._entries[channel_name]

    def get_entry_data_size(self, entry_id: int):
        return self._sizes[entry_id]

    def close(self):
        self.closed = True


def test_iter_messages_uses_ecal_api(monkeypatch, tmp_path):
    measurement_dir = tmp_path / "measurement"
    measurement_dir.mkdir()

    monkeypatch.setattr(
        "measurement_inspector.io.ecal_reader.importlib.import_module",
        lambda _: SimpleNamespace(Meas=FakeMeas),
    )

    adapter = EcalHdfAdapter()
    rows = list(adapter.iter_messages(str(measurement_dir), topics=["camera/front"]))

    assert len(rows) == 2
    assert rows[0] == {
        "stream_id": "camera/front",
        "topic": "camera/front",
        "send_ts": 1_000_000.0,
        "recv_ts": 1_020_000.0,
        "counter": 10,
        "size_bytes": 1024,
    }
    assert rows[1]["size_bytes"] == 2048
    assert rows[1]["send_ts"] == 1_100_000.0
    assert rows[1]["recv_ts"] == 1_120_000.0


def test_list_streams_aggregates_counts(monkeypatch, tmp_path):
    measurement_dir = tmp_path / "measurement"
    measurement_dir.mkdir()

    monkeypatch.setattr(
        "measurement_inspector.io.ecal_reader.importlib.import_module",
        lambda _: SimpleNamespace(Meas=FakeMeas),
    )

    adapter = EcalHdfAdapter()
    streams = adapter.list_streams(str(measurement_dir))

    assert len(streams) == 2
    assert streams.loc[streams["stream_id"] == "camera/front", "message_count"].item() == 2
    assert streams.loc[streams["stream_id"] == "imu/main", "message_count"].item() == 1
