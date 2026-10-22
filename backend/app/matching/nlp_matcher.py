"""TF-IDF + cosine similarity blended with skill-overlap scoring.

Produces a single 0-100 match score per candidate per job, plus the
component scores and the list of job-required skills the candidate is
missing (used downstream for skill-gap recommendations).
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_tfidf_similarity(job_text: str, resume_text: str) -> float:
    """Return a 0-1 cosine similarity score between job text and resume text."""
    job_text = (job_text or "").strip()
    resume_text = (resume_text or "").strip()
    if not job_text or not resume_text:
        return 0.0
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform([job_text, resume_text])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(max(0.0, min(1.0, similarity)))
    except ValueError:
        # e.g. empty vocabulary after stop-word removal (very short texts)
        return 0.0


def compute_skill_overlap(candidate_skills: list[str], required_skills: list[str]) -> tuple[float, list[str]]:
    """Return (overlap_ratio 0-1, missing_skills list)."""
    if not required_skills:
        return 1.0, []
    candidate_set = {s.lower().strip() for s in candidate_skills}
    required_set = {s.lower().strip() for s in required_skills}
    matched = candidate_set & required_set
    missing = sorted(required_set - candidate_set)
    overlap_ratio = len(matched) / len(required_set) if required_set else 1.0
    return overlap_ratio, missing


def compute_match_score(
    job_description: str,
    required_skills: list[str],
    resume_text: str,
    candidate_skills: list[str],
    tfidf_weight: float = 0.5,
    skill_weight: float = 0.5,
) -> dict:
    """Return a dict with blended score (0-100) and component scores."""
    tfidf_sim = compute_tfidf_similarity(job_description, resume_text)
    skill_overlap, missing_skills = compute_skill_overlap(candidate_skills, required_skills)

    total_weight = tfidf_weight + skill_weight
    if total_weight <= 0:
        tfidf_weight, skill_weight = 0.5, 0.5
        total_weight = 1.0

    blended = (tfidf_sim * tfidf_weight + skill_overlap * skill_weight) / total_weight
    score_0_100 = round(blended * 100, 2)

    return {
        "score": score_0_100,
        "tfidf_score": round(tfidf_sim * 100, 2),
        "skill_overlap_score": round(skill_overlap * 100, 2),
        "missing_skills": missing_skills,
    }
