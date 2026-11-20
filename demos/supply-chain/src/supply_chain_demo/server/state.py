"""Shared state, fault-injection configuration, and call metrics for the mock server."""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class FaultConfig(BaseModel):
    """Mutable latency and failure-injection knobs controlled via /admin/faults."""

    erp_latency_ms: int = Field(default=600, ge=0, le=15000)
    freight_latency_min_ms: int = Field(default=600, ge=0, le=15000)
    freight_latency_max_ms: int = Field(default=1100, ge=0, le=15000)
    news_latency_ms: int = Field(default=800, ge=0, le=15000)
    compliance_latency_ms: int = Field(default=400, ge=0, le=15000)
    freight_failure_mode: Literal["healthy", "flaky", "outage_503", "rate_limit_429"] = "healthy"
    freight_error_rate: float = Field(default=0.4, ge=0.0, le=1.0)
    freight_failure_latency_ms: int = Field(default=1200, ge=0, le=15000)


class FaultUpdate(BaseModel):
    """Partial update schema for POST /admin/faults."""

    erp_latency_ms: int | None = Field(default=None, ge=0, le=15000)
    freight_latency_min_ms: int | None = Field(default=None, ge=0, le=15000)
    freight_latency_max_ms: int | None = Field(default=None, ge=0, le=15000)
    news_latency_ms: int | None = Field(default=None, ge=0, le=15000)
    compliance_latency_ms: int | None = Field(default=None, ge=0, le=15000)
    freight_failure_mode: Literal["healthy", "flaky", "outage_503", "rate_limit_429"] | None = None
    freight_error_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    freight_failure_latency_ms: int | None = Field(default=None, ge=0, le=15000)


class CallRecord(BaseModel):
    """Single HTTP request telemetry entry captured by the mock server."""

    request_id: str
    service: str
    endpoint: str
    params: dict[str, Any]
    started_at: float
    ended_at: float
    duration_ms: float
    status_code: int
    response_chars: int


class ServerState:
    """Thread-safe container holding live fault configuration and recorded call traces."""

    def __init__(self, initial_faults: FaultConfig | None = None) -> None:
        self._lock = threading.Lock()
        self._faults = initial_faults.model_copy() if initial_faults else FaultConfig()
        self._records: list[CallRecord] = []
        self._freight_counter: int = 0

    def get_faults(self) -> FaultConfig:
        with self._lock:
            return self._faults.model_copy()

    def update_faults(self, updates: dict[str, Any]) -> FaultConfig:
        with self._lock:
            merged = self._faults.model_dump()
            for key, value in updates.items():
                if value is not None:
                    merged[key] = value
            if merged["freight_latency_max_ms"] < merged["freight_latency_min_ms"]:
                merged["freight_latency_max_ms"] = merged["freight_latency_min_ms"]
            self._faults = FaultConfig(**merged)
            return self._faults.model_copy()

    def reset_faults(self) -> FaultConfig:
        with self._lock:
            self._faults = FaultConfig()
            return self._faults.model_copy()

    def next_freight_seq(self) -> int:
        with self._lock:
            self._freight_counter += 1
            return self._freight_counter

    def record_call(
        self,
        *,
        service: str,
        endpoint: str,
        params: dict[str, Any],
        started_at: float,
        ended_at: float | None = None,
        status_code: int,
        response_chars: int,
    ) -> None:
        finished = ended_at if ended_at is not None else time.perf_counter()
        record = CallRecord(
            request_id=uuid.uuid4().hex[:8],
            service=service,
            endpoint=endpoint,
            params=params,
            started_at=started_at,
            ended_at=finished,
            duration_ms=round((finished - started_at) * 1000.0, 2),
            status_code=status_code,
            response_chars=response_chars,
        )
        with self._lock:
            self._records.append(record)

    def reset_metrics(self) -> None:
        with self._lock:
            self._records.clear()

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            records = list(self._records)
            faults = self._faults.model_dump()

        calls_by_service: dict[str, int] = {}
        errors_by_service: dict[str, int] = {}
        total_response_chars = 0

        for rec in records:
            calls_by_service[rec.service] = calls_by_service.get(rec.service, 0) + 1
            if rec.status_code >= 400:
                errors_by_service[rec.service] = errors_by_service.get(rec.service, 0) + 1
            total_response_chars += rec.response_chars

        if records:
            t0 = min(r.started_at for r in records)
            t_end = max(r.ended_at for r in records)
            window_span_ms = round((t_end - t0) * 1000.0, 2)
        else:
            t0 = 0.0
            window_span_ms = 0.0

        serialized_calls = [
            {
                "request_id": r.request_id,
                "service": r.service,
                "endpoint": r.endpoint,
                "params": r.params,
                "start_offset_ms": round((r.started_at - t0) * 1000.0, 2) if records else 0.0,
                "end_offset_ms": round((r.ended_at - t0) * 1000.0, 2) if records else 0.0,
                "duration_ms": r.duration_ms,
                "status_code": r.status_code,
                "response_chars": r.response_chars,
            }
            for r in records
        ]

        return {
            "total_calls": len(records),
            "calls_by_service": calls_by_service,
            "errors_by_service": errors_by_service,
            "total_errors": sum(errors_by_service.values()),
            "total_response_chars": total_response_chars,
            "window_span_ms": window_span_ms,
            "faults": faults,
            "calls": serialized_calls,
        }
