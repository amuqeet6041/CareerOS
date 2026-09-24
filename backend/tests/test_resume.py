"""Tests for resume upload, parsing, and persistence.

Uses the shared in-memory SQLite test database defined in conftest.py.
PDF/DOCX fixtures are generated in-memory with PyMuPDF and python-docx.
"""

import io

import pymupdf
from docx import Document

from tests.conftest import client, TestingSessionLocal

from app.core.config import settings
from app.services.resume_parser import parse_resume
from app.models.resume import Resume, Skill

DOCX_CT = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

RESUME_TEXT = """John Doe
Data Analyst

Summary
Experienced data analyst.

Skills
Python, SQL, Pandas, Power BI, Excel

Education
Bachelor of Science in Computer Science, University of Ottawa, 2015-2019

Work Experience
Data Analyst at Acme Inc.
Analyzed sales data using SQL and Power BI
Built automated reports with Pandas

Certifications
AWS Certified Solutions Architect - Amazon Web Services
PMP Project Management Professional (2019)
"""


def make_docx(text=RESUME_TEXT):
    buffer = io.BytesIO()
    doc = Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    doc.save(buffer)
    return buffer.getvalue()


def make_pdf(text=RESUME_TEXT):
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


def make_empty_pdf():
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def register_user(email="resume.user@example.com"):
    return client.post(
        "/api/auth/register",
        json={"name": "Resume Tester", "email": email, "password": "secret123"},
    )


def login_user(email="resume.user@example.com"):
    return client.post("/api/auth/login", json={"email": email, "password": "secret123"})


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def upload_headers(token):
    return auth_headers(token)


def test_upload_requires_auth():
    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
    )
    assert response.status_code == 401


def test_upload_pdf_success():
    register_user(email="pdf@example.com")
    token = login_user(email="pdf@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        headers=upload_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["file_name"] == "resume.pdf"
    skill_names = [skill["name"] for skill in data["skills"]]
    assert "Python" in skill_names
    assert "Power BI" in skill_names
    assert data["education"][0]["institution"] == "University of Ottawa"
    assert data["experience"][0]["company"] == "Acme Inc."
    assert data["certifications"][0]["name"] == "AWS Certified Solutions Architect"


def test_upload_docx_success():
    register_user(email="docx@example.com")
    token = login_user(email="docx@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.docx", make_docx(), DOCX_CT)},
        headers=upload_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    skill_names = [skill["name"] for skill in data["skills"]]
    assert "Python" in skill_names
    assert data["education"][0]["degree"] == "Bachelor of Science"


def test_unsupported_file_rejected():
    register_user(email="txt@example.com")
    token = login_user(email="txt@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.txt", b"plain text resume", "text/plain")},
        headers=upload_headers(token),
    )
    assert response.status_code == 415

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.jpg", b"\xff\xd8\xff", "image/jpeg")},
        headers=upload_headers(token),
    )
    assert response.status_code == 415


def test_content_type_conflict_rejected():
    register_user(email="mime@example.com")
    token = login_user(email="mime@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_pdf(), "image/png")},
        headers=upload_headers(token),
    )
    assert response.status_code == 415


def test_oversized_file_rejected(monkeypatch):
    register_user(email="big@example.com")
    token = login_user(email="big@example.com").json()["access_token"]

    monkeypatch.setattr(settings, "MAX_RESUME_SIZE_MB", 0)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        headers=upload_headers(token),
    )
    assert response.status_code == 413


def test_empty_pdf_rejected():
    register_user(email="empty@example.com")
    token = login_user(email="empty@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_empty_pdf(), "application/pdf")},
        headers=upload_headers(token),
    )
    assert response.status_code == 400


def test_malformed_files_rejected():
    register_user(email="bad@example.com")
    token = login_user(email="bad@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", b"not a pdf at all", "application/pdf")},
        headers=upload_headers(token),
    )
    assert response.status_code == 400

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.docx", b"not a docx either", DOCX_CT)},
        headers=upload_headers(token),
    )
    assert response.status_code == 400


def test_analysis_without_resume_returns_404():
    register_user(email="newcomer@example.com")
    token = login_user(email="newcomer@example.com").json()["access_token"]

    response = client.get("/api/resume/analysis", headers=auth_headers(token))
    assert response.status_code == 404


def test_analysis_returns_own_resume():
    register_user(email="owner@example.com")
    token = login_user(email="owner@example.com").json()["access_token"]

    client.post(
        "/api/resume/upload",
        files={"file": ("resume.docx", make_docx(), DOCX_CT)},
        headers=upload_headers(token),
    )

    response = client.get("/api/resume/analysis", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "resume.docx"
    skill_names = [skill["name"] for skill in data["skills"]]
    assert "Python" in skill_names


def test_user_cannot_see_another_users_resume():
    register_user(email="alice@example.com")
    alice_token = login_user(email="alice@example.com").json()["access_token"]
    register_user(email="bob@example.com")
    bob_token = login_user(email="bob@example.com").json()["access_token"]

    client.post(
        "/api/resume/upload",
        files={"file": ("alice.docx", make_docx(), DOCX_CT)},
        headers=upload_headers(alice_token),
    )

    bob_response = client.get("/api/resume/analysis", headers=auth_headers(bob_token))
    assert bob_response.status_code == 404


def test_second_upload_replaces_child_records():
    user_id = register_user(email="repeat@example.com").json()["id"]
    token = login_user(email="repeat@example.com").json()["access_token"]

    v1 = """Skills
Python, SQL
"""
    v2 = """Skills
Java, Go
"""
    client.post(
        "/api/resume/upload",
        files={"file": ("v1.docx", make_docx(v1), DOCX_CT)},
        headers=upload_headers(token),
    )
    client.post(
        "/api/resume/upload",
        files={"file": ("v2.docx", make_docx(v2), DOCX_CT)},
        headers=upload_headers(token),
    )

    response = client.get("/api/resume/analysis", headers=auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    skill_names = [skill["name"] for skill in data["skills"]]
    assert skill_names == ["Java", "Go"]

    db = TestingSessionLocal()
    try:
        resumes = (
            db.query(Resume).filter(Resume.user_id == user_id).count()
        )
        skills = (
            db.query(Skill)
            .join(Resume, Skill.resume_id == Resume.id)
            .filter(Resume.user_id == user_id)
            .count()
        )
    finally:
        db.close()
    assert resumes == 1
    assert skills == 2


def test_upload_pdf_with_ai_disabled_returns_parsed(monkeypatch):
    """Uploading a PDF must succeed when AI_PROVIDER is empty, and the resume
    must be stored as a deterministic parse (never a failure)."""
    monkeypatch.setattr(settings, "AI_PROVIDER", "")
    register_user(email="nodeai@example.com")
    token = login_user(email="nodeai@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        files={"file": ("resume.pdf", make_pdf(), "application/pdf")},
        headers=upload_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "parsed"
    assert data["file_name"] == "resume.pdf"
    # Deterministic-only path never invents experience.
    assert data["total_experience_years"] is None


def test_upload_with_nonfile_part_rejected():
    """A multipart part carrying a plain string instead of a real file must be
    rejected cleanly. Guards against clients that append an object to the
    FormData (browsers coerce it to "[object Object]"), which is how an
    earlier frontend bug used to trigger a second phantom upload."""
    register_user(email="formstr@example.com")
    token = login_user(email="formstr@example.com").json()["access_token"]

    response = client.post(
        "/api/resume/upload",
        data={"file": str({"id": 1, "file_name": "resume.pdf"})},
        headers=upload_headers(token),
    )
    assert response.status_code == 422


def test_deterministic_extraction():
    result = parse_resume(make_docx(), "resume.docx", DOCX_CT)

    assert "Python" in result["skills"]
    assert "SQL" in result["skills"]
    assert "Power BI" in result["skills"]

    education = result["education"]
    assert any(entry["institution"] == "University of Ottawa" for entry in education)
    assert any(entry["degree"] == "Bachelor of Science" for entry in education)

    experience = result["experience"]
    assert any(
        entry["company"] == "Acme Inc." and entry["title"] == "Data Analyst"
        for entry in experience
    )

    certifications = result["certifications"]
    assert any(
        entry["name"] == "AWS Certified Solutions Architect"
        and entry["issuer"] == "Amazon Web Services"
        for entry in certifications
    )


def test_deterministic_skills_one_per_line():
    """One skill per line (the dominant resume layout) must yield each skill
    as its own item — never merged into a single blob."""
    text = """Technical Skills
Python
SQL
Pandas
NumPy
Power BI
Excel
"""
    result = parse_resume(make_docx(text), "skills.docx", DOCX_CT)
    assert result["skills"] == ["Python", "SQL", "Pandas", "NumPy", "Power BI", "Excel"]


def test_deterministic_skills_bullets_and_comma_mix():
    text = """Skills
\u2022 Python, SQL
\u2022 Pandas
\u2022 Power BI | Tableau
"""
    result = parse_resume(make_docx(text), "skills.docx", DOCX_CT)
    assert result["skills"] == ["Python", "SQL", "Pandas", "Power BI", "Tableau"]


def test_deterministic_skills_case_dedupe_keeps_versions():
    """Case variants collapse to one skill (display spelling = first seen), but
    versioned variants like "Python 3" stay distinct skills — the normalizer is
    deliberately conservative and never merges unrelated concepts."""
    text = """Skills
Python
python
PYTHON
Python 3
Pandas
"""
    result = parse_resume(make_docx(text), "skills.docx", DOCX_CT)
    assert result["skills"] == ["Python", "Python 3", "Pandas"]


def test_deterministic_qualification_formats():
    """Short-form degrees and pre-university qualifications are recognized and
    preserved (degree + field where the layout permits), even when the line
    carries no institution name."""
    text = """Education
Bachelor of Science in Economics and Data Science
BS Economics and Data Science
Bachelor of Science in Computer Science
BSc Economics
Master of Business Administration
MBA
MS Data Science
Intermediate
A Levels
"""
    result = parse_resume(make_docx(text), "quals.docx", DOCX_CT)
    by_degree = {(e["degree"], e["field_of_study"]) for e in result["education"]}
    assert ("Bachelor of Science", "Economics and Data Science") in by_degree
    assert ("BS", "Economics and Data Science") in by_degree
    assert ("Bachelor of Science", "Computer Science") in by_degree
    assert ("BSc", "Economics") in by_degree
    assert ("Master of Business Administration", None) in by_degree
    assert ("MBA", None) in by_degree
    assert ("MS", "Data Science") in by_degree
    assert ("Intermediate", None) in by_degree
    assert ("A Levels", None) in by_degree


def test_deterministic_qualification_matches_job_requirement_shape():
    """A short-form qualification parses into matchable tokens; the exact-match
    engine (no synonyms) scores 100% when the job lists the same normalized
    token — e.g. an MBA vs a job requiring an MBA."""
    from app.services.matching_engine import qualification_match

    text = """Education
MBA
"""
    result = parse_resume(make_docx(text), "quals.docx", DOCX_CT)
    candidate = ["MBA"]
    assert qualification_match(candidate, ["MBA"]).percentage == 100.0
    # The parsed entry keeps the meaningful short-form degree intact.
    assert result["education"][0]["degree"] == "MBA"

    text2 = """Education
BS Economics and Data Science
"""
    result2 = parse_resume(make_docx(text2), "quals.docx", DOCX_CT)
    entry = result2["education"][0]
    # build_candidate_profile emits the combined "<degree> in <field>" token.
    candidate_profile = ["BS", "Economics and Data Science", "BS in Economics and Data Science"]
    assert entry["degree"] == "BS"
    assert entry["field_of_study"] == "Economics and Data Science"
    assert qualification_match(candidate_profile, ["BS in Economics and Data Science"]).percentage == 100.0


def test_deterministic_upload_with_ai_disabled_keeps_line_skills(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "")
    register_user(email="lineskills@example.com")
    token = login_user(email="lineskills@example.com").json()["access_token"]

    text = """Skills
Python
SQL
Power BI
"""
    response = client.post(
        "/api/resume/upload",
        files={"file": ("lineskills.docx", make_docx(text), DOCX_CT)},
        headers=upload_headers(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["analysis_status"] == "parsed"
    assert [s["name"] for s in data["skills"]] == ["Python", "SQL", "Power BI"]