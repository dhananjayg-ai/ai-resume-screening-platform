"""Interview scheduling CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import InterviewCreate, InterviewOut, InterviewUpdate
from app.serializers import interview_to_out

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/", response_model=InterviewOut)
def create_interview(payload: InterviewCreate, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    interview = models.InterviewSchedule(
        candidate_id=payload.candidate_id,
        job_id=payload.job_id,
        scheduled_at=payload.scheduled_at,
        interviewer=payload.interviewer,
        status=payload.status,
        notes=payload.notes,
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    return interview_to_out(interview)


@router.get("/", response_model=list[InterviewOut])
def list_interviews(db: Session = Depends(get_db)):
    interviews = (
        db.query(models.InterviewSchedule)
        .order_by(models.InterviewSchedule.scheduled_at.asc())
        .all()
    )
    return [interview_to_out(i) for i in interviews]


@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.InterviewSchedule).filter(models.InterviewSchedule.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview_to_out(interview)


@router.put("/{interview_id}", response_model=InterviewOut)
def update_interview(interview_id: int, payload: InterviewUpdate, db: Session = Depends(get_db)):
    interview = db.query(models.InterviewSchedule).filter(models.InterviewSchedule.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interview, key, value)

    db.commit()
    db.refresh(interview)
    return interview_to_out(interview)


@router.delete("/{interview_id}")
def delete_interview(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(models.InterviewSchedule).filter(models.InterviewSchedule.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    db.delete(interview)
    db.commit()
    return {"detail": "Interview deleted"}
