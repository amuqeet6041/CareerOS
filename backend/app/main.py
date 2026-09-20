from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, auth, resume, jobs, matching, applications

app = FastAPI(title="CareerOS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(matching.router, prefix="/api/matching", tags=["matching"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])


@app.get("/")
def root():
    return {"message": "CareerOS API is running. See /docs for API documentation."}
