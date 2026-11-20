"""Tests for the FastAPI mock enterprise microservice server and Jupyter launcher."""

from __future__ import annotations

import socket
from collections.abc import Iterator

import httpx
import pytest

from supply_chain_demo.server.launcher import MockEnterpriseServer, start_mock_server


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def mock_server() -> Iterator[MockEnterpriseServer]:
    port = _get_free_port()
    server = start_mock_server(host="127.0.0.1", port=port)
    # Speed up latency slightly for fast unit tests while keeping realistic structure
    server.set_faults(
        erp_latency_ms=30,
        freight_latency_min_ms=25,
        freight_latency_max_ms=40,
        news_latency_ms=30,
        compliance_latency_ms=20,
        freight_failure_latency_ms=40,
    )
    server.reset_metrics()
    try:
        yield server
    finally:
        server.stop()


def test_start_mock_server_is_idempotent(mock_server: MockEnterpriseServer) -> None:
    reused = start_mock_server(host=mock_server.host, port=mock_server.port, reset_state=False)
    assert reused is mock_server
    assert reused.is_running()


def test_erp_scorecard_sqlite_and_cache_headers(mock_server: MockEnterpriseServer) -> None:
    resp_204 = httpx.get(f"{mock_server.url}/api/erp/vendors/VND-204/scorecard", timeout=5.0)
    assert resp_204.status_code == 200
    assert resp_204.headers["cache-control"] == "public, max-age=86400"
    data_204 = resp_204.json()
    assert data_204["vendor_id"] == "VND-204"
    assert data_204["defect_rate_pct"] == pytest.approx(0.35, abs=0.05)
    assert data_204["on_time_delivery_pct"] >= 96.0
    assert data_204["certifications"]["iatf_16949_status"] == "ACTIVE"

    resp_309 = httpx.get(f"{mock_server.url}/api/erp/vendors/VND-309/scorecard", timeout=5.0)
    assert resp_309.status_code == 200
    data_309 = resp_309.json()
    assert data_309["defect_rate_pct"] == pytest.approx(2.40, abs=0.05)
    assert data_309["certifications"]["iatf_16949_status"] == "EXPIRED"

    resp_missing = httpx.get(f"{mock_server.url}/api/erp/vendors/VND-999/scorecard", timeout=5.0)
    assert resp_missing.status_code == 404


def test_freight_rates_dynamic_quotes_and_fault_injection(mock_server: MockEnterpriseServer) -> None:
    q1 = httpx.get(
        f"{mock_server.url}/api/freight/rates",
        params={"origin_port": "DEHAM", "dest_port": "ROCND"},
        timeout=5.0,
    )
    q2 = httpx.get(
        f"{mock_server.url}/api/freight/rates",
        params={"origin_port": "DEHAM", "dest_port": "ROCND"},
        timeout=5.0,
    )
    assert q1.status_code == 200
    assert q2.status_code == 200
    assert q1.headers["cache-control"] == "no-store"
    assert q1.json()["quote_id"] != q2.json()["quote_id"]

    # Inject 503 outage
    mock_server.set_faults(freight_failure_mode="outage_503")
    r_503 = httpx.get(
        f"{mock_server.url}/api/freight/rates",
        params={"origin_port": "CNSHA", "dest_port": "ROCND"},
        timeout=5.0,
    )
    assert r_503.status_code == 503

    # Inject 429 rate limit
    mock_server.set_faults(freight_failure_mode="rate_limit_429")
    r_429 = httpx.get(
        f"{mock_server.url}/api/freight/rates",
        params={"origin_port": "TRIZM", "dest_port": "ROCND"},
        timeout=5.0,
    )
    assert r_429.status_code == 429
    assert r_429.headers.get("retry-after") == "2"

    # Reset faults restores healthy responses
    mock_server.reset_faults()
    mock_server.set_faults(freight_latency_min_ms=10, freight_latency_max_ms=20)
    r_ok = httpx.get(
        f"{mock_server.url}/api/freight/rates",
        params={"origin_port": "ITTRS", "dest_port": "ROCND"},
        timeout=5.0,
    )
    assert r_ok.status_code == 200


@pytest.mark.parametrize(
    "region",
    [
        "south_china_sea_red_sea",
        "north_sea_danube",
        "black_sea_bosporus",
        "adriatic_mediterranean",
    ],
)
def test_news_vector_search_relevance_and_token_bloat(
    mock_server: MockEnterpriseServer, region: str
) -> None:
    resp = httpx.get(
        f"{mock_server.url}/api/news/disruptions",
        params={"region": region, "top_k": 3},
        timeout=5.0,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["bulletins"]) == 3
    assert all(b["region"] == region for b in data["bulletins"])
    # Each call is designed to produce ~2,000 tokens of verbose RAG payload
    assert 1800 <= data["approx_tokens"] <= 2350


def test_compliance_policy_and_admin_metrics(mock_server: MockEnterpriseServer) -> None:
    mock_server.reset_metrics()
    resp = httpx.get(
        f"{mock_server.url}/api/compliance/policies/automotive_semiconductors",
        timeout=5.0,
    )
    assert resp.status_code == 200
    assert resp.headers["cache-control"] == "public, max-age=31536000, immutable"
    policy = resp.json()
    assert policy["mandatory_thresholds"]["max_defect_rate_pct"] == 1.50
    assert policy["mandatory_thresholds"]["min_on_time_delivery_pct"] == 90.0

    metrics = mock_server.get_metrics()
    assert metrics["total_calls"] == 1
    assert metrics["calls_by_service"] == {"compliance": 1}

    mock_server.reset_metrics()
    assert mock_server.get_metrics()["total_calls"] == 0
