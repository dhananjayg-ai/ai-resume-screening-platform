"""Candidate-to-job matching and ranking endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import json_utils, models
from app.config import settings
from app.database import get_db
from app.matching.nlp_matcher import compute_match_score
from app.matching.skill_gap import build_skill_gap_recommendations
from app.schemas import CandidateRanking, MatchScoreOut, RunMatchingRequest
from app.serializers import candidate_to_out, match_score_to_out

router = APIRouter(prefix="/matching", tags=["matching"])


@router.post("/run", response_model=list[MatchScoreOut])
def run_matching(payload: RunMatchingRequest, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    required_skills = json_utils.loads(job.required_skills, [])
    candidates = db.query(models.Candidate).all()

    results: list[models.MatchScore] = []
    for candidate in candidates:
        candidate_skills = json_utils.loads(candidate.skills, [])
        resume_text = candidate.translated_text or candidate.raw_text

        result = compute_match_score(
            job_description=job.description,
            required_skills=required_skills,
            resume_text=resume_text,
            candidate_skills=candidate_skills,
            tfidf_weight=settings.tfidf_weight,
            skill_weight=settings.skill_weight,
        )

        existing = (
            db.query(models.MatchScore)
            .filter(
                models.MatchScore.job_id == job.id,
                models.MatchScore.candidate_id == candidate.id,
            )
            .first()
        )
        if existing:
            existing.score = result["score"]
            existing.tfidf_score = result["tfidf_score"]
            existing.skill_overlap_score = result["skill_overlap_score"]
            existing.missing_skills = json_utils.dumps(result["missing_skills"])
            match_row = existing
        else:
            match_row = models.MatchScore(
                job_id=job.id,
                candidate_id=candidate.id,
                score=result["score"],
                tfidf_score=result["tfidf_score"],
                skill_overlap_score=result["skill_overlap_score"],
                missing_skills=json_utils.dumps(result["missing_skills"]),
            )
            db.add(match_row)
        results.append(match_row)

    db.commit()
    for r in results:
        db.refresh(r)

    results.sort(key=lambda r: r.score, reverse=True)
    return [match_score_to_out(r) for r in results]


@router.get("/scores", response_model=list[MatchScoreOut])
def list_all_match_scores(db: Session = Depends(get_db)):
    """Every match score across every job, used by the Dashboard page for
    cross-job aggregations (candidates-per-job, score distribution, top
    candidates overall)."""
    scores = db.query(models.MatchScore).order_by(models.MatchScore.score.desc()).all()
    return [match_score_to_out(s) for s in scores]


@router.get("/rankings/{job_id}", response_model=list[CandidateRanking])
def get_rankings(job_id: int, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    rows = (
        db.query(models.MatchScore, models.Candidate)
        .join(models.Candidate, models.MatchScore.candidate_id == models.Candidate.id)
        .filter(models.MatchScore.job_id == job_id)
        .order_by(models.MatchScore.score.desc())
        .all()
    )

    rankings = []
    for match_row, candidate in rows:
        missing_skills = json_utils.loads(match_row.missing_skills, [])
        rankings.append(
            CandidateRanking(
                candidate=candidate_to_out(candidate),
                match=match_score_to_out(match_row),
                learning_resources=build_skill_gap_recommendations(missing_skills),
            )
        )
    return rankings
