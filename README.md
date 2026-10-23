# AI Insurance Claim Assistant

> **Multi-Agent Insurance Claim Analysis Prototype**  
> *Academic Project — Multi-Agent Systems with CrewAI*

---

## 1. Project Title
**AI Insurance Claim Assistant** — A multi-agent AI prototype for preliminary insurance claim analysis.

---

## 2. Project Objective
Demonstrate how multiple specialized AI agents can collaborate in a sequential workflow to perform a preliminary analysis of an insurance claim submission, using CrewAI as the multi-agent orchestration framework.

---

## 3. Problem Definition
Insurance claim processing involves multiple specialized tasks: data extraction, policy eligibility checking, risk assessment, and report generation. This project models each task as an independent AI agent, showcasing multi-agent collaboration in a real-world domain context.

---

## 4. Features
- 🤖 **4 Specialized AI Agents** working in sequence
- 📋 **Structured Claim Analysis** with Pydantic models
- 🎨 **Clean Streamlit UI** with sample data loader
- 📊 **Visual Confidence Score** indicator
- 📄 **Complete Preliminary Assessment Report**
- ⚠️ **Clear Educational Disclaimer** on all outputs
- 🔒 **Environment-based API key** management

---

## 5. Multi-Agent Architecture

```
User Input (Streamlit)
        │
        ▼
┌─────────────────────────┐
│  Agent 1                │
│  Claim Information Agent│  ← Extracts & organizes claim data
└────────────┬────────────┘
             │ context
             ▼
┌─────────────────────────┐
│  Agent 2                │
│  Policy Eligibility     │  ← Checks coverage, limits, waiting period
│  Agent                  │
└────────────┬────────────┘
             │ context
             ▼
┌─────────────────────────┐
│  Agent 3                │
│  Claim Assessment Agent │  ← Synthesizes findings, flags concerns
└────────────┬────────────┘
             │ context
             ▼
┌─────────────────────────┐
│  Agent 4                │
│  Report Generation      │  ← Produces final structured report
│  Agent                  │
└─────────────────────────┘
             │
             ▼
  Final Preliminary Assessment
```

---

## 6. Agent Responsibilities

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Agent 1** | Claim Information Specialist | Extracts and organizes all claim details; identifies missing documents/information |
| **Agent 2** | Policy Eligibility Analyst | Evaluates treatment coverage, amount vs. limit, waiting period, policy conditions |
| **Agent 3** | Senior Claim Assessor | Synthesizes Agent 1 & 2 outputs; flags concerns, recommends next steps |
| **Agent 4** | Claim Report Writer | Produces the complete structured preliminary assessment report |

---

## 7. Technology Stack

| Technology | Purpose | Version |
|-----------|---------|---------|
| Python | Core language | 3.12+ |
| CrewAI | Multi-agent orchestration | ≥0.80.0 |
| Google Gemini | LLM (via LiteLLM) | gemini-1.5-flash |
| Streamlit | Web UI | ≥1.28.0 |
| Pydantic | Data validation & models | ≥2.0.0 |
| python-dotenv | Environment variables | ≥1.0.0 |

---

## 8. Project Structure

```
ai-insurance-claim-assistant/
│
├── app.py              # Streamlit UI (main entry point)
├── crew.py             # CrewAI Crew assembly & execution
├── agents.py           # 4 CrewAI Agent definitions
├── tasks.py            # 4 CrewAI Task definitions
├── models.py           # Pydantic data models
├── requirements.txt    # Python dependencies
├── .env.example        # API key template
├── .gitignore          # Git ignore rules
├── README.md           # This file
│
└── sample_data/
    └── sample_claims.json  # 3 sample test scenarios
```

---

## 9. Installation

### Prerequisites
- Python 3.12 or higher
- pip package manager
- A Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))

### Install dependencies

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install "crewai[google-genai]" streamlit python-dotenv pydantic
```

---

## 10. Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   On Windows:
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` and add your Gemini API key:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```

---

## 11. How to Run

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

---

## 12. Sample Input

**Sample 1 — Normal Hospitalization:**
- Claim Type: Hospitalization
- Hospital: Apollo Hospitals, Chennai
- Treatment: Appendectomy
- Claim Amount: ₹85,000
- Coverage Limit: ₹5,00,000
- Waiting Period: Satisfied
- Documents: Hospital Bill, Discharge Summary, Medical Reports, ID Proof

---

## 13. Sample Output

The system generates:
- **Claim Summary** — Organized claim details
- **Policy Summary** — Coverage analysis
- **Eligibility Assessment** — Likely Eligible / Requires Review / Insufficient Information
- **Missing Documents** — List of gaps
- **Key Observations** — Critical findings
- **Preliminary Recommendation** — Next steps
- **Confidence Score** — High / Medium / Low with visual bar
- **Full Report** — Complete agent-generated assessment

---

## 14. Deployment on Streamlit Community Cloud

1. Push the project to a **public GitHub repository**.
2. Remove `.env` from the repository (it is in `.gitignore`).
3. Go to [share.streamlit.io](https://share.streamlit.io) and log in.
4. Click **New app** and select your repository.
5. Set the main file to `app.py`.
6. In **Advanced Settings → Secrets**, add:
   ```toml
   GEMINI_API_KEY = "your_google_gemini_api_key_here"
   ```
7. Click **Deploy**.

---

## 15. Limitations

- **Educational prototype only** — not suitable for real insurance claim processing.
- LLM output may vary slightly between runs.
- Gemini API usage is subject to rate limits and quotas.
- Analysis time is approximately 60–120 seconds depending on API response speed.
- Designed for simple claim scenarios; does not handle complex multi-policy cases.

---

## 16. Educational Disclaimer

> **This project is created solely for academic and educational purposes.**  
> It demonstrates multi-agent AI system design using CrewAI.  
> It does **NOT** make actual insurance claim decisions, approvals, or rejections.  
> It does **NOT** use real customer data or connect to real insurance systems.  
> All claim scenarios used are fictional examples.  
> Real insurance claims must always be handled by qualified insurance professionals in accordance with actual policy terms and applicable regulations.

---

*Developed as part of an academic project on Multi-Agent Systems with CrewAI.*