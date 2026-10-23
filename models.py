"""
models.py — Pydantic data models for the AI Insurance Claim Assistant.
All models use Pydantic v2 syntax (model_validator, field_validator, etc.).
"""

from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input models (Streamlit → CrewAI)
# ---------------------------------------------------------------------------

class ClaimInput(BaseModel):
    """Raw claim data submitted by the user via Streamlit."""

    claim_type: str = Field(..., description="Type of claim (Hospitalization, Accident, Medical, Other)")
    hospital_name: str = Field(..., description="Hospital or provider name")
    treatment_description: str = Field(..., description="Treatment or procedure description")
    claim_amount: float = Field(..., description="Claimed amount in INR (₹)")
    policy_coverage_limit: float = Field(..., description="Maximum coverage limit in INR (₹)")
    waiting_period_satisfied: bool = Field(..., description="Whether the waiting period has been completed")
    coverage_categories: List[str] = Field(default_factory=list, description="List of covered categories/treatments")
    documents_provided: List[str] = Field(default_factory=list, description="List of submitted documents")
    additional_info: str = Field(default="", description="Any additional claim information")


# ---------------------------------------------------------------------------
# Agent output models
# ---------------------------------------------------------------------------

class ClaimAnalysis(BaseModel):
    """Output of Agent 1 — Claim Information Agent."""

    claim_type: str
    treatment: str
    hospital: str
    claim_amount_inr: float
    policy_coverage_limit_inr: float
    waiting_period_satisfied: bool
    coverage_categories: List[str]
    documents_provided: List[str]
    missing_documents: List[str]
    missing_information: List[str]
    key_details: str
    summary: str


class EligibilityAnalysis(BaseModel):
    """Output of Agent 2 — Policy Eligibility Agent."""

    eligibility_status: str          # "Likely Eligible", "Requires Review", "Insufficient Information"
    treatment_covered: bool
    amount_within_limit: bool
    waiting_period_ok: bool
    conditions_met: bool
    coverage_observations: List[str]
    reasoning: str


class ClaimAssessment(BaseModel):
    """Output of Agent 3 — Claim Assessment Agent."""

    important_observations: List[str]
    coverage_concerns: List[str]
    missing_documents: List[str]
    missing_information: List[str]
    areas_requiring_human_review: List[str]
    preliminary_recommendation: str
    confidence_score: float          # 0.0 – 1.0


class FinalReport(BaseModel):
    """Output of Agent 4 — Report Generation Agent."""

    claim_summary: str
    policy_summary: str
    eligibility_assessment: str
    missing_documents_section: str
    key_observations: str
    preliminary_recommendation: str
    confidence_score: float          # 0.0 – 1.0
    confidence_label: str            # "High", "Medium", "Low"
    full_report: str
    disclaimer: str
