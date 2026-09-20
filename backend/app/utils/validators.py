"""Backend-side validation helpers."""

ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_APPLICATION_STATUSES = {"applied", "in_review", "interview", "offer", "rejected"}

RESUME_CONTENT_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}


def allowed_resume_extension(filename: str) -> str | None:
    """Return the lowercase extension if `filename` is a supported resume type."""
    lowered = filename.lower()
    for ext in ALLOWED_RESUME_EXTENSIONS:
        if lowered.endswith(ext):
            return ext
    return None


def matches_resume_content_type(filename: str, content_type: str | None) -> bool:
    """Return whether the given MIME type is compatible with `filename`.

    Unknown/generic content types (e.g. application/octet-stream) are accepted
    so browsers that do not set a specific type still work; a *known* type that
    conflicts with the extension is rejected.
    """
    if not content_type:
        return True
    content_type = content_type.lower()
    if content_type in {"application/octet-stream", "binary/octet-stream"}:
        return True
    ext = allowed_resume_extension(filename)
    if ext is None:
        return False
    return content_type in RESUME_CONTENT_TYPES[ext]


def is_valid_email(email: str) -> bool:
    import re
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email or ""))


def is_valid_application_status(status: str) -> bool:
    return status in ALLOWED_APPLICATION_STATUSES
