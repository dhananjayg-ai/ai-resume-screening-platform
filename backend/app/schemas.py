"""Pydantic v2 schemas used for request/response validation."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------
class JobCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    required_skills: list[str] = Field(default_factory=list)
    required_experience: float = 0.0
    required_education: str = ""


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    required_skills: list[str]
    required_experience: float
    required_education: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------
class QualityFeedbackItem(BaseModel):
    category: str
    message: str


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    email: str | None
    phone: str | None
    resume_filename: str
    detected_language: str
    skills: list[str]
    education: list[str]
    experience_years: float
    certifications: list[str]
    quality_score: float
    quality_feedback: list[str]
    duplicate_of_candidate_id: int | None
    duplicate_similarity: float | None
    created_at: datetime


class CandidateUploadResponse(BaseModel):
    candidate: CandidateOut
    is_possible_duplicate: bool
    duplicate_candidate_id: int | None = None
    duplicate_similarity: float | None = None
    ocr_used: bool = False
    translation_used: bool = False


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
class MatchScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    candidate_id: int
    score: float
    skill_overlap_score: float
    tfidf_score: float
    missing_skills: list[str]
    created_at: datetime


class CandidateRanking(BaseModel):
    candidate: CandidateOut
    match: MatchScoreOut
    learning_resources: dict[str, list[dict[str, str]]] = Field(default_factory=dict)


class RunMatchingRequest(BaseModel):
    job_id: int


# ---------------------------------------------------------------------------
# Interview scheduling
# ---------------------------------------------------------------------------
class InterviewCreate(BaseModel):
    candidate_id: int
    job_id: int
    scheduled_at: datetime
    interviewer: str = ""
    status: str = "scheduled"
    notes: str | None = None


class InterviewUpdate(BaseModel):
    scheduled_at: datetime | None = None
    interviewer: str | None = None
    status: str | None = None
    notes: str | None = None


class InterviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int
    scheduled_at: datetime
    interviewer: str
    status: str
    notes: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
class NotificationRequest(BaseModel):
    candidate_id: int
    job_id: int | None = None
    subject: str
    body: str


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    candidate_id: int
    job_id: int | None
    channel: str
    subject: str
    body: str
    status: str
    created_at: datetime


class SmtpTestRequest(BaseModel):
    to_email: str | None = None


class SmtpTestResult(BaseModel):
    status: str
    detail: str


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------
class ChatbotQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)


class ChatbotQueryResponse(BaseModel):
    query: str
    response: str


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
class DuplicateCheckResult(BaseModel):
    candidate_id: int
    is_duplicate: bool
    duplicate_of_candidate_id: int | None
    similarity: float
