"""Demo job provider.

Serves a fixed, realistic set of jobs using fictitious company names so the
job pipeline can be exercised end-to-end without an external API key. All
application links point to clearly-marked demo pages -- none of these jobs
are real postings and the companies are invented for demonstration purposes.
"""

from datetime import datetime

from app.services.providers.base import JobProvider, ProviderJob

# Fixed reference "today" used to keep the demo dataset deterministic. Jobs
# posted through the demo provider always have an expiry in the future.
_POSTED_AT = datetime(2026, 8, 1)
_EXPIRES_AT = datetime(2027, 1, 1)

_DEMO_JOBS: list[dict] = [
    {
        "external_id": "demo-01",
        "title": "Junior Data Analyst",
        "company": "DataWorks Pakistan",
        "location": "Lahore, Pakistan",
        "work_mode": "remote",
        "employment_type": "full-time",
        "salary_min": 600_000,
        "salary_max": 800_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-01",
        "minimum_experience_years": 0,
        "maximum_experience_years": 2,
        "description": (
            "Support the analytics team with reporting, data cleaning, and "
            "dashboard maintenance. Ideal for recent graduates eager to grow."
        ),
        "required_skills": ["Excel", "SQL", "Data Visualization"],
        "qualifications": ["Bachelor's in Data Science", "Bachelor's in Statistics"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-02",
        "title": "Data Analyst",
        "company": "Insight Analytics",
        "location": "Karachi, Pakistan",
        "work_mode": "hybrid",
        "employment_type": "full-time",
        "salary_min": 1_000_000,
        "salary_max": 1_400_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-02",
        "minimum_experience_years": 2,
        "maximum_experience_years": 5,
        "description": (
            "Build analytical insights for client engagements, own end-to-end "
            "data pipelines, and present findings to stakeholders."
        ),
        "required_skills": ["SQL", "Python", "Tableau"],
        "qualifications": ["Bachelor's in Computer Science", "Bachelor's in Business Analytics"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-03",
        "title": "Business Intelligence Intern",
        "company": "Market Intelligence Group",
        "location": "Islamabad, Pakistan",
        "work_mode": "onsite",
        "employment_type": "internship",
        "salary_min": 40_000,
        "salary_max": 50_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-03",
        "minimum_experience_years": 0,
        "maximum_experience_years": 0,
        "description": (
            "Six-month internship supporting dashboard builds and ad-hoc "
            "analyses. Mentorship and a pathway to a full-time offer."
        ),
        "required_skills": ["SQL", "Microsoft Excel"],
        "qualifications": ["Enrolled in an undergraduate program"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-04",
        "title": "Python Developer",
        "company": "TechNova",
        "location": "Remote",
        "work_mode": "remote",
        "employment_type": "contract",
        "salary_min": 3_000,
        "salary_max": 4_500,
        "currency": "USD",
        "application_url": "https://careeros-demo.example/apply/demo-04",
        "minimum_experience_years": 3,
        "maximum_experience_years": 7,
        "description": (
            "Develop and maintain Python backend services and integrations for "
            "a remote-first product team. Monthly contract with renewal."
        ),
        "required_skills": ["Python", "Django", "REST APIs"],
        "qualifications": ["Bachelor's in Computer Science"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-05",
        "title": "Business Analyst",
        "company": "DataWorks Pakistan",
        "location": "Lahore, Pakistan",
        "work_mode": "hybrid",
        "employment_type": "full-time",
        "salary_min": 1_100_000,
        "salary_max": 1_500_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-05",
        "minimum_experience_years": 2,
        "maximum_experience_years": 5,
        "description": (
            "Translate business requirements into data models and reporting "
            "frameworks for enterprise clients."
        ),
        "required_skills": ["Excel", "SQL", "Process Mapping"],
        "qualifications": ["Bachelor's in Business Administration"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-06",
        "title": "Junior Software Engineer",
        "company": "TechNova",
        "location": "Remote",
        "work_mode": "remote",
        "employment_type": "full-time",
        "salary_min": 1_500,
        "salary_max": 2_500,
        "currency": "USD",
        "application_url": "https://careeros-demo.example/apply/demo-06",
        "minimum_experience_years": 1,
        "maximum_experience_years": 3,
        "description": (
            "Join a small squad shipping web applications. Strong mentoring "
            "culture and modern stack."
        ),
        "required_skills": ["JavaScript", "React", "Python"],
        "qualifications": ["Bachelor's in Computer Science", "Bachelor's in Software Engineering"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-07",
        "title": "Data Science Intern",
        "company": "Insight Analytics",
        "location": "Remote",
        "work_mode": "remote",
        "employment_type": "internship",
        "salary_min": 400,
        "salary_max": 600,
        "currency": "USD",
        "application_url": "https://careeros-demo.example/apply/demo-07",
        "minimum_experience_years": 0,
        "maximum_experience_years": 0,
        "description": (
            "Work alongside data scientists on forecasting and experiment "
            "analysis. Remote internship with a strong probability of extension."
        ),
        "required_skills": ["Python", "Pandas", "Machine Learning Fundamentals"],
        "qualifications": ["Enrolled in a graduate program", "Enrolled in a data science bootcamp"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-08",
        "title": "Financial Data Analyst",
        "company": "Market Intelligence Group",
        "location": "Karachi, Pakistan",
        "work_mode": "onsite",
        "employment_type": "full-time",
        "salary_min": 900_000,
        "salary_max": 1_300_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-08",
        "minimum_experience_years": 2,
        "maximum_experience_years": 4,
        "description": (
            "Own financial reporting models and market research datasets used "
            "in investment decisions."
        ),
        "required_skills": ["Excel", "Financial Modeling", "SQL"],
        "qualifications": ["Bachelor's in Finance", "Bachelor's in Economics"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-09",
        "title": "BI Analyst",
        "company": "DataWorks Pakistan",
        "location": "Lahore, Pakistan",
        "work_mode": "hybrid",
        "employment_type": "full-time",
        "salary_min": 1_100_000,
        "salary_max": 1_500_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-09",
        "minimum_experience_years": 3,
        "maximum_experience_years": 6,
        "description": (
            "Design and maintain self-serve BI dashboards and data models that "
            "power company-wide decisions."
        ),
        "required_skills": ["Power BI", "SQL", "Data Modeling"],
        "qualifications": ["Bachelor's in Computer Science", "Bachelor's in Information Systems"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
    {
        "external_id": "demo-10",
        "title": "Research Analyst",
        "company": "Insight Analytics",
        "location": "Islamabad, Pakistan",
        "work_mode": "hybrid",
        "employment_type": "full-time",
        "salary_min": 700_000,
        "salary_max": 950_000,
        "currency": "PKR",
        "application_url": "https://careeros-demo.example/apply/demo-10",
        "minimum_experience_years": 1,
        "maximum_experience_years": 3,
        "description": (
            "Conduct secondary research, summarize findings, and prepare "
            "reports for consulting-style client deliverables."
        ),
        "required_skills": ["Research", "Excel", "Report Writing"],
        "qualifications": ["Bachelor's in Economics", "Bachelor's in Social Sciences"],
        "posted_at": _POSTED_AT,
        "expires_at": _EXPIRES_AT,
    },
]


class DemoJobProvider(JobProvider):
    """Provider that serves the built-in fictional demo job set."""

    name = "demo"

    def fetch_jobs(self) -> list[ProviderJob]:
        return [self.fetch_job(item["external_id"]) for item in _DEMO_JOBS]

    def fetch_job(self, external_id: str) -> ProviderJob | None:
        for item in _DEMO_JOBS:
            if item["external_id"] == external_id:
                return ProviderJob(source=self.name, **item)
        return None