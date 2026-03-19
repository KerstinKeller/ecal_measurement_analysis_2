from __future__ import annotations

from pathlib import Path

import pandas as pd
import panel as pn
import typer

from measurement_inspector.app import build_dashboard
from measurement_inspector.config.schema import AnalysisConfig
from measurement_inspector.io.ecal_reader import EcalHdfAdapter, records_to_frame
from measurement_inspector.model.derived_metrics import build_base_table
from measurement_inspector.model.summaries import stream_summary

app = typer.Typer(help="Inspect eCAL measurements locally via Panel.")


@app.command()
def main(
    measurement_path: Path,
    topic: list[str] | None = typer.Option(default=None),
    stream_id: list[str] | None = typer.Option(default=None),
    counter_bits: int = typer.Option(default=16),
    counter_wrap: bool = typer.Option(default=True),
    expected_rate_hz: float | None = typer.Option(default=None),
    expected_period_ms: float | None = typer.Option(default=None),
    open_browser: bool = typer.Option(default=True),
    port: int = typer.Option(default=0),
):
    """Run local measurement dashboard for one measurement path."""
    if not measurement_path.exists():
        raise typer.BadParameter(f"Path does not exist: {measurement_path}")

    cfg = AnalysisConfig(
        counter_bits=counter_bits,
        counter_wrap=counter_wrap,
        expected_freq_hz=expected_rate_hz,
        expected_period_s=(expected_period_ms / 1000.0) if expected_period_ms else None,
    )

    adapter = EcalHdfAdapter()
    try:
        raw_df = records_to_frame(adapter.iter_messages(str(measurement_path), stream_ids=stream_id, topics=topic))
    except NotImplementedError:
        typer.echo("eCAL adapter is a stub. Load cached CSV-style data for preview mode.")
        csv_path = measurement_path / "messages.csv"
        if csv_path.exists():
            raw_df = pd.read_csv(csv_path)
        else:
            raw_df = pd.DataFrame(columns=["stream_id", "topic", "send_ts", "recv_ts", "counter", "size_bytes"])

    base = build_base_table(raw_df, cfg)
    summary = stream_summary(base)
    typer.echo(f"Loaded {len(base)} messages across {summary['stream_id'].nunique() if not summary.empty else 0} streams")

    dashboard = build_dashboard(base, cfg)
    pn.serve(dashboard, show=open_browser, port=port, title="Measurement Inspector")


if __name__ == "__main__":
    app()
