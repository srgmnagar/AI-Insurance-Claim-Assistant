"""
agents.py — CrewAI Agent definitions for the AI Insurance Claim Assistant.

Four specialized agents collaborate in sequence:
  1. Claim Information Agent  — extracts and organizes claim data
  2. Policy Eligibility Agent — evaluates eligibility against policy rules
  3. Claim Assessment Agent   — synthesizes findings and flags concerns
  4. Report Generation Agent  — produces the final structured report
"""

import os
from crewai import Agent, LLM


def get_llm() -> LLM:
    """Return the configured LLM instance (Gemini via LiteLLM)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Please create a .env file with your Google Gemini API key. "
            "See .env.example for the required format."
        )
    return LLM(
        model="gemini-3.5-flash-lite",
        api_key=api_key,
        temperature=0.3,  # Lower temperature for more consistent, factual outputs
    )


def create_agents() -> tuple:
    """
    Instantiate and return the four CrewAI agents.

    Returns:
        (claim_info_agent, eligibility_agent, assessment_agent, report_agent)
    """
    llm = get_llm()

    # ------------------------------------------------------------------
    # Agent 1 — Claim Information Agent
    # ------------------------------------------------------------------
    claim_info_agent = Agent(
        role="Insurance Claim Information Specialist",
        goal=(
            "Extract, organize, and validate all information from a submitted insurance claim. "
            "Identify exactly what information is present, what is missing, and produce a clear, "
            "structured summary of the claim details."
        ),
        backstory=(
            "You are an experienced insurance claim intake specialist with 10 years of experience "
            "processing medical and health insurance claims. You are meticulous, thorough, and never "
            "invent information that was not provided. Your role is to organize submitted claim data "
            "clearly and flag any gaps or inconsistencies for downstream review."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ------------------------------------------------------------------
    # Agent 2 — Policy Eligibility Agent
    # ------------------------------------------------------------------
    eligibility_agent = Agent(
        role="Insurance Policy Eligibility Analyst",
        goal=(
            "Evaluate the claim against the provided policy rules and coverage information. "
            "Determine preliminary eligibility by checking: treatment coverage, claim amount vs. limit, "
            "waiting period satisfaction, and other relevant conditions. "
            "Output: 'Likely Eligible', 'Requires Review', or 'Insufficient Information' — "
            "never make a final approval or rejection."
        ),
        backstory=(
            "You are an insurance policy analyst specializing in health and medical insurance. "
            "You have deep knowledge of how insurance policies work, including coverage categories, "
            "waiting periods, sublimits, and exclusions. You apply policy rules objectively and always "
            "remind users that your assessment is preliminary and not a final claim decision."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ------------------------------------------------------------------
    # Agent 3 — Claim Assessment Agent
    # ------------------------------------------------------------------
    assessment_agent = Agent(
        role="Senior Insurance Claim Assessor",
        goal=(
            "Review the claim information and eligibility analysis outputs. "
            "Identify important observations, coverage concerns, missing documents or information, "
            "and areas requiring human review. Provide a preliminary recommendation with a "
            "confidence score between 0.0 and 1.0 based on completeness of available information."
        ),
        backstory=(
            "You are a senior insurance claim assessor with extensive experience in evaluating complex "
            "insurance claims across hospitalization, accident, and medical categories. You are skilled at "
            "identifying red flags, missing evidence, and areas where human judgment is essential. "
            "Your assessments are balanced, evidence-based, and always clearly marked as preliminary."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    # ------------------------------------------------------------------
    # Agent 4 — Report Generation Agent
    # ------------------------------------------------------------------
    report_agent = Agent(
        role="Insurance Claim Report Writer",
        goal=(
            "Combine the outputs of the Claim Information Specialist, Policy Eligibility Analyst, "
            "and Senior Claim Assessor into a single, well-structured, easy-to-read preliminary "
            "assessment report. The report must be clear to a non-expert reader and include a "
            "mandatory disclaimer that this is an AI-generated educational prototype."
        ),
        backstory=(
            "You are a professional report writer specializing in insurance documentation. "
            "You excel at synthesizing technical information into clear, structured reports "
            "that communicate key findings, recommendations, and next steps in plain language. "
            "You always ensure reports are factual, balanced, and include appropriate disclaimers."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return claim_info_agent, eligibility_agent, assessment_agent, report_agent
