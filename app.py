"""
app.py — Streamlit UI for the AI Insurance Claim Assistant.

Run with:
    streamlit run app.py

Requires a .env file with GEMINI_API_KEY set.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Insurance Claim Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Custom CSS — clean, professional styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #1a3a5c 0%, #2d6a9f 50%, #1a3a5c 100%);
    padding: 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
    color: white;
    box-shadow: 0 4px 20px rgba(26,58,92,0.3);
}
.main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}
.main-header p {
    font-size: 1rem;
    margin: 0.5rem 0 0 0;
    opacity: 0.85;
}

/* Info box */
.info-box {
    background: #e8f4fd;
    border-left: 4px solid #2d6a9f;
    padding: 1rem 1.2rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: 1.5rem;
    font-size: 0.92rem;
    color: #1a3a5c;
}

/* Section cards */
.result-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.result-card h3 {
    color: #1a3a5c;
    font-size: 1.05rem;
    font-weight: 600;
    margin-top: 0;
    margin-bottom: 0.6rem;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 0.5rem;
}

/* Status badges */
.badge-eligible {
    background: #d4edda;
    color: #155724;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    display: inline-block;
}
.badge-review {
    background: #fff3cd;
    color: #856404;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    display: inline-block;
}
.badge-insufficient {
    background: #f8d7da;
    color: #721c24;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.9rem;
    display: inline-block;
}

/* Disclaimer */
.disclaimer-box {
    background: #fff8e1;
    border: 1px solid #f0c040;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-top: 1.5rem;
    font-size: 0.85rem;
    color: #5c4800;
}

/* Progress steps */
.step-active {
    color: #2d6a9f;
    font-weight: 600;
}
.step-done {
    color: #28a745;
}
.step-pending {
    color: #adb5bd;
}

/* Confidence bar */
.confidence-bar-outer {
    background: #e9ecef;
    border-radius: 10px;
    height: 14px;
    width: 100%;
    margin: 8px 0;
}
.confidence-bar-inner {
    height: 14px;
    border-radius: 10px;
    transition: width 0.5s ease;
}
.confidence-high { background: linear-gradient(90deg, #28a745, #5cb85c); }
.confidence-medium { background: linear-gradient(90deg, #ffc107, #fd7e14); }
.confidence-low { background: linear-gradient(90deg, #dc3545, #f86c6b); }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def load_sample_claims() -> list:
    """Load sample claims from the JSON file."""
    sample_file = Path(__file__).parent / "sample_data" / "sample_claims.json"
    if sample_file.exists():
        with open(sample_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def check_api_key() -> bool:
    """Return True if GEMINI_API_KEY is set in environment."""
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


def get_eligibility_badge_html(status: str) -> str:
    """Return HTML badge for the given eligibility status string."""
    s = status.lower()
    if "likely eligible" in s:
        return '<span class="badge-eligible">✅ Likely Eligible</span>'
    elif "requires review" in s:
        return '<span class="badge-review">⚠️ Requires Review</span>'
    elif "insufficient" in s:
        return '<span class="badge-insufficient">❌ Insufficient Information</span>'
    else:
        return f'<span class="badge-review">⚠️ {status}</span>'


def render_confidence_bar(score: float, label: str):
    """Render a styled HTML confidence bar."""
    pct = int(score * 100)
    css_class = {
        "High": "confidence-high",
        "Medium": "confidence-medium",
        "Low": "confidence-low",
    }.get(label, "confidence-medium")

    st.markdown(
        f"""
        <div style="margin-bottom:0.3rem;">
            <strong>Confidence: {label} ({pct}%)</strong>
        </div>
        <div class="confidence-bar-outer">
            <div class="confidence-bar-inner {css_class}" style="width:{pct}%;"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def validate_inputs(
    hospital_name: str,
    treatment_description: str,
    claim_amount: float,
    policy_coverage_limit: float,
) -> list[str]:
    """Return a list of validation error messages (empty list = all valid)."""
    errors = []
    if not hospital_name.strip():
        errors.append("Hospital / Provider Name is required.")
    if not treatment_description.strip():
        errors.append("Treatment / Description is required.")
    if claim_amount <= 0:
        errors.append("Claim Amount must be greater than ₹0.")
    if policy_coverage_limit <= 0:
        errors.append("Policy Coverage Limit must be greater than ₹0.")
    if claim_amount > 10_000_000:  # Sanity check: ₹1 crore
        errors.append("Claim Amount seems unusually high. Please verify.")
    return errors


