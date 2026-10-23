"""
tasks.py — CrewAI Task definitions for the AI Insurance Claim Assistant.

Tasks are created fresh for each claim submission so that input data
can be injected into task descriptions at runtime.
"""

from __future__ import annotations
from typing import Any

from crewai import Task
from models import ClaimInput


# ---------------------------------------------------------------------------
# Helper: format claim input into a readable block for task descriptions
# ---------------------------------------------------------------------------

def _format_claim_context(claim: ClaimInput) -> str:
    docs = ", ".join(claim.documents_provided) if claim.documents_provided else "None provided"
    cats = ", ".join(claim.coverage_categories) if claim.coverage_categories else "Not specified"
    waiting = "Yes (waiting period has been satisfied)" if claim.waiting_period_satisfied else "No (waiting period NOT satisfied)"

    return f"""
=== CLAIM SUBMISSION DATA ===

Claim Type          : {claim.claim_type}
Hospital / Provider : {claim.hospital_name}
Treatment           : {claim.treatment_description}
Claim Amount        : ₹{claim.claim_amount:,.2f}
Policy Limit        : ₹{claim.policy_coverage_limit:,.2f}
Waiting Period      : {waiting}
Coverage Categories : {cats}
Documents Provided  : {docs}
Additional Info     : {claim.additional_info if claim.additional_info else "None"}

=============================
""".strip()


# ---------------------------------------------------------------------------
# Task factory — creates all 4 tasks for a given claim input
# ---------------------------------------------------------------------------

