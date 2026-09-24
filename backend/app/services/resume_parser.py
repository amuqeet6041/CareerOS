"""
Resume parsing service.

Extracts raw text from uploaded resume files (PDF/DOCX) and applies
deterministic, conservative heuristics to pull structured information
(skills, education, experience, certifications).

This phase intentionally does NOT use an LLM: AI-powered extraction belongs
to Phase 4. The parser never invents values; fields that cannot be resolved
confidently are left absent.
"""

import io
import re
from typing import Any

from app.utils.validators import allowed_resume_extension, matches_resume_content_type


class ResumeParseError(Exception):
    """Base error for resume parsing failures."""


class UnsupportedResumeTypeError(ResumeParseError):
    """Raised when the uploaded file is not a supported resume type."""


class MalformedResumeError(ResumeParseError):
    """Raised when a file cannot be read as its declared type."""


class EmptyResumeError(ResumeParseError):
    """Raised when a document yields no extractable text."""


_SECTION_HEADINGS: dict[str, set[str]] = {
    "skills": {
        "skills",
        "skill set",
        "technical skills",
        "core competencies",
        "competencies",
        "technologies",
        "technical stack",
        "tools & technologies",
        "tools and technologies",
        "it skills",
        "computer skills",
    },
    "education": {
        "education",
        "academic background",
        "academics",
        "educational background",
        "qualifications",
    },
    "experience": {
        "experience",
        "work experience",
        "professional experience",
        "employment",
        "work history",
        "career history",
        "relevant experience",
        "professional background",
        "employment history",
    },
    "certifications": {
        "certifications",
        "certification",
        "certificates",
        "licenses",
        "licences",
        "professional certifications",
        "professional certificates",
    },
}

_BULLET_PREFIX_RE = re.compile(
    r"^\s*(?:[•▪●◦‣❖]\s*|\*\s+|\-\s+|–\s+|—\s+|\d{1,2}[.)]\s*)"
)
_DEGREE_RE = re.compile(
    r"(\b(?:Bachelor'?s?|Master'?s?|Associate'?s?)\b"
    r"|\b(?:Bachelor|Master|Doctor)\s+of\s+(?:Science|Arts|Business\s+Administration|Engineering|Education|Laws|Philosophy|Fine\s+Arts)\b"
    r"|\b(?:B\.?Sc|B\.?A|B\.?S|B\.?Eng|B\.?Tech|BBA|BCom|MBA|M\.?A|M\.?Sc|M\.?S|M\.?Eng|M\.?Tech|MPhil|PhD|Ph\.?D|Doctorate|Diploma|LLB|LL\.?B|JD|MD)\b"
    r"|\b(?:Intermediate|Intermediate\s+Examination|A[- ]Levels?|O[- ]Levels?)\b)",
    re.IGNORECASE,
)
# Short degree abbreviations only (used to split "BSc Economics" into
# degree "BSc" + field "Economics"). Wordy forms like "Bachelor of Science"
# are handled by the " in " branch of _split_degree_field instead.
_DEGREE_ABBREV_RE = re.compile(
    r"^(?:B\.?Sc|B\.?A|B\.?S|B\.?Eng|B\.?Tech|BBA|BCom|MBA|M\.?A|M\.?Sc|M\.?S|M\.?Eng|M\.?Tech|MPhil|PhD|Ph\.?D|LLB|LL\.?B|JD|MD)(?=[\s,;:\u2013\u2014|.]|$)",
    re.IGNORECASE,
)
_INSTITUTION_RE = re.compile(
    r"\b(?:University|College|Institut|Institute|Academy|School|Polytechnic|Universidad|Hochschule)\b",
    re.IGNORECASE,
)
_DATE_ONLY_RE = re.compile(
    r"\b(?:19|20)\d{2}\b(?:[\s/-]*–?[\s/-]*(?:present|current|now|(?:19|20)\d{2}))?"
)
_EXPERIENCE_AT_RE = re.compile(r"^(.{1,80}?)\s+(?:at|@)\s+(.{1,100})$", re.IGNORECASE)
_EXPERIENCE_SEP_RE = re.compile(r"^(.{1,80}?)\s*(?:[–—]|│|\|)\s*(.{1,100})$")
_COMPANY_KEYWORDS_RE = re.compile(
    r"\b(?:Inc|Inc\.|Corp|Corporation|LLC|Limited|Ltd|Company|Co\.|Co|GmbH|AG|Pty|Group|Technologies?|Systems|Labs|Laboratories?|Consulting|Solutions|Services|Industries|University|College|Hospital|Agency|Startup|Studio|Global|Digital|Analytics|Software|Banks?)\b",
    re.IGNORECASE,
)
_EXPERIENCE_COMMA_RE = re.compile(r"^(.{1,80}?),\s*(.{1,100})$")
_CERT_SEPARATORS = (" – ", " — ", " | ", " · ", " - ", " issued by ", " by ")
_SKILL_SPLIT_RE = re.compile(r"[,;]|\s+•\s*|\s+\*\s*|\s*\|\s*|\u2022|\u25cf")
_SKILL_COLON_RE = re.compile(r"^[A-Za-z][A-Za-zÆØÅ&/+.\- ]{0,20}:\s*(.+)$")
_SKILL_STOP_WORDS = {
    "and",
    "or",
    "etc",
    "etc.",
    "including",
    "include",
    "proficient",
    "knowledge",
    "experience",
    "ability",
    "skills",
    "skill",
}
_TRAILING_PAREN_YEAR_RE = re.compile(r"\s*\(\s*(?:19|20)\d{2}\s*\)\s*$")
_CREDENTIAL_ID_RE = re.compile(r"\s*(?:ID|id)[:#]\s*[\w\-/]+\s*$")
_HASH_ID_RE = re.compile(r"\s*#[\w\-/]+\s*$")


