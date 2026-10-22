"""Rule-based / retrieval-style HR chatbot.

Intent pattern-matching (regex/keyword rules) mapped to DB queries -- no
external LLM API calls. Each intent handler queries the DB via SQLAlchemy
and formats a natural-language response.
"""
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import json_utils, models

# ---------------------------------------------------------------------------
# Intent patterns
# ---------------------------------------------------------------------------
TOP_CANDIDATES_RE = re.compile(
    r"top\s*(\d+)?\s*candidates?\s*(?:for|in)\s*(?:job\s*)?(.+)", re.IGNORECASE
)
HOW_MANY_RESUMES_TODAY_RE = re.compile(
    r"how many resumes?.*(today|uploaded today)", re.IGNORECASE
)
HOW_MANY_RESUMES_RE = re.compile(r"how many (resumes|candidates)", re.IGNORECASE)
HOW_MANY_JOBS_RE = re.compile(r"how many jobs", re.IGNORECASE)
CANDIDATES_WITH_SKILL_RE = re.compile(
    r"(?:show|list|find)\s*candidates?\s*(?:with|who have|having)\s*(.+?)\s*(?:skills?)?$",
    re.IGNORECASE,
)
LIST_JOBS_RE = re.compile(r"(list|show)\s*(all\s*)?jobs", re.IGNORECASE)
AVERAGE_SCORE_RE = re.compile(
    r"average (?:match )?score.*(?:for|in)\s*(?:job\s*)?(.+)", re.IGNORECASE
)
UPCOMING_INTERVIEWS_RE = re.compile(r"upcoming interviews?", re.IGNORECASE)
HELP_RE = re.compile(r"^(help|what can you do)\??$", re.IGNORECASE)


def _find_job_by_title(db: Session, title_fragment: str) -> models.Job | None:
    title_fragment = title_fragment.strip().strip("?").strip()
    return (
        db.query(models.Job)
        .filter(models.Job.title.ilike(f"%{title_fragment}%"))
        .order_by(models.Job.created_at.desc())
        .first()
    )


def _handle_top_candidates(db: Session, match: re.Match) -> str:
    n = int(match.group(1)) if match.group(1) else 3
    job_title_fragment = match.group(2).strip()
    job = _find_job_by_title(db, job_title_fragment)
    if not job:
        return f"I couldn't find a job matching '{job_title_fragment}'."

    rows = (
        db.query(models.MatchScore, models.Candidate)
        .join(models.Candidate, models.MatchScore.candidate_id == models.Candidate.id)
        .filter(models.MatchScore.job_id == job.id)
        .order_by(models.MatchScore.score.desc())
        .limit(n)
        .all()
    )
    if not rows:
        return f"No candidates have been matched to '{job.title}' yet. Run matching first."

    lines = [f"Top {len(rows)} candidate(s) for '{job.title}':"]
    for i, (match_score, candidate) in enumerate(rows, start=1):
        lines.append(
            f"{i}. {candidate.name or candidate.email or ('Candidate #' + str(candidate.id))} "
            f"- score {match_score.score:.1f}/100"
        )
    return "\n".join(lines)


def _handle_resumes_today(db: Session, match: re.Match) -> str:
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    count = (
        db.query(func.count(models.Candidate.id))
        .filter(models.Candidate.created_at >= start_of_day)
        .scalar()
    )
    return f"{count} resume(s) have been uploaded today."


def _handle_how_many_resumes(db: Session, match: re.Match) -> str:
    count = db.query(func.count(models.Candidate.id)).scalar()
    return f"There are {count} candidate(s)/resume(s) in the system."


def _handle_how_many_jobs(db: Session, match: re.Match) -> str:
    count = db.query(func.count(models.Job.id)).scalar()
    return f"There are {count} job posting(s) in the system."


def _handle_candidates_with_skill(db: Session, match: re.Match) -> str:
    skill_fragment = match.group(1).strip().strip("?").lower()
    candidates = db.query(models.Candidate).all()
    matches = []
    for c in candidates:
        skills = json_utils.loads(c.skills, [])
        if any(skill_fragment in s.lower() for s in skills):
            matches.append(c)
    if not matches:
        return f"No candidates found with '{skill_fragment}' skills."
    lines = [f"Candidates with '{skill_fragment}' skills ({len(matches)}):"]
    for c in matches[:20]:
        lines.append(f"- {c.name or c.email or ('Candidate #' + str(c.id))}")
    return "\n".join(lines)


def _handle_list_jobs(db: Session, match: re.Match) -> str:
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).all()
    if not jobs:
        return "No jobs have been posted yet."
    lines = [f"There are {len(jobs)} job(s):"]
    for j in jobs[:20]:
        lines.append(f"- [{j.id}] {j.title}")
    return "\n".join(lines)


def _handle_average_score(db: Session, match: re.Match) -> str:
    job_title_fragment = match.group(1).strip().strip("?").strip()
    job = _find_job_by_title(db, job_title_fragment)
    if not job:
        return f"I couldn't find a job matching '{job_title_fragment}'."
    avg_score = (
        db.query(func.avg(models.MatchScore.score))
        .filter(models.MatchScore.job_id == job.id)
        .scalar()
    )
    if avg_score is None:
        return f"No match scores yet for '{job.title}'."
    return f"The average match score for '{job.title}' is {avg_score:.1f}/100."


def _handle_upcoming_interviews(db: Session, match: re.Match) -> str:
    now = datetime.now(timezone.utc)
    upcoming = (
        db.query(models.InterviewSchedule)
        .filter(models.InterviewSchedule.scheduled_at >= now)
        .order_by(models.InterviewSchedule.scheduled_at.asc())
        .limit(10)
        .all()
    )
    if not upcoming:
        return "There are no upcoming interviews scheduled."
    lines = [f"Upcoming interviews ({len(upcoming)}):"]
    for interview in upcoming:
        lines.append(
            f"- Candidate #{interview.candidate_id} for Job #{interview.job_id} "
            f"at {interview.scheduled_at.isoformat()} (status: {interview.status})"
        )
    return "\n".join(lines)


def _handle_help(db: Session, match: re.Match) -> str:
    return (
        "I can answer questions like:\n"
        "- 'top 3 candidates for job <title>'\n"
        "- 'how many resumes were uploaded today'\n"
        "- 'show candidates with Python skills'\n"
        "- 'how many jobs'\n"
        "- 'list jobs'\n"
        "- 'average score for job <title>'\n"
        "- 'upcoming interviews'"
    )


# Order matters: more specific patterns first.
_INTENT_HANDLERS: list[tuple[re.Pattern, callable]] = [
    (HOW_MANY_RESUMES_TODAY_RE, _handle_resumes_today),
    (TOP_CANDIDATES_RE, _handle_top_candidates),
    (AVERAGE_SCORE_RE, _handle_average_score),
    (CANDIDATES_WITH_SKILL_RE, _handle_candidates_with_skill),
    (HOW_MANY_JOBS_RE, _handle_how_many_jobs),
    (HOW_MANY_RESUMES_RE, _handle_how_many_resumes),
    (LIST_JOBS_RE, _handle_list_jobs),
    (UPCOMING_INTERVIEWS_RE, _handle_upcoming_interviews),
    (HELP_RE, _handle_help),
]


def answer_query(db: Session, query_text: str) -> str:
    query_text = query_text.strip()
    if not query_text:
        return "Please ask me something, e.g. 'top 3 candidates for job Data Analyst'."

    for pattern, handler in _INTENT_HANDLERS:
        match = pattern.search(query_text)
        if match:
            try:
                return handler(db, match)
            except Exception as exc:  # pragma: no cover - defensive
                return f"Sorry, I ran into an error answering that: {exc}"

    return (
        "I didn't understand that. Try things like 'top 3 candidates for job <title>', "
        "'how many resumes were uploaded today', or 'show candidates with Python skills'. "
        "Type 'help' to see more examples."
    )
