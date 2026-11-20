"""Static corporate procurement compliance policies by material category."""

from __future__ import annotations

from typing import Any

COMPLIANCE_POLICIES: dict[str, dict[str, Any]] = {
    "automotive_semiconductors": {
        "material_category": "automotive_semiconductors",
        "policy_version": "PROC-AUTO-2026.4",
        "effective_date": "2026-01-01",
        "mandatory_thresholds": {
            "max_defect_rate_pct": 1.50,
            "min_on_time_delivery_pct": 90.0,
            "min_financial_rating": "BBB",
            "require_active_iatf_16949": True,
            "require_iso_14001": True,
            "require_eu_rohs_reach": True,
        },
        "sourcing_and_risk_rules": [
            "Automatic disqualification if defect_rate_pct exceeds 1.50% OR IATF 16949 certificate status is EXPIRED.",
            "Mandatory switch or dual-source escalation if incumbent route faces HIGH/CRITICAL geopolitical or weather disruptions causing transit > PO max_transit_days.",
            "EU CBAM & customs rules require verified EUR.1 / REX origin declarations for non-EU suppliers.",
            "Single supplier allocation must not exceed 70% of annual MCU spend without VP Procurement sign-off.",
        ],
        "cache_hint": "Static regulatory policy; immutable for policy version PROC-AUTO-2026.4.",
    },
    "industrial_polymers": {
        "material_category": "industrial_polymers",
        "policy_version": "PROC-POLY-2026.2",
        "effective_date": "2026-02-01",
        "mandatory_thresholds": {
            "max_defect_rate_pct": 2.00,
            "min_on_time_delivery_pct": 88.0,
            "min_financial_rating": "BBB-",
            "require_active_iatf_16949": False,
            "require_iso_14001": True,
            "require_eu_rohs_reach": True,
        },
        "sourcing_and_risk_rules": [
            "REACH SVHC declaration mandatory for every polymer resin batch.",
            "Temperature-controlled container surcharge requires CFO approval above $3,200/TEU.",
        ],
        "cache_hint": "Static regulatory policy; immutable for policy version PROC-POLY-2026.2.",
    },
    "precision_alloys": {
        "material_category": "precision_alloys",
        "policy_version": "PROC-ALLOY-2026.1",
        "effective_date": "2026-01-15",
        "mandatory_thresholds": {
            "max_defect_rate_pct": 1.00,
            "min_on_time_delivery_pct": 92.0,
            "min_financial_rating": "BBB+",
            "require_active_iatf_16949": True,
            "require_iso_14001": True,
            "require_eu_rohs_reach": True,
        },
        "sourcing_and_risk_rules": [
            "Full EU CBAM embedded-emissions certificate required at customs clearance.",
            "EN 10204 3.1 mill test certificate mandatory per heat lot.",
        ],
        "cache_hint": "Static regulatory policy; immutable for policy version PROC-ALLOY-2026.1.",
    },
}


def get_policy_for_category(material_category: str) -> dict[str, Any] | None:
    """Return the static compliance ruleset for a material category."""
    return COMPLIANCE_POLICIES.get(material_category)