def _strip_bullet(line: str) -> str:
    cleaned = _BULLET_PREFIX_RE.sub("", line)
    if cleaned != line:
        return cleaned.strip()
    return line.strip()


def _heading_for(line: str) -> str | None:
    key = line.lower().rstrip(".:").strip()
    if not key or len(key) > 45:
        return None
    for section, aliases in _SECTION_HEADINGS.items():
        if key in aliases:
            return section
    return None


def _split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {
        "skills": [],
        "education": [],
        "experience": [],
        "certifications": [],
    }
    current: str | None = None
    for raw in lines:
        cleaned = _strip_bullet(raw)
        heading = _heading_for(cleaned)
        if cleaned == "":
            if current:
                sections[current].append("")
            continue
        if heading:
            current = heading
            continue
        if current:
            sections[current].append(cleaned)
    return sections


def _clean_skill_item(item: str) -> str:
    cleaned = item.strip().strip(".").strip(":")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def parse_skills(section_lines: list[str]) -> list[str]:
    seen: set[str] = set()
    skills: list[str] = []

    def add_token(item: str) -> None:
        cleaned = _clean_skill_item(item)
        colon_match = _SKILL_COLON_RE.match(cleaned)
        if colon_match:
            cleaned = _clean_skill_item(colon_match.group(1))
        if not cleaned or cleaned.lower() in _SKILL_STOP_WORDS:
            return
        if len(cleaned) < 2 or len(cleaned) > 60:
            return
        key = cleaned.lower()
        if key in seen:
            return
        seen.add(key)
        skills.append(cleaned)

    for raw in section_lines:
        line = _strip_bullet(raw)
        if not line:
            continue
        colon_match = _SKILL_COLON_RE.match(line)
        if colon_match:
            line = colon_match.group(1)
        parts = _SKILL_SPLIT_RE.split(line)
        if len(parts) == 1:
            # No in-line delimiter (comma, bullet, pipe): the whole line is one
            # skill item ("Data Analysis", "Python Programming"). One skill per
            # line is the dominant resume layout, so a line boundary must never
            # merge separate skills into one ("Python SQL Pandas").
            parts = [line]
        for part in parts:
            add_token(part)
    return skills


def _split_degree_field(line: str) -> tuple[str | None, str | None]:
    parts = re.split(r"[,;–—|]|\.\s+", line)
    degree: str | None = None
    field: str | None = None
    for part in parts:
        segment = part.strip().strip(".")
        if not segment:
            continue
        lower = segment.lower()
        if " in " in lower and _DEGREE_RE.search(segment):
            degree_text, _, field_text = segment.partition(" in ")
            if degree_text.strip() and field_text.strip():
                degree = degree_text.strip()
                field = field_text.strip()
        elif degree is None and _DEGREE_ABBREV_RE.match(segment):
            # "BS Economics and Data Science" -> degree "BS", field
            # "Economics and Data Science" so the meaningful qualification is
            # preserved and matchable instead of one opaque blob.
            degree = _DEGREE_ABBREV_RE.match(segment).group(0)
            field = segment[len(degree):].strip() or None
        elif degree is None and _DEGREE_RE.search(segment):
            degree = segment
    return degree, field


