# Multi-Vendor Supply Chain & Procurement Risk Analyst

Hands-on production AI agent engineering demo.

## Scenario & Architecture

**Carpathia Precision Motors S.A.** must decide whether to **approve** its incumbent supplier or **switch** suppliers for purchase order `PO-2026-0412` (`automotive_semiconductors`) across three candidates:

| Vendor ID | Supplier | Route | Expected Trade-off |
| --- | --- | --- | --- |
| `VND-101` | ShenZhen MicroFab Ltd. *(incumbent)* | `CNSHA` → `ROCND` | Strong historical ERP, but severe Red Sea / typhoon disruption and expensive, slow freight |
| `VND-204` | Baltic Silicon GmbH | `DEHAM` → `ROCND` | Best ERP reliability (97.1% OTD, 0.35% defect rate), low corridor disruption, SLA-compliant |
| `VND-309` | Anatolia ElectroParts A.S. | `TRIZM` → `ROCND` | Lowest freight quote, but 2.40% defect rate & expired IATF 16949 certificate violate policy |

A second scenario (`FOLLOWUP_PO`, `PO-2026-0419`) introduces `VND-415` while overlapping `VND-204`, `VND-309`, and `automotive_semiconductors` so students can verify cross-run caching.

## The 4 Mock Enterprise Microservices

Implemented in `src/supply_chain_demo/server/` with FastAPI (and launchable directly inside Jupyter via `start_mock_server()`):

| Tool / Endpoint | Backend Simulation | Production Engineering Challenge |
| --- | --- | --- |
| `get_vendor_historical_scorecard(vendor_id)`<br>`GET /api/erp/vendors/{vendor_id}/scorecard` | In-memory SQLite ERP database (~600 ms latency, `Cache-Control: public, max-age=86400`) | Slow legacy DB lookup; safe to cache for 24h |
| `check_live_freight_rates(origin_port, dest_port)`<br>`GET /api/freight/rates` | Jittery external shipping API (600–1,100 ms, `Cache-Control: no-store`, fault-injectable `429` / `503`) | Volatile real-time quote; **must not** be cached, needs retries & circuit breaker |
| `scan_port_disruption_news(region)`<br>`GET /api/news/disruptions` | Pure-Python TF-IDF vector search over 28 maritime bulletins (~800 ms, **~2,000 tokens/call**) | Verbose RAG noise bloats prompt prefix / vLLM KV-cache across turns |
| `get_compliance_policy(material_category)`<br>`GET /api/compliance/policies/{material_category}` | Static regulatory thresholds (~400 ms, `Cache-Control: public, max-age=31536000, immutable`) | 100% static & immutable; ideal infinite-TTL cache target |

Admin endpoints for live chaos engineering & mock-server HTTP inspection:
- `GET /admin/metrics` & `POST /admin/metrics/reset`
- `GET /admin/faults`, `POST /admin/faults`, & `POST /admin/faults/reset`

Agent-level tracing, LLM span latency, and token accounting are intentionally left to standard observability tools (**LangSmith**, **LangFuse**, or **LangChain's built-in OpenTelemetry** support) — evaluation entrypoints accept an optional `config` (e.g. `config={"callbacks": [...], "tags": [...]}`). `benchmark.py` focuses solely on end-to-end wall-clock timing and mock-server HTTP waterfalls.

## Quickstart

### Install dependencies

We recommend using [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

### Configure your OpenAI-compatible endpoint

Start from the `.env` file template:

```bash
cp .env.example .env
```

Edit `.env` and configure your team's API key:

```env
OPENAI_API_KEY=your-api-key
```

`build_chat_model()` configures the official `langchain_openai.ChatOpenAI` client with `use_responses_api=False` so all requests target standard `/v1/chat/completions`.

### 3. Launch the Guided Jupyter Lab

```bash
uv run jupyter lab notebooks/supply_chain_lab.ipynb
```

You do **not** need a second terminal for the mock server — Section 0 of the notebook calls `start_mock_server()`, which runs FastAPI/Uvicorn in a Jupyter-safe background daemon thread.

*(Optional)* Standalone CLI server launch:

```bash
uv run python -m supply_chain_demo.server --host 127.0.0.1 --port 8000
```

## Student Lab Exercises (TODOs)

This repository intentionally provides only the **naive sequential baseline** and **skeleton TODO placeholders** for the four optimization exercises:

1. **Exercise 1 — Async Parallelization** ([async_tools.py](src/supply_chain_demo/tools/async_tools.py), [optimized.py](src/supply_chain_demo/agent/optimized.py)):
   Replace blocking single-connection sync calls with `httpx.AsyncClient` tools and `asyncio.gather` multi-vendor fan-out.
2. **Exercise 2 — Selective TTL Caching** ([exercises.py](src/supply_chain_demo/middleware/exercises.py) → `SelectiveCacheMiddleware`):
   Intercept `awrap_tool_call` to cache Compliance (`infinite`) and ERP Scorecards (`86,400s`), while bypassing `check_live_freight_rates`.
3. **Exercise 3 — Circuit Breaker & Retries** ([exercises.py](src/supply_chain_demo/middleware/exercises.py) → `FreightCircuitBreakerMiddleware`):
   Implement `CLOSED → OPEN → HALF_OPEN` state transitions, compose cleanly with LangChain's `ToolRetryMiddleware`, and survive injected `503` outages gracefully.
4. **Exercise 4 — Context / KV-Cache Compaction** ([exercises.py](src/supply_chain_demo/middleware/exercises.py) → `NewsContextCompactionMiddleware`):
   Strip raw telemetry/manifest noise from `scan_port_disruption_news` responses before they enter agent message history and vLLM's KV cache.

## Running Automated Tests

```bash
uv run pytest -v
```
