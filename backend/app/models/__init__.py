# Import every model so that `Base.metadata` (used by Alembic and create_all
# in tests) is fully populated whenever `app.models` is imported.
from app.models.user import User
from app.models.resume import Resume, Skill, Education, Experience, Certification
from app.models.job import Job
from app.models.application import SavedJob, Application, UserPreference

__all__ = [
    "User",
    "Resume",
    "Skill",
    "Education",
    "Experience",
    "Certification",
    "Job",
    "SavedJob",
    "Application",
    "UserPreference",
]