def _extract_institution(line: str) -> str | None:
    parts = re.split(r"[,;–—|]|\.\s+", line)
    for part in parts:
        segment = part.strip().strip(".")
        if _INSTITUTION_RE.search(segment):
            cleaned = _DATE_ONLY_RE.sub("", segment).strip(" ,;–—|–.:")
            return cleaned or None
    return None


def parse_education(section_lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    degree: str | None = None
    field: str | None = None
    institution: str | None = None

    def flush() -> None:
        nonlocal degree, field, institution
        # A degree alone (no institution line) is still a meaningful
        # qualification — never drop it ("MBA", "Intermediate", "BS Economics").
        if degree or institution:
            entries.append(
                {
                    "institution": institution,
                    "degree": degree,
                    "field_of_study": field,
                    # Deterministic parser never guesses dates; these keys are
                    # present so AI and fallback share the canonical shape.
                    "start_year": None,
                    "end_year": None,
                }
            )
        degree = field = institution = None

    for raw in section_lines:
        line = _strip_bullet(raw)
        date_only = _DATE_ONLY_RE.fullmatch(line.strip()) is not None
        if line == "" or date_only:
            flush()
            continue
        has_degree = _DEGREE_RE.search(line) is not None
        has_institution = _INSTITUTION_RE.search(line) is not None
        if not has_degree and not has_institution:
            continue
        flush()
        if has_degree:
            degree, field = _split_degree_field(line)
        if has_institution:
            institution = _extract_institution(line)
    flush()
    return entries


def _match_experience_entry(line: str) -> dict[str, str] | None:
    at_match = _EXPERIENCE_AT_RE.match(line)
    if at_match:
        return {"title": at_match.group(1).strip(), "company": at_match.group(2).strip()}
    sep_match = _EXPERIENCE_SEP_RE.match(line)
    if sep_match:
        return {
            "title": sep_match.group(1).strip(),
            "company": sep_match.group(2).strip(),
        }
    comma_match = _EXPERIENCE_COMMA_RE.match(line)
    if comma_match and _COMPANY_KEYWORDS_RE.search(comma_match.group(2)):
        return {
            "title": comma_match.group(1).strip(),
            "company": comma_match.group(2).strip(),
        }
    return None


def parse_experience(section_lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal current
        if current:
            entries.append(current)
        current = None

    for raw in section_lines:
        line = _strip_bullet(raw)
        if line == "":
            flush()
            continue
        entry = _match_experience_entry(line)
        if entry:
            flush()
            current = {
                "title": entry["title"],
                "company": entry["company"],
                "description": None,
                "_desc_lines": [],
            }
            continue
        if _DATE_ONLY_RE.search(line) and len(_DATE_ONLY_RE.sub("", line).strip()) < 3:
            flush()
            continue
        if current is not None and not _heading_for(line):
            current["_desc_lines"].append(line)

    flush()
    result: list[dict[str, Any]] = []
    for entry in entries:
        description_lines = entry["_desc_lines"]
        entry_copy = {
            "company": entry["company"],
            "title": entry["title"],
            "description": " ".join(description_lines) if description_lines else None,
            # Canonical shape parity with AI output; deterministic parser never
            # guesses dates/roles, so these stay absent (null).
            "location": None,
            "start_date": None,
            "end_date": None,
            "currently_employed": False,
        }
        result.append(entry_copy)
    return result


def _looks_like_issuer(text: str) -> bool:
    text = text.strip()
    if not text or len(text) > 80:
        return False
    if _DATE_ONLY_RE.fullmatch(text):
        return False
    if _DATE_ONLY_RE.search(text) and len(_DATE_ONLY_RE.sub("", text).strip()) < 3:
        return False
    return bool(re.search(r"[A-Za-zÁ-ÿ]{2}", text))


def _clean_certificate_name(name: str) -> str:
    cleaned = name.strip()
    cleaned = _TRAILING_PAREN_YEAR_RE.sub("", cleaned).strip()
    cleaned = _CREDENTIAL_ID_RE.sub("", cleaned).strip()
    cleaned = _HASH_ID_RE.sub("", cleaned).strip()
    cleaned = _DATE_ONLY_RE.sub("", cleaned).rstrip(" ,;–—|").strip()
    return cleaned


def parse_certifications(section_lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    for raw in section_lines:
        line = _strip_bullet(raw)
        if not line:
            continue
        if _DATE_ONLY_RE.fullmatch(line):
            continue
        name = line
        issuer: str | None = None
        for separator in _CERT_SEPARATORS:
            if separator in line:
                left, right = line.split(separator, 1)
                if _looks_like_issuer(right):
                    name, issuer = left.strip(), right.strip()
                break
        cleaned_name = _clean_certificate_name(name)
        if not cleaned_name:
            continue
        entries.append(
            {
                "name": cleaned_name,
                "issuer": issuer,
                # Canonical shape parity with AI output (deterministic parser
                # never guesses issue/expiry years).
                "issue_year": None,
                "expiry_year": None,
            }
        )
    return entries


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ").replace("\xa0", " ")
    text = text.replace("\u200b", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import pymupdf
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise ResumeParseError("PDF support is not available on this server.") from exc

    try:
        document = pymupdf.open(stream=file_bytes, filetype="pdf")
    except pymupdf.EmptyFileError as exc:
        raise EmptyResumeError("The uploaded PDF is empty.") from exc
    except (pymupdf.FileDataError, ValueError, RuntimeError) as exc:
        raise MalformedResumeError(
            "The PDF could not be read. It may be corrupted or not a valid PDF file."
        ) from exc

    try:
        if document.needs_pass and not document.authenticate(""):
            raise MalformedResumeError(
                "The PDF is password-protected and cannot be read."
            )
        pages = []
        for page in document:
            text = page.get_text("text")
            if text:
                pages.append(text)
    finally:
        document.close()
    return "\n".join(pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        from docx import Document
        from docx.oxml.ns import qn
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError as exc:  # pragma: no cover - dependency is pinned
        raise ResumeParseError("DOCX support is not available on this server.") from exc

    try:
        document = Document(io.BytesIO(file_bytes))
    except Exception as exc:
        raise MalformedResumeError(
            "The document could not be read. It may be corrupted or not a valid DOCX file."
        ) from exc

    lines: list[str] = []
    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            text = Paragraph(child, document).text
            if text.strip():
                lines.append(text.strip())
        elif child.tag == qn("w:tbl"):
            for row in Table(child, document).rows:
                cells = [cell.text.strip() for cell in row.cells]
                row_text = " | ".join(cell for cell in cells if cell)
                if row_text:
                    lines.append(row_text)
    return "\n".join(lines)


def parse_resume(
    file_bytes: bytes,
    filename: str | None,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Parse an uploaded resume and return its structured contents."""
    name = filename or ""
    ext = allowed_resume_extension(name)
    if ext is None or not matches_resume_content_type(name, content_type):
        raise UnsupportedResumeTypeError(
            "Unsupported file type. Please upload a PDF or DOCX resume."
        )

    if ext == ".pdf":
        if not file_bytes[:5] == b"%PDF-":
            raise MalformedResumeError("The file does not appear to be a PDF.")
        raw_text = extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        if len(file_bytes) < 4 or file_bytes[:2] != b"PK":
            raise MalformedResumeError("The file does not appear to be a DOCX archive.")
        raw_text = extract_text_from_docx(file_bytes)
    else:  # pragma: no cover - extension guard above
        raise UnsupportedResumeTypeError(
            "Unsupported file type. Please upload a PDF or DOCX resume."
        )

    normalized = normalize_text(raw_text)
    if not normalized.strip():
        raise EmptyResumeError("The document contains no extractable text.")

    lines = normalized.split("\n")
    sections = _split_sections(lines)

    return {
        "raw_text": normalized,
        "skills": parse_skills(sections["skills"]),
        "education": parse_education(sections["education"]),
        "experience": parse_experience(sections["experience"]),
        "certifications": parse_certifications(sections["certifications"]),
    }