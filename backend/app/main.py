import json
import uuid
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app import rules as rules_module
from app.agent import run_agent
from app.db import (
    get_messages,
    get_report,
    get_reviews,
    init_db,
    list_reports,
    save_message,
    save_report,
    save_review,
)
from app.mock_data import MOCK_REPORT
from app.rules import decide_status, evaluate_batch
from app.schemas import BatchInfo, ChatRequest, HumanReview, ReviewReport

app = FastAPI(title="FoodRescue Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
if get_report(MOCK_REPORT.case_id) is None:
    save_report(MOCK_REPORT)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def new_case_id() -> str:
    return f"case-{uuid.uuid4().hex[:6]}"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    case_id = req.case_id or new_case_id()
    history = get_messages(case_id)
    save_message(case_id, "user", req.message)

    async def stream():
    yield sse("case", {"case_id": case_id})
    try:
        async for event, data in run_agent(case_id, req.message, history):
            if event == "final_report":
                save_report(ReviewReport.model_validate(data))
                save_message(case_id, "assistant", data["summary"])
            elif event == "question":
                save_message(case_id, "assistant", data["text"])

            yield sse(event, data)

    except Exception as exc:
        yield sse("error", {"message": f"Agent failed: {type(exc).__name__}"})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/cases")
def cases():
    return list_reports()


@app.get("/cases/{case_id}", response_model=ReviewReport)
def case_detail(case_id: str):
    report = get_report(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return report


@app.get("/cases/{case_id}/messages")
def case_messages(case_id: str):
    return get_messages(case_id)


@app.post("/cases/{case_id}/review")
def review_case(case_id: str, review: HumanReview):
    if get_report(case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    save_review(case_id, review)
    return {"case_id": case_id, "review": review}


@app.get("/cases/{case_id}/reviews")
def case_reviews(case_id: str):
    if get_report(case_id) is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return get_reviews(case_id)


@app.post("/rules/check")
def rules_check(batch: BatchInfo):
    results = evaluate_batch(batch)
    return {
        "results": [asdict(r) for r in results],
        "workflow_status": decide_status(results),
    }


@app.get("/rules/limits")
def rules_limits():
    return {
        "count": len(rules_module.LIMITS),
        "limits": [asdict(r) for r in rules_module.LIMITS],
        "warnings": rules_module.LIMIT_WARNINGS,
    }


@app.post("/rules/reload")
def rules_reload():
    rules_module.reload_limits()
    return {
        "count": len(rules_module.LIMITS),
        "warnings": rules_module.LIMIT_WARNINGS,
    }