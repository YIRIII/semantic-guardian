from pydantic import BaseModel, Field
from typing import Optional


class EmployeePayload(BaseModel):
    age: int
    gender: Optional[str] = None
    education_level: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: Optional[int] = None
    weekly_working_hours: Optional[int] = None
    employment_type: Optional[str] = None
    monthly_income: Optional[str] = None


class RecordCreate(BaseModel):
    age: int
    gender: str = ""
    education_level: str = ""
    job_title: str = ""
    years_of_experience: int = 0
    weekly_working_hours: int = 40
    employment_type: str = "دوام كامل"
    monthly_income: str = ""


class IssueOut(BaseModel):
    fields: list[str]
    description_ar: str
    severity: str
    confidence: float


class ValidationResult(BaseModel):
    issues: list[IssueOut] = Field(default_factory=list)
    overall_trust_score: float = 0.0


class StatsOut(BaseModel):
    total: int = 0
    valid: int = 0
    invalid: int = 0
    avg_trust: float = 0.0
