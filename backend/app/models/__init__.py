# Import every model so that `Base.metadata` (used by Alembic and create_all
# in tests) is fully populated whenever `app.models` is imported.
from app.models.user import User
from app.models.resume import Resume, Skill, Education, Experience, Certification
from app.models.job import Job, JobSkill, JobQualification
from app.models.application import SavedJob, Application, UserPreference
from app.models.profile import UserProfile

__all__ = [
    "User",
    "Resume",
    "Skill",
    "Education",
    "Experience",
    "Certification",
    "Job",
    "JobSkill",
    "JobQualification",
    "SavedJob",
    "Application",
    "UserPreference",
    "UserProfile",
]