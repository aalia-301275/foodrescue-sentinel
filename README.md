
# 🍃 FoodRescue Sentinel

### AI-Powered Evidence Review for Surplus Food Donations

**Built for the Nebius × NVIDIA Global AI Hackathon 2026 — Apps & Agents Track**

FoodRescue Sentinel is an AI-powered food donation review assistant that helps food banks, community kitchens, and food-rescue organisations evaluate donation records before considering food for redistribution.

The system uses an **NVIDIA Nemotron AI agent**, a **deterministic food-safety rules engine**, and a **human-in-the-loop review workflow** to transform natural-language donor descriptions into structured evidence reports.

> ⚠️ **Important:** FoodRescue Sentinel does not certify food as safe or automatically authorise distribution. All final decisions require human review.

---

## 🚀 What Does FoodRescue Sentinel Do?

Food donation records often lack essential information such as:

- Food preparation date and time
- Storage temperature
- Storage and handling history
- Packaging condition
- Supporting evidence

FoodRescue Sentinel helps reviewers identify these gaps through an AI-assisted workflow.

### Key Features

- **Conversational AI Agent:** Accepts natural-language food donation descriptions.
- **Structured Data Extraction:** Identifies food type, quantity, preparation time, storage conditions, and packaging details.
- **Evidence Tracking:** Distinguishes confirmed, inferred, and unknown information.
- **Follow-Up Questions:** Requests clarification when important details are missing.
- **Deterministic Rules Engine:** Evaluates available information against configured food-safety references.
- **Agent Activity Streaming:** Displays AI processing and rule-checking events using Server-Sent Events (SSE).
- **Safety Review Reports:** Generates structured findings for human reviewers.
- **Human Oversight:** Keeps final decisions with a human reviewer.
- **SQLite Persistence:** Stores case reports, conversation history, and review records.

---

## 🧠 How It Works

```text
          Donor Submits Food Details
                      |
                      v
             NVIDIA Nemotron AI
                      |
                      v
          Structured Data Extraction
                      |
                      v
          Missing Evidence Detection
                      |
                      v
           Food Safety Rules Engine
                      |
                      v
            AI Safety Review Report
                      |
                      v
               Human Reviewer
                      |
                      v
              Final Human Decision
```

The AI agent interprets donor messages and prepares structured information.

The rules engine independently checks available evidence against configured reference limits.

Missing information remains unknown rather than being assumed.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| AI Model | NVIDIA Nemotron (`nvidia/nemotron-3.5-bolt-e4b`) |
| Current AI Inference | NVIDIA API |
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| API Communication | REST + Server-Sent Events |
| Validation | Pydantic |
| Rules Engine | Python |
| Reference Data | CSV |
| Database | SQLite |
| Testing | pytest |

**Hackathon integration note:** The current development implementation uses the NVIDIA API. Nebius Token Factory or Nebius AI Cloud integration must be completed and verified to satisfy the hackathon's platform requirement. Do not treat the current NVIDIA API configuration as a verified Nebius deployment.

---

# 💻 Getting Started — Run Locally

Follow these instructions to run FoodRescue Sentinel on your computer.

## 1. Prerequisites

Install:

- Python 3.11 or newer
- Git
- A modern browser (Chrome, Edge, or Firefox)
- An NVIDIA API key with access to the configured model

You can obtain an NVIDIA API key through:

https://build.nvidia.com/

> API access, model availability, and usage limits depend on your NVIDIA account.

## 2. Clone the Repository

Open a terminal and run:

```bash
git clone https://github.com/aalia-301275/foodrescue-sentinel.git
cd foodrescue-sentinel
```

**Important:** If the AI agent and demo frontend have not yet been merged into `main`, switch to the development branch:

```bash
git checkout feature/ai-agent
```

The commands below assume this branch contains the `backend/` and `frontend/` directories.

## 3. Set Up the Backend

Open a terminal in the project root.

Navigate to the backend directory:

```bash
cd backend
```

Create a Python virtual environment:

```bash
python -m venv venv
```

### Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install -r requirements.txt
```

Wait until installation completes.

## 4. Configure the AI API Key

The AI agent requires an NVIDIA API key.

Inside the `backend/` directory, create a file named:

```text
.env
```

If an `.env.example` file exists, you can copy it.

**Windows PowerShell:**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
cp .env.example .env
```

