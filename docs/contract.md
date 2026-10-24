# API Contract (v1, mock)

Base URL (local): http://127.0.0.1:8000

- GET  /health
- POST /chat               body: {case_id?, message}  -> SSE stream
- GET  /cases              -> list of reports
- GET  /cases/{id}         -> one report
- POST /cases/{id}/review  body: {reviewer, decision, notes}

SSE event names: thought, tool_call, tool_result, rule_check, question, final_report
Data shapes: see backend/app/schemas.py
Rule: field names and event names do not change without telling the group.