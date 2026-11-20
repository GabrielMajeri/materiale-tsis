"""Tests for the naive baseline agent, benchmark utilities, and student TODO placeholders."""

from __future__ import annotations

import importlib
import re
import socket
from collections.abc import Iterator, Sequence
from typing import Any

import httpx
import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool

from supply_chain_demo.agent.baseline import evaluate_purchase_order_sync
from supply_chain_demo.agent.optimized import (
    evaluate_purchase_order_async,
    evaluate_vendor_async,
)
from supply_chain_demo.benchmark import compare_reports, print_report, render_waterfall
from supply_chain_demo.config import Settings, build_chat_model, validate_llm_config
from supply_chain_demo.data.scenarios import PRIMARY_PO
from supply_chain_demo.middleware.exercises import (
    FreightCircuitBreakerMiddleware,
    NewsContextCompactionMiddleware,
    SelectiveCacheMiddleware,
)
from supply_chain_demo.server.launcher import MockEnterpriseServer, start_mock_server
from supply_chain_demo.tools.async_tools import create_async_tools


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class FakeProcurementChatModel(BaseChatModel):
    """Test-only deterministic chat model emitting all 4 tool calls in one turn."""

    vendor_lookup: dict[str, dict[str, str]] = {
        v.vendor_id: {
            "origin_port": v.origin_port,
            "dest_port": v.dest_port,
            "region": v.region,
        }
        for v in PRIMARY_PO.candidate_vendors
    }

    @property
    def _llm_type(self) -> str:
        return "fake-procurement"

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Any | BaseTool],
        **kwargs: Any,
    ) -> FakeProcurementChatModel:
        _ = tools, kwargs
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        _ = stop, run_manager, kwargs
        last_msg = messages[-1]

        # Synthesis prompt has all dossiers combined
        if isinstance(last_msg, HumanMessage) and "=== CANDIDATE VENDOR RISK DOSSIERS ===" in str(
            last_msg.content
        ):
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content=(
                                "DECISION: SWITCH SUPPLIER to VND-204 (Baltic Silicon GmbH). "
                                "VND-101 faces Red Sea disruptions; VND-309 fails defect and IATF policy."
                            ),
                            usage_metadata={
                                "input_tokens": 900,
                                "output_tokens": 120,
                                "total_tokens": 1020,
                            },
                        )
                    )
                ]
            )

        has_tool_results = any(isinstance(m, ToolMessage) for m in messages)
        if not has_tool_results:
            prompt_text = str(last_msg.content)
            match = re.search(r"vendor_id:\s*(VND-\d+)", prompt_text)
            assert match is not None, f"Could not parse vendor_id from prompt: {prompt_text}"
            vendor_id = match.group(1)
            meta = self.vendor_lookup[vendor_id]
            tool_calls = [
                {
                    "id": f"call_{vendor_id}_erp",
                    "name": "get_vendor_historical_scorecard",
                    "args": {"vendor_id": vendor_id},
                },
                {
                    "id": f"call_{vendor_id}_freight",
                    "name": "check_live_freight_rates",
                    "args": {
                        "origin_port": meta["origin_port"],
                        "dest_port": meta["dest_port"],
                    },
                },
                {
                    "id": f"call_{vendor_id}_news",
                    "name": "scan_port_disruption_news",
                    "args": {"region": meta["region"]},
                },
                {
                    "id": f"call_{vendor_id}_compliance",
                    "name": "get_compliance_policy",
                    "args": {"material_category": PRIMARY_PO.material_category},
                },
            ]
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content="",
                            tool_calls=tool_calls,
                            usage_metadata={
                                "input_tokens": 350,
                                "output_tokens": 95,
                                "total_tokens": 445,
                            },
                        )
                    )
                ]
            )

        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="Vendor Risk Dossier synthesized from all 4 enterprise services.",
                        usage_metadata={
                            "input_tokens": 2400,
                            "output_tokens": 160,
                            "total_tokens": 2560,
                        },
                    )
                )
            ]
        )


