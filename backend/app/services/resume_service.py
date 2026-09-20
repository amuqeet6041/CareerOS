"""
Resume persistence service.

Owns how a parsed resume is saved for an authenticated user: a user has at
most one Resume record, and re-uploading replaces the previous children
(skills, education, experience, certifications) rather than appending
duplicates.

AI-structured data (skills with AI spelling, dated experience, etc.) is
persisted through the same children, plus the deterministic
``total_experience_years`` and the ``analysis_status`` field.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.resume import Certification, Education, Experience, Resume, Skill


def get_resume_for_user(db: Session, user_id: int) -> Resume | None:
    return db.query(Resume).filter(Resume.user_id == user_id).first()


def _rebuild_children(db: Session, resume: Resume, source: dict) -> None:
    """Replace all child rows from a persistence-shaped source dict."""
    db.query(Skill).filter(Skill.resume_id == resume.id).delete(synchronize_session=False)
    db.query(Education).filter(Education.resume_id == resume.id).delete(synchronize_session=False)
    db.query(Experience).filter(Experience.resume_id == resume.id).delete(synchronize_session=False)
    db.query(Certification).filter(Certification.resume_id == resume.id).delete(synchronize_session=False)

    for skill in source.get("skills", []):
        if skill:
            db.add(Skill(resume_id=resume.id, name=skill))

    for item in source.get("education", []):
        db.add(
            Education(
                resume_id=resume.id,
                institution=item.get("institution"),
                degree=item.get("degree"),
                field_of_study=item.get("field_of_study"),
                start_year=item.get("start_year"),
                end_year=item.get("end_year"),
            )
        )

    for item in source.get("experience", []):
        if not item.get("company"):
            continue
        db.add(
            Experience(
                resume_id=resume.id,
                company=item["company"],
                title=item.get("title"),
                description=item.get("description"),
                location=item.get("location"),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
                currently_employed=bool(item.get("currently_employed")),
            )
        )

    for item in source.get("certifications", []):
        db.add(
            Certification(
                resume_id=resume.id,
                name=item["name"],
                issuer=item.get("issuer"),
                issue_year=item.get("issue_year"),
                expiry_year=item.get("expiry_year"),
            )
        )


def save_resume(
    db: Session,
    user_id: int,
    file_name: str,
    parsed: dict,
    *,
    analysis_status: str = "parsed",
    structured: dict | None = None,
) -> Resume:
    """Persist a parsed resume, optionally enriched with AI-structured data.

    ``structured`` is the validated persistence shape from the AI pipeline;
    when provided it is persisted as-is (including ``total_experience_years``).
    Otherwise the deterministic parse is persisted and experience is left
    unknown (``None``), never guessed as zero.
    """
    resume = get_resume_for_user(db, user_id)
    if resume is None:
        resume = Resume(
            user_id=user_id,
            file_name=file_name,
            raw_text=parsed["raw_text"],
        )
        db.add(resume)
    else:
        resume.file_name = file_name
        resume.raw_text = parsed["raw_text"]
        resume.uploaded_at = datetime.utcnow()

    db.flush()

    if structured is not None:
        _rebuild_children(db, resume, structured)
        resume.total_experience_years = structured.get("total_experience_years")
    else:
        _rebuild_children(db, resume, parsed)
        resume.total_experience_years = None
    resume.analysis_status = analysis_status

    db.commit()
    db.refresh(resume)
    return resume


def update_resume_analysis(
    db: Session,
    resume: Resume,
    *,
    structured: dict | None,
    analysis_status: str,
) -> Resume:
    """Replace a stored resume's structure with a new AI analysis.

    When ``structured`` is None (AI re-analysis failed), the existing children
    and total experience are preserved; only the status is updated so the
    caller's data is never destroyed by an AI failure.
    """
    if structured is not None:
        _rebuild_children(db, resume, structured)
        resume.total_experience_years = structured.get("total_experience_years")
    resume.analysis_status = analysis_status

    db.commit()
    db.refresh(resume)
    return resume