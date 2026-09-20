"""
Prompts sent to the resume-intelligence provider.

The prompt demands strict JSON output matching
:class:`app.services.ai.schemas.AIResumeExtraction` and explicitly forbids
matching/score calculations and invented information. It never includes data
about jobs, so the model cannot tailor extraction to any employer.
"""

from __future__ import annotations

SYSTEM_PROMPT = """You extract structured information from resume text for a job-matching application.

Rules:
- Return ONLY a single JSON object. No markdown, no code fences, no commentary.
- Do not calculate match percentages, scores, or recommendations.
- Do not guess or invent anything that is not present in the text. Use null for missing values and [] for empty lists.
- For dates, use the format YYYY-MM (year-month). If only a year is given, use YYYY-01.
- For a role described in the present tense (or marked as current), set currently_employed to true and omit end_date.
- Output exactly this schema:
{
  "skills": ["string"],
  "education": [{"institution": "string", "degree": "string", "field_of_study": "string", "start_year": int, "end_year": int}],
  "certifications": [{"name": "string", "issuer": "string", "issue_year": int, "expiry_year": int}],
  "experience": [{"company": "string", "job_title": "string", "description": "string", "location": "string", "start_date": "YYYY-MM", "end_date": "YYYY-MM", "currently_employed": bool}]
}
- Keep company names, job titles, skill names, and degree names word-for-word as they appear."""


def build_messages(raw_text: str) -> list[dict]:
    """Full message list sent to the provider chat-completions endpoint."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Resume text:\n\n" + raw_text},
    ]


def truncate_resume_text(raw_text: str, max_chars: int) -> str:
    """Keep the head of the resume within the provider's context budget."""
    raw_text = raw_text or ""
    if max_chars <= 0 or len(raw_text) <= max_chars:
        return raw_text
    return raw_text[:max_chars]