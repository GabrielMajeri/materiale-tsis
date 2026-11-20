"""Benchmark reporting, ASCII HTTP waterfalls, and cross-stage comparison tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.table import Table


@dataclass
class RunReport:
    """Aggregated latency and mock-server HTTP metrics for one PO evaluation run."""

    label: str
    wall_time_s: float
    total_http_calls: int
    calls_by_service: dict[str, int]
    errors_by_service: dict[str, int]
    total_http_errors: int
    server_window_span_ms: float
    calls: list[dict[str, Any]]
    final_decision: str


def build_run_report(
    label: str,
    wall_time_s: float,
    server_metrics: dict[str, Any],
    final_decision: str,
) -> RunReport:
    """Build a RunReport from wall-clock timing and mock-server HTTP metrics."""
    return RunReport(
        label=label,
        wall_time_s=round(wall_time_s, 3),
        total_http_calls=int(server_metrics.get("total_calls", 0)),
        calls_by_service=dict(server_metrics.get("calls_by_service", {})),
        errors_by_service=dict(server_metrics.get("errors_by_service", {})),
        total_http_errors=int(server_metrics.get("total_errors", 0)),
        server_window_span_ms=float(server_metrics.get("window_span_ms", 0.0)),
        calls=list(server_metrics.get("calls", [])),
        final_decision=final_decision,
    )


def print_report(report: RunReport, console: Console | None = None) -> None:
    """Display a summary table for a single evaluation run."""
    out = console or Console()
    table = Table(title=f"Run Report — {report.label}", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    service_breakdown = ", ".join(
        f"{svc}: {cnt}" for svc, cnt in sorted(report.calls_by_service.items())
    ) or "none"
    error_breakdown = ", ".join(
        f"{svc}: {cnt}" for svc, cnt in sorted(report.errors_by_service.items())
    ) or "0"

    table.add_row("End-to-End Wall Time", f"{report.wall_time_s:.2f} s")
    table.add_row("Server I/O Window Span", f"{report.server_window_span_ms:.0f} ms")
    table.add_row("Server HTTP Calls", f"{report.total_http_calls} ({service_breakdown})")
    table.add_row("Server HTTP Errors (429/503)", f"{report.total_http_errors} ({error_breakdown})")
    out.print(table)


def render_waterfall(report: RunReport, width: int = 50) -> str:
    """Render an ASCII Gantt waterfall from server-recorded HTTP call offsets and durations."""
    if not report.calls:
        return f"HTTP Waterfall: {report.label} (0 server HTTP calls — 100% cache/circuit hit)"

    sorted_calls = sorted(report.calls, key=lambda c: (float(c["start_offset_ms"]), float(c["end_offset_ms"])))
    max_end = max(float(c["end_offset_ms"]) for c in sorted_calls)
    span_ms = max(max_end, 1.0)

    lines = [
        f"HTTP Waterfall: {report.label} "
        f"(server span: {report.server_window_span_ms:.0f} ms, {len(sorted_calls)} calls)"
    ]
    for call in sorted_calls:
        start_ms = float(call["start_offset_ms"])
        duration_ms = float(call["duration_ms"])
        end_ms = float(call["end_offset_ms"])
        service = str(call["service"])
        status = int(call["status_code"])

        start_col = min(width - 1, max(0, int((start_ms / span_ms) * width)))
        end_col = min(width, max(start_col + 1, int((end_ms / span_ms) * width)))
        bar = ("." * start_col) + ("#" * (end_col - start_col)) + ("." * (width - end_col))
        err_flag = " ERR" if status >= 400 else ""
        param_summary = ",".join(f"{v}" for v in (call.get("params") or {}).values())
        lines.append(
            f"[{service:<10}] {start_ms / 1000.0:5.2f}s |{bar}| "
            f"{duration_ms:5.0f}ms ({status}{err_flag}) {param_summary}"
        )
    return "\n".join(lines)


def compare_reports(reports: list[RunReport], console: Console | None = None) -> None:
    """Print a side-by-side comparison table across optimization stages."""
    out = console or Console()
    if not reports:
        out.print("[yellow]No RunReports provided to compare.[/yellow]")
        return

    baseline_time = max(reports[0].wall_time_s, 0.001)
    table = Table(
        title="Optimization Benchmark Comparison",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("Stage", style="bold")
    table.add_column("Wall Time", justify="right")
    table.add_column("Speedup", justify="right")
    table.add_column("Server Span", justify="right")
    table.add_column("HTTP Calls", justify="right")
    table.add_column("HTTP Errors", justify="right")

    for r in reports:
        speedup = baseline_time / max(r.wall_time_s, 0.001)
        table.add_row(
            r.label,
            f"{r.wall_time_s:.2f}s",
            f"{speedup:.2f}x",
            f"{r.server_window_span_ms:.0f} ms",
            str(r.total_http_calls),
            str(r.total_http_errors),
        )
    out.print(table)
