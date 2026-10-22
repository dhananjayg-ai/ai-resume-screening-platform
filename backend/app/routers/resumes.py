"""Resume upload & screening endpoint: extraction, language detection,
quality scoring and duplicate detection all happen here at upload time."""
import logging
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import json_utils, models
from app.config import settings
from app.database import get_db
from app.matching.duplicate_detector import find_most_similar_candidate
from app.matching.quality_scorer import score_resume_quality
from app.parsing.field_extractor import extract_all_fields
from app.parsing.language import detect_language, translate_to_english
from app.parsing.resume_parser import ResumeParsingError, extract_text
from app.schemas import CandidateUploadResponse, DuplicateCheckResult
from app.serializers import candidate_to_out

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resumes", tags=["resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def _ensure_upload_dir() -> str:
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@router.post("/upload", response_model=CandidateUploadResponse)
async def upload_resume(file: UploadFile, db: Session = Depends(get_db)):
    original_filename = file.filename or "unknown"
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only PDF and DOCX files are accepted.",
        )

    upload_dir = _ensure_upload_dir()
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(upload_dir, stored_filename)

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    with open(stored_path, "wb") as f:
        f.write(contents)

    # --- Text extraction (with OCR fallback for scanned PDFs) ---
    try:
        raw_text, ocr_used = extract_text(stored_path, original_filename)
    except ResumeParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # --- Multi-language support ---
    detected_language = detect_language(raw_text)
    translated_text = None
    translation_used = False
    text_for_nlp = raw_text
    if detected_language != "en":
        translated_text = translate_to_english(raw_text, detected_language)
        if translated_text:
            translation_used = True
            text_for_nlp = translated_text

    # --- Field extraction ---
    fields = extract_all_fields(text_for_nlp)

    # --- Quality scoring ---
    quality_score, quality_feedback = score_resume_quality(
        raw_text=text_for_nlp,
        email=fields["email"],
        phone=fields["phone"],
        skills=fields["skills"],
    )

    # --- Duplicate detection against existing candidates ---
    existing = db.query(models.Candidate.id, models.Candidate.raw_text).all()
    existing_pairs = [(c.id, c.raw_text) for c in existing]
    duplicate_id, similarity = find_most_similar_candidate(
        raw_text,
        existing_pairs,
        k=settings.duplicate_shingle_size,
        threshold=settings.duplicate_similarity_threshold,
    )

    candidate = models.Candidate(
        name=fields["name"],
        email=fields["email"],
        phone=fields["phone"],
        resume_filename=stored_filename,
        raw_text=raw_text,
        detected_language=detected_language,
        translated_text=translated_text,
        skills=json_utils.dumps(fields["skills"]),
        education=json_utils.dumps(fields["education"]),
        experience_years=fields["experience_years"],
        certifications=json_utils.dumps(fields["certifications"]),
        quality_score=quality_score,
        quality_feedback=json_utils.dumps(quality_feedback),
        duplicate_of_candidate_id=duplicate_id,
        duplicate_similarity=similarity if duplicate_id else None,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return CandidateUploadResponse(
        candidate=candidate_to_out(candidate),
        is_possible_duplicate=duplicate_id is not None,
        duplicate_candidate_id=duplicate_id,
        duplicate_similarity=similarity if duplicate_id else None,
        ocr_used=ocr_used,
        translation_used=translation_used,
    )


@router.get("/duplicates/{candidate_id}", response_model=DuplicateCheckResult)
def check_duplicate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    others = (
        db.query(models.Candidate.id, models.Candidate.raw_text)
        .filter(models.Candidate.id != candidate_id)
        .all()
    )
    other_pairs = [(c.id, c.raw_text) for c in others]
    duplicate_id, similarity = find_most_similar_candidate(
        candidate.raw_text,
        other_pairs,
        k=settings.duplicate_shingle_size,
        threshold=settings.duplicate_similarity_threshold,
    )

    # Persist the (possibly updated) duplicate flag.
    candidate.duplicate_of_candidate_id = duplicate_id
    candidate.duplicate_similarity = similarity if duplicate_id else None
    db.commit()

    return DuplicateCheckResult(
        candidate_id=candidate_id,
        is_duplicate=duplicate_id is not None,
        duplicate_of_candidate_id=duplicate_id,
        similarity=similarity,
    )