Edit `backend/.env` and configure:

```dotenv
NVIDIA_API_KEY=your_nvidia_api_key_here
```

The AI client currently uses the model identifier:

```text
nvidia/nemotron-3.5-bolt-e4b
```

Check `backend/app/llm_client.py` if the model configuration has changed.

**Never commit your `.env` file or share your API key.**

## 5. Start the Backend

Make sure your terminal is inside `backend/` and the virtual environment is active.

Run:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

The backend should start at:

http://127.0.0.1:8000

### Verify the Backend

Open:

http://127.0.0.1:8000/health

Expected response:

```json
{
  "status": "ok"
}
```

### API Documentation

FastAPI automatically generates interactive documentation:

http://127.0.0.1:8000/docs

You can inspect and test the available API endpoints there.
API LABEL : nvidia/nemotron-3.5-bolt-e4b

**Keep the backend terminal running.**

---

## 6. Start the Frontend

Open a **second terminal**.

From the project root, navigate to:

```bash
cd frontend
```

Start a local HTTP server:

**Windows:**

```bash
python -m http.server 5500
```

**macOS / Linux:**

```bash
python3 -m http.server 5500
```

Now open your browser:

### 🌐 http://127.0.0.1:5500/index.html

You should see the **FoodRescue Sentinel AI Dashboard**.

The frontend communicates with the FastAPI backend at:

```text
http://127.0.0.1:8000/chat
```

**Important:** Keep both terminals running.

If the frontend cannot connect, verify that:

1. The backend is running on port `8000`.
2. The frontend is running on port `5500`.
3. `frontend/script.js` points to `http://127.0.0.1:8000/chat`.
4. FastAPI CORS configuration permits `http://127.0.0.1:5500`.
5. Your NVIDIA API key is correctly configured.

---

# 🧪 Try the AI Agent

Once the dashboard is open, enter a food donation description in the chat.

## Demo 1 — Detailed Food Donation

```text
We have 20 sealed boxes of cooked rice, prepared
today at 10 AM.

The food was refrigerated immediately after
preparation and continuously stored at 4°C.

All containers are clean, sealed, and undamaged.

We want to donate them today.
```

**What to observe:**

- The AI agent processes the donor description.
- Food batch information is extracted.
- Available evidence is evaluated.
- Missing or uncertain information may be identified.
- A structured report is prepared for human review.

A detailed record does not automatically establish that food is safe.

## Demo 2 — Missing Temperature Evidence

```text
We have 15 containers of cooked vegetable curry.

It was prepared this morning and placed in a
refrigerator.

We don't know the refrigerator temperature.

Can we donate it?
```

**Expected review behaviour:**

The agent should identify the missing temperature evidence rather than assume that refrigeration conditions were adequate.

It may ask follow-up questions before completing the review.

## Demo 3 — Damaged Packaging

```text
We have 30 boxes of cooked food prepared today.

The food has been refrigerated, but several
containers have damaged lids and broken seals.

Can we distribute them?
```

**Expected review behaviour:**

The system should identify the reported packaging concern and flag it for appropriate human assessment.

It must not automatically authorise distribution.

---

# 📊 Understanding the Dashboard

The demo frontend provides three main areas.

### 1. AI Chat

Enter natural-language food donation information and respond to the agent's follow-up questions.

### 2. Agent Activity

Observe streamed processing events such as:

- Agent reasoning summaries
- Tool calls
- Tool results
- Rule checks
- Follow-up questions

Displayed events depend on the agent's execution path.

### 3. Safety Review Report

Inspect the structured report, including:

- Food batch details
- Available evidence
- Missing evidence
- Safety concerns
- References
- Recommended next step
- Workflow status

The report supports human review; it is not a food-safety certificate.

---

# 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Backend health check |
| POST | `/chat` | AI agent conversation with SSE |
| GET | `/cases` | List saved reports |
| GET | `/cases/{case_id}` | Retrieve a case report |
| GET | `/cases/{case_id}/messages` | Retrieve conversation history |
| POST | `/cases/{case_id}/review` | Submit a human review |
| GET | `/cases/{case_id}/reviews` | Retrieve human reviews |
| POST | `/rules/check` | Evaluate structured food information |
| GET | `/rules/limits` | View configured reference limits |
| POST | `/rules/reload` | Reload food-safety rules |

### Example Chat Request

