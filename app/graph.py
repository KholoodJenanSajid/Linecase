from __future__ import annotations

import json
import os
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from app.catalog import reconcile
from app.models import WorkOrder
from app.rag import retrieve


class GraphState(TypedDict, total=False):
    notes: str
    language: str
    image_b64: str | None
    mime: str
    scene: str
    retrieved: list[dict]
    work_order: dict
    trace: list[str]


def _llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"),
        temperature=0.2,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        # Free tier allows 5 requests/min and a case costs two calls, so fail
        # fast on 429 instead of backing off for a minute behind the request.
        max_retries=1,
    )


def see_node(state: GraphState) -> dict[str, Any]:
    notes = state.get("notes") or ""
    image_b64 = state.get("image_b64")
    mime = state.get("mime") or "image/jpeg"
    llm = _llm()
    if image_b64:
        msg = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "You are a factory technician's eyes. Describe the machine, "
                        "alarms, HMI text, leaks, smoke, damage. Be specific. "
                        f"Operator notes: {notes or '(none)'}"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": f"data:{mime};base64,{image_b64}",
                },
            ]
        )
        scene = llm.invoke([msg]).content
    else:
        scene = llm.invoke(
            [
                SystemMessage(
                    content="You are a factory technician inferring the scene from notes only."
                ),
                HumanMessage(content=notes or "No notes. Ask what is missing, then assume a plausible APX-PEN-01 fault."),
            ]
        ).content
    if not isinstance(scene, str):
        scene = str(scene)
    trace = list(state.get("trace") or [])
    trace.append("see: multimodal scene locked")
    return {"scene": scene, "trace": trace}


def retrieve_node(state: GraphState) -> dict[str, Any]:
    q = f"{state.get('scene', '')}\n{state.get('notes', '')}"
    hits = retrieve(q, k=4)
    trace = list(state.get("trace") or [])
    trace.append("retrieve: " + ", ".join(h["source"] for h in hits))
    return {"retrieved": hits, "trace": trace}


def act_node(state: GraphState) -> dict[str, Any]:
    context = "\n\n".join(
        f"### {h['source']}\n{h['text']}" for h in state.get("retrieved") or []
    )
    language = state.get("language") or "English"
    schema = WorkOrder.model_json_schema()
    prompt = f"""You are Linecase, a plant reliability agent for Apex Precision Penang (APX-PEN-01).

Write a CMMS-ready work order. Cite only the plant corpus. If unsure, say so in root_cause and choose conservative LOTO.

Operator notes:
{state.get('notes')}

Scene:
{state.get('scene')}

Plant corpus:
{context}

Respond in JSON matching this schema (no markdown):
{json.dumps(schema)}

Rules:
- language field must be {language}. All human-readable strings (title, root_cause, steps, loto) in {language}.
- asset_id must be one of HAAS-VF2-04, CONV-12, PKG-A if possible.
- citations[].source = corpus filename. excerpt = short quote.
- cmms_payload = compact JSON the CMMS would POST (asset, priority, description, parts).
- time_to_first_action_minutes = realistic minutes for this crew with Linecase in hand (usually 4–12).
"""
    raw = _llm().invoke(
        [
            SystemMessage(content="Return only valid JSON."),
            HumanMessage(content=prompt),
        ]
    ).content
    if not isinstance(raw, str):
        raw = str(raw)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    try:
        data = json.loads(raw)
        wo = WorkOrder.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        wo = WorkOrder(
            title="Manual review required",
            asset_id="UNKNOWN",
            severity="medium",
            root_cause=f"Agent could not structure the case ({exc}). Scene: {state.get('scene', '')[:400]}",
            time_to_first_action_minutes=15,
            steps=[{"order": 1, "action": "Supervisor review on the floor", "owner": "supervisor"}],
            parts=[],
            loto=["Follow APX-EHS-07 until the asset is identified"],
            citations=[],
            language=language,
            cmms_payload={"status": "needs_review"},
        )
    trace = list(state.get("trace") or [])
    trace.append("act: work order drafted")

    data = wo.model_dump()
    parts, notes = reconcile(data["parts"])
    data["parts"] = parts
    payload = data.get("cmms_payload")
    if isinstance(payload, dict):
        payload["required_parts"] = [
            {"sku": p["sku"], "bin": p["bin"], "qty": p["qty"]} for p in parts
        ]
    trace.append(
        "catalog: " + ("; ".join(notes) if notes else "all parts matched the catalog")
    )
    return {"work_order": data, "trace": trace}


def compile_graph():
    g = StateGraph(GraphState)
    g.add_node("see", see_node)
    g.add_node("retrieve", retrieve_node)
    g.add_node("act", act_node)
    g.add_edge(START, "see")
    g.add_edge("see", "retrieve")
    g.add_edge("retrieve", "act")
    g.add_edge("act", END)
    return g.compile()


GRAPH = compile_graph()
