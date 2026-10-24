from app.schemas import ReviewReport

MOCK_REPORT = ReviewReport.model_validate({
    "case_id": "case-001",
    "summary": "Cooked vegetarian biryani from a wedding event, about 200 plates. Storage history is incomplete.",
    "batch": {
        "product_type": {"value": "cooked veg biryani", "status": "confirmed"},
        "quantity": {"value": "200 plates", "status": "confirmed"},
        "prepared_at": {"value": "18:00", "status": "confirmed"},
        "storage_temperature": {"value": None, "status": "unknown"},
        "storage_history": {"value": "kept covered at room temperature, duration unclear", "status": "inferred"},
        "packaging_condition": {"value": "steel containers", "status": "confirmed"},
    },
    "missing_evidence": ["Storage temperature record", "Time food was first served"],
    "concerns": [
        {"text": "No temperature record for cooked food held for an unknown time.", "source": "REF-001"}
    ],
    "references": [
        {
            "id": "REF-001",
            "title": "PLACEHOLDER guidance for demo only",
            "passage": "Placeholder text. The knowledge lead will replace this with real, cited guidance.",
        }
    ],
    "next_step": "Ask donor for temperature and timing records, then send to a human reviewer.",
    "workflow_status": "more_information_required",
})

MOCK_EVENTS = [
    ("thought", {"text": "Reading the donor's message and extracting batch details."}),
    ("tool_call", {"tool": "corpus_lookup", "input": "cooked rice storage time guidance"}),
    ("tool_result", {"tool": "corpus_lookup", "summary": "Found 1 relevant passage (REF-001)."}),
    ("tool_call", {"tool": "web_search", "input": "recent recall alerts cooked food India"}),
    ("tool_result", {"tool": "web_search", "summary": "No relevant alerts found."}),
    ("rule_check", {"rule": "storage_temperature_present", "passed": False}),
    ("question", {"text": "What temperature was the food stored at, and for how long?"}),
    ("final_report", MOCK_REPORT.model_dump()),
]