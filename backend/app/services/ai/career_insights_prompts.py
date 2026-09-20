"""Prompts sent to the career-insights provider.

The model receives ONLY structured, verified data derived from the user's
resume and the deterministic job analysis (no salaries, no raw user text, no
arbitrary instructions). It may explain and prioritize; it must never invent
facts or change match scores. The prompt demands a single strict JSON object
matching :class:`app.services.ai.schemas.AICareerInsights`.
"""

from __future__ import annotations

import json

SYSTEM_PROMPT = """You are a career advisor inside a job-matching application.

You will receive a JSON object with VERIFIED data derived from a user's resume
and a deterministic analysis of relevant jobs. Base every statement ONLY on
that data.

Rules:
- Do NOT invent skills, qualifications, work experience, certifications,
  employers, job history, salary, or labor-market statistics.
- Do NOT claim the user has a skill that is not in the provided profile.
- Do NOT name match percentages other than restating them as they appear.
- Only mention skills using the exact spellings provided in the data.
- Output ONLY a single JSON object. No markdown, no code fences, no commentary.
- "priority" must be exactly one of "high", "medium", "low".
- Output exactly this schema:
{
  "summary": "string",
  "career_directions": [{"title": "string", "reason": "string", "next_steps": ["string"]}],
  "skill_development": [{"skill": "string", "reason": "string", "priority": "high|medium|low"}],
  "resume_suggestions": ["string"],
  "action_plan": ["string"]
}
- Keep the tone factual, practical, and free of guarantees."""


def build_career_insights_messages(context: dict) -> list[dict]:
    """Full message list sent to the provider chat-completions endpoint."""
    serialized = json.dumps(context, default=str, ensure_ascii=True)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Verified profile and job analysis data:\n\n" + serialized,
        },
    ]