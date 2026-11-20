"""FastAPI mock enterprise microservice backend simulating ERP, Freight, News RAG, and Compliance."""

from __future__ import annotations

import asyncio
import json
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from supply_chain_demo.server.compliance_data import get_policy_for_category
from supply_chain_demo.server.erp_db import ERPDatabase
from supply_chain_demo.server.state import FaultUpdate, ServerState
from supply_chain_demo.server.vector_store import MaritimeBulletinIndex

_ROUTE_RATES: dict[tuple[str, str], dict[str, Any]] = {
    ("CNSHA", "ROCND"): {
        "carrier": "Maersk / Mediterranean Loop",
        "base_rate_usd_per_teu": 3650.0,
        "transit_days": 34,
        "route_note": "Cape of Good Hope diversion active; Suez transit suspended.",
    },
    ("DEHAM", "ROCND"): {
        "carrier": "Danube Intermodal / Short-Sea",
        "base_rate_usd_per_teu": 1890.0,
        "transit_days": 11,
        "route_note": "Hamburg rail-barge / short-sea lane operating normally.",
    },
    ("TRIZM", "ROCND"): {
        "carrier": "Aegean-Black Sea Feeder",
        "base_rate_usd_per_teu": 1320.0,
        "transit_days": 8,
        "route_note": "Subject to Bosporus Strait pilotage queue (1-3 days).",
    },
    ("ITTRS", "ROCND"): {
        "carrier": "Adriatic EU Green Feeder",
        "base_rate_usd_per_teu": 1740.0,
        "transit_days": 9,
        "route_note": "Trieste-Piraeus-Constanta intra-EU feeder operating normally.",
    },
}


def _jittered_delay_s(base_ms: int, jitter_ms: int) -> float:
    if base_ms <= 0:
        return 0.0
    ms = max(10.0, base_ms + random.uniform(-jitter_ms, jitter_ms))
    return ms / 1000.0


def create_app(state: ServerState | None = None) -> FastAPI:
    """Create the FastAPI app exposing all 4 enterprise services and admin fault controls."""
    shared_state = state or ServerState()
    erp_db = ERPDatabase()
    bulletin_index = MaritimeBulletinIndex()

    app = FastAPI(
        title="Supply Chain Mock Enterprise Services",
        version="0.1.0",
        description="Simulates slow ERP SQL, flaky Freight API, verbose Maritime RAG, and static Compliance rules.",
    )
    app.state.server_state = shared_state

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/erp/vendors/{vendor_id}/scorecard")
    async def get_vendor_scorecard(vendor_id: str) -> JSONResponse:
        started = time.perf_counter()
        faults = shared_state.get_faults()
        await asyncio.sleep(_jittered_delay_s(faults.erp_latency_ms, 40))

        scorecard = erp_db.query_vendor_scorecard(vendor_id)
        if scorecard is None:
            body = {"detail": f"Vendor '{vendor_id}' not found in ERP."}
            raw = json.dumps(body)
            shared_state.record_call(
                service="erp",
                endpoint=f"/api/erp/vendors/{vendor_id}/scorecard",
                params={"vendor_id": vendor_id},
                started_at=started,
                status_code=404,
                response_chars=len(raw),
            )
            return JSONResponse(content=body, status_code=404)

        raw = json.dumps(scorecard)
        shared_state.record_call(
            service="erp",
            endpoint=f"/api/erp/vendors/{vendor_id}/scorecard",
            params={"vendor_id": vendor_id},
            started_at=started,
            status_code=200,
            response_chars=len(raw),
        )
        return JSONResponse(
            content=scorecard,
            status_code=200,
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/api/freight/rates")
    async def get_live_freight_rates(
        origin_port: str = Query(..., description="Origin UN/LOCODE, e.g. DEHAM"),
        dest_port: str = Query(..., description="Destination UN/LOCODE, e.g. ROCND"),
    ) -> JSONResponse:
        started = time.perf_counter()
        faults = shared_state.get_faults()
        seq = shared_state.next_freight_seq()
        endpoint = "/api/freight/rates"
        params = {"origin_port": origin_port, "dest_port": dest_port}

        failure_status: int | None = None
        if faults.freight_failure_mode == "outage_503":
            failure_status = 503
        elif faults.freight_failure_mode == "rate_limit_429":
            failure_status = 429
        elif faults.freight_failure_mode == "flaky" and random.random() < faults.freight_error_rate:
            failure_status = 503 if seq % 2 == 0 else 429

        if failure_status == 503:
            await asyncio.sleep(faults.freight_failure_latency_ms / 1000.0)
            body = {
                "detail": "503 Service Unavailable: Upstream freight carrier quoting gateway timed out.",
                "origin_port": origin_port,
                "dest_port": dest_port,
            }
            shared_state.record_call(
                service="freight",
                endpoint=endpoint,
                params=params,
                started_at=started,
                status_code=503,
                response_chars=len(json.dumps(body)),
            )
            return JSONResponse(
                content=body,
                status_code=503,
                headers={"Cache-Control": "no-store"},
            )

        if failure_status == 429:
            await asyncio.sleep(0.05)
            body = {
                "detail": "429 Too Many Requests: Freight spot API rate limit exceeded. Retry after 2s.",
                "origin_port": origin_port,
                "dest_port": dest_port,
            }
            shared_state.record_call(
                service="freight",
                endpoint=endpoint,
                params=params,
                started_at=started,
                status_code=429,
                response_chars=len(json.dumps(body)),
            )
            return JSONResponse(
                content=body,
                status_code=429,
                headers={"Cache-Control": "no-store", "Retry-After": "2"},
            )

        latency_ms = random.uniform(faults.freight_latency_min_ms, faults.freight_latency_max_ms)
        await asyncio.sleep(max(0.01, latency_ms / 1000.0))

        route = _ROUTE_RATES.get(
            (origin_port.upper(), dest_port.upper()),
            {
                "carrier": "Global Spot Container Line",
                "base_rate_usd_per_teu": 2400.0,
                "transit_days": 15,
                "route_note": "Standard international container routing.",
            },
        )
        spot_delta = round(random.uniform(-65.0, 85.0), 2)
        payload = {
            "quote_id": f"QT-{uuid.uuid4().hex[:10].upper()}",
            "quoted_at": datetime.now(timezone.utc).isoformat(),
            "origin_port": origin_port.upper(),
            "dest_port": dest_port.upper(),
            "carrier": route["carrier"],
            "spot_rate_usd_per_teu": round(route["base_rate_usd_per_teu"] + spot_delta, 2),
            "estimated_transit_days": route["transit_days"],
            "valid_for_seconds": 60,
            "route_note": route["route_note"],
            "cache_hint": "Volatile spot quote (no-store); do not cache across procurement runs.",
        }
        raw = json.dumps(payload)
        shared_state.record_call(
            service="freight",
            endpoint=endpoint,
            params=params,
            started_at=started,
            status_code=200,
            response_chars=len(raw),
        )
        return JSONResponse(
            content=payload,
            status_code=200,
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/api/news/disruptions")
    async def scan_disruption_news(
        region: str = Query(..., description="Maritime corridor region identifier"),
        top_k: int = Query(default=3, ge=1, le=6),
    ) -> JSONResponse:
        started = time.perf_counter()
        faults = shared_state.get_faults()
        await asyncio.sleep(_jittered_delay_s(faults.news_latency_ms, 50))

        matches = bulletin_index.search(region=region, top_k=top_k)
        payload: dict[str, Any] = {
            "region_query": region,
            "top_k": top_k,
            "bulletins": matches,
        }
        serialized = json.dumps(payload)
        payload["approx_tokens"] = len(serialized) // 4
        final_len = len(json.dumps(payload))

        shared_state.record_call(
            service="news",
            endpoint="/api/news/disruptions",
            params={"region": region, "top_k": top_k},
            started_at=started,
            status_code=200,
            response_chars=final_len,
        )
        return JSONResponse(content=payload, status_code=200)

    @app.get("/api/compliance/policies/{material_category}")
    async def get_compliance_policy(material_category: str) -> JSONResponse:
        started = time.perf_counter()
        faults = shared_state.get_faults()
        await asyncio.sleep(_jittered_delay_s(faults.compliance_latency_ms, 30))

        policy = get_policy_for_category(material_category)
        if policy is None:
            body = {"detail": f"Unknown material_category '{material_category}'."}
            shared_state.record_call(
                service="compliance",
                endpoint=f"/api/compliance/policies/{material_category}",
                params={"material_category": material_category},
                started_at=started,
                status_code=404,
                response_chars=len(json.dumps(body)),
            )
            return JSONResponse(content=body, status_code=404)

        raw = json.dumps(policy)
        shared_state.record_call(
            service="compliance",
            endpoint=f"/api/compliance/policies/{material_category}",
            params={"material_category": material_category},
            started_at=started,
            status_code=200,
            response_chars=len(raw),
        )
        return JSONResponse(
            content=policy,
            status_code=200,
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    @app.get("/admin/metrics")
    async def admin_metrics() -> dict[str, Any]:
        return shared_state.get_metrics()

    @app.post("/admin/metrics/reset")
    async def admin_metrics_reset() -> dict[str, str]:
        shared_state.reset_metrics()
        return {"status": "reset"}

    @app.get("/admin/faults")
    async def admin_faults_get() -> dict[str, Any]:
        return shared_state.get_faults().model_dump()

    @app.post("/admin/faults")
    async def admin_faults_update(update: FaultUpdate) -> dict[str, Any]:
        updated = shared_state.update_faults(update.model_dump(exclude_none=True))
        return updated.model_dump()

    @app.post("/admin/faults/reset")
    async def admin_faults_reset() -> dict[str, Any]:
        return shared_state.reset_faults().model_dump()

    return app


app = create_app()