@pytest.fixture
def fast_server() -> Iterator[MockEnterpriseServer]:
    port = _get_free_port()
    server = start_mock_server(host="127.0.0.1", port=port)
    server.set_faults(
        erp_latency_ms=40,
        freight_latency_min_ms=40,
        freight_latency_max_ms=55,
        news_latency_ms=45,
        compliance_latency_ms=30,
    )
    server.reset_metrics()
    try:
        yield server
    finally:
        server.stop()


def test_config_builds_chat_openai_for_litellm_gateway() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        validate_llm_config(Settings(openai_api_key="sk-replace-me"))

    model = build_chat_model(
        Settings(
            openai_base_url="http://vllm-litellm.local:4000/v1",
            openai_api_key="sk-student-test-key",
            openai_model="qwen2.5-72b-instruct",
        )
    )
    assert model.use_responses_api is False
    assert model.openai_api_base == "http://vllm-litellm.local:4000/v1"
    assert model.model_name == "qwen2.5-72b-instruct"


def test_baseline_agent_executes_12_sequential_http_calls(
    fast_server: MockEnterpriseServer,
) -> None:
    fake_model = FakeProcurementChatModel()
    decision, report = evaluate_purchase_order_sync(
        PRIMARY_PO,
        fake_model,
        fast_server.url,
        config={"tags": ["lab-baseline"]},
    )

    assert "SWITCH SUPPLIER" in decision
    assert report.total_http_calls == 12
    assert report.calls_by_service == {
        "erp": 3,
        "freight": 3,
        "news": 3,
        "compliance": 3,
    }
    assert report.total_http_errors == 0

    # Verify strict sequential wire execution: no overlapping HTTP spans
    ordered = sorted(report.calls, key=lambda c: float(c["start_offset_ms"]))
    assert len(ordered) == 12
    for prev_call, next_call in zip(ordered, ordered[1:], strict=False):
        assert float(next_call["start_offset_ms"]) >= float(prev_call["end_offset_ms"]) - 2.0

    # Verify benchmark rendering helpers work cleanly
    waterfall = render_waterfall(report)
    assert "HTTP Waterfall:" in waterfall
    assert len(waterfall.splitlines()) == 13
    print_report(report)
    compare_reports([report])


def test_handwritten_telemetry_module_is_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("supply_chain_demo.middleware.telemetry")


@pytest.mark.asyncio
async def test_exercise_placeholders_raise_not_implemented() -> None:
    async with httpx.AsyncClient() as client:
        async_tools = create_async_tools(client, "http://127.0.0.1:8000")
        assert len(async_tools) == 4
        sample_args = [
            {"vendor_id": "VND-101"},
            {"origin_port": "DEHAM", "dest_port": "ROCND"},
            {"region": "north_sea_danube"},
            {"material_category": "automotive_semiconductors"},
        ]
        for tool_obj, args in zip(async_tools, sample_args, strict=True):
            with pytest.raises(NotImplementedError, match="Exercise 1"):
                await tool_obj.ainvoke(args)

    fake_model = FakeProcurementChatModel()
    with pytest.raises(NotImplementedError, match="Exercise 1"):
        await evaluate_vendor_async(object(), PRIMARY_PO.candidate_vendors[0], PRIMARY_PO)

    with pytest.raises(NotImplementedError, match="Exercise 1"):
        await evaluate_purchase_order_async(
            PRIMARY_PO, fake_model, async_tools, "http://127.0.0.1:8000"
        )

    for mw_cls, ex_label in [
        (SelectiveCacheMiddleware, "Exercise 2"),
        (FreightCircuitBreakerMiddleware, "Exercise 3"),
        (NewsContextCompactionMiddleware, "Exercise 4"),
    ]:
        mw = mw_cls()
        with pytest.raises(NotImplementedError, match=ex_label):
            mw.wrap_tool_call(None, None)  # type: ignore[arg-type]
        with pytest.raises(NotImplementedError, match=ex_label):
            await mw.awrap_tool_call(None, None)  # type: ignore[arg-type]
