"""Naive synchronous tools using a single serialized httpx.Client connection."""

from __future__ import annotations

import threading

import httpx
from langchain_core.tools import BaseTool, tool


def create_sync_client(timeout_s: float = 30.0) -> httpx.Client:
    """Create a single-connection synchronous HTTP client (naive baseline bottleneck)."""
    return httpx.Client(
        limits=httpx.Limits(max_connections=1, max_keepalive_connections=1),
        timeout=timeout_s,
    )


def create_sync_tools(
    base_url: str,
    *,
    client: httpx.Client | None = None,
) -> list[BaseTool]:
    """Create the 4 enterprise tools backed by blocking synchronous HTTP calls."""
    normalized_url = base_url.rstrip("/")
    http_client = client if client is not None else create_sync_client()
    # Explicit lock guarantees sequential wire execution even if a caller threads tool calls.
    serial_lock = threading.Lock()

    @tool
    def get_vendor_historical_scorecard(vendor_id: str) -> str:
        """Query the enterprise ERP SQL database for a vendor's 12-month historical scorecard.

        Returns on-time delivery rate, defect rate, historical average lead time,
        certifications (IATF 16949, ISO 14001, RoHS/REACH), and quality incidents.
        """
        with serial_lock:
            response = http_client.get(f"{normalized_url}/api/erp/vendors/{vendor_id}/scorecard")
            response.raise_for_status()
            return response.text

    @tool
    def check_live_freight_rates(origin_port: str, dest_port: str) -> str:
        """Query the external freight carrier API for live container spot rates and transit days.

        Args:
            origin_port: Origin UN/LOCODE (e.g. 'CNSHA', 'DEHAM', 'TRIZM', 'ITTRS').
            dest_port: Destination UN/LOCODE (e.g. 'ROCND').
        """
        with serial_lock:
            response = http_client.get(
                f"{normalized_url}/api/freight/rates",
                params={"origin_port": origin_port, "dest_port": dest_port},
            )
            response.raise_for_status()
            return response.text

    @tool
    def scan_port_disruption_news(region: str) -> str:
        """Run semantic vector search over maritime, weather, and geopolitical disruption bulletins.

        Args:
            region: Maritime corridor identifier (e.g. 'south_china_sea_red_sea',
                'north_sea_danube', 'black_sea_bosporus', 'adriatic_mediterranean').
        """
        with serial_lock:
            response = http_client.get(
                f"{normalized_url}/api/news/disruptions",
                params={"region": region, "top_k": 3},
            )
            response.raise_for_status()
            return response.text

    @tool
    def get_compliance_policy(material_category: str) -> str:
        """Look up static corporate procurement compliance thresholds and sourcing rules.

        Args:
            material_category: Procurement category (e.g. 'automotive_semiconductors').
        """
        with serial_lock:
            response = http_client.get(
                f"{normalized_url}/api/compliance/policies/{material_category}"
            )
            response.raise_for_status()
            return response.text

    return [
        get_vendor_historical_scorecard,
        check_live_freight_rates,
        scan_port_disruption_news,
        get_compliance_policy,
    ]
