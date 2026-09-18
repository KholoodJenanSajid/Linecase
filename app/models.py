from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    source: str
    excerpt: str


class WorkStep(BaseModel):
    order: int
    action: str
    owner: str = "operator"


class PartNeed(BaseModel):
    sku: str
    name: str
    bin: str
    qty: int = 1


class WorkOrder(BaseModel):
    title: str
    asset_id: str
    severity: Literal["low", "medium", "high", "critical"]
    root_cause: str
    time_to_first_action_minutes: int = Field(ge=1, le=180)
    steps: list[WorkStep]
    parts: list[PartNeed]
    loto: list[str]
    citations: list[Citation]
    language: str
    cmms_payload: dict


class CaseResult(BaseModel):
    case_id: str
    plant: str = "APX-PEN-01"
    scene: str
    work_order: WorkOrder
    agent_trace: list[str]
    mode: Literal["gemini", "offline"] = "gemini"
