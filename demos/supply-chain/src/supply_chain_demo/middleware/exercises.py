"""Student exercise middleware stubs (Exercises 2, 3, and 4).

NOTE FOR STUDENTS:
All three middleware classes below are intentionally left as skeletons (`NotImplementedError`).
Implement each one using LangChain v1's `AgentMiddleware` interface (`awrap_tool_call` / `wrap_tool_call`).
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any

from frozendict import frozendict
from langchain.agents.middleware import AgentMiddleware
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command


class SelectiveCacheMiddleware(AgentMiddleware):
    """Exercise 2: Selective TTL-aware tool-call caching middleware.

    Design goal:
        - Cache static or slow-changing lookups:
            * `get_compliance_policy`: infinite TTL (`None`) — static ruleset.
            * `get_vendor_historical_scorecard`: 86,400s TTL (24h) — daily ERP snapshot.
        - NEVER cache volatile real-time data:
            * `check_live_freight_rates`: `0` (uncached) — spot prices change continuously.
        - On cache hit, short-circuit `handler(request)` and return a fresh
          `ToolMessage(content=cached_content, tool_call_id=request.tool_call["id"], name=tool_name)`.
          (Important: always bind the *current* `request.tool_call["id"]`, never a stale ID!)
    """

    DEFAULT_TTL_POLICY: frozendict[str, float | None] = frozendict(
        {
            "get_compliance_policy": None,  # Infinite TTL (immutable policy)
            "get_vendor_historical_scorecard": 86400.0,  # 24 hours
            "check_live_freight_rates": 0.0,  # Never cache live spot rates
        }
    )

    def __init__(self, ttl_by_tool: dict[str, float | None] | None = None) -> None:
        super().__init__()
        self.ttl_by_tool: dict[str, float | None] = (
            dict(ttl_by_tool)
            if ttl_by_tool is not None
            else dict(self.DEFAULT_TTL_POLICY)
        )
        # Cache structure suggestion: key -> (ToolMessage.content, expires_at_monotonic | None)
        self._cache: dict[tuple[str, str], tuple[str, float | None]] = {}
        self.hits: int = 0
        self.misses: int = 0
        self.bypassed: int = 0

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        raise NotImplementedError(
            "TODO (Exercise 2): Implement synchronous cache lookup/storage or use awrap_tool_call."
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """TODO (Exercise 2): Implement selective TTL caching around `await handler(request)`.

        Suggested steps:
            1. Extract `tool_name` (`request.tool.name if request.tool else request.tool_call["name"]`)
               and check `tool_name in self.ttl_by_tool`.
            2. Read `ttl = self.ttl_by_tool.get(tool_name, 0.0)`. If `ttl == 0`, increment
               `self.bypassed` and directly `return await handler(request)`.
            3. Build a deterministic cache key `(tool_name, json.dumps(args, sort_keys=True))`.
            4. If key is in `self._cache` and not expired (`expires_at is None or time.monotonic() < expires_at`):
               increment `self.hits` and return a NEW `ToolMessage(content=..., tool_call_id=request.tool_call["id"], name=tool_name)`.
            5. Otherwise increment `self.misses`, call `result = await handler(request)`, and if
               `isinstance(result, ToolMessage)` with `getattr(result, "status", None) != "error"`,
               store `(str(result.content), expires_at)` in `self._cache` and return `result`.
        """
        _ = request, handler, time, ToolMessage
        raise NotImplementedError(
            "TODO (Exercise 2): Implement SelectiveCacheMiddleware.awrap_tool_call."
        )


class CircuitState(str, Enum):
    """Three-state circuit breaker FSM."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class FreightCircuitBreakerMiddleware(AgentMiddleware):
    """Exercise 3: Circuit breaker middleware protecting the agent from slow 503/429 outages.

    Composition tip with LangChain's built-in `ToolRetryMiddleware`:
        Place `FreightCircuitBreakerMiddleware` *before* `ToolRetryMiddleware` in the
        `middleware=[...]` list so that when the circuit is `OPEN`, calls fail fast
        without sleeping through retry backoffs. Remember that if `ToolRetryMiddleware`
        uses `on_failure="continue"`, exhausted retries return a `ToolMessage(status="error")`
        rather than raising an exception — your circuit breaker should inspect both!
    """

    def __init__(
        self,
        target_tools: tuple[str, ...] = ("check_live_freight_rates",),
        failure_threshold: int = 2,
        recovery_timeout_s: float = 30.0,
    ) -> None:
        super().__init__()
        self.target_tools = set(target_tools)
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.state: CircuitState = CircuitState.CLOSED
        self.failure_count: int = 0
        self.opened_at: float | None = None
        self.short_circuited_calls: int = 0

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        raise NotImplementedError(
            "TODO (Exercise 3): Implement synchronous circuit breaker or use awrap_tool_call."
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """TODO (Exercise 3): Implement CLOSED -> OPEN -> HALF_OPEN circuit breaker logic.

        Suggested steps:
            1. Pass through immediately (`return await handler(request)`) if `tool_name` is
               not in `self.target_tools`.
            2. If `self.state == CircuitState.OPEN`:
               - Check whether `time.monotonic() - self.opened_at >= self.recovery_timeout_s`.
               - If cooldown has NOT elapsed: increment `self.short_circuited_calls` and
                 return a structured fallback `ToolMessage` with `status="error"` telling the LLM
                 that the live freight quoting service is temporarily unavailable (circuit OPEN),
                 so it should rely on historical lead times / risk notes without retrying.
               - If cooldown HAS elapsed: transition to `CircuitState.HALF_OPEN` and allow one probe.
            3. Inside `try / except Exception`, call `result = await handler(request)`:
               - Treat an exception OR a `ToolMessage` with `status == "error"` as a failure:
                 increment `self.failure_count`; if `self.failure_count >= self.failure_threshold`
                 (or state was `HALF_OPEN`), transition to `CircuitState.OPEN` and set `self.opened_at`.
                 Return a graceful error `ToolMessage` instead of crashing the whole multi-vendor gather!
               - On success: reset `self.failure_count = 0`, set `self.state = CircuitState.CLOSED`,
                 and return `result`.
        """
        _ = request, handler, time, ToolMessage
        raise NotImplementedError(
            "TODO (Exercise 3): Implement FreightCircuitBreakerMiddleware.awrap_tool_call."
        )


class NewsContextCompactionMiddleware(AgentMiddleware):
    """Exercise 4: Context-bloat compaction middleware for verbose maritime RAG outputs.

    Why this matters in production (vLLM / LiteLLM):
        Each `scan_port_disruption_news` call returns ~2,000 tokens of raw AIS telemetry
        and legal boilerplate (`[TELEMETRY_LOG]`, `[VESSEL_ANCHORAGE_MANIFEST]`,
        `[ARCHIVE_AND_LEGAL_NOTICE]`). Across 3 vendors, ~6,000 noisy tokens enter the
        prompt prefix and KV cache, inflating Time-To-First-Token (TTFT) and risk dilution.

        Compare intercepting the raw tool payload *before* it enters `AgentState`
        (`awrap_tool_call`) vs summarizing multi-turn history later (`SummarizationMiddleware`).
    """

    def __init__(
        self,
        target_tool: str = "scan_port_disruption_news",
        max_chars_per_bulletin: int = 600,
    ) -> None:
        super().__init__()
        self.target_tool = target_tool
        self.max_chars_per_bulletin = max_chars_per_bulletin
        self.chars_saved: int = 0

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        raise NotImplementedError(
            "TODO (Exercise 4): Implement synchronous news compaction or use awrap_tool_call."
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """TODO (Exercise 4): Strip verbose telemetry/archive noise from news tool responses.

        Suggested steps:
            1. Call `result = await handler(request)` first.
            2. If `tool_name != self.target_tool` or `not isinstance(result, ToolMessage)`,
               return `result` untouched.
            3. Parse the JSON string in `result.content` (`data = json.loads(result.content)`).
            4. For each bulletin in `data.get("bulletins", [])`, keep only the decision-critical
               fields (`bulletin_id`, `region`, `published_at`, `alert_severity`,
               `estimated_delay_days`, `summary`) and drop `raw_chunk_text` (or truncate to
               `self.max_chars_per_bulletin` if keeping a snippet).
            5. Serialize the compacted JSON string, update `self.chars_saved`, and return a
               `ToolMessage(content=compacted_json, tool_call_id=request.tool_call["id"], name=tool_name)`.
        """
        _ = request, handler, ToolMessage
        raise NotImplementedError(
            "TODO (Exercise 4): Implement NewsContextCompactionMiddleware.awrap_tool_call."
        )
