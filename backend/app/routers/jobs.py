"""Job posting endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import json_utils, models, schemas
from app.database import get_db

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _job_to_out(job: models.Job) -> schemas.JobOut:
    return schemas.JobOut(
        id=job.id,
        title=job.title,
        description=job.description,
        required_skills=json_utils.loads(job.required_skills, []),
        required_experience=job.required_experience,
        required_education=job.required_education,
        created_at=job.created_at,
    )


@router.post("/", response_model=schemas.JobOut)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    job = models.Job(
        title=payload.title,
        description=payload.description,
        required_skills=json_utils.dumps(payload.required_skills),
        required_experience=payload.required_experience,
        required_education=payload.required_education,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_to_out(job)


@router.get("/", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    return [_job_to_out(j) for j in jobs]


@router.get("/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_out(job)