```json
{
  "message": "We have 10 sealed boxes of cooked rice stored at 4°C.",
  "case_id": null
}
```

The `/chat` endpoint returns a stream of Server-Sent Events rather than a single JSON response.

Example event types:

```text
case
thought
tool_call
tool_result
rule_check
question
final_report
error
```

A `case_id` is generated for a new conversation and can be reused for follow-up messages.

---

# 🛡️ Food Safety and Responsible AI

FoodRescue Sentinel is designed as a decision-support tool.

### Safety Principles

**1. No automatic approval**

The system does not independently certify food as safe for consumption.

**2. Unknown means unknown**

Missing information must not be presented as verified evidence.

**3. Deterministic rule checks**

Reference-based food-safety evaluations are performed separately from AI-generated interpretations.

**4. Human oversight**

Final decisions remain with responsible human reviewers.

**5. Evidence transparency**

Reports identify available evidence, uncertainties, concerns, and applicable references.

### Workflow Statuses

| Status | Meaning |
|---|---|
| `ready_for_human_review` | The case can proceed to human assessment |
| `more_information_required` | Additional evidence or clarification is needed |
| `urgent_review_or_hold` | The case requires priority attention or a hold pending review |

These are workflow classifications, not declarations that food is safe or unsafe.

---

# 📚 Food Safety Reference Sources

The prototype uses a limited reference library based on guidance from:

| Organisation | Reference |
|---|---|
| FSSAI | Direction on Schedule 4 Part V, Licensing and Registration of Food Business Amendment Regulations, 2021 |
| FSSAI | Food Industry Guide to Implement GMP/GHP Requirements: Catering, 2017 |
| WHO | Five Keys to Safer Food |

Reference limits are maintained in structured data.

This reference library is not comprehensive. Applicable official guidance must be verified before real-world use.

---

# 🧪 Run Automated Tests

Open a terminal in the `backend/` directory with the virtual environment activated.

Run:

```bash
python -m pytest
```

This executes the available automated tests.

Test coverage and results depend on the current repository version.

---

# 📁 Project Structure

```text
foodrescue-sentinel/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── agent.py
│   │   ├── llm_client.py
│   │   ├── rules.py
│   │   ├── schemas.py
│   │   ├── db.py
│   │   └── mock_data.py
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── .env              # Local only; never commit
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
└── README.md
```

Additional reference files, tests, and backend modules may be present.

---

# ⚠️ Current Limitations

FoodRescue Sentinel is a hackathon prototype.

- **Limited rules:** The food-safety reference library covers selected scenarios only.
- **AI reliability:** Model responses can vary, fail, or time out.
- **Evidence quality:** The system relies on information supplied by donors.
- **Date and time ambiguity:** Relative descriptions such as "this morning" may require clarification.
- **Text-based intake:** Image and document processing are not part of the current demo workflow.
- **No production safety certification:** Human review remains essential.
- **Local demo:** The instructions above run the project locally; they do not represent a hosted production deployment.
- **Platform integration:** Nebius integration must be verified separately from the current NVIDIA API implementation.

If AI inference is unavailable, some agent operations may be incomplete or may require further information. The system should not invent missing safety evidence.

---

# 🔮 Future Improvements

- Nebius inference integration and deployment verification
- Expanded food-safety reference coverage
- Temperature-record and document uploads
- Image-based packaging inspection
- Multilingual donor conversations
- Improved date and timezone handling
- Reviewer authentication and role-based access
- Integration with food banks and donation platforms
- Real-world validation with qualified food-safety reviewers

---

# 👥 Team

FoodRescue Sentinel was developed collaboratively for the Nebius × NVIDIA Global AI Hackathon 2026.

| Responsibility | Team Member |
|---|---|
| Backend integration, database, rules engine | Aalia Khan |
| Knowledge library and food-safety references | Team member |
| AI agent and NVIDIA Nemotron integration | Team member |
| Frontend development | Team member |

---

# 🏆 Hackathon

**Event:** Nebius × NVIDIA Global AI Hackathon 2026

**Track:** Apps & Agents

**Project:** FoodRescue Sentinel

**Focus:** Agentic AI, evidence-based decision support, food donation review, and responsible AI.

---

# 📄 License

To be confirmed.

---

### 🍃 FoodRescue Sentinel

**Better evidence. Clearer reviews. Human decisions.**
