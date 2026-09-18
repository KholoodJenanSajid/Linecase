---
title: Linecase
emoji: 🛠
colorFrom: gray
colorTo: red
sdk: docker
app_port: 8080
pinned: false
license: mit
---

# Linecase

A downtime case file, not a chatbot.

On a real shop floor, a fault still lives in WhatsApp videos, paper SOPs, and one supervisor's head. Linecase takes a photo or a messy operator note and files a **work order**: what happened, which manuals say so, lockout steps, parts with real bin numbers, and a CMMS payload. In the operator's language.

This is a working prototype running against a seeded reference plant. The plant is fictional. The workflow is not.

## What you get back

Not a chat transcript. A case:

- **Scene** — Gemini looks at the photo / notes
- **Root cause** — grounded in this plant's SOPs, not the open web
- **LOTO** — isolation sequence before anyone puts a hand in
- **Steps and parts** — who does what, which SKU, which bin
- **Citations** — which file and which line
- **CMMS payload** — JSON a maintenance system could actually POST

Bin locations come from the parts catalog, not the model. If Gemini invents a shelf, we overwrite it and say so in the agent trace. That is the whole point.

## The plant

**Apex Precision, Penang (`APX-PEN-01`)** — a contract manufacturer. Three assets, closed-world manuals:

| Asset | What goes wrong |
| --- | --- |
| `HAAS-VF2-04` | Spindle overtemp, coolant, chips |
| `CONV-12` | Jam, dusty photoeye, overload trip |
| `PKG-A` | Recipe CRC after a brownout, seal wrinkles |

If the agent cannot cite a manual, it asks for supervisor review instead of guessing.

## How it runs

```
see  →  retrieve  →  act  →  catalog
```

Gemini (default `gemini-3.6-flash`) describes the scene, Chroma / keyword search pulls SOPs, LangGraph drafts the work order, then `app/catalog.py` reconciles every part against `data/corpus/parts-catalog.md`.

Stack: FastAPI, LangGraph, `langchain-google-genai`, Chroma, a static case-file UI, Docker.

## Run it

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Put a Gemini key from [Google AI Studio](https://aistudio.google.com/apikey) in `.env`:

```
GOOGLE_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-3.6-flash
```

New Google accounts cannot use `gemini-2.5-flash` anymore. Restart the server after editing `.env` — reload only watches Python files.

```powershell
uvicorn app.main:app --reload --port 8080
```

Open [http://localhost:8080](http://localhost:8080). Click **Demo: spindle overtemp**. You want:

- no red "offline fixture" stamp
- trace ending in `see → retrieve → act → catalog`
- `NZ-FL-14` in bin `MRO-CNC-02`, not wherever the model first guessed

`GET /health` should report `"gemini": true` once the key is live.

### If you don't have a key yet

Leave `GOOGLE_API_KEY` as the placeholder, or set `LINECASE_OFFLINE=1`. The API still returns a real work-order shape from canned fixtures, stamped `mode: "offline"`. Useful for UI work, not for evaluating the reasoning.

Free-tier Gemini allows about 5 requests a minute. Each live case costs two model calls, so wait a minute between runs if you hit a 429.

## Deploy

The repo ships a `Dockerfile` that listens on `$PORT`, so it runs on anything that takes a container.

**Hugging Face Spaces** — free, public, no billing account. Create a Space (SDK: Docker), add `GOOGLE_API_KEY` under *Settings → Variables and secrets*, then:

```powershell
git remote add space https://huggingface.co/spaces/<user>/linecase
git push space main
```

**Cloud Run**:

```powershell
gcloud run deploy linecase --source . --region asia-southeast1 --allow-unauthenticated --set-env-vars GEMINI_MODEL=gemini-3.6-flash
```

Pass the key as a secret, not a build arg. Do not bake it into the image.

## API

`POST /api/case` (multipart)

| Field | What it is |
| --- | --- |
| `notes` | What the operator said |
| `language` | Language for the work order |
| `image` | Optional photo |
| `demo` | `spindle`, `conveyor`, or `sealer` |

Returns `case_id`, `scene`, `work_order`, `agent_trace`, `mode`.

## What this is not

- Not a SCADA replacement. Wiring a PLC is a sales cycle.
- Not "AI for all manufacturing." One plant, three machines.
- Not a chatbot with a manufacturing skin.

## License

MIT. Plant names and tickets are made up.
