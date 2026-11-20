"""Exercise 1 placeholder: Asynchronous enterprise tools using httpx.AsyncClient."""

from __future__ import annotations

import httpx
from langchain_core.tools import BaseTool, tool


def create_async_tools(client: httpx.AsyncClient, base_url: str) -> list[BaseTool]:
    """Create async versions of the 4 enterprise tools sharing a pooled httpx.AsyncClient.

    TODO (Exercise 1):
        Implement each coroutine tool below using `await client.get(...)`,
        call `response.raise_for_status()`, and return `response.text`.
        Using `async def` tools with `await agent.ainvoke(...)` allows LangGraph's
        `ToolNode` to execute multiple tool calls concurrently on the event loop.
    """
    normalized_url = base_url.rstrip("/")

    @tool
    async def get_vendor_historical_scorecard(vendor_id: str) -> str:
        """Query the enterprise ERP SQL database for a vendor's 12-month historical scorecard.

        Returns on-time delivery rate, defect rate, historical average lead time,
        certifications (IATF 16949, ISO 14001, RoHS/REACH), and quality incidents.
        """
        # TODO (Exercise 1): Replace this stub with:
        #   response = await client.get(f"{normalized_url}/api/erp/vendors/{vendor_id}/scorecard")
        #   response.raise_for_status()
        #   return response.text
        _ = normalized_url, client
        raise NotImplementedError(
            "TODO (Exercise 1): Implement async get_vendor_historical_scorecard using httpx.AsyncClient."
        )

    @tool
    async def check_live_freight_rates(origin_port: str, dest_port: str) -> str:
        """Query the external freight carrier API for live container spot rates and transit days.

        Args:
            origin_port: Origin UN/LOCODE (e.g. 'CNSHA', 'DEHAM', 'TRIZM', 'ITTRS').
            dest_port: Destination UN/LOCODE (e.g. 'ROCND').
        """
        # TODO (Exercise 1): Perform an async GET to
        #   f"{normalized_url}/api/freight/rates"
        # with params={"origin_port": origin_port, "dest_port": dest_port},
        # call response.raise_for_status(), and return response.text.
        _ = normalized_url, client
        raise NotImplementedError(
            "TODO (Exercise 1): Implement async check_live_freight_rates using httpx.AsyncClient."
        )

    @tool
    async def scan_port_disruption_news(region: str) -> str:
        """Run semantic vector search over maritime, weather, and geopolitical disruption bulletins.

        Args:
            region: Maritime corridor identifier (e.g. 'south_china_sea_red_sea',
                'north_sea_danube', 'black_sea_bosporus', 'adriatic_mediterranean').
        """
        # TODO (Exercise 1): Perform an async GET to
        #   f"{normalized_url}/api/news/disruptions"
        # with params={"region": region, "top_k": 3},
        # call response.raise_for_status(), and return response.text.
        _ = normalized_url, client
        raise NotImplementedError(
            "TODO (Exercise 1): Implement async scan_port_disruption_news using httpx.AsyncClient."
        )

    @tool
    async def get_compliance_policy(material_category: str) -> str:
        """Look up static corporate procurement compliance thresholds and sourcing rules.

        Args:
            material_category: Procurement category (e.g. 'automotive_semiconductors').
        """
        # TODO (Exercise 1): Perform an async GET to
        #   f"{normalized_url}/api/compliance/policies/{material_category}"
        # call response.raise_for_status(), and return response.text.
        _ = normalized_url, client
        raise NotImplementedError(
            "TODO (Exercise 1): Implement async get_compliance_policy using httpx.AsyncClient."
        )

    return [
        get_vendor_historical_scorecard,
        check_live_freight_rates,
        scan_port_disruption_news,
        get_compliance_policy,
    ]