def create_tasks(
    claim: ClaimInput,
    claim_info_agent: Any,
    eligibility_agent: Any,
    assessment_agent: Any,
    report_agent: Any,
) -> tuple:
    """
    Create and return the four sequential CrewAI tasks.
    Later tasks use `context` to receive outputs from earlier tasks.

    Returns:
        (task1, task2, task3, task4)
    """

    claim_context = _format_claim_context(claim)

    # ------------------------------------------------------------------
    # Task 1 — Claim Information Extraction
    # ------------------------------------------------------------------
    task1 = Task(
        description=f"""
You are the Claim Information Specialist. Analyze the following insurance claim submission
and produce a structured information summary.

{claim_context}

Your output MUST include the following sections clearly labeled:

1. CLAIM TYPE: (exact type)
2. TREATMENT/PROCEDURE: (what treatment was performed)
3. HOSPITAL/PROVIDER: (name of hospital or provider)
4. CLAIM AMOUNT: (₹ amount)
5. POLICY COVERAGE LIMIT: (₹ limit)
6. WAITING PERIOD STATUS: (satisfied or not satisfied)
7. COVERAGE CATEGORIES: (list all provided categories)
8. DOCUMENTS PROVIDED: (list all documents submitted)
9. MISSING DOCUMENTS: (list any commonly required documents that appear to be missing, such as: Hospital Bill, Discharge Summary, Prescription, Medical Reports, ID Proof)
10. MISSING INFORMATION: (any gaps in the claim information that need clarification)
11. KEY DETAILS: (any other relevant observations about the claim data)
12. CLAIM SUMMARY: (2-3 sentence overview of the claim)

Important: Do NOT invent information. If a field is not provided, state "Not provided".
Do NOT make any eligibility determination — that is handled by the next agent.
""",
        expected_output="""
A structured claim information report with all 12 labeled sections filled in accurately.
Include a clear list of missing documents and missing information.
No eligibility verdict — only organized factual information.
""",
        agent=claim_info_agent,
    )

    # ------------------------------------------------------------------
    # Task 2 — Policy Eligibility Assessment
    # ------------------------------------------------------------------
    task2 = Task(
        description=f"""
You are the Policy Eligibility Analyst. Using the claim information extracted by the
Claim Information Specialist (provided in the context above), evaluate whether this
claim appears eligible based on the following policy rules.

ORIGINAL CLAIM DATA FOR REFERENCE:
{claim_context}

POLICY RULES TO APPLY:
- Coverage check: The claimed treatment/procedure must fall under one of the listed coverage categories.
  If the coverage categories list is empty or vague, note this as a concern.
- Amount check: The claim amount must not exceed the policy coverage limit.
- Waiting period: If waiting period is NOT satisfied, the claim is typically NOT eligible.
- Document completeness: All standard required documents should be present.

Your output MUST include the following sections:

1. ELIGIBILITY STATUS: Choose EXACTLY one of:
   - "Likely Eligible" (all checks pass, documents appear sufficient)
   - "Requires Review" (one or more checks fail or are unclear)
   - "Insufficient Information" (critical data is missing to make any determination)

2. TREATMENT COVERED: Yes / No / Uncertain — with explanation
3. AMOUNT WITHIN LIMIT: Yes / No — with amounts stated
4. WAITING PERIOD SATISFIED: Yes / No / Not Stated
5. ALL CONDITIONS MET: Yes / No / Partially
6. COVERAGE OBSERVATIONS: Bullet list of specific coverage-related observations
7. REASONING: 3-5 sentences explaining the overall eligibility determination

Important: This is a PRELIMINARY assessment only.
Do NOT use the words "approved" or "rejected". Use "Likely Eligible", "Requires Review", or "Insufficient Information".
""",
        expected_output="""
A structured eligibility report with all 7 labeled sections.
Eligibility status must be exactly one of: "Likely Eligible", "Requires Review", or "Insufficient Information".
Clear reasoning for the determination.
""",
        agent=eligibility_agent,
        context=[task1],  # Receives Task 1 output as context
    )

    # ------------------------------------------------------------------
    # Task 3 — Claim Assessment
    # ------------------------------------------------------------------
    task3 = Task(
        description=f"""
You are the Senior Claim Assessor. Review the outputs from:
- The Claim Information Specialist (Task 1)
- The Policy Eligibility Analyst (Task 2)

Both outputs are provided in the context above.

ORIGINAL CLAIM DATA FOR REFERENCE:
{claim_context}

Produce a comprehensive assessment covering:

1. IMPORTANT OBSERVATIONS: Bullet list of key facts and notable aspects of this claim
2. COVERAGE CONCERNS: Bullet list of any specific coverage issues, exclusions, or policy concerns identified
3. MISSING DOCUMENTS: Bullet list of all documents that are missing and why they matter
4. MISSING INFORMATION: Bullet list of all information gaps that need clarification
5. AREAS REQUIRING HUMAN REVIEW: Bullet list of aspects that a human insurance professional must evaluate
6. PRELIMINARY RECOMMENDATION: One clear sentence recommendation (e.g., "Proceed with documentation review", "Request missing documents before processing", "Flag for specialist review due to coverage concerns")
7. CONFIDENCE SCORE: A number between 0.0 and 1.0 representing confidence in the preliminary assessment based on completeness of information
   - 0.9-1.0: All information present, clear case
   - 0.7-0.8: Minor gaps, mostly clear
   - 0.5-0.6: Significant gaps or concerns
   - Below 0.5: Major missing information or multiple red flags

Important: Base your assessment ONLY on the information provided. Do not assume or invent facts.
""",
        expected_output="""
A structured assessment report with all 7 labeled sections.
Confidence score must be a decimal between 0.0 and 1.0.
Concrete, actionable observations and recommendations.
""",
        agent=assessment_agent,
        context=[task1, task2],  # Receives both Task 1 and Task 2 outputs
    )

    # ------------------------------------------------------------------
    # Task 4 — Final Report Generation
    # ------------------------------------------------------------------
    task4 = Task(
        description=f"""
You are the Insurance Claim Report Writer. Synthesize the outputs from all three
previous agents into one complete, well-structured preliminary assessment report.

All three previous agent outputs are available in the context above.

ORIGINAL CLAIM DATA FOR REFERENCE:
{claim_context}

Generate a final report with the following clearly labeled sections:

## CLAIM SUMMARY
A 3-4 sentence narrative summary of the claim details.

## POLICY SUMMARY
A 2-3 sentence summary of the policy coverage details and any notable policy conditions.

## ELIGIBILITY ASSESSMENT
The eligibility status (Likely Eligible / Requires Review / Insufficient Information)
with a 3-4 sentence explanation of the determination.

## MISSING DOCUMENTS
A formatted list of missing documents with brief explanations of why each is needed.
If no documents are missing, state "All required documents appear to be present."

## KEY OBSERVATIONS
The most important findings from the assessment, as a numbered list.

## PRELIMINARY RECOMMENDATION
A clear, specific recommendation for the next steps to be taken by the insurance team.

## CONFIDENCE SCORE
State the confidence score (0.0 to 1.0) and label (High: 0.8-1.0, Medium: 0.5-0.79, Low: below 0.5).
Include a one-sentence explanation of what drives the confidence level.

## DISCLAIMER
Include the following disclaimer verbatim:
"This report is an AI-generated preliminary assessment created for educational demonstration 
purposes only. It is NOT a final insurance claim decision, approval, or rejection. 
All claims must be reviewed and decided by qualified insurance professionals in accordance 
with the actual policy terms and applicable regulations."

Write in clear, professional language suitable for both insurance professionals and claimants.
""",
        expected_output="""
A complete, well-formatted preliminary assessment report with all 8 labeled sections.
Professional tone. Clear structure. Mandatory disclaimer included verbatim.
Confidence score between 0.0 and 1.0 with a label (High/Medium/Low).
""",
        agent=report_agent,
        context=[task1, task2, task3],  # Receives all three previous task outputs
    )

    return task1, task2, task3, task4
