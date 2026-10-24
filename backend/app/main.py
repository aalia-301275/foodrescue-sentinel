import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.mock_data import MOCK_EVENTS, MOCK_REPORT
from app.schemas import ChatRequest, HumanReview, ReviewReport

app = FastAPI(title="FoodRescue Sentinel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CASES = {MOCK_REPORT.case_id: MOCK_REPORT}
REVIEWS = {}


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
def list_cases():
    return list(CASES.values())


@app.get("/cases/{case_id}", response_model=ReviewReport)
def get_case(case_id: str):
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    return CASES[case_id]


@app.post("/cases/{case_id}/review")
def review_case(case_id: str, review: HumanReview):
    if case_id not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    REVIEWS[case_id] = review
    return {"case_id": case_id, "review": review}