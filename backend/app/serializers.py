"""Shared helpers to convert ORM models to Pydantic response schemas.

Centralized here so candidate (de)serialization logic isn't duplicated across
the resumes/candidates/matching routers.
"""
from app import json_utils, models, schemas


def candidate_to_out(candidate: models.Candidate) -> schemas.CandidateOut:
    return schemas.CandidateOut(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        resume_filename=candidate.resume_filename,
        detected_language=candidate.detected_language,
        skills=json_utils.loads(candidate.skills, []),
        education=json_utils.loads(candidate.education, []),
        experience_years=candidate.experience_years,
        certifications=json_utils.loads(candidate.certifications, []),
        quality_score=candidate.quality_score,
        quality_feedback=json_utils.loads(candidate.quality_feedback, []),
        duplicate_of_candidate_id=candidate.duplicate_of_candidate_id,
        duplicate_similarity=candidate.duplicate_similarity,
        created_at=candidate.created_at,
    )


def match_score_to_out(match: models.MatchScore) -> schemas.MatchScoreOut:
    return schemas.MatchScoreOut(
        id=match.id,
        job_id=match.job_id,
        candidate_id=match.candidate_id,
        score=match.score,
        skill_overlap_score=match.skill_overlap_score,
        tfidf_score=match.tfidf_score,
        missing_skills=json_utils.loads(match.missing_skills, []),
        created_at=match.created_at,
    )


def interview_to_out(interview: models.InterviewSchedule) -> schemas.InterviewOut:
    return schemas.InterviewOut(
        id=interview.id,
        candidate_id=interview.candidate_id,
        job_id=interview.job_id,
        scheduled_at=interview.scheduled_at,
        interviewer=interview.interviewer,
        status=interview.status,
        notes=interview.notes,
        created_at=interview.created_at,
    )


def notification_to_out(notification: models.NotificationLog) -> schemas.NotificationOut:
    return schemas.NotificationOut(
        id=notification.id,
        candidate_id=notification.candidate_id,
        job_id=notification.job_id,
        channel=notification.channel,
        subject=notification.subject,
        body=notification.body,
        status=notification.status,
        created_at=notification.created_at,
    )
