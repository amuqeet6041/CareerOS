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