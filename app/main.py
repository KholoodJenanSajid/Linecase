from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.config import api_key, offline
from app.rag import collection_count
from app.service import CaseError, file_case


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


@app.post("/api/case")
async def open_case(
    notes: str = Form(""),
    language: str = Form("English"),
    demo: str | None = Form(None),
    image: UploadFile | None = File(None),
):
    blob = None
    mime = "image/jpeg"
    if image and image.filename:
        blob = await image.read()
        mime = image.content_type or mime
    try:
        return file_case(
            notes=notes,
            language=language,
            demo=demo,
            image_bytes=blob,
            mime=mime,
        )
    except CaseError as exc:
        raise HTTPException(exc.status, exc.detail) from exc
