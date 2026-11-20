"""Mock SQLite ERP backend for historical vendor reliability scorecards."""

from __future__ import annotations

import sqlite3
import threading
from typing import Any


class ERPDatabase:
    """Thread-safe in-memory SQLite database storing vendor delivery and quality records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._initialize_schema()
        self._seed_data()

    def _initialize_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript(
                """
                CREATE TABLE vendors (
                    vendor_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    country TEXT NOT NULL,
                    erp_tier TEXT NOT NULL,
                    financial_rating TEXT NOT NULL,
                    iatf_16949_status TEXT NOT NULL,
                    iatf_valid_until TEXT NOT NULL,
                    iso_14001_certified INTEGER NOT NULL,
                    rohs_reach_verified INTEGER NOT NULL
                );

                CREATE TABLE quarterly_deliveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_id TEXT NOT NULL,
                    quarter TEXT NOT NULL,
                    total_shipments INTEGER NOT NULL,
                    on_time_shipments INTEGER NOT NULL,
                    units_delivered INTEGER NOT NULL,
                    defective_units INTEGER NOT NULL,
                    avg_lead_time_days REAL NOT NULL,
                    FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
                );

                CREATE TABLE quality_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vendor_id TEXT NOT NULL,
                    incident_date TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (vendor_id) REFERENCES vendors (vendor_id)
                );
                """
            )
            self._conn.commit()

    def _seed_data(self) -> None:
        vendors = [
            ("VND-101", "ShenZhen MicroFab Ltd.", "China", "Tier-1 Strategic", "A-", "ACTIVE", "2027-06-30", 1, 1),
            ("VND-204", "Baltic Silicon GmbH", "Germany", "Tier-1 Approved", "AA", "ACTIVE", "2028-01-15", 1, 1),
            ("VND-309", "Anatolia ElectroParts A.S.", "Turkey", "Tier-2 Conditional", "BBB-", "EXPIRED", "2026-08-31", 1, 1),
            ("VND-415", "Adriatic MicroSystems S.r.l.", "Italy", "Tier-1 Approved", "A+", "ACTIVE", "2027-11-30", 1, 1),
        ]
        deliveries = [
            # VND-101: 93.5% OTD (187/200), 0.80% defect (1600/200000), ~28d lead time
            ("VND-101", "2026-Q1", 50, 47, 50_000, 390, 27.5),
            ("VND-101", "2026-Q2", 50, 47, 50_000, 410, 28.0),
            ("VND-101", "2026-Q3", 50, 46, 50_000, 420, 29.0),
            ("VND-101", "2026-Q4", 50, 47, 50_000, 380, 27.5),
            # VND-204: 97.1% OTD (165/170), 0.35% defect (595/170000), ~11d lead time
            ("VND-204", "2026-Q1", 40, 39, 40_000, 140, 11.2),
            ("VND-204", "2026-Q2", 45, 44, 45_000, 155, 10.8),
            ("VND-204", "2026-Q3", 45, 43, 45_000, 160, 11.1),
            ("VND-204", "2026-Q4", 40, 39, 40_000, 140, 10.9),
            # VND-309: 88.0% OTD (110/125), 2.40% defect (3000/125000), ~9d lead time
            ("VND-309", "2026-Q1", 30, 27, 30_000, 630, 8.8),
            ("VND-309", "2026-Q2", 30, 26, 30_000, 720, 9.1),
            ("VND-309", "2026-Q3", 35, 30, 35_000, 910, 9.4),
            ("VND-309", "2026-Q4", 30, 27, 30_000, 740, 8.7),
            # VND-415: 95.2% OTD (119/125), 0.55% defect (688/125000), ~10d lead time
            ("VND-415", "2026-Q1", 30, 29, 30_000, 165, 10.2),
            ("VND-415", "2026-Q2", 30, 28, 30_000, 170, 10.0),
            ("VND-415", "2026-Q3", 35, 34, 35_000, 190, 9.8),
            ("VND-415", "2026-Q4", 30, 28, 30_000, 163, 10.0),
        ]
        incidents = [
            ("VND-101", "2026-07-14", "MINOR", "Delayed EUR/customs commercial invoice attachment; cleared in 36h.", "RESOLVED"),
            ("VND-204", "2026-03-08", "INFO", "Routine annual quality surveillance passed with zero non-conformities.", "CLOSED"),
            ("VND-309", "2026-08-19", "MAJOR", "Solderability failure on MCU Lot #TR-884 (2.9% batch defect rate).", "OPEN"),
            ("VND-309", "2026-09-02", "CRITICAL", "IATF 16949 certificate lapsed on 2026-08-31 pending re-audit.", "OPEN"),
            ("VND-415", "2026-06-11", "MINOR", "Moisture barrier reel label mismatch corrected before dispatch.", "RESOLVED"),
        ]
        with self._lock:
            cur = self._conn.cursor()
            cur.executemany("INSERT INTO vendors VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", vendors)
            cur.executemany(
                "INSERT INTO quarterly_deliveries (vendor_id, quarter, total_shipments, on_time_shipments, units_delivered, defective_units, avg_lead_time_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
                deliveries,
            )
            cur.executemany(
                "INSERT INTO quality_incidents (vendor_id, incident_date, severity, summary, status) VALUES (?, ?, ?, ?, ?)",
                incidents,
            )
            self._conn.commit()

    def query_vendor_scorecard(self, vendor_id: str) -> dict[str, Any] | None:
        """Execute SQL aggregation to build a vendor's historical ERP scorecard."""
        with self._lock:
            cur = self._conn.cursor()
            vendor = cur.execute(
                "SELECT * FROM vendors WHERE vendor_id = ?",
                (vendor_id,),
            ).fetchone()
            if vendor is None:
                return None

            agg = cur.execute(
                """
                SELECT
                    SUM(total_shipments) AS total_shipments,
                    SUM(on_time_shipments) AS on_time_shipments,
                    SUM(units_delivered) AS units_delivered,
                    SUM(defective_units) AS defective_units,
                    AVG(avg_lead_time_days) AS avg_lead_time_days
                FROM quarterly_deliveries
                WHERE vendor_id = ?
                """,
                (vendor_id,),
            ).fetchone()

            incidents = cur.execute(
                """
                SELECT incident_date, severity, summary, status
                FROM quality_incidents
                WHERE vendor_id = ?
                ORDER BY incident_date DESC
                """,
                (vendor_id,),
            ).fetchall()

        total_shipments = agg["total_shipments"] or 0
        on_time_shipments = agg["on_time_shipments"] or 0
        units_delivered = agg["units_delivered"] or 0
        defective_units = agg["defective_units"] or 0

        otd_pct = round((on_time_shipments / total_shipments) * 100.0, 2) if total_shipments else 0.0
        defect_pct = round((defective_units / units_delivered) * 100.0, 2) if units_delivered else 0.0

        return {
            "vendor_id": vendor["vendor_id"],
            "name": vendor["name"],
            "country": vendor["country"],
            "erp_tier": vendor["erp_tier"],
            "financial_rating": vendor["financial_rating"],
            "on_time_delivery_pct": otd_pct,
            "defect_rate_pct": defect_pct,
            "total_shipments_12m": total_shipments,
            "units_delivered_12m": units_delivered,
            "historical_avg_lead_time_days": round(float(agg["avg_lead_time_days"] or 0.0), 1),
            "certifications": {
                "iatf_16949_status": vendor["iatf_16949_status"],
                "iatf_16949_valid_until": vendor["iatf_valid_until"],
                "iso_14001_certified": bool(vendor["iso_14001_certified"]),
                "rohs_reach_verified": bool(vendor["rohs_reach_verified"]),
            },
            "recent_incidents": [dict(row) for row in incidents],
            "cache_hint": "Historical ERP scorecard refreshed daily at 02:00 UTC.",
        }
