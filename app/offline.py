"""Deterministic case fixtures used when no Gemini key is available.

These are hand-written from the same corpus the agent retrieves over. Nothing
here is model output — the API labels every response built this way as
`mode: "offline"` so a fixture is never mistaken for a real agent run.
"""

from __future__ import annotations

from app.models import WorkOrder
from app.rag import retrieve

ASSET_KEYWORDS = {
    "HAAS-VF2-04": ("spindle", "haas", "vf-2", "vf2", "overtemp", "coolant", "north-2"),
    "CONV-12": ("conveyor", "conv-12", "jam", "photoeye", "pe-12", "movimot", "roller"),
    "PKG-A": ("pkg-a", "seal", "sealer", "recipe", "crc", "watchdog", "vision", "plc"),
}

FIXTURES: dict[str, dict] = {
    "HAAS-VF2-04": {
        "title": "Spindle overtemp on HAAS-VF2-04 — coolant concentration suspected",
        "severity": "high",
        "root_cause": (
            "Consistent with the plant's top failure mode: coolant concentration drifted "
            "below 6% (61% of overtemp events here), with chip packing at the spindle nose "
            "as a secondary contributor."
        ),
        "minutes": 6,
        "steps": [
            ("Press FEED HOLD. Do not rapid-retract if the tool is in a cut.", "operator"),
            ("If smoke or burning smell, E-STOP and LOTO at panel N2-DISC-04.", "operator"),
            ("Idle-cool 8 minutes if 70-85 C; power down 20 minutes if above 90 C.", "operator"),
            ("Test coolant tank T-04 with the refractometer. Target 8-10% for 6061.", "technician"),
            ("If Brix below 6%, add Apex-Kool AL per SDS-COOL-2, recirculate 10 min, retest.", "technician"),
            ("Clear chips at the spindle nose and confirm the flood nozzle hits the tool-work interface.", "technician"),
            ("Record spindle temp at alarm and at restart in this case file before resuming.", "supervisor"),
            ("If the alarm returns within 30 minutes, quarantine the job and escalate to the spindle specialist.", "supervisor"),
        ],
        "parts": [
            ("Apex-Kool AL", "Coolant concentrate", "RAW-C-12", 1),
            ("NZ-FL-14", "Flood nozzle 1/4 NPT", "MRO-CNC-02", 1),
        ],
        "loto": [
            "Feed hold, then spindle stop, then E-stop.",
            "Open N2-DISC-04 (415V 3-phase) and apply personal red lock plus supervisor blue lock.",
            "Lock air drop AIR-N2-4 and isolate hydraulic unit HU-04.",
            "Try-start prove-out, then bleed air before any contact.",
        ],
        "sources": ("haas-spindle-overtemp.md", "loto-north-cell.md", "closed-tickets.md"),
    },
    "CONV-12": {
        "title": "CONV-12 jam with overload trip — debris and photoeye alignment",
        "severity": "medium",
        "root_cause": (
            "Jam latch set by PE-12A blocked over 8 seconds. Plant history points to debris "
            "under the belt (48%) or PE-12A dusty/misaligned after a forklift bump (27%)."
        ),
        "minutes": 8,
        "steps": [
            ("LOTO CONV-12-DISC on the east column.", "technician"),
            ("Clear debris and vacuum chips. Do not blow air toward electronics.", "operator"),
            ("Wipe the PE-12A lens and confirm alignment to the yellow scribe on the bracket.", "technician"),
            ("Reset the overload on the MOVIMOT drive (blue button).", "technician"),
            ("Check PKG-A infeed — if packaging is starved, the backup is not a conveyor fault.", "operator"),
            ("Jog empty for 30 seconds before releasing to production.", "operator"),
            ("If the overload trips twice in one shift, replace cartridge ROL-IR-90.", "technician"),
        ],
        "parts": [("ROL-IR-90", "Interroll roller cartridge", "MRO-CONV-06", 1)],
        "loto": [
            "Disconnect CONV-12-DISC on the east column and apply personal lock.",
            "Mind pinch points at the infeed rollers; never reach under a live belt.",
            "Do not bypass PE-12A with tape — see near-miss NCR-2025-441.",
        ],
        "sources": ("conveyor-jam.md", "closed-tickets.md"),
    },
    "PKG-A": {
        "title": "PKG-A recipe CRC after brownout with seal wrinkles",
        "severity": "critical",
        "root_cause": (
            "Watchdog/recipe CRC following a power event, with seal wrinkles indicating an "
            "open zone-2 thermocouple on HS-A rather than a true cold seal."
        ),
        "minutes": 10,
        "steps": [
            ("Freeze the lot. Do not power-cycle the 24V rail — it corrupts recipe memory.", "supervisor"),
            ("Print the last 50 VIS-A images into this case file before touching the recipe.", "supervisor"),
            ("Controls tech loads last known good from MMC slot 2 (LKG-2026-08).", "technician"),
            ("Check the HS-A zone 2 thermocouple; replace TC-K-2M if open.", "technician"),
            ("Do not raise zone 1 temperature to compensate — that drives the scrap spike.", "operator"),
            ("Recalibrate VIS-A with gold sample GS-PKG-3 if rejects persist after a bulb change.", "technician"),
            ("Brief the customer engineer in English, then Japanese, before restart.", "supervisor"),
        ],
        "parts": [
            ("TC-K-2M", "Thermocouple type K 2 m", "MRO-PKG-11", 1),
            ("BELT-HS-40", "Sealer belt 40 mm", "MRO-PKG-04", 1),
        ],
        "loto": [
            "PLC cabinet work is restricted to controls techs with the S7-1500 card.",
            "Isolate HS-A heaters before any thermocouple work; surfaces stay hot.",
            "Two-person verify on restart because the lot is automotive PPAP.",
        ],
        "sources": ("packaging-watchdog.md", "closed-tickets.md"),
    },
}