# ---------------------------------------------------------------------------
# Sidebar — sample data loader
# ---------------------------------------------------------------------------

_ALL_DOCS = ["Hospital Bill", "Discharge Summary", "Prescription", "Medical Reports", "ID Proof", "Other"]
_CLAIM_TYPES = ["Hospitalization", "Accident", "Medical", "Other"]


def _apply_sample_to_session(sample: dict):
    """Directly write each widget's session-state key so Streamlit picks them up on rerun."""
    claim_type = sample.get("claim_type", "Hospitalization")
    st.session_state["claim_type"] = claim_type if claim_type in _CLAIM_TYPES else "Hospitalization"
    st.session_state["hospital_name"] = sample.get("hospital_name", "")
    st.session_state["treatment_description"] = sample.get("treatment_description", "")
    st.session_state["claim_amount"] = float(sample.get("claim_amount", 0.0))
    st.session_state["policy_coverage_limit"] = float(sample.get("policy_coverage_limit", 0.0))
    st.session_state["waiting_period_satisfied"] = bool(sample.get("waiting_period_satisfied", True))
    st.session_state["coverage_categories"] = [
        c for c in sample.get("coverage_categories", [])
        if c in [
            "Hospitalization", "Surgical Procedures", "In-patient Treatment",
            "Out-patient Treatment", "Emergency Treatment", "Maternity",
            "Critical Illness", "Dental", "Vision / Ophthalmic",
            "Mental Health", "Accident", "Physiotherapy",
        ]
    ]
    provided_docs = sample.get("documents_provided", [])
    for doc in _ALL_DOCS:
        st.session_state[f"doc_{doc}"] = doc in provided_docs
    st.session_state["additional_info"] = sample.get("additional_info", "")
    # Also keep form_data in sync for reference
    st.session_state.form_data = sample


def render_sidebar(sample_claims: list) -> dict | None:
    """Render the sidebar with sample claim loader. Returns selected sample or None."""
    with st.sidebar:
        st.markdown("### 📂 Sample Claims")
        st.markdown("Load a pre-filled example to test the system:")

        selected_sample = None
        for sample in sample_claims:
            if st.button(sample["label"], key=f"sample_{sample['id']}", use_container_width=True):
                selected_sample = sample

        if selected_sample:
            st.success(f"✅ Loaded: {selected_sample['label']}")
            st.markdown(f"*{selected_sample['description']}*")

        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown(
            "**AI Insurance Claim Assistant**\n\n"
            "An educational multi-agent prototype using CrewAI.\n\n"
            "4 specialized AI agents collaborate to analyze claims:\n\n"
            "1. 📋 **Claim Information Agent**\n"
            "2. 📊 **Policy Eligibility Agent**\n"
            "3. 🔍 **Claim Assessment Agent**\n"
            "4. 📄 **Report Generation Agent**"
        )
        st.markdown("---")
        st.markdown(
            "<small>⚠️ For educational use only. Not actual insurance advice.</small>",
            unsafe_allow_html=True,
        )

    return selected_sample


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------

def main():
    # -----------------------------------------------------------------------
    # Header
    # -----------------------------------------------------------------------
    st.markdown("""
    <div class="main-header">
        <h1>🏥 AI Insurance Claim Assistant</h1>
        <p>Multi-Agent Insurance Claim Analysis Prototype</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-box">
        <strong>ℹ️ Educational Prototype</strong><br>
        This system uses multiple AI agents to perform a <em>preliminary</em> insurance claim analysis.
        It does <strong>not</strong> make actual claim settlement decisions and is intended solely
        for educational demonstration of multi-agent AI systems.
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # API key check
    # -----------------------------------------------------------------------
    if not check_api_key():
        st.error(
            "🔑 **GEMINI_API_KEY not found.**\n\n"
            "Please create a `.env` file in the project directory with:\n"
            "```\nGEMINI_API_KEY=your_google_gemini_api_key_here\n```\n\n"
            "Get a free API key at: https://aistudio.google.com/app/apikey"
        )
        st.stop()

    # -----------------------------------------------------------------------
    # Load samples and sidebar
    # -----------------------------------------------------------------------
    sample_claims = load_sample_claims()
    selected_sample = render_sidebar(sample_claims)

    # -----------------------------------------------------------------------
    # Session state — persist form values when a sample is loaded
    # -----------------------------------------------------------------------
    if "form_data" not in st.session_state:
        st.session_state.form_data = {}

    if selected_sample:
        _apply_sample_to_session(selected_sample)
        st.rerun()

    fd = st.session_state.form_data  # Shorthand

    # -----------------------------------------------------------------------
    # Input form
    # -----------------------------------------------------------------------
    st.markdown("## 📝 Claim Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Claim Information")

        claim_type = st.selectbox(
            "Claim Type *",
            options=["Hospitalization", "Accident", "Medical", "Other"],
            index=["Hospitalization", "Accident", "Medical", "Other"].index(
                fd.get("claim_type", "Hospitalization")
            ),
            key="claim_type",
        )

        hospital_name = st.text_input(
            "Hospital / Provider Name *",
            value=fd.get("hospital_name", ""),
            placeholder="e.g., Apollo Hospitals, Chennai",
            key="hospital_name",
        )

        treatment_description = st.text_area(
            "Treatment / Description *",
            value=fd.get("treatment_description", ""),
            placeholder="Describe the medical treatment or procedure...",
            height=120,
            key="treatment_description",
        )

        claim_amount = st.number_input(
            "Claim Amount (₹) *",
            min_value=0.0,
            max_value=10_000_000.0,
            value=float(fd.get("claim_amount", 0.0)),
            step=1000.0,
            format="%.2f",
            key="claim_amount",
        )

    with col2:
        st.markdown("### Policy Information")

        policy_coverage_limit = st.number_input(
            "Policy Coverage Limit (₹) *",
            min_value=0.0,
            max_value=50_000_000.0,
            value=float(fd.get("policy_coverage_limit", 0.0)),
            step=10000.0,
            format="%.2f",
            key="policy_coverage_limit",
        )

        waiting_period_satisfied = st.radio(
            "Waiting Period Satisfied?",
            options=[True, False],
            format_func=lambda x: "Yes — Waiting period has been completed" if x else "No — Still within waiting period",
            index=0 if fd.get("waiting_period_satisfied", True) else 1,
            key="waiting_period_satisfied",
        )

        # Coverage categories — multiselect with defaults from sample
        all_coverage_cats = [
            "Hospitalization",
            "Surgical Procedures",
            "In-patient Treatment",
            "Out-patient Treatment",
            "Emergency Treatment",
            "Maternity",
            "Critical Illness",
            "Dental",
            "Vision / Ophthalmic",
            "Mental Health",
            "Accident",
            "Physiotherapy",
        ]
        default_cats = fd.get("coverage_categories", [])
        coverage_categories = st.multiselect(
            "Coverage Categories (from policy)",
            options=all_coverage_cats,
            default=[c for c in default_cats if c in all_coverage_cats],
            key="coverage_categories",
        )

    # Documents section
    st.markdown("### 📄 Documents Provided")
    all_documents = [
        "Hospital Bill",
        "Discharge Summary",
        "Prescription",
        "Medical Reports",
        "ID Proof",
        "Other",
    ]
    default_docs = fd.get("documents_provided", [])

    doc_cols = st.columns(3)
    documents_provided = []
    for i, doc in enumerate(all_documents):
        with doc_cols[i % 3]:
            checked = doc in default_docs
            if st.checkbox(doc, value=checked, key=f"doc_{doc}"):
                documents_provided.append(doc)

    # Additional info
    st.markdown("### 💬 Additional Information")
    additional_info = st.text_area(
        "Additional Claim Details (optional)",
        value=fd.get("additional_info", ""),
        placeholder="Any additional context, notes, or relevant information about this claim...",
        height=100,
        key="additional_info",
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # Analyze button
    # -----------------------------------------------------------------------
    analyze_clicked = st.button(
        "🔍 Analyze Claim",
        type="primary",
        use_container_width=True,
        key="analyze_btn",
    )

    # -----------------------------------------------------------------------
    # Analysis execution
    # -----------------------------------------------------------------------
    if analyze_clicked:
        # Validate inputs
        errors = validate_inputs(
            hospital_name=hospital_name,
            treatment_description=treatment_description,
            claim_amount=claim_amount,
            policy_coverage_limit=policy_coverage_limit,
        )

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
            st.stop()

        # Import here to avoid loading CrewAI before API key is confirmed
        try:
            from models import ClaimInput
            from crew import run_claim_analysis
        except ImportError as e:
            st.error(
                f"❌ **Import Error:** {e}\n\n"
                "Please ensure all dependencies are installed:\n"
                "```\npip install crewai[google-genai] streamlit python-dotenv\n```"
            )
            st.stop()

        # Build claim input
        claim = ClaimInput(
            claim_type=claim_type,
            hospital_name=hospital_name,
            treatment_description=treatment_description,
            claim_amount=claim_amount,
            policy_coverage_limit=policy_coverage_limit,
            waiting_period_satisfied=waiting_period_satisfied,
            coverage_categories=coverage_categories,
            documents_provided=documents_provided,
            additional_info=additional_info,
        )

        # -----------------------------------------------------------------------
        # Progress display
        # -----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("## ⚙️ Running Multi-Agent Analysis")

        progress_container = st.container()
        result_placeholder = st.empty()

        with progress_container:
            steps = [
                ("🤖 Agent 1: Analyzing claim information...", "Claim Information Agent"),
                ("📊 Agent 2: Checking policy eligibility...", "Policy Eligibility Agent"),
                ("🔍 Agent 3: Assessing claim...", "Claim Assessment Agent"),
                ("📄 Agent 4: Generating final report...", "Report Generation Agent"),
            ]

            step_statuses = {i: "pending" for i in range(4)}
            step_containers = [st.empty() for _ in steps]

            def render_steps(active_step: int = -1):
                for i, (label, agent_name) in enumerate(steps):
                    if i < active_step:
                        step_containers[i].markdown(f"✅ ~~{label}~~ **Done**")
                    elif i == active_step:
                        step_containers[i].markdown(f"⏳ **{label}**")
                    else:
                        step_containers[i].markdown(f"⬜ {label}")

            render_steps(0)

            status_text = st.empty()
            current_step = [0]

            def status_callback(msg: str):
                status_text.info(f"ℹ️ {msg}")
                if "Agent 1" in msg:
                    render_steps(0)
                elif "Agent 2" in msg:
                    render_steps(1)
                elif "Agent 3" in msg:
                    render_steps(2)
                elif "Agent 4" in msg:
                    render_steps(3)
                elif "completed" in msg.lower() or "parsing" in msg.lower():
                    render_steps(4)

        # -----------------------------------------------------------------------
        # Execute the crew
        # -----------------------------------------------------------------------
        try:
            with st.spinner("Running multi-agent analysis... This may take 1-2 minutes."):
                report = run_claim_analysis(claim=claim, status_callback=status_callback)

            # All steps done
            render_steps(4)
            status_text.success("✅ Multi-agent analysis complete!")

        except EnvironmentError as e:
            st.error(f"🔑 **API Key Error:**\n{e}")
            st.stop()
        except RuntimeError as e:
            st.error(
                f"❌ **Analysis Failed:**\n\n{e}\n\n"
                "Please check your API key and network connection, then try again."
            )
            st.stop()
        except Exception as e:
            st.error(
                f"❌ **Unexpected Error:**\n\n{type(e).__name__}: {e}\n\n"
                "Please try again. If the problem persists, check the terminal for details."
            )
            st.stop()

        # -----------------------------------------------------------------------
        # Display results
        # -----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("## 📊 Preliminary Assessment Results")

        # -- Claim Summary --
        with st.expander("📋 Claim Summary", expanded=True):
            st.markdown(f"""
            <div class="result-card">
                <h3>📋 Claim Summary</h3>
                {report.claim_summary}
            </div>
            """, unsafe_allow_html=True)

        # -- Policy Summary --
        with st.expander("📜 Policy Summary", expanded=True):
            st.markdown(f"""
            <div class="result-card">
                <h3>📜 Policy Summary</h3>
                {report.policy_summary}
            </div>
            """, unsafe_allow_html=True)

        # -- Eligibility Assessment --
        with st.expander("✅ Eligibility Assessment", expanded=True):
            badge_html = get_eligibility_badge_html(report.eligibility_assessment)
            st.markdown(f"""
            <div class="result-card">
                <h3>✅ Eligibility Assessment</h3>
                {badge_html}
                <br><br>
                {report.eligibility_assessment}
            </div>
            """, unsafe_allow_html=True)

        # -- Missing Documents --
        with st.expander("📂 Missing Documents & Information", expanded=True):
            missing_content = report.missing_documents_section
            if not missing_content or "all required" in missing_content.lower():
                missing_display = "✅ All required documents appear to be present."
            else:
                missing_display = missing_content
            st.markdown(f"""
            <div class="result-card">
                <h3>📂 Missing Documents & Information</h3>
                {missing_display}
            </div>
            """, unsafe_allow_html=True)

        # -- Key Observations --
        with st.expander("🔍 Key Observations", expanded=True):
            st.markdown(f"""
            <div class="result-card">
                <h3>🔍 Key Observations</h3>
                {report.key_observations}
            </div>
            """, unsafe_allow_html=True)

        # -- Preliminary Recommendation --
        with st.expander("💡 Preliminary Recommendation", expanded=True):
            st.markdown(f"""
            <div class="result-card">
                <h3>💡 Preliminary Recommendation</h3>
                <strong>{report.preliminary_recommendation}</strong>
            </div>
            """, unsafe_allow_html=True)

        # -- Confidence Score --
        st.markdown("### 📈 Confidence Level")
        render_confidence_bar(report.confidence_score, report.confidence_label)

        # -- Full Report --
        with st.expander("📄 Full Assessment Report", expanded=False):
            st.markdown(report.full_report)

        # -- Disclaimer --
        st.markdown(f"""
        <div class="disclaimer-box">
            <strong>⚠️ Disclaimer:</strong><br>
            {report.disclaimer}
        </div>
        """, unsafe_allow_html=True)

        # -- Quick summary metrics --
        st.markdown("---")
        st.markdown("### 📊 Quick Summary")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Claim Amount", f"₹{claim_amount:,.0f}")
        with m2:
            st.metric("Coverage Limit", f"₹{policy_coverage_limit:,.0f}")
        with m3:
            coverage_pct = (claim_amount / policy_coverage_limit * 100) if policy_coverage_limit > 0 else 0
            st.metric("% of Limit Used", f"{coverage_pct:.1f}%")
        with m4:
            st.metric("Confidence", f"{report.confidence_label} ({int(report.confidence_score*100)}%)")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    main()
