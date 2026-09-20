from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    job_id: int


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    status: str
    applied_at: datetime

    class Config:
        from_attributes = True


class ApplicationStatusUpdate(BaseModel):
    status: str
