"""Multi-Vendor Supply Chain & Procurement Risk Analyst teaching demo."""

from __future__ import annotations

import warnings

# LangChain/LangGraph internals can touch pydantic.v1 compatibility shims on Python 3.14.
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*Pydantic V1 functionality isn't compatible with Python 3\.14.*",
)

from supply_chain_demo.config import Settings, build_chat_model, load_settings
from supply_chain_demo.data.scenarios import FOLLOWUP_PO, PRIMARY_PO, CandidateVendor, PurchaseOrder
from supply_chain_demo.server.launcher import MockEnterpriseServer, start_mock_server

__all__ = [
    "CandidateVendor",
    "FOLLOWUP_PO",
    "MockEnterpriseServer",
    "PRIMARY_PO",
    "PurchaseOrder",
    "Settings",
    "build_chat_model",
    "load_settings",
    "start_mock_server",
]
