# CareerOS — Project Overview

## What is CareerOS?
CareerOS is an AI-powered career platform that helps job seekers understand
their own professional profile and discover job opportunities that genuinely
match their skills and qualifications.

## Problem
Job seekers often apply broadly without a clear sense of how well their
background actually fits a given role, leading to wasted effort and
low-quality applications.

## Solution
CareerOS extracts a structured profile from a user's resume (skills,
education, experience, certifications) and matches it against live job
listings, surfacing clear Skill Match % and Qualification Match % scores.

## Main Features
- Resume upload and AI-assisted structured extraction
- Skill / qualification / experience extraction
- Job discovery from approved job data sources
- Skill Match % and Qualification Match % per job
- Job filtering (location, work mode, job type, salary)
- Saved jobs and application tracking
- Personalized career dashboard and insights

## Target Users
- University students and recent graduates entering the job market
- Early-to-mid career professionals looking for a better-fitting role

## Tech Stack
- **Frontend:** Next.js (App Router), React, Tailwind CSS, Lucide icons
- **Backend:** FastAPI, Pydantic, SQLAlchemy, Alembic, Pandas, NumPy
- **Database:** PostgreSQL (via SQLAlchemy; SDK-free SQLite used in tests)
- **AI:** Provider-agnostic LLM integration for resume analysis (reserved, not
  yet implemented)

## Current Status
The foundation is stable (see `docs/PHASE_0_REPORT.md`): JWT auth, resume
parsing/persistence, placeholder job provider, application tracking backend,
and Alembic migrations are in place with a passing test suite. AI analysis,
real job providers, advanced matching, and most dashboard data flows are
planned but not implemented.
