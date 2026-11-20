"System and task prompts shared between the naive baseline and the exercises."

from __future__ import annotations

from supply_chain_demo.data.scenarios import CandidateVendor, PurchaseOrder

VENDOR_ANALYST_SYSTEM_PROMPT = """You are a Senior Supply Chain & Procurement Risk Analyst.
Your job is to evaluate a single candidate vendor for a corporate purchase order.

Before producing your assessment, you MUST call all four enterprise tools:
1. `get_vendor_historical_scorecard` with the vendor's `vendor_id`
2. `check_live_freight_rates` with the vendor's `origin_port` and `dest_port`
3. `scan_port_disruption_news` with the vendor's maritime `region`
4. `get_compliance_policy` with the purchase order's `material_category`

Resilience rule:
- If any tool returns an error or circuit-breaker notice (e.g., 503 outage or 429 rate limit),
  do NOT retry indefinitely; record the missing live signal explicitly and complete your risk
  dossier using the remaining evidence.

Output format:
Provide a concise, factual Vendor Risk Dossier covering:
- Historical ERP Reliability (on-time delivery %, defect rate %, average lead time, certs, incidents)
- Live Freight & Transit Check (spot USD/TEU and transit days vs PO caps, or outage status)
- Maritime Corridor Disruption Risk (severity, estimated delay days, key operational driver)
- Compliance Verdict (PASS or FAIL against every mandatory rule in the policy)
- Overall Vendor Recommendation (RECOMMENDED / CONDITIONAL / DISQUALIFY).
"""

SYNTHESIS_SYSTEM_PROMPT = """You are the Chief Procurement Risk Officer making the final purchase order decision.
Review all candidate vendor risk dossiers alongside the purchase order constraints.

Rules:
- Reject any vendor that fails mandatory regulatory compliance thresholds (defect rate cap,
  on-time delivery floor, or active certifications).
- Weigh incumbent switching risks against route disruptions, total transit SLA, freight cap,
  and unit price.
- Produce a clear executive decision beginning with `DECISION: APPROVE INCUMBENT` or
  `DECISION: SWITCH SUPPLIER`, naming the chosen vendor, summarizing why rejected vendors were
  ruled out with exact metrics, and listing operational next steps.
"""


def format_vendor_prompt(vendor: CandidateVendor, po: PurchaseOrder) -> str:
    """Format the per-vendor evaluation prompt passed to the single-vendor ReAct agent."""
    incumbent_label = "YES (Current Incumbent)" if vendor.is_incumbent else "NO (Alternative Candidate)"
    return (
        f"Evaluate candidate vendor for Purchase Order {po.po_id} ({po.company}):\n"
        f"- Material Category: {po.material_category}\n"
        f"- Item & Quantity: {po.item_description} ({po.quantity:,} units)\n"
        f"- PO Constraints: max freight <= ${po.max_freight_usd_per_teu:,.2f}/TEU, "
        f"max transit <= {po.max_transit_days} days to {po.dest_port}\n"
        f"- SLA Summary: {po.required_sla_summary}\n\n"
        f"Candidate Vendor Details:\n"
        f"- vendor_id: {vendor.vendor_id}\n"
        f"- name: {vendor.name} ({vendor.country})\n"
        f"- origin_port: {vendor.origin_port}\n"
        f"- dest_port: {vendor.dest_port}\n"
        f"- region: {vendor.region}\n"
        f"- quoted_unit_price_eur: {vendor.quoted_unit_price_eur:.2f}\n"
        f"- incumbent: {incumbent_label}\n\n"
        "Call all 4 enterprise tools now and return the structured Vendor Risk Dossier."
    )


def format_synthesis_prompt(
    po: PurchaseOrder,
    dossiers: list[tuple[CandidateVendor, str]],
) -> str:
    """Format the multi-vendor synthesis prompt combining all vendor dossiers."""
    sections = [
        f"Purchase Order {po.po_id} — {po.company}",
        f"Material Category: {po.material_category}",
        f"Item: {po.item_description} (Qty: {po.quantity:,})",
        f"SLA Caps: freight <= ${po.max_freight_usd_per_teu:,.2f}/TEU, transit <= {po.max_transit_days} days",
        f"Required SLA: {po.required_sla_summary}",
        "",
        "=== CANDIDATE VENDOR RISK DOSSIERS ===",
    ]
    for vendor, dossier in dossiers:
        tag = "INCUMBENT" if vendor.is_incumbent else "CANDIDATE"
        sections.append(
            f"\n--- {vendor.vendor_id}: {vendor.name}" +
            f" ({tag}, €{vendor.quoted_unit_price_eur:.2f}/unit) ---\n" +
            f"{dossier}"
        )
    sections.append(
        "\nSynthesize the final procurement decision (`APPROVE INCUMBENT` or `SWITCH SUPPLIER`)."
    )
    return "\n".join(sections)
