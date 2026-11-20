"""Naive synchronous baseline agent built with LangChain v1 create_agent."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import httpx
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from supply_chain_demo.agent.prompts import (
    SYNTHESIS_SYSTEM_PROMPT,
    VENDOR_ANALYST_SYSTEM_PROMPT,
    format_synthesis_prompt,
    format_vendor_prompt,
)
from supply_chain_demo.benchmark import RunReport, build_run_report
from supply_chain_demo.data.scenarios import CandidateVendor, PurchaseOrder
from supply_chain_demo.tools.sync_tools import create_sync_client, create_sync_tools


def extract_message_text(message: AnyMessage) -> str:
    """Extract plain text from a LangChain AIMessage across string and block payloads."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts)
    return str(content)


def build_vendor_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    *,
    middleware: Sequence[AgentMiddleware] | None = None,
    system_prompt: str = VENDOR_ANALYST_SYSTEM_PROMPT,
) -> CompiledStateGraph[AgentState[Any], None, Any, Any]:
    """Create a LangChain v1 ReAct vendor evaluation agent via `create_agent`."""
    return create_agent(
        model=model,
        tools=list(tools),
        system_prompt=system_prompt,
        middleware=list(middleware or ()),
    )


def evaluate_vendor_sync(
    agent: Any,
    vendor: CandidateVendor,
    po: PurchaseOrder,
    *,
    config: dict[str, Any] | None = None,
) -> str:
    """Synchronously evaluate a single candidate vendor using a blocking `agent.invoke` call."""
    prompt = format_vendor_prompt(vendor, po)
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]}, config=config)
    messages = result.get("messages", [])
    if not messages:
        return ""
    return extract_message_text(messages[-1])


def evaluate_purchase_order_sync(
    po: PurchaseOrder,
    model: BaseChatModel,
    api_base_url: str,
    *,
    extra_middleware: Sequence[AgentMiddleware[Any, Any]] | None = None,
    label: str = "Baseline (Sync Sequential)",
    config: dict[str, Any] | None = None,
) -> tuple[str, RunReport]:
    """Run the naive sequential baseline across all candidate vendors for a purchase order."""
    normalized_url = api_base_url.rstrip("/")
    middleware_chain: list[AgentMiddleware[Any, Any]] = list(extra_middleware or ())

    httpx.post(f"{normalized_url}/admin/metrics/reset", timeout=5.0).raise_for_status()

    wall_started = time.perf_counter()
    dossiers: list[tuple[CandidateVendor, str]] = []

    with create_sync_client() as http_client:
        tools = create_sync_tools(normalized_url, client=http_client)
        agent = build_vendor_agent(model, tools, middleware=middleware_chain)

        # Naive bottleneck: vendors (and each vendor's 4 tool calls) execute sequentially.
        for vendor in po.candidate_vendors:
            dossier = evaluate_vendor_sync(agent, vendor, po, config=config)
            dossiers.append((vendor, dossier))

    synthesis_prompt = format_synthesis_prompt(po, dossiers)
    synthesis_msg = model.invoke(
        [
            SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
            HumanMessage(content=synthesis_prompt),
        ],
        config=config,
    )
    final_decision = extract_message_text(synthesis_msg)

    wall_time_s = time.perf_counter() - wall_started
    metrics_resp = httpx.get(f"{normalized_url}/admin/metrics", timeout=5.0)
    metrics_resp.raise_for_status()

    report = build_run_report(
        label=label,
        wall_time_s=wall_time_s,
        server_metrics=metrics_resp.json(),
        final_decision=final_decision,
    )
    return final_decision, report
