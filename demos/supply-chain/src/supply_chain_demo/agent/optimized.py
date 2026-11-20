"""Exercise 1 placeholder: Asynchronous parallel multi-vendor agent evaluation."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from typing import Any

import httpx
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from supply_chain_demo.agent.baseline import build_vendor_agent, extract_message_text
from supply_chain_demo.agent.prompts import (
    SYNTHESIS_SYSTEM_PROMPT,
    format_synthesis_prompt,
    format_vendor_prompt,
)
from supply_chain_demo.benchmark import RunReport, build_run_report
from supply_chain_demo.data.scenarios import CandidateVendor, PurchaseOrder


async def evaluate_vendor_async(
    agent: Any,
    vendor: CandidateVendor,
    po: PurchaseOrder,
    *,
    config: dict[str, Any] | None = None,
) -> str:
    """TODO (Exercise 1): Asynchronously evaluate one candidate vendor via `await agent.ainvoke(...)`.

    Suggested steps:
        1. Build the user prompt using `format_vendor_prompt(vendor, po)`.
        2. Run `result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]}, config=config)`.
        3. Return `extract_message_text(result["messages"][-1])`.
    """
    _ = agent, vendor, po, config, HumanMessage, format_vendor_prompt, extract_message_text
    raise NotImplementedError(
        "TODO (Exercise 1): Implement evaluate_vendor_async using await agent.ainvoke(...)."
    )


async def evaluate_purchase_order_async(
    po: PurchaseOrder,
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    api_base_url: str,
    *,
    middleware: Sequence[AgentMiddleware[Any, Any]] | None = None,
    label: str = "Optimized (Async Parallel)",
    config: dict[str, Any] | None = None,
) -> tuple[str, RunReport]:
    """TODO (Exercise 1): Evaluate all candidate vendors concurrently with `asyncio.gather`.

    Suggested steps:
        1. Build the agent once with `build_vendor_agent(model, tools, middleware=middleware)`.
        2. Reset server metrics before timing via an async POST to
           `f"{normalized_url}/admin/metrics/reset"`.
        3. Start `wall_started = time.perf_counter()` and fan out across `po.candidate_vendors`:
           `dossiers_text = await asyncio.gather(*(evaluate_vendor_async(agent, v, po, config=config) for v in po.candidate_vendors))`
        4. Pair `dossiers = list(zip(po.candidate_vendors, dossiers_text, strict=True))` and
           synthesize asynchronously with `await model.ainvoke([SystemMessage(...), HumanMessage(...)], config=config)`.
        5. Fetch `/admin/metrics` with `httpx.AsyncClient`, and return
           `(final_decision, build_run_report(label=label, wall_time_s=..., server_metrics=..., final_decision=...))`.
    """
    _ = (
        po,
        model,
        tools,
        api_base_url,
        middleware,
        label,
        config,
        asyncio,
        time,
        httpx,
        SystemMessage,
        format_synthesis_prompt,
        build_vendor_agent,
        build_run_report,
    )
    raise NotImplementedError(
        "TODO (Exercise 1): Implement evaluate_purchase_order_async with asyncio.gather fan-out."
    )
