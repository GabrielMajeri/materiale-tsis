"""Mock maritime, weather, and geopolitical disruption bulletin corpus for RAG search."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BulletinRecord:
    """A single maritime disruption bulletin with structured header and verbose RAG tail."""

    bulletin_id: str
    region: str
    published_at: str
    alert_severity: str
    estimated_delay_days: int
    summary: str
    text: str


def _format_bulletin(
    *,
    bulletin_id: str,
    region: str,
    corridor_label: str,
    published_at: str,
    alert_severity: str,
    estimated_delay_days: int,
    summary: str,
    telemetry_rows: list[str],
    manifest_rows: list[str],
    advisory_notes: str,
) -> BulletinRecord:
    """Build a bulletin whose top-3 retrieval footprint averages ~2,000 tokens total."""
    header = (
        f"BULLETIN_ID: {bulletin_id}\n"
        f"REGION: {region} ({corridor_label})\n"
        f"PUBLISHED_AT: {published_at}\n"
        f"ALERT_SEVERITY: {alert_severity}\n"
        f"ESTIMATED_DELAY_DAYS: {estimated_delay_days}\n"
        f"SUMMARY: {summary}\n"
    )
    telemetry_block = "[TELEMETRY_LOG]\n" + "\n".join(telemetry_rows) + "\n"
    manifest_block = "[VESSEL_ANCHORAGE_MANIFEST]\n" + "\n".join(manifest_rows) + "\n"
    archive_block = (
        "[ARCHIVE_AND_LEGAL_NOTICE]\n"
        f"{advisory_notes} "
        "Notice: Automatic Identification System (AIS) terrestrial and satellite transponder pings are "
        "archived at 15-minute resolution under EU Maritime Single Window Directive (EU) 2019/1239. "
        "Historical berth congestion indices, pilot boarding wait histograms, bunker fuel sulfur-cap "
        "compliance telemetry (IMO 2020 Annex VI), and regional hydrographic meteorological station logs "
        "are included verbatim for downstream compliance auditability. Port authority slot allocations "
        "remain subject to Force Majeure Clauses 14.b and 19.c under standard BIMCO liner terms, and "
        "shippers are advised to retain full raw telemetry payloads in immutable procurement audit trails "
        "for a minimum retention horizon of sixty (60) calendar months across ERP archive partitions. "
        "Verification checksums, NAVTEX station relay headers, and VHF Coastal Broadcast transcripts are "
        "appended in standardized UTC epoch serialization without lossy truncation by the RAG ingestion "
        "pipeline so secondary risk underwriters can verify raw navigational warnings independently.\n"
    )
    full_text = f"{header}\n{telemetry_block}\n{manifest_block}\n{archive_block}"
    return BulletinRecord(
        bulletin_id=bulletin_id,
        region=region,
        published_at=published_at,
        alert_severity=alert_severity,
        estimated_delay_days=estimated_delay_days,
        summary=summary,
        text=full_text,
    )


def _build_corpus() -> list[BulletinRecord]:
    specs = [
        # --- 1. south_china_sea_red_sea (6 bulletins) ---
        dict(
            bulletin_id="MAR-2026-1101",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-18T06:00:00Z",
            alert_severity="CRITICAL",
            estimated_delay_days=14,
            summary=(
                "Bab el-Mandeb security threat escalates; major container alliances suspend Suez transits "
                "from CNSHA/Yantian to ROCND and reroute around Cape of Good Hope (+14 days transit, +$1,450/TEU war-risk surcharge)."
            ),
            telemetry_rows=[
                "2026-11-18T01:00Z | Sector=Bab-el-Mandeb-12N43E | TransitCount=4 (-78% vs baseline) | RiskLevel=CRITICAL | UKMTO_Advisory=Active",
                "2026-11-18T02:30Z | Sector=Suez-South-Anchorage | QueueVessels=11 | AvgWaitHours=38.4 | BunkerSpread_VLSFO=+$94/mt",
                "2026-11-18T04:15Z | Sector=Cape-Good-Hope-Diversion | ReroutedTEUs=412000 | AddedDistanceNM=3480 | SpeedKnots=17.2",
                "2026-11-18T05:45Z | Sector=CNSHA-Yangshan-Berth4 | CraneMovesPerHour=24.1 | YardDensity=91% | FeederBacklog=52h",
            ],
            manifest_rows=[
                "IMO 9842110 MV NORDIC HORIZON | CNSHA -> ROCND | Status: DIVERTED_CAPE | Delay: +14d | Cargo: Electronics/Auto",
                "IMO 9795542 MV PACIFIC STARLIGHT | CNSHA -> NLRTM | Status: DIVERTED_CAPE | Delay: +13d | Cargo: Containers",
                "IMO 9910328 MV AEGEAN TRADER | CNSZX -> ROCND | Status: HELD_PORT_SAID | Delay: +11d | Cargo: Semiconductor Reels",
            ],
            advisory_notes=(
                "Joint Maritime Information Center (JMIC) Threat Bulletin 2026-44 warns commercial semiconductor and "
                "electronics carriers departing CNSHA and CNSZX along south_china_sea_red_sea routes face mandatory "
                "insurance war-risk riders and prolonged Cape diversions."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-1102",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-17T18:30:00Z",
            alert_severity="HIGH",
            estimated_delay_days=11,
            summary=(
                "Typhoon Krosa outer rainbands close Shanghai Yangshan (CNSHA) container terminals for 36 hours; "
                "feeder schedules to Singapore transshipment hub disrupted by 4 to 11 days."
            ),
            telemetry_rows=[
                "2026-11-17T12:00Z | Station=Yangshan-Met-02 | GustKnots=58kt | WaveHeightM=4.6 | Pilotage=SUSPENDED",
                "2026-11-17T14:00Z | Station=EastChinaSea-Buoy19 | PressureHPa=968 | VisibilityNM=0.4 | ChannelStatus=CLOSED",
                "2026-11-17T16:30Z | Station=Singapore-PSA-Tuas | TransshipmentDwellDays=6.8 | BerthUtilization=94% | BlankSailings=7",
                "2026-11-17T18:00Z | Station=Malacca-Strait-VTIS | TrafficDensity=HIGH | ConvoySpacingNM=2.1 | DelayTrend=WORSENING",
            ],
            manifest_rows=[
                "IMO 9811402 MV SHANGHAI EXPRESS | CNSHA -> SGSIN | Status: ANCHORED_OUTER | Delay: +5d | Cargo: Industrial MCUs",
                "IMO 9754209 MV CORAL DYNASTY | CNSHA -> ROCND | Status: SKIPPED_PORT_CALL | Delay: +11d | Cargo: Mixed TEU",
                "IMO 9889123 MV PEARL RIVER | CNNBO -> SGSIN | Status: WEATHER_HOLD | Delay: +4d | Cargo: Automotive Parts",
            ],
            advisory_notes=(
                "Shanghai Maritime Safety Administration suspended pilot boarding across Yangtze Estuary and Yangshan "
                "Deepwater Port, compounding south_china_sea_red_sea schedule unreliability."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-1103",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-16T09:15:00Z",
            alert_severity="HIGH",
            estimated_delay_days=12,
            summary=(
                "Singapore and Port Klang transshipment hubs report 6-day container dwell spikes due to bunched "
                "Cape-rerouted East Asia-to-Europe loops; Constanta (ROCND) feeders delayed."
            ),
            telemetry_rows=[
                "2026-11-16T03:00Z | Hub=SGSIN-PasirPanjang | AnchoredVessels=44 | MedianWaitHours=82.5 | YardOccupancy=93%",
                "2026-11-16T05:00Z | Hub=MYPKG-Westports | FeederTurnaroundHours=54.0 | ChassisAvailability=TIGHT | RollRate=22%",
                "2026-11-16T07:00Z | Hub=EGPSD-PortSaid-Feeder | BlackSeaConnections=REDUCED | WaitDays=4.5 | PrioritySlots=NONE",
                "2026-11-16T09:00Z | Hub=ROCND-Feeder-Link | ExpectedSlippageDays=12 | ReliabilityIndex=41% | ReeferPlugs=98%",
            ],
            manifest_rows=[
                "IMO 9823401 MV MEDITERRANEAN LINK | SGSIN -> ROCND | Status: ROLLOVER_CARGO | Delay: +12d | Cargo: Semiconductors",
                "IMO 9740991 MV ASIAN FORTUNE | CNSHA -> EGPSD | Status: REROUTED | Delay: +10d | Cargo: Electronics",
                "IMO 9900112 MV DANUBE CARRIER | EGPSD -> ROCND | Status: WAITING_FEEDER | Delay: +6d | Cargo: Consolidated",
            ],
            advisory_notes=(
                "Drewry East-West congestion tracker flags acute schedule bunching on south_china_sea_red_sea lanes, "
                "with vessel reliability falling below 45% for Constanta-bound shipments."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-1104",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-14T11:00:00Z",
            alert_severity="HIGH",
            estimated_delay_days=10,
            summary=(
                "Joint War Committee maintains Red Sea High-Risk Area designation; emergency bunker and security "
                "surcharges add $900-$1,400/TEU on CNSHA-ROCND bills of lading."
            ),
            telemetry_rows=[
                "2026-11-14T06:00Z | Policy=JWC-HRA-RedSea | HullWarPremiumPct=0.75% | TransitInsurance=SURCHARGE_ACTIVE",
                "2026-11-14T07:30Z | Index=SCFI-Shanghai-Med | SpotRateDelta=+34% | EquipmentImbalance=40HC_SHORTAGE",
                "2026-11-14T09:00Z | Route=CNSHA-Cape-Gibraltar-ROCND | SeaDays=39 | ReliabilityPct=44% | BunkerBurnTonDay=68",
                "2026-11-14T10:45Z | Advisory=EU-Naval-Aspides | EscortWaitDays=5 | CommercialVesselsGuided=18",
            ],
            manifest_rows=[
                "IMO 9861120 MV ORIENTAL TRIDENT | CNSHA -> ROCND | Status: SURCHARGE_APPLIED | Delay: +10d | Cargo: Auto",
                "IMO 9712884 MV RED SEA PIONEER | CNSZX -> GRPIR | Status: ESCORT_QUEUE | Delay: +9d | Cargo: Tech",
                "IMO 9855301 MV BLACK SEA HORIZON | GRPIR -> ROCND | Status: FEEDER_DELAYED | Delay: +4d | Cargo: General",
            ],
            advisory_notes=(
                "Underwriters require 72-hour advance voyage declaration for any vessel transiting south_china_sea_red_sea "
                "corridor waypoints south of 18N latitude."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-1105",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-12T15:40:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=7,
            summary=(
                "South China Sea seasonal monsoon swell slows feeder barges out of Pearl River Delta and Yantian; "
                "customs export inspections add 48-hour gate-in holds for dual-use microcontrollers."
            ),
            telemetry_rows=[
                "2026-11-12T10:00Z | Sector=PearlRiverDelta-Barge | WindForce=7Bft | BargeDelayHours=32 | GateHold=48h",
                "2026-11-12T11:30Z | Sector=CNSHA-Customs-HS8542 | InspectionRate=18% | HoldMedianHours=46 | ClearanceQueue=HIGH",
                "2026-11-12T13:15Z | Sector=Spratly-Nav-Warn | WavePeriodS=11 | DiversionRoute=Palawan | AddedHours=19",
                "2026-11-12T15:00Z | Sector=Malacca-Westbound | TrafficIndex=88 | SpeedRestrictionKnots=12 | Queue=MODERATE",
            ],
            manifest_rows=[
                "IMO 9803344 MV GUANGDONG FEEDER | CNSZX -> HKHKG | Status: CUSTOMS_HOLD | Delay: +3d | Cargo: Integrated Circuits",
                "IMO 9871290 MV SUEZ MARINER | HKHKG -> ROCND | Status: DELAYED_DEPARTURE | Delay: +7d | Cargo: Electronics",
                "IMO 9766510 MV CELTIC VOYAGER | CNSHA -> ROCND | Status: SLOW_STEAM | Delay: +6d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Export customs verification on HS 8542 automotive microcontrollers compounds transit volatility across "
                "south_china_sea_red_sea departure terminals."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-1106",
            region="south_china_sea_red_sea",
            corridor_label="South China Sea / Red Sea / Suez Corridor",
            published_at="2026-11-10T08:00:00Z",
            alert_severity="HIGH",
            estimated_delay_days=9,
            summary=(
                "Blank sailings on Asia-East Mediterranean alliance loops cut weekly capacity to Piraeus and Constanta "
                "by 28%, pushing spot container rates and rollover risk sharply higher."
            ),
            telemetry_rows=[
                "2026-11-10T02:00Z | Loop=AEM-EastMed-Weekly | BlankedDepartures=3/11 | EffectiveCapacity=-28% | RollRisk=HIGH",
                "2026-11-10T04:00Z | Port=GRPIR-Piraeus-Pier3 | FeederWaitDays=4.2 | DwellTimeHours=112 | CraneOutage=1",
                "2026-11-10T06:00Z | Port=CNSHA-ExportGate | AllocationTightness=SEVERE | Empty40FT=SCARCE | BookingLead=14d",
                "2026-11-10T07:45Z | Corridor=south_china_sea_red_sea | CompositeDisruptionScore=8.9/10 | Trend=ELEVATED",
            ],
            manifest_rows=[
                "IMO 9894412 MV AEGEAN BRIDGE | CNSHA -> GRPIR | Status: BLANK_SAILING | Delay: +9d | Cargo: Auto Components",
                "IMO 9833219 MV LEVANT SPIRIT | GRPIR -> ROCND | Status: REBOOKED_NEXT_WEEK | Delay: +7d | Cargo: Electronics",
                "IMO 9771005 MV YANGTZE CROWN | CNNBO -> ROCND | Status: ROLLED | Delay: +8d | Cargo: Electrical",
            ],
            advisory_notes=(
                "Procurement teams relying on single-source south_china_sea_red_sea ocean routes are advised to hold "
                "minimum 21-day safety stock or qualify European short-sea alternatives."
            ),
        ),
        # --- 2. north_sea_danube (6 bulletins) ---
        dict(
            bulletin_id="MAR-2026-2101",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-18T07:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Port of Hamburg (DEHAM) container terminals and Rhine-Main-Danube / rail-barge intermodal corridors "
                "to Constanta (ROCND) report normal operations, 97% schedule reliability, and zero lock closures."
            ),
            telemetry_rows=[
                "2026-11-18T01:00Z | Port=DEHAM-CTA-Altenwerder | CraneProductivity=36.4MPH | TruckTurnaroundMin=29 | BerthWait=0.8h",
                "2026-11-18T03:00Z | Waterway=Danube-Lock-IronGates1 | WaterLevelCM=412 | LockQueueVessels=0 | TransitStatus=NORMAL",
                "2026-11-18T05:00Z | Rail=Hamburg-Curtici-Constanta-Shuttle | OnTimePct=96.8% | BorderWaitHours=1.2 | Capacity=OPEN",
                "2026-11-18T06:45Z | SeaLane=DEHAM-Gibraltar-ROCND | SeaState=2 | VisibilityNM=10+ | WeatherAlert=NONE",
            ],
            manifest_rows=[
                "IMO 9819204 MV ELBE TRADER | DEHAM -> ROCND | Status: ON_SCHEDULE | Delay: 0d | Cargo: Automotive MCUs",
                "BARGE RMD-408 DANUBE STAR | DEHAM/REGENSBURG -> ROCND | Status: CLEARED_LOCK | Delay: 0d | Cargo: High-Tech",
                "BLOCK-TRAIN DE-RO-772 | DEHAM -> ROCND | Status: IN_TRANSIT_ON_TIME | Delay: 0d | Cargo: Electronics",
            ],
            advisory_notes=(
                "German and Romanian transport ministries confirm unobstructed intermodal and short-sea flow across the "
                "north_sea_danube corridor with customs pre-clearance active under EU Single Market rules."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-2102",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-17T14:20:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Minor 6-hour scheduled night maintenance at Danube Gabcikovo right chamber; bypass chamber remains open "
                "with under 1 day impact on DEHAM-to-ROCND barge connections."
            ),
            telemetry_rows=[
                "2026-11-17T08:00Z | Lock=SK-Gabcikovo-Right | MaintenanceWindow=00:00-06:00Z | LeftChamber=OPERATIONAL | Wait=4h",
                "2026-11-17T10:00Z | Gauge=Budapest-Danube | StageCM=345 | NavigableDepthM=3.2 | LoadFactorAllowed=100%",
                "2026-11-17T12:00Z | Port=DEHAM-Burchardkai | YardDensity=68% | RailSidingUtilization=74% | Congestion=NONE",
                "2026-11-17T14:00Z | Corridor=north_sea_danube | CompositeDisruptionScore=1.2/10 | Trend=STABLE",
            ],
            manifest_rows=[
                "BARGE RMD-215 CARPATHIA | PASSAU -> ROCND | Status: TRANSITING_LEFT_CHAMBER | Delay: 0.2d | Cargo: Auto Parts",
                "IMO 9840092 MV HANSA CARRIER | DEHAM -> NLRTM | Status: ON_TIME | Delay: 0d | Cargo: Semiconductors",
                "BARGE RMD-502 SILICON LINE | REGENSBURG -> ROCND | Status: ON_SCHEDULE | Delay: 0d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Danube Commission hydrological forecast indicates stable water levels for the next 21 days along the "
                "entire north_sea_danube inland and Black Sea river-sea interface."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-2103",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-15T10:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "North Sea autumn wind front passes without port closures at Hamburg or Rotterdam; English Channel and "
                "Western Med short-sea feeders maintain normal timetable."
            ),
            telemetry_rows=[
                "2026-11-15T04:00Z | Station=Elbe-Pilot-Helgoland | WindKnots=21kt | WaveHeightM=1.8 | PilotBoarding=NORMAL",
                "2026-11-15T06:00Z | Station=Dover-Strait-VTIS | TrafficFlow=UNRESTRICTED | FogVisibility=8NM | Delays=0h",
                "2026-11-15T08:00Z | Port=ROCND-Constanta-South | Berth4-Gate=OPEN | CustomsClearanceEU=INSTANT | Yard=61%",
                "2026-11-15T09:45Z | Corridor=north_sea_danube | ScheduleAdherence=97.4% | WeatherRisk=LOW",
            ],
            manifest_rows=[
                "IMO 9874410 MV BALTIC PIONEER | DEHAM -> ROCND | Status: UNDERWAY_NOMINAL | Delay: 0d | Cargo: Electronics",
                "IMO 9761188 MV NORTH SEA LINK | DEHAM -> BEANR | Status: BERTHED_ON_TIME | Delay: 0d | Cargo: Machinery",
                "BLOCK-TRAIN DE-RO-768 | DEHAM -> ROCND | Status: DELIVERED | Delay: 0d | Cargo: Semiconductor Modules",
            ],
            advisory_notes=(
                "Intra-EU origin documentation removes third-country customs border bottlenecks for DEHAM -> ROCND "
                "shipments via north_sea_danube logistics channels."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-2104",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-13T16:45:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Constanta Danube-Black Sea Canal Lock Cernavoda reports smooth throughput; zero backlog for "
                "north_sea_danube container barges and coastal feeders."
            ),
            telemetry_rows=[
                "2026-11-13T10:00Z | Canal=Cernavoda-Agigea | LockCycleMin=38 | QueueLength=1 | WaterDepthM=7.0",
                "2026-11-13T12:00Z | Port=ROCND-DPW-Terminal | CraneAvailability=100% | DwellHours=14.2 | GateQueue=5min",
                "2026-11-13T14:00Z | Rail=Arad-Bucharest-Constanta | AxleLoad=NORMAL | SpeedRestriction=NONE | OnTime=98%",
                "2026-11-13T16:30Z | Corridor=north_sea_danube | ReliabilityScore=9.6/10 | DisruptionProbability=5%",
            ],
            manifest_rows=[
                "BARGE RMD-119 STUTTGART | VIENNA -> ROCND | Status: CLEARED_CERNAVODA | Delay: 0d | Cargo: Auto Electronics",
                "IMO 9912304 MV BLACK SEA FEEDER | DEHAM -> ROCND | Status: ETA_ON_TIME | Delay: 0d | Cargo: High-Value",
                "BARGE RMD-310 MUNICH | REGENSBURG -> ROCND | Status: DISCHARGING | Delay: 0d | Cargo: Precision Parts",
            ],
            advisory_notes=(
                "All primary and secondary intermodal gateways on the north_sea_danube route operate well below "
                "congestion thresholds with spare weekly slot capacity."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-2105",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-11T09:30:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Hamburg Eurogate and CTA terminals expand automated night-shift rail loading slots for Southeastern "
                "Europe automotive supply chains."
            ),
            telemetry_rows=[
                "2026-11-11T03:00Z | Port=DEHAM-Eurogate | RailShuntsPerDay=42 | NightSlotsAdded=+6 | DwellHours=18",
                "2026-11-11T05:00Z | Customs=EU-T2L-Status | BorderChecks=EXEMPT_INTRA_EU | ReleaseTimeMin=12",
                "2026-11-11T07:00Z | River=Main-Danube-Bamberg | IceRisk=NONE | TemperatureC=7.5 | FlowRate=NOMINAL",
                "2026-11-11T09:15Z | Corridor=north_sea_danube | SLA_Compliance=98.2% | AlertStatus=GREEN",
            ],
            manifest_rows=[
                "BLOCK-TRAIN DE-RO-760 | DEHAM -> ROCND | Status: DEPARTED_ON_TIME | Delay: 0d | Cargo: Inverter MCUs",
                "IMO 9820015 MV RHEIN EXPRESS | DEHAM -> NLRTM | Status: ON_SCHEDULE | Delay: 0d | Cargo: Containers",
                "BARGE RMD-604 DANUBIA | PASSAU -> ROCND | Status: TRANSITING | Delay: 0d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Enhanced Hamburg-to-Constanta rail-barge redundancy keeps north_sea_danube transit variance under 12 hours."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-2106",
            region="north_sea_danube",
            corridor_label="North Sea / Hamburg / Rhine-Main-Danube Corridor",
            published_at="2026-11-09T13:10:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Light morning river mist near Regensburg briefly reduced barge night speed; schedule recovered within "
                "16 hours with negligible impact on Constanta delivery windows."
            ),
            telemetry_rows=[
                "2026-11-09T06:00Z | Gauge=Regensburg-Km2379 | VisibilityM=350 | SpeedAdvisory=REDUCED | ClearedAt=10:00Z",
                "2026-11-09T09:00Z | Port=DEHAM-Weather | WindKnots=14kt | TideLevel=NORMAL | CraneDelay=0h",
                "2026-11-09T11:00Z | Port=ROCND-Terminal | ReceivingCapacity=OPEN | CustomsQueue=NONE | Turnaround=18min",
                "2026-11-09T13:00Z | Corridor=north_sea_danube | DelayImpactDays=0-1 | Status=GREEN",
            ],
            manifest_rows=[
                "BARGE RMD-104 BAVARIA | REGENSBURG -> ROCND | Status: RESUMED_FULL_SPEED | Delay: 0.5d | Cargo: Auto",
                "IMO 9808877 MV HANSEATIC | DEHAM -> ROCND | Status: ON_SCHEDULE | Delay: 0d | Cargo: Tech",
                "BLOCK-TRAIN DE-RO-755 | DEHAM -> ROCND | Status: ARRIVED | Delay: 0d | Cargo: Semiconductor Reels",
            ],
            advisory_notes=(
                "Seasonal river mist advisories on the upper Danube remain minor and do not impair north_sea_danube SLAs."
            ),
        ),
        # --- 3. black_sea_bosporus (6 bulletins) ---
        dict(
            bulletin_id="MAR-2026-3101",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-18T05:30:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=3,
            summary=(
                "Autumn sea fog and southbound tanker traffic priority create 48-to-72 hour Bosporus Strait northbound "
                "wait queues for feeder vessels sailing from Izmir (TRIZM) to Constanta (ROCND)."
            ),
            telemetry_rows=[
                "2026-11-18T00:00Z | Strait=Bosporus-Northbound | VisibilityNM=0.6 | SuspendedHours=10 | QueueVessels=29",
                "2026-11-18T02:00Z | Strait=Dardanelles-Marmara | PilotQueueHours=18.5 | ConvoyDirection=SOUTHBOUND_PRIORITY",
                "2026-11-18T04:00Z | Port=TRIZM-Alsancak-Container | CraneQueue=14h | CustomsExportHold=6h | BerthUtil=84%",
                "2026-11-18T05:15Z | Corridor=black_sea_bosporus | EstimatedTransitSlip=3d | WarRiskZone=NORTH_ONLY",
            ],
            manifest_rows=[
                "IMO 9732104 MV ANATOLIA FEEDER | TRIZM -> ROCND | Status: ANCHORED_MARMARA | Delay: +3d | Cargo: Electronics",
                "IMO 9699012 MV MARMARA SPIRIT | TRIZM -> BGVAR | Status: PILOT_QUEUE | Delay: +2d | Cargo: Auto Parts",
                "IMO 9804551 MV BOSPORUS STAR | TRAMB -> ROCND | Status: FOG_HOLD | Delay: +3d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Turkish Directorate General of Coastal Safety alternates one-way strait transits during morning fog, "
                "adding 2-3 days on black_sea_bosporus short-sea runs."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-3102",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-16T19:00:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=2,
            summary=(
                "Black Sea Naval Mine Countermeasure sweeps near western shipping lanes require mandatory daytime "
                "corridor routing into Constanta (ROCND), adding 1-2 days to TRIZM feeder voyages."
            ),
            telemetry_rows=[
                "2026-11-16T12:00Z | NAVTEX=BlackSea-Warn-419 | Corridor=Western-Coastal-Lane | NightTransit=RESTRICTED",
                "2026-11-16T14:30Z | Port=ROCND-OuterAnchorage | InspectionWaitHours=16.0 | CustomsNonEU=22h | Priority=PASSENGER",
                "2026-11-16T17:00Z | Port=TRIZM-NemrutBay | FeederLoadingDelay=12h | GateCongestion=MODERATE | Cranes=ACTIVE",
                "2026-11-16T18:45Z | Corridor=black_sea_bosporus | RiskLevel=MEDIUM | InsuranceAddon=+$110/TEU",
            ],
            manifest_rows=[
                "IMO 9751120 MV PONTIC BREEZE | TRIZM -> ROCND | Status: DAYLIGHT_CONVOY | Delay: +2d | Cargo: Components",
                "IMO 9811900 MV IZMIR EXPRESS | TRIZM -> ROCND | Status: CUSTOMS_INSPECTION | Delay: +2d | Cargo: Auto MCUs",
                "IMO 9723480 MV THRACE TRADER | TRIST -> ROCND | Status: ANCHOR_WAIT | Delay: +1d | Cargo: General TEU",
            ],
            advisory_notes=(
                "Non-EU customs declarations and Black Sea coastal convoy windows introduce recurring 2-day variability "
                "along the black_sea_bosporus maritime lane."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-3103",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-14T10:15:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=2,
            summary=(
                "Izmir Alsancak container berth gantry crane maintenance reduces terminal throughput by 20% this week; "
                "customs ATR/EUR.1 inspection queue adds 1 day for EU-bound electronics."
            ),
            telemetry_rows=[
                "2026-11-14T04:00Z | Port=TRIZM-Alsancak | ActiveGantries=4/5 | VesselTurnaroundHours=39 | YardFill=86%",
                "2026-11-14T06:30Z | Customs=TR-EU-ATR-Check | PhysicalExamRate=14% | ClearanceHours=26 | PaperworkHold=HIGH",
                "2026-11-14T08:30Z | Strait=Canakkale-North | CurrentKnots=3.8 | PilotDelayHours=11 | Queue=19_SHIPS",
                "2026-11-14T10:00Z | Corridor=black_sea_bosporus | DelayRangeDays=2-3 | Trend=PERSISTENT",
            ],
            manifest_rows=[
                "IMO 9788231 MV AEGEAN SUN | TRIZM -> ROCND | Status: BERTH_WAIT | Delay: +2d | Cargo: Electronics",
                "IMO 9684420 MV CONSTANTZA LINK | TRIZM -> ROCND | Status: CUSTOMS_HOLD | Delay: +2d | Cargo: Semiconductors",
                "IMO 9830019 MV GALATA STAR | TRGEM -> ROCND | Status: SLOW_TRANSIT | Delay: +1d | Cargo: Machinery",
            ],
            advisory_notes=(
                "Suppliers shipping out of TRIZM must validate Turkish-EU customs certificates 48 hours prior to vessel "
                "cutoff to avoid missed black_sea_bosporus feeder sailings."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-3104",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-12T08:45:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Strong northeasterly Black Sea winds eased overnight; Bosporus Strait backlog clearing gradually with "
                "residual 24-hour feeder schedule slippage."
            ),
            telemetry_rows=[
                "2026-11-12T02:00Z | Station=Rumeli-Feneri | WindKnots=24kt | WaveHeightM=2.1 | StraitStatus=OPEN_ONE_WAY",
                "2026-11-12T04:30Z | Strait=Bosporus-Queue | RemainingVessels=16 | AvgWaitHours=21 | ClearanceRate=HIGH",
                "2026-11-12T07:00Z | Port=ROCND-Gate | NonEU_CustomsWait=14h | BerthAvailability=GOOD | Yard=65%",
                "2026-11-12T08:30Z | Corridor=black_sea_bosporus | ResidualDelayDays=1 | Trend=IMPROVING",
            ],
            manifest_rows=[
                "IMO 9791200 MV BLACK SEA RUNNER | TRIZM -> ROCND | Status: CLEARED_STRAIT | Delay: +1d | Cargo: Auto Parts",
                "IMO 9719934 MV EGE FEEDER | TRIZM -> BGVAR | Status: EN_ROUTE | Delay: +1d | Cargo: Containers",
                "IMO 9842290 MV DOBROGEA | TRAMB -> ROCND | Status: BERTHING | Delay: +1d | Cargo: Electrical",
            ],
            advisory_notes=(
                "Residual queue clearance along the black_sea_bosporus route remains subject to winter cold-front spikes."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-3105",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-10T14:00:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=3,
            summary=(
                "Elevated grain-corridor bulk carrier density in the Sea of Marmara slows container feeder transit slots "
                "through the Turkish Straits by up to 3 days."
            ),
            telemetry_rows=[
                "2026-11-10T08:00Z | Sector=Marmara-Anchorage | BulkCarriersWaiting=58 | ContainerSlotPriority=STANDARD",
                "2026-11-10T10:30Z | Strait=Bosporus-VTS | NorthboundSlotsPerDay=18 | FeederWaitHours=52 | TugAvailability=TIGHT",
                "2026-11-10T12:30Z | Port=TRIZM-Gate | TruckQueueHours=5.5 | ContainerDepot=82% | FeederFreq=3xWeekly",
                "2026-11-10T13:50Z | Corridor=black_sea_bosporus | DelayDays=3 | ReliabilityIndex=74%",
            ],
            manifest_rows=[
                "IMO 9760011 MV MARMARA FEEDER | TRIZM -> ROCND | Status: SLOT_WAIT | Delay: +3d | Cargo: Electronics",
                "IMO 9829941 MV BALKAN TRADER | TRIST -> ROCND | Status: DELAYED | Delay: +2d | Cargo: Auto",
                "IMO 9705533 MV ODESSA STAR | TRIZM -> ROCND | Status: ANCHORED | Delay: +3d | Cargo: Mixed",
            ],
            advisory_notes=(
                "High bulk vessel volume through the Turkish Straits routinely displaces smaller container feeders in the "
                "black_sea_bosporus corridor."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-3106",
            region="black_sea_bosporus",
            corridor_label="Black Sea / Turkish Straits / Bosporus Corridor",
            published_at="2026-11-08T11:20:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Routine customs tariff audit update at Izmir port causes minor 18-hour manifest re-filing delay for "
                "automotive electrical subassemblies."
            ),
            telemetry_rows=[
                "2026-11-08T06:00Z | Port=TRIZM-Customs | ElectronicManifestUpdate=ACTIVE | AvgHoldHours=18 | Backlog=LOW",
                "2026-11-08T08:30Z | Strait=Dardanelles | TransitNormal=YES | PilotWaitHours=4.5 | Visibility=GOOD",
                "2026-11-08T10:00Z | Port=ROCND-Terminal | DischargeRate=31MPH | CustomsExam=STANDARD | Queue=LOW",
                "2026-11-08T11:10Z | Corridor=black_sea_bosporus | ImpactDays=1 | Alert=LOW",
            ],
            manifest_rows=[
                "IMO 9743310 MV SMYRNA BAY | TRIZM -> ROCND | Status: MANIFEST_CLEARED | Delay: +1d | Cargo: Electrical",
                "IMO 9810022 MV PONTUS | TRIZM -> BGVAR | Status: UNDERWAY | Delay: 0d | Cargo: Containers",
                "IMO 9778899 MV CARPATHIAN SEA | TRAMB -> ROCND | Status: ON_TIME | Delay: 0d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Paperwork compliance audits remain a secondary latency factor on black_sea_bosporus export sailings."
            ),
        ),
        # --- 4. adriatic_mediterranean (6 bulletins) ---
        dict(
            bulletin_id="MAR-2026-4101",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-18T06:45:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Port of Trieste (ITTRS) and Adriatic-Aegean feeder lane to Constanta (ROCND) running on normal schedule; "
                "light Bora wind gust forecast adds at most 12-24 hours buffer."
            ),
            telemetry_rows=[
                "2026-11-18T01:00Z | Port=ITTRS-Trieste-PierVII | CraneMPH=34.0 | WindGustKnots=28kt | BerthWait=2.1h",
                "2026-11-18T03:00Z | Sea=Adriatic-Otranto-Strait | WaveHeightM=1.9 | FeederSpeedKnots=16.8 | Delays=NONE",
                "2026-11-18T05:00Z | Hub=GRPIR-Feeder-Berth | IntraEU-Priority=YES | TransshipmentDwell=18h | Status=SMOOTH",
                "2026-11-18T06:30Z | Corridor=adriatic_mediterranean | DelayEstimate=1d | ReliabilityPct=94.5%",
            ],
            manifest_rows=[
                "IMO 9850123 MV ADRIATICA EXPRESS | ITTRS -> ROCND | Status: ON_SCHEDULE | Delay: 0.5d | Cargo: Automotive MCUs",
                "IMO 9792211 MV VENETO FEEDER | ITTRS -> GRPIR | Status: BERTHED | Delay: 0d | Cargo: Electronics",
                "IMO 9867740 MV IONIAN LINK | ITTRS -> ROCND | Status: UNDERWAY | Delay: 1d | Cargo: Industrial Tech",
            ],
            advisory_notes=(
                "Trieste Pier VII maintains continuous EU green-lane rail and sea connectivity across the "
                "adriatic_mediterranean network."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-4102",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-16T15:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Trieste-to-Constanta intra-EU feeder vessel frequency increased with an extra weekly sailing; "
                "customs transit under EU T2L procedure requires zero border inspection."
            ),
            telemetry_rows=[
                "2026-11-16T09:00Z | Port=ITTRS-Terminal7 | WeeklySailingsToBlackSea=3 | YardUtilization=64% | GateWait=11min",
                "2026-11-16T11:30Z | Sea=Ionian-Aegean-Lane | VisibilityNM=10+ | WindForce=4Bft | Routing=DIRECT",
                "2026-11-16T13:30Z | Customs=EU-T2L-Trieste-ROCND | InspectionDelay=0h | DigitalPreClearance=ACTIVE",
                "2026-11-16T14:50Z | Corridor=adriatic_mediterranean | Reliability=95.8% | DisruptionScore=1.5/10",
            ],
            manifest_rows=[
                "IMO 9881122 MV JULIA STAR | ITTRS -> ROCND | Status: DEPARTED_ON_TIME | Delay: 0d | Cargo: Semiconductors",
                "IMO 9773301 MV CORFU TRADER | ITTRS -> GRTHS | Status: ON_SCHEDULE | Delay: 0d | Cargo: Containers",
                "IMO 9904411 MV AQUILEIA | ITTRS -> ROCND | Status: LOADING | Delay: 0d | Cargo: Auto Systems",
            ],
            advisory_notes=(
                "Additional feeder capacity reinforces adriatic_mediterranean delivery stability for Italian and Central "
                "European semiconductor fabs."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-4103",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-13T12:15:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Moderate Aegean southerly swell slows feeder speed by 1.5 knots south of Peloponnese; "
                "1-day arrival buffer absorbed within standard SLA."
            ),
            telemetry_rows=[
                "2026-11-13T06:00Z | Sea=Aegean-South-36N24E | WaveHeightM=2.6 | SpeedAdjustment=-1.5kt | ImpactHours=18",
                "2026-11-13T08:30Z | Port=ITTRS-Gate | RailIntake=NORMAL | DwellHours=16 | CraneOutages=0",
                "2026-11-13T10:30Z | Port=ROCND-Terminal | BerthSlotGuaranteed=YES | UnloadingDelay=0h",
                "2026-11-13T12:00Z | Corridor=adriatic_mediterranean | ImpactDays=1 | Trend=STABLE",
            ],
            manifest_rows=[
                "IMO 9821990 MV DALMATIA | ITTRS -> ROCND | Status: SLIGHT_WEATHER_SLIP | Delay: +1d | Cargo: Electronics",
                "IMO 9784502 MV SALONIKA | GRPIR -> ROCND | Status: UNDERWAY | Delay: +1d | Cargo: Auto Parts",
                "IMO 9849001 MV TRIESTE BAY | ITTRS -> GRPIR | Status: ON_TIME | Delay: 0d | Cargo: General",
            ],
            advisory_notes=(
                "Adriatic and Aegean weather holds remain brief and well within adriatic_mediterranean carrier tolerances."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-4104",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-11T10:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Port of Trieste rail-sea intermodal terminal clears record container volume with zero gate delays; "
                "automated container scanning accelerates electronics release."
            ),
            telemetry_rows=[
                "2026-11-11T04:00Z | Port=ITTRS-RailTerminal | TrainsPerDay=26 | CraneMPH=35.2 | DwellHours=15",
                "2026-11-11T06:30Z | Sea=NorthAdriatic | WindForce=3Bft | PilotWait=0.5h | TugStatus=AVAILABLE",
                "2026-11-11T08:30Z | Security=EU-ISPS-Level1 | ClearanceSpeed=FAST | Queue=NONE",
                "2026-11-11T09:45Z | Corridor=adriatic_mediterranean | Status=GREEN | DelayDays=0",
            ],
            manifest_rows=[
                "IMO 9853320 MV SAN MARCO | ITTRS -> ROCND | Status: ON_SCHEDULE | Delay: 0d | Cargo: Microcontrollers",
                "IMO 9798801 MV ISTRIA LINK | ITTRS -> SITR | Status: ON_TIME | Delay: 0d | Cargo: Containers",
                "IMO 9870019 MV AEGEAN PEARL | ITTRS -> ROCND | Status: BERTHED | Delay: 0d | Cargo: Auto Modules",
            ],
            advisory_notes=(
                "High terminal automation makes ITTRS one of the lowest-variance adriatic_mediterranean embarkation ports."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-4105",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-09T17:30:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Piraeus feeder berth transfer window shifts 14 hours due to regional cruise vessel priority; "
                "subsequent Constanta leg stays inside 11-day transit cap."
            ),
            telemetry_rows=[
                "2026-11-09T11:00Z | Port=GRPIR-Feeder | ShiftHours=14 | BerthReassigned=Pier1-East | Dwell=24h",
                "2026-11-09T13:30Z | Port=ITTRS-Dispatch | DepartureOnTime=YES | StowagePlan=CONFIRMED",
                "2026-11-09T15:30Z | Strait=Dardanelles-North | WaitHours=8 | Pilotage=NORMAL",
                "2026-11-09T17:15Z | Corridor=adriatic_mediterranean | EstimatedDelay=1d | Status=NOMINAL",
            ],
            manifest_rows=[
                "IMO 9841223 MV MED FEEDER ONE | ITTRS -> ROCND | Status: MINOR_BERTH_SHIFT | Delay: +1d | Cargo: Tech",
                "IMO 9768810 MV OLYMPUS | GRPIR -> ROCND | Status: ON_SCHEDULE | Delay: 0d | Cargo: General",
                "IMO 9883400 MV TIMAVO | ITTRS -> GRPIR | Status: ARRIVED | Delay: 0d | Cargo: Electronics",
            ],
            advisory_notes=(
                "Minor Aegean port-window shifts do not materially threaten adriatic_mediterranean delivery schedules."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-4106",
            region="adriatic_mediterranean",
            corridor_label="Adriatic / Trieste / Eastern Mediterranean Corridor",
            published_at="2026-11-07T08:15:00Z",
            alert_severity="LOW",
            estimated_delay_days=0,
            summary=(
                "Clear autumn weather across Northern Adriatic and Ionian Sea; zero navigational restrictions for "
                "Trieste-Constanta container lines."
            ),
            telemetry_rows=[
                "2026-11-07T02:00Z | Station=Trieste-Barcola | WindKnots=9kt | WaveHeightM=0.5 | Visibility=12NM",
                "2026-11-07T04:30Z | Station=Corinth-Ionian-Buoy | SwellM=0.9 | TrafficFlow=NORMAL | Incidents=0",
                "2026-11-07T06:30Z | Port=ROCND-Receiving | CraneAvailability=100% | Dwell=13h | GateQueue=NONE",
                "2026-11-07T08:00Z | Corridor=adriatic_mediterranean | Status=CLEAR | DelayDays=0",
            ],
            manifest_rows=[
                "IMO 9861199 MV VENICE EXPRESS | ITTRS -> ROCND | Status: ON_TIME | Delay: 0d | Cargo: Semiconductors",
                "IMO 9790044 MV HELLAS TRADER | GRPIR -> ROCND | Status: ON_TIME | Delay: 0d | Cargo: Auto Parts",
                "IMO 9837711 MV FRIULI | ITTRS -> GRTHS | Status: ON_SCHEDULE | Delay: 0d | Cargo: Industrial",
            ],
            advisory_notes=(
                "Optimal hydrographic conditions persist across the adriatic_mediterranean shipping corridor."
            ),
        ),
        # --- 5. Global distractors (4 bulletins) so TF-IDF must rank accurately ---
        dict(
            bulletin_id="MAR-2026-9001",
            region="panama_transpacific",
            corridor_label="Panama Canal / Trans-Pacific Corridor",
            published_at="2026-11-17T12:00:00Z",
            alert_severity="MEDIUM",
            estimated_delay_days=4,
            summary=(
                "Gatun Lake draft restrictions limit Neopanamax lock transits to 32 vessels/day; US East Coast "
                "imports experience 4-day booking queues."
            ),
            telemetry_rows=[
                "2026-11-17T06:00Z | Canal=Panama-GatunLake | LevelFeet=83.2 | MaxDraftFeet=46.5 | DailySlots=32",
                "2026-11-17T08:00Z | Anchorage=Balboa-South | WaitingVessels=38 | AuctionSlotUSD=$410000 | Delay=4d",
                "2026-11-17T10:00Z | Port=USLAX-Pier400 | RailDwellDays=3.1 | ChassisPool=ADEQUATE | BerthWait=12h",
                "2026-11-17T11:45Z | Corridor=panama_transpacific | RiskLevel=MEDIUM | RelevanceToEurope=NONE",
            ],
            manifest_rows=[
                "IMO 9890123 MV PACIFIC BRIDGE | KRPUS -> USNYC | Status: LOCK_QUEUE | Delay: +4d | Cargo: Consumer Goods",
                "IMO 9817720 MV ISTHMUS STAR | JPTYO -> USSAV | Status: AUCTION_WAIT | Delay: +3d | Cargo: Machinery",
                "IMO 9758821 MV BALBOA BAY | CNYTN -> USLAX | Status: ON_TIME | Delay: 0d | Cargo: Retail",
            ],
            advisory_notes=(
                "Panama Canal Authority reviews Gatun Lake rainfall weekly for trans-Pacific and US East Coast routes."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-9002",
            region="west_africa_atlantic",
            corridor_label="West Africa / Gulf of Guinea Corridor",
            published_at="2026-11-15T14:00:00Z",
            alert_severity="HIGH",
            estimated_delay_days=8,
            summary=(
                "Lagos Apapa and Tema container terminals report 8-day anchorage congestion following regional port "
                "customs IT migration."
            ),
            telemetry_rows=[
                "2026-11-15T08:00Z | Port=NGAPP-Apapa | AnchoredShips=27 | WaitDays=8.0 | YardOccupancy=96%",
                "2026-11-15T10:00Z | Port=GHTEM-Tema | CustomsSystem=MIGRATING | GateOutPerHour=18 | Backlog=HIGH",
                "2026-11-15T12:00Z | Sector=GulfOfGuinea | MaritimeSecurity=LEVEL_2 | EscortRecommended=YES",
                "2026-11-15T13:45Z | Corridor=west_africa_atlantic | CompositeScore=7.4/10 | Trend=CONGESTED",
            ],
            manifest_rows=[
                "IMO 9741100 MV GUINEA TRADER | BEANR -> NGAPP | Status: ANCHOR_QUEUE | Delay: +8d | Cargo: Industrial",
                "IMO 9822301 MV ATLANTIC DAWN | FRLEH -> GHTEM | Status: CUSTOMS_WAIT | Delay: +6d | Cargo: General",
                "IMO 9694401 MV VOLTA LINK | ESALG -> CIABJ | Status: BERTHED | Delay: +2d | Cargo: Machinery",
            ],
            advisory_notes=(
                "West African Maritime Trade Organization coordinates staggered vessel arrivals during customs cutover."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-9003",
            region="baltic_ice_corridor",
            corridor_label="Gulf of Finland / Northern Baltic Corridor",
            published_at="2026-11-14T09:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "Finnish and Swedish maritime administrations position winter icebreaker fleet at Bothnian Bay ports "
                "ahead of seasonal freeze; Helsinki and Gdansk remain ice-free."
            ),
            telemetry_rows=[
                "2026-11-14T03:00Z | Sector=BothnianBay | SeaTempC=1.4 | IceClassRequired=NONE_YET | Icebreakers=STANDBY",
                "2026-11-14T05:30Z | Port=PLGDN-DeepwaterDCT | CraneMPH=33.8 | RailTurnaround=NORMAL | Congestion=LOW",
                "2026-11-14T07:30Z | Port=FIHEL-Vuosaari | BerthWait=1.2h | YardFill=62% | Schedule=ON_TIME",
                "2026-11-14T08:50Z | Corridor=baltic_ice_corridor | Status=PREPARATORY | ImpactDays=0-1",
            ],
            manifest_rows=[
                "IMO 9859902 MV FINNLAND | DEHAM -> FIHEL | Status: ON_SCHEDULE | Delay: 0d | Cargo: Paper/Machinery",
                "IMO 9774419 MV GDANSK EXPRESS | NLRTM -> PLGDN | Status: BERTHED | Delay: 0d | Cargo: Containers",
                "IMO 9813320 MV BOTHNIA | SEGOT -> FIOUL | Status: UNDERWAY | Delay: 0d | Cargo: Timber",
            ],
            advisory_notes=(
                "Ice class 1A restrictions are not anticipated in the southern Baltic or North Sea gateways."
            ),
        ),
        dict(
            bulletin_id="MAR-2026-9004",
            region="st_lawrence_great_lakes",
            corridor_label="St. Lawrence Seaway / Great Lakes Corridor",
            published_at="2026-11-10T16:00:00Z",
            alert_severity="LOW",
            estimated_delay_days=1,
            summary=(
                "St. Lawrence Seaway announces December seasonal lock closure schedule; Montreal container terminals "
                "operate smoothly with minor rail dwell."
            ),
            telemetry_rows=[
                "2026-11-10T10:00Z | Seaway=Montreal-LakeOntario | ClosingNotice=DEC_29 | CurrentQueue=2_SHIPS | Flow=NORMAL",
                "2026-11-10T12:00Z | Port=CAMTR-Montreal | RailDwellDays=2.4 | GateWait=22min | YardUtil=71%",
                "2026-11-10T14:00Z | Weather=NorthAtlantic | LowPressureTrack=EASTBOUND | SwellM=3.1 | Speed=NORMAL",
                "2026-11-10T15:45Z | Corridor=st_lawrence_great_lakes | Alert=LOW | DelayDays=1",
            ],
            manifest_rows=[
                "IMO 9801122 MV LAURENTIAN | BEANR -> CAMTR | Status: ON_TIME | Delay: 0d | Cargo: Auto Parts",
                "IMO 9739910 MV ONTARIO BULK | CAMTR -> USCLE | Status: TRANSITING_LOCKS | Delay: +1d | Cargo: Alloys",
                "IMO 9875541 MV QUEBEC LINK | NLRTM -> CAMTR | Status: UNDERWAY | Delay: 0d | Cargo: Machinery",
            ],
            advisory_notes=(
                "Great Lakes seasonal closing schedules apply strictly to North American inland waterways."
            ),
        ),
    ]
    return [_format_bulletin(**spec) for spec in specs]


MARITIME_BULLETINS: list[BulletinRecord] = _build_corpus()
