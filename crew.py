"""
crew.py — CrewAI Crew orchestration for the AI Insurance Claim Assistant.

Assembles the four agents and four tasks into a sequential Crew
and provides the run_claim_analysis() function used by app.py.
"""

from __future__ import annotations

import os

# Disable CrewAI / OpenTelemetry telemetry prompt
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
import re
from typing import Callable, Optional

from dotenv import load_dotenv
from crewai import Crew, Process

from agents import create_agents
from tasks import create_tasks
from models import ClaimInput, FinalReport

# Load .env at module import time
load_dotenv()


# ---------------------------------------------------------------------------
# Output parsing helpers
# ---------------------------------------------------------------------------

def _extract_section(text: str, section_header: str, next_header: Optional[str] = None) -> str:
    """
    Extract a named section from structured agent output text.
    Handles both '## HEADER' and 'HEADER:' formats.
    """
    # Try markdown heading style first (## SECTION)
    pattern_md = rf"##\s*{re.escape(section_header)}\s*\n(.*?)(?=##\s|\Z)"
    match = re.search(pattern_md, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try label style (SECTION: ...)
    pattern_label = rf"{re.escape(section_header)}\s*:?\s*\n?(.*?)(?=\n[A-Z][A-Z\s]+:|\Z)"
    match = re.search(pattern_label, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def _extract_confidence_score(text: str) -> float:
    """Extract a confidence score (0.0-1.0) from agent output text."""
    # Look for decimal like 0.85 or 0.7
    match = re.search(r'\b(0\.\d+|1\.0)\b', text)
    if match:
        score = float(match.group(1))
        return max(0.0, min(1.0, score))
    # Look for percentage like 85%
    match = re.search(r'(\d{1,3})\s*%', text)
    if match:
        pct = float(match.group(1))
        return max(0.0, min(1.0, pct / 100.0))
    return 0.5  # Default medium confidence


def _get_confidence_label(score: float) -> str:
    if score >= 0.8:
        return "High"
    elif score >= 0.5:
        return "Medium"
    else:
        return "Low"


def _parse_final_report(raw_output: str, claim: ClaimInput) -> FinalReport:
    """
    Parse the Report Generation Agent's raw text output into a FinalReport model.
    Falls back to sensible defaults if sections cannot be extracted.
    """
    text = str(raw_output)

    claim_summary = _extract_section(text, "CLAIM SUMMARY") or (
        f"A {claim.claim_type} claim for {claim.treatment_description} at "
        f"{claim.hospital_name} for ₹{claim.claim_amount:,.2f}."
    )

    policy_summary = _extract_section(text, "POLICY SUMMARY") or (
        f"Policy coverage limit: ₹{claim.policy_coverage_limit:,.2f}. "
        f"Waiting period satisfied: {'Yes' if claim.waiting_period_satisfied else 'No'}."
    )

    eligibility_assessment = (
        _extract_section(text, "ELIGIBILITY ASSESSMENT")
        or _extract_section(text, "ELIGIBILITY STATUS")
        or "Eligibility assessment details are in the full report below."
    )

    missing_docs = (
        _extract_section(text, "MISSING DOCUMENTS")
        or "See full report for missing document details."
    )

    key_observations = (
        _extract_section(text, "KEY OBSERVATIONS")
        or _extract_section(text, "IMPORTANT OBSERVATIONS")
        or "See full report for key observations."
    )

    recommendation = (
        _extract_section(text, "PRELIMINARY RECOMMENDATION")
        or "See full report for recommendation."
    )

    confidence_score = _extract_confidence_score(text)
    confidence_label = _get_confidence_label(confidence_score)

    disclaimer = (
        "This report is an AI-generated preliminary assessment created for educational demonstration "
        "purposes only. It is NOT a final insurance claim decision, approval, or rejection. "
        "All claims must be reviewed and decided by qualified insurance professionals in accordance "
        "with the actual policy terms and applicable regulations."
    )

    return FinalReport(
        claim_summary=claim_summary,
        policy_summary=policy_summary,
        eligibility_assessment=eligibility_assessment,
        missing_documents_section=missing_docs,
        key_observations=key_observations,
        preliminary_recommendation=recommendation,
        confidence_score=confidence_score,
        confidence_label=confidence_label,
        full_report=text,
        disclaimer=disclaimer,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_claim_analysis(
    claim: ClaimInput,
    status_callback: Optional[Callable[[str], None]] = None,
) -> FinalReport:
    """
    Run the full 4-agent sequential CrewAI pipeline for the given claim.

    Args:
        claim: Validated ClaimInput with all claim details.
        status_callback: Optional callable to receive progress status strings.

    Returns:
        FinalReport: Structured output from the Report Generation Agent.

    Raises:
        EnvironmentError: If GEMINI_API_KEY is not configured.
        RuntimeError: If the CrewAI execution fails.
    """

    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    _status("🔍 Initializing agents...")

    # Create agents (validates API key here)
    claim_info_agent, eligibility_agent, assessment_agent, report_agent = create_agents()

    _status("📋 Creating tasks...")

    # Create tasks with claim context injected into descriptions
    task1, task2, task3, task4 = create_tasks(
        claim=claim,
        claim_info_agent=claim_info_agent,
        eligibility_agent=eligibility_agent,
        assessment_agent=assessment_agent,
        report_agent=report_agent,
    )

    # Real-time step messages — fired by task_callback after each task completes
    _step_messages = [
        "🤖 Agent 1/4: Analyzing claim information...",
        "📊 Agent 2/4: Checking policy eligibility...",
        "🔍 Agent 3/4: Assessing claim...",
        "📄 Agent 4/4: Generating final report...",
    ]
    _completed = [0]  # mutable counter for closure

    def _task_done_callback(task_output):
        """Called by CrewAI after each task finishes; advance the status indicator."""
        _completed[0] += 1
        next_idx = _completed[0]
        if next_idx < len(_step_messages):
            _status(_step_messages[next_idx])

    # Assemble the sequential Crew
    crew = Crew(
        agents=[claim_info_agent, eligibility_agent, assessment_agent, report_agent],
        tasks=[task1, task2, task3, task4],
        process=Process.sequential,
        verbose=True,
        task_callback=_task_done_callback,
    )

    _status("🤖 Agent 1/4: Analyzing claim information...")

    try:
        result = crew.kickoff()
    except Exception as exc:
        raise RuntimeError(
            f"CrewAI execution failed: {exc}\n\n"
            "Please check your API key, network connection, and try again."
        ) from exc

    _status("✅ All agents completed. Parsing report...")

    # The final result is the output of Task 4 (Report Generation Agent)
    raw_output = str(result)
    report = _parse_final_report(raw_output, claim)

    return report
