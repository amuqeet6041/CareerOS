"""
Resume persistence service.

Owns how a parsed resume is saved for an authenticated user: a user has at
most one Resume record, and re-uploading replaces the previous children
(skills, education, experience, certifications) rather than appending
duplicates.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.resume import Certification, Education, Experience, Resume, Skill


def get_resume_for_user(db: Session, user_id: int) -> Resume | None:
    return db.query(Resume).filter(Resume.user_id == user_id).first()


def save_resume(
    db: Session,
    user_id: int,
    file_name: str,
    parsed: dict,
) -> Resume:
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

    db.query(Skill).filter(Skill.resume_id == resume.id).delete(
        synchronize_session=False
    )
    db.query(Education).filter(Education.resume_id == resume.id).delete(
        synchronize_session=False
    )
    db.query(Experience).filter(Experience.resume_id == resume.id).delete(
        synchronize_session=False
    )
    db.query(Certification).filter(Certification.resume_id == resume.id).delete(
        synchronize_session=False
    )

    for skill in parsed.get("skills", []):
        db.add(Skill(resume_id=resume.id, name=skill))

    for item in parsed.get("education", []):
        db.add(
            Education(
                resume_id=resume.id,
                institution=item["institution"],
                degree=item.get("degree"),
                field_of_study=item.get("field_of_study"),
            )
        )

    for item in parsed.get("experience", []):
        if not item.get("company"):
            continue
        db.add(
            Experience(
                resume_id=resume.id,
                company=item["company"],
                title=item.get("title"),
                description=item.get("description"),
            )
        )

    for item in parsed.get("certifications", []):
        db.add(
            Certification(
                resume_id=resume.id,
                name=item["name"],
                issuer=item.get("issuer"),
            )
        )

    db.commit()
    db.refresh(resume)
    return resume