from __future__ import annotations

import base64
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.config import api_key, offline
from app.models import CaseResult, WorkOrder
from app.offline import build_offline_case
from app.rag import collection_count


def _graph():
    from app.graph import GRAPH

    return GRAPH


WEB = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="Linecase", version="0.1.0")
if WEB.exists():
    app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/health")
def health():
    keyed = api_key() is not None
    n = 0
    try:
        n = collection_count()
    except Exception:
        n = -1
    return {
        "ok": True,
        "gemini": keyed,
        "mode": "offline" if offline() else "gemini",
        "corpus_docs": n,
    }


@app.get("/")
def index():
    index = WEB / "index.html"
    if not index.exists():
        raise HTTPException(404, "UI missing")
    return FileResponse(index)


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


@app.post("/api/case")
async def open_case(
    notes: str = Form(""),
    language: str = Form("English"),
    demo: str | None = Form(None),
    image: UploadFile | None = File(None),
):
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
    mime = "image/jpeg"
    if image and image.filename:
        blob = await image.read()
        if len(blob) > 8_000_000:
            raise HTTPException(413, "Image too large")
        image_b64 = base64.b64encode(blob).decode("ascii")
        mime = image.content_type or mime
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
            raise HTTPException(
                401,
                "Gemini rejected the API key. Check GOOGLE_API_KEY in .env "
                "(get one at https://aistudio.google.com/apikey) and restart the server.",
            ) from exc
        if "ResourceExhausted" in detail or "429" in detail or "quota" in detail.lower():
            raise HTTPException(
                429,
                "Gemini rate limit hit. The free tier allows 5 requests per minute and "
                "each case costs two calls — wait about a minute and file the case again.",
            ) from exc
        if "PERMISSION_DENIED" in detail:
            raise HTTPException(
                403,
                "Gemini denied the request. Check that the key's project has the "
                "Generative Language API enabled and the key is restricted to it.",
            ) from exc
        raise HTTPException(502, f"Agent run failed: {detail[:300]}") from exc
    wo = WorkOrder.model_validate(state["work_order"])
    return CaseResult(
        case_id=f"LC-{uuid.uuid4().hex[:6].upper()}",
        scene=state.get("scene") or "",
        work_order=wo,
        agent_trace=state.get("trace") or [],
    )