def detect_asset(text: str) -> str:
    low = text.lower()
    best, score = "HAAS-VF2-04", 0
    for asset, words in ASSET_KEYWORDS.items():
        hits = sum(1 for w in words if w in low)
        if hits > score:
            best, score = asset, hits
    return best


def build_offline_case(notes: str, language: str) -> tuple[WorkOrder, list[str], str]:
    """Return (work_order, trace, scene) without calling any model."""
    asset = detect_asset(notes)
    fx = FIXTURES[asset]
    hits = retrieve(notes or asset, k=3)
    excerpts = {h["source"]: h["text"].strip().splitlines() for h in hits}

    citations = []
    for source in fx["sources"]:
        lines = excerpts.get(source)
        snippet = next(
            (ln.strip() for ln in (lines or []) if len(ln.strip()) > 40),
            f"See {source} in the plant corpus.",
        )
        citations.append({"source": source, "excerpt": snippet[:220]})

    wo = WorkOrder(
        title=fx["title"],
        asset_id=asset,
        severity=fx["severity"],
        root_cause=fx["root_cause"],
        time_to_first_action_minutes=fx["minutes"],
        steps=[
            {"order": i + 1, "action": action, "owner": owner}
            for i, (action, owner) in enumerate(fx["steps"])
        ],
        parts=[
            {"sku": sku, "name": name, "bin": bin_, "qty": qty}
            for sku, name, bin_, qty in fx["parts"]
        ],
        loto=fx["loto"],
        citations=citations,
        language="English",
        cmms_payload={
            "asset": asset,
            "priority": fx["severity"],
            "description": fx["title"],
            "parts": [sku for sku, *_ in fx["parts"]],
            "source": "linecase-offline-fixture",
        },
    )
    trace = [
        "offline: no Gemini call",
        f"detect: asset matched {asset} by keyword",
        "retrieve: " + ", ".join(h["source"] for h in hits),
        "fixture: canned work order for this asset",
    ]
    scene = (
        f"Offline fixture for {asset}. No image was analysed and no model was called. "
        f"Operator notes taken as given: {notes.strip() or '(none)'}"
    )
    if language and language.lower() != "english":
        trace.append(f"note: {language} output needs Gemini; fixture is English only")
    return wo, trace, scene
