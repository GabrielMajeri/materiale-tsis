"""Procurement scenarios and domain models for the supply chain risk analyst demo."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateVendor(BaseModel):
    """A candidate supplier being evaluated for a purchase order."""

    vendor_id: str
    name: str
    country: str
    origin_port: str = Field(description="UN/LOCODE of the vendor's shipping origin port.")
    dest_port: str = Field(description="UN/LOCODE of the receiving destination port.")
    region: str = Field(description="Maritime corridor identifier for disruption scanning.")
    quoted_unit_price_eur: float
    is_incumbent: bool = False


class PurchaseOrder(BaseModel):
    """A purchase order requiring multi-vendor procurement risk analysis."""

    po_id: str
    company: str
    material_category: str
    item_description: str
    quantity: int
    dest_port: str
    max_freight_usd_per_teu: float
    max_transit_days: int
    required_sla_summary: str
    candidate_vendors: list[CandidateVendor]


PRIMARY_PO = PurchaseOrder(
    po_id="PO-2026-0412",
    company="Carpathia Precision Motors S.A.",
    material_category="automotive_semiconductors",
    item_description="AEC-Q100 Grade-1 32-bit Traction Inverter MCUs (60,000 units)",
    quantity=60_000,
    dest_port="ROCND",
    max_freight_usd_per_teu=2900.0,
    max_transit_days=18,
    required_sla_summary=(
        "Max defect rate <= 1.50%; minimum on-time delivery >= 90.0%; active "
        "non-expired IATF 16949 and EU RoHS/REACH compliance; freight <= $2,900/TEU; "
        "total transit time <= 18 days to Constanta (ROCND)."
    ),
    candidate_vendors=[
        CandidateVendor(
            vendor_id="VND-101",
            name="ShenZhen MicroFab Ltd.",
            country="China",
            origin_port="CNSHA",
            dest_port="ROCND",
            region="south_china_sea_red_sea",
            quoted_unit_price_eur=14.20,
            is_incumbent=True,
        ),
        CandidateVendor(
            vendor_id="VND-204",
            name="Baltic Silicon GmbH",
            country="Germany",
            origin_port="DEHAM",
            dest_port="ROCND",
            region="north_sea_danube",
            quoted_unit_price_eur=15.10,
            is_incumbent=False,
        ),
        CandidateVendor(
            vendor_id="VND-309",
            name="Anatolia ElectroParts A.S.",
            country="Turkey",
            origin_port="TRIZM",
            dest_port="ROCND",
            region="black_sea_bosporus",
            quoted_unit_price_eur=13.40,
            is_incumbent=False,
        ),
    ],
)

FOLLOWUP_PO = PurchaseOrder(
    po_id="PO-2026-0419",
    company="Carpathia Precision Motors S.A.",
    material_category="automotive_semiconductors",
    item_description="AEC-Q100 Grade-1 Battery Management Gate Drivers (45,000 units)",
    quantity=45_000,
    dest_port="ROCND",
    max_freight_usd_per_teu=2700.0,
    max_transit_days=15,
    required_sla_summary=(
        "Max defect rate <= 1.50%; minimum on-time delivery >= 90.0%; active "
        "non-expired IATF 16949 and EU RoHS/REACH compliance; freight <= $2,700/TEU; "
        "total transit time <= 15 days to Constanta (ROCND)."
    ),
    candidate_vendors=[
        CandidateVendor(
            vendor_id="VND-204",
            name="Baltic Silicon GmbH",
            country="Germany",
            origin_port="DEHAM",
            dest_port="ROCND",
            region="north_sea_danube",
            quoted_unit_price_eur=11.80,
            is_incumbent=False,
        ),
        CandidateVendor(
            vendor_id="VND-309",
            name="Anatolia ElectroParts A.S.",
            country="Turkey",
            origin_port="TRIZM",
            dest_port="ROCND",
            region="black_sea_bosporus",
            quoted_unit_price_eur=10.90,
            is_incumbent=False,
        ),
        CandidateVendor(
            vendor_id="VND-415",
            name="Adriatic MicroSystems S.r.l.",
            country="Italy",
            origin_port="ITTRS",
            dest_port="ROCND",
            region="adriatic_mediterranean",
            quoted_unit_price_eur=12.10,
            is_incumbent=False,
        ),
    ],
)
