"""SQLAlchemy ORM models."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    required_experience: Mapped[float] = mapped_column(Float, default=0.0)
    required_education: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    match_scores: Mapped[list["MatchScore"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["InterviewSchedule"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resume_filename: Mapped[str] = mapped_column(String(512))
    raw_text: Mapped[str] = mapped_column(Text, default="")
    detected_language: Mapped[str] = mapped_column(String(16), default="en")
    translated_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    education: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    experience_years: Mapped[float] = mapped_column(Float, default=0.0)
    certifications: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_feedback: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    duplicate_of_candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id"), nullable=True
    )
    duplicate_similarity: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    match_scores: Mapped[list["MatchScore"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["InterviewSchedule"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class MatchScore(Base):
    __tablename__ = "match_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    skill_overlap_score: Mapped[float] = mapped_column(Float, default=0.0)
    tfidf_score: Mapped[float] = mapped_column(Float, default=0.0)
    missing_skills: Mapped[str] = mapped_column(Text, default="[]")  # JSON list
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    job: Mapped["Job"] = relationship(back_populates="match_scores")
    candidate: Mapped["Candidate"] = relationship(back_populates="match_scores")


class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    interviewer: Mapped[str] = mapped_column(String(255), default="")
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    candidate: Mapped["Candidate"] = relationship(back_populates="interviews")
    job: Mapped["Job"] = relationship(back_populates="interviews")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    job_id: Mapped[int | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(32), default="email")
    subject: Mapped[str] = mapped_column(String(512), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class ChatbotQueryLog(Base):
    __tablename__ = "chatbot_query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query_text: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
