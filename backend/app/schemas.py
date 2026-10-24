from typing import List, Literal, Optional
from pydantic import BaseModel

FieldStatus = Literal["confirmed", "unknown", "inferred"]

WorkflowStatus = Literal[
    "ready_for_human_review",
    "more_information_required",
    "urgent_review_or_hold",
]


class TrackedValue(BaseModel):
    value: Optional[str] = None
    status: FieldStatus = "unknown"


class BatchInfo(BaseModel):
    product_type: TrackedValue
    quantity: TrackedValue
    prepared_at: TrackedValue
    storage_temperature: TrackedValue
    storage_history: TrackedValue
    packaging_condition: TrackedValue


class Concern(BaseModel):
    text: str
    source: str


class Reference(BaseModel):
    id: str
    title: str
    passage: str


class ReviewReport(BaseModel):
    case_id: str
    summary: str
    batch: BatchInfo
    missing_evidence: List[str]
    concerns: List[Concern]
    references: List[Reference]
    next_step: str
    workflow_status: WorkflowStatus


class ChatRequest(BaseModel):
    case_id: Optional[str] = None
    message: str


class HumanReview(BaseModel):
    reviewer: str
    decision: Literal["proceed", "request_info", "hold", "reject"]
    notes: str = ""