# FoodRescue Sentinel

**An AI-powered evidence review assistant for surplus-food donations.**

Built for the **Nebius × NVIDIA Global AI Hackathon 2026 — Apps & Agents Track**.

FoodRescue Sentinel helps food banks, community kitchens and food-rescue teams review surplus-food donation records before considering them for redistribution.

It transforms donor descriptions into structured batch information, identifies missing evidence, checks available information against sourced food-safety guidance and prepares a report for human review.

> **FoodRescue Sentinel does not certify food as safe or authorise its distribution. Final decisions must always be made by a human reviewer.**

---

## The Problem

Surplus food can help communities, but donation records are not always complete.

Important details may be missing, including:
- Preparation date and time.
- Storage temperature.
- Food handling and storage history.
- Packaging condition.
- Supporting records and evidence.

Reviewers may need to contact donors repeatedly to collect this information. This can make the review process slower and less consistent.

Most food-rescue platforms focus on connecting surplus food with people who need it. FoodRescue Sentinel focuses on an earlier question:

**What do we know about this batch, what evidence is missing, and what needs human attention?**

## Our Solution

FoodRescue Sentinel combines an AI agent with a deterministic rules engine to organise donation information and support evidence-based review.

Its intended workflow includes:

1. **Conversational intake:** Donors describe a food batch in natural language.
2. **Structured extraction:** The AI identifies relevant information such as food type, quantity, preparation time and storage conditions.
3. **Evidence identification:** Missing or uncertain information is highlighted, and follow-up questions can be requested.
4. **Rule evaluation:** The backend checks available information against sourced food-safety guidance.
5. **Review report:** The system organises findings, missing evidence, concerns and references for a human reviewer.

## How It Works

```text
Donor Message
     |
     v
AI Agent
(NVIDIA Nemotron)
     |
     v
Structured Batch Information
     |
     v
Evidence and Missing-Information Checks
     |
     v
Deterministic Rules Engine
     |
     v
Review Report
     |
     v
Human Review and Final Decision
```

The AI agent is responsible for interpreting natural-language information. The rules engine performs deterministic checks using the available reference data.

The system is designed to distinguish between confirmed, inferred and unknown information rather than silently filling gaps.

## Safety Design

Food safety is central to the design of FoodRescue Sentinel.

- **No automatic safety certification:** AI-generated reports are not approval decisions.
- **Unknown information remains unknown:** Missing temperature records or storage details must not be treated as confirmed.
- **Source-based rules:** Time limits should only be applied when supported by a documented source.
- **Condition-aware evaluation:** A refrigerated-food limit should not be applied when refrigeration has not been established.
- **Human oversight:** A qualified human reviewer remains responsible for the final decision.
- **Secure configuration:** API credentials are stored in environment variables and must never be committed to the repository.

Workflow statuses such as `ready_for_human_review`, `more_information_required` and `urgent_review_or_hold` describe review requirements. They do not establish whether food is safe or unsafe.

## Reference Data

The prototype uses food-safety guidance from:

| Source | Intended use |
|---|---|
| FSSAI Direction on Schedule 4 Part V, Licensing and Registration of Food Business Amendment Regulations 2021 | Hot-food handling guidance |
| FSSAI Food Industry Guide to implement GMP/GHP requirements: Catering (2017) | Refrigerated cooked-food guidance |
| WHO Five Keys to Safer Food | General food-handling guidance |

Reference limits are maintained in a structured data file with source information.

This is a limited prototype reference library, not a comprehensive food-safety database. Official guidance must be checked before real-world use.

## Technology Stack

| Component | Technology |
|---|---|
| AI model | NVIDIA Nemotron 3.5 Lightning |
| Intended inference platform | Nebius Token Factory |
| Backend | Python, FastAPI |
| Data validation | Pydantic |
| Communication | Server-Sent Events (SSE) |
| Rules engine | Python |
| Reference data | CSV |
| Database | SQLite, where implemented |
| Testing | pytest |
| Optional search | Tavily, if configured |

**Model and platform note:** The final submission should identify the actual model endpoint used in the demonstration. The Nebius Token Factory integration must be verified before claiming it as the deployed inference platform.

## Getting Started

### Requirements

- Python 3.11 or newer.
- Git.
- A Nebius Token Factory API key for the intended model integration.

### Installation

Clone the repository:

```bash
git clone https://github.com/aalia-301275/foodrescue-sentinel.git
cd foodrescue-sentinel/backend
```

Create and activate a virtual environment:

**Windows PowerShell**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the backend directory using `.env.example` as a template.

Configure the following variables:

```dotenv
NEBIUS_API_KEY=
NEBIUS_BASE_URL=
MODEL_NAME=nvidia/Nemotron-3_5-Lightning
TAVILY_API_KEY=
```

Never commit `.env` or expose API credentials.

### Run the Backend

From the backend directory:

```bash
uvicorn app.main:app --reload
```

Open the interactive API documentation:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Run automated tests:

```bash
python -m pytest
```

## API Overview

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API status |
| POST | `/chat` | Send a donor message and receive streamed agent events |
| GET | `/cases` | List saved cases |
| GET | `/cases/{case_id}` | Retrieve a case report |
| GET | `/cases/{case_id}/messages` | Retrieve case conversation |
| POST | `/cases/{case_id}/review` | Submit a human review |
| GET | `/cases/{case_id}/reviews` | Retrieve human reviews |
| POST | `/rules/check` | Evaluate a batch against configured rules |
| GET | `/rules/limits` | View loaded rule limits |
| POST | `/rules/reload` | Reload rule data |

## Demo Scenarios

The prototype is designed to demonstrate three important review situations:

**Case 1 — Complete Batch**

A donor provides food details, preparation time, storage information, temperature and packaging condition. The system organises the evidence and prepares the case for human review.

**Case 2 — Missing Temperature Record**

A donor provides storage information but cannot confirm the actual refrigerator temperature. The system should identify the missing evidence instead of assuming that the food was stored correctly.

**Case 3 — Damaged Packaging**

A donor reports damaged container lids or seals. The system should record the concern and flag the batch for appropriate human assessment.

All demonstration cases use synthetic data. They do not establish the real-world safety of any food.

## Limitations

FoodRescue Sentinel is a hackathon prototype and has important limitations:

- **Limited reference coverage:** The available rules cover only a small selection of cooked-food scenarios.
- **No safety certification:** The system cannot independently establish that food is safe for consumption.
- **Incomplete evidence:** AI extraction depends on the accuracy and completeness of donor-provided information.
- **Time interpretation:** Ambiguous preparation times and missing dates can affect elapsed-time calculations.
- **No image processing:** Photographs and scanned documents are outside the current text-based workflow unless separately implemented.
- **Human verification required:** Official guidance and batch information must be checked by a responsible reviewer.

## Future Improvements

- Expand the sourced food-safety reference library.
- Support photographs and scanned temperature records.
- Improve date, time and timezone handling.
- Add reviewer accounts and role-based access.
- Support multilingual donor communication.
- Pilot the system with a food-rescue organisation.

## Team

| Team member | Responsibility |
|---|---|
| Aalia Khan | Backend integration, database and rules engine |
| Khunsa Mahmood | Knowledge library and food-safety references |
| Amina Hasanaath | AI agent and Nemotron integration |
| Ayesha Sultana | Frontend development |

## Acknowledgements

Developed for the **Nebius × NVIDIA Global AI Hackathon 2026**.

Food-safety reference guidance is drawn from the FSSAI and WHO publications listed above.

## License

To be confirmed.