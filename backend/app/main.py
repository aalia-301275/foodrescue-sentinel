import asyncio
import json
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.db import (
    get_report,
    get_reviews,
    init_db,
    list_reports,
    save_report,
    save_review,
)
from app.mock_data import MOCK_EVENTS, MOCK_REPORT
from app.rules import decide_status, evaluate_batch
from app.schemas import BatchInfo, ChatRequest, HumanReview, ReviewReport

app = FastAPI(title="FoodRescue Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Runs once when the server starts.
init_db()
if get_report(MOCK_REPORT.case_id) is None:
    save_report(MOCK_REPORT)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    async def stream():
        for event, data in MOCK_EVENTS:
            yield sse(event, data)
            await asyncio.sleep(0.8)

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