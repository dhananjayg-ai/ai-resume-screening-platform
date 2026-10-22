"""Candidate listing/detail endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.schemas import CandidateOut
from app.serializers import candidate_to_out

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("/", response_model=list[CandidateOut])
def list_candidates(db: Session = Depends(get_db)):
    candidates = db.query(models.Candidate).order_by(models.Candidate.created_at.desc()).all()
    return [candidate_to_out(c) for c in candidates]


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate_to_out(candidate)
