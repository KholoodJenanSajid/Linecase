from __future__ import annotations

import base64
import uuid
from pathlib import Path

from app.config import api_key, offline
from app.models import CaseResult, WorkOrder
from app.offline import build_offline_case

DEMOS = {
    "spindle": {
        "notes": "North-2 Haas VF-2. Red banner SPINDLE OVERTEMP, HMI 82C, coolant looks watery, chips packed at the nose. Shift C.",
        "language": "English",
    },
    "conveyor": {
        "notes": "CONV-12 humming, boxes stuck at CNC chute, photoeye PE-12A dusty, OL tripped on MOVIMOT once already this shift.",
        "language": "English",
    },
    "sealer": {
        "notes": "PKG-A HMI recipe CRC after brownout. Seal wrinkles. Japanese customer engineer on site. Do not cycle 24V.",
        "language": "Japanese",
    },
}


class CaseError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _graph():
    from app.graph import GRAPH

    return GRAPH


def file_case(
    notes: str = "",
    language: str = "English",
    demo: str | None = None,
    image_bytes: bytes | None = None,
    mime: str = "image/jpeg",
) -> CaseResult:
    if demo and demo in DEMOS:
        notes = notes or DEMOS[demo]["notes"]
        language = language or DEMOS[demo]["language"]
    if offline():
        wo, trace, scene = build_offline_case(notes, language)
        return CaseResult(
            case_id=f"LC-{uuid.uuid4().hex[:6].upper()}",
            scene=scene,
            work_order=wo,
            agent_trace=trace,
            mode="offline",
        )
    image_b64 = None
    if image_bytes:
        if len(image_bytes) > 8_000_000:
            raise CaseError(413, "Image too large")
        image_b64 = base64.b64encode(image_bytes).decode("ascii")
    try:
        state = _graph().invoke(
            {
                "notes": notes,
                "language": language,
                "image_b64": image_b64,
                "mime": mime,
                "trace": [],
            }
        )
    except Exception as exc:
        detail = str(exc)
        if "API_KEY_INVALID" in detail or "API key not valid" in detail:
            raise CaseError(
                401,
                "Gemini rejected the API key. Set GOOGLE_API_KEY as a Space secret "
                "(https://aistudio.google.com/apikey).",
            ) from exc
        if "ResourceExhausted" in detail or "429" in detail or "quota" in detail.lower():
            raise CaseError(
                429,
                "Gemini rate limit hit. Free tier allows about 5 requests a minute "
                "and each case costs two calls — wait a minute and try again.",
            ) from exc
        if "PERMISSION_DENIED" in detail:
            raise CaseError(
                403,
                "Gemini denied the request. Enable the Generative Language API for this key.",
            ) from exc
        raise CaseError(502, f"Agent run failed: {detail[:300]}") from exc
    wo = WorkOrder.model_validate(state["work_order"])
    return CaseResult(
        case_id=f"LC-{uuid.uuid4().hex[:6].upper()}",
        scene=state.get("scene") or "",
        work_order=wo,
        agent_trace=state.get("trace") or [],
        mode="gemini" if api_key() else "offline",
    )


def read_image(path: str | Path | None) -> tuple[bytes | None, str]:
    if not path:
        return None, "image/jpeg"
    p = Path(path)
    if not p.exists():
        return None, "image/jpeg"
    suffix = p.suffix.lower()
    mime = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(
        suffix, "image/jpeg"
    )
    return p.read_bytes(), mime
