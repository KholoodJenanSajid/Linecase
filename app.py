"""Hugging Face Spaces entrypoint (free Gradio / ZeroGPU)."""

from __future__ import annotations

import json

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

from app.service import DEMOS, CaseError, file_case, read_image


def _format(result) -> str:
    wo = result.work_order
    lines = [
        f"# {result.case_id} · {wo.title}",
        f"**Plant** {result.plant} · **Asset** `{wo.asset_id}` · **Severity** {wo.severity} · **Mode** {result.mode}",
        f"**First action in** {wo.time_to_first_action_minutes} min · **Language** {wo.language}",
        "",
        "## Scene",
        result.scene or "_(no photo description)_",
        "",
        "## Root cause",
        wo.root_cause,
        "",
        "## LOTO",
        *[f"- {step}" for step in wo.loto] or ["- _(none)_"],
        "",
        "## Steps",
        *[f"{s.order}. **{s.owner}** — {s.action}" for s in wo.steps],
        "",
        "## Parts",
        *[f"- `{p.sku}` {p.name} · bin `{p.bin}` · qty {p.qty}" for p in wo.parts]
        or ["- _(none)_"],
        "",
        "## Citations",
        *[f"- **{c.source}** — {c.excerpt}" for c in wo.citations] or ["- _(none)_"],
        "",
        "## Agent trace",
        " → ".join(result.agent_trace) if result.agent_trace else "_(empty)_",
        "",
        "## CMMS payload",
        "```json",
        json.dumps(wo.cmms_payload, indent=2),
        "```",
    ]
    return "\n".join(lines)


def run(notes, language, demo, image):
    key = None
    if demo:
        label = str(demo).split(":")[0].strip().lower()
        if label in DEMOS:
            key = label
    try:
        blob, mime = read_image(image)
        result = file_case(
            notes=notes or "",
            language=language or "English",
            demo=key,
            image_bytes=blob,
            mime=mime,
        )
        return _format(result)
    except CaseError as exc:
        return f"**Could not file the case** ({exc.status})\n\n{exc.detail}"


with gr.Blocks(title="Linecase") as demo:
    gr.Markdown(
        "# Linecase\n"
        "A downtime case file, not a chatbot. Photo or notes from the floor → "
        "cited work order with LOTO, parts, and a CMMS payload."
    )
    with gr.Row():
        with gr.Column():
            notes = gr.Textbox(
                label="Operator notes",
                lines=6,
                placeholder="What the operator actually said…",
            )
            language = gr.Dropdown(
                ["English", "Malay", "Japanese", "Mandarin", "Tamil"],
                value="English",
                label="Language out",
            )
            demo_pick = gr.Dropdown(
                [
                    "",
                    "spindle: Haas overtemp",
                    "conveyor: jam at chute",
                    "sealer: recipe CRC",
                ],
                value="",
                label="Or load a sample fault",
            )
            image = gr.Image(label="Floor photo (optional)", type="filepath")
            go = gr.Button("File case", variant="primary")
        with gr.Column():
            out = gr.Markdown("No case yet. Load a sample fault, or describe one in your own words.")
    go.click(run, [notes, language, demo_pick, image], out)

if __name__ == "__main__":
    demo.launch()
