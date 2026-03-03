from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class UploadBatch(Base):
    __tablename__ = "upload_batch"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_records = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending / processing / completed

    records = relationship("EmployeeRecord", back_populates="batch", cascade="all, delete-orphan")


class EmployeeRecord(Base):
    __tablename__ = "employee_record"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("upload_batch.id"), nullable=True)
    record_id = Column(String, index=True)

    age = Column(Integer)
    gender = Column(String)
    education_level = Column(String)
    job_title = Column(String)
    years_of_experience = Column(Integer)
    weekly_working_hours = Column(Integer)
    employment_type = Column(String)
    monthly_income = Column(String)

    trust_score = Column(Float, default=0.0)
    is_valid = Column(Boolean, default=False)
    issues_count = Column(Integer, default=0)
    validation_method = Column(String, default="pending")  # gemini / offline / pending
    validated_at = Column(DateTime, nullable=True)

    batch = relationship("UploadBatch", back_populates="records")
    issues = relationship("ValidationIssue", back_populates="record", cascade="all, delete-orphan")


class ValidationIssue(Base):
    __tablename__ = "validation_issue"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("employee_record.id"), nullable=False)

    fields = Column(Text)  # JSON array stored as text
    description_ar = Column(Text)
    severity = Column(String)  # low / medium / high
    confidence = Column(Float, default=0.0)

    record = relationship("EmployeeRecord", back_populates="issues")
