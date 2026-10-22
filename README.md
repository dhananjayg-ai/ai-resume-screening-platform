# AI Resume Screening and Recruitment Platform

A full-stack portfolio project: a FastAPI backend with SQLAlchemy + SQLite, and a
Streamlit frontend, implementing an end-to-end AI-assisted resume screening and
recruitment workflow using classical NLP/ML (TF-IDF, cosine similarity, regex/keyword
extraction) -- **no external LLM API calls or API keys required** for any core feature.

## Features

### Core
1. **Post a job** -- title, description, required skills, experience, education.
2. **Upload & screen resumes** -- PDF (pdfplumber) and DOCX (python-docx) parsing;
   extracts name, email, phone, skills, education, experience, certifications via
   regex + a curated skills keyword list.
3. **NLP matching** -- TF-IDF vectorization + cosine similarity between job description
   and resume text, blended with skill-overlap into a single 0-100 match score.
4. **Candidate ranking** -- candidates per job, sorted by match score, with a
   score breakdown (TF-IDF component vs skill-overlap component).

### Advanced
5. **AI chatbot for HR queries** -- rule-based intent matching (regex/keywords) mapped
   to DB queries; no external LLM. E.g. "top 3 candidates for job X", "how many resumes
   were uploaded today", "show candidates with Python skills".
6. **Email notifications** -- SMTP (smtplib) notifications to shortlisted candidates,
   fully configurable via env vars; gracefully no-ops and logs to `NotificationLog`
   if SMTP isn't configured, so the system never crashes without real SMTP creds.
7. **OCR for scanned resumes** -- `pdf2image` + `pytesseract` fallback when `pdfplumber`
   extracts near-empty text from a PDF. Requires the `poppler-utils` and `tesseract-ocr`
   system packages (already included in the backend Dockerfile).
8. **Duplicate resume detection** -- Jaccard similarity over shingled (k-gram) tokens,
   flags resumes above a similarity threshold as likely duplicates of an existing candidate.
9. **Interview scheduling** -- full CRUD for interviews (candidate, job, datetime,
   interviewer, status, notes).
10. **Resume quality feedback** -- heuristic scoring (contact info, quantified
    achievements, action verbs, length, section completeness, formatting red flags)
    with actionable suggestions.
11. **Skill-gap recommendations** -- missing required skills mapped to a curated
    dictionary of learning resources (20+ entries: Python, SQL, AWS, Docker, React, etc).
12. **Multi-language resume support** -- `langdetect` for language detection,
    `deep-translator` (GoogleTranslator) to translate non-English resumes to English
    before NLP matching. Both original and translated text are stored.

## Architecture overview

```
ai-resume-screening-platform/
  backend/
    app/
      main.py            FastAPI app: CORS, startup table creation, router wiring
      config.py           Pydantic Settings (env-based configuration)
      database.py         SQLAlchemy engine/session/Base/get_db
      models.py           SQLAlchemy ORM models
      schemas.py          Pydantic v2 request/response schemas
      json_utils.py        Centralized JSON (de)serialization for Text columns
      serializers.py       ORM -> Pydantic schema conversion helpers
      parsing/
        resume_parser.py   PDF/DOCX text extraction + OCR fallback
        field_extractor.py Regex/keyword extraction (name/email/phone/skills/etc)
        language.py          langdetect + deep-translator wrapper
      matching/
        nlp_matcher.py      TF-IDF + cosine + skill overlap -> blended score
        quality_scorer.py   Resume quality heuristic scoring
        skill_gap.py          Missing-skill -> learning resource mapping
        duplicate_detector.py Jaccard/shingle duplicate detection
      chatbot/
        engine.py            Rule-based intent matching -> DB queries
      notifications/
        emailer.py           SMTP sending with graceful NotificationLog fallback
      routers/               One FastAPI router per resource (jobs, resumes,
                              candidates, matching, interviews, notifications, chatbot)
    requirements.txt
    Dockerfile
  frontend/
    Home.py                 Streamlit landing page
    pages/                  One Streamlit page per feature area
    utils/api_client.py     requests-based wrapper around the backend API
    requirements.txt
    Dockerfile
  docker-compose.yml
  .env.example
  .gitignore
  README.md
```

### Data model
- `Job` -- title, description, required_skills (JSON), required_experience, required_education
- `Candidate` -- name, email, phone, resume_filename, raw_text, detected_language,
  translated_text, skills/education/certifications (JSON), experience_years,
  quality_score, quality_feedback (JSON), duplicate_of_candidate_id, duplicate_similarity
- `MatchScore` -- job_id, candidate_id, score, skill_overlap_score, tfidf_score, missing_skills (JSON)
- `InterviewSchedule` -- candidate_id, job_id, scheduled_at, interviewer, status, notes
- `NotificationLog` -- candidate_id, job_id, channel, subject, body, status
- `ChatbotQueryLog` -- query_text, response_text

List/dict fields are stored as JSON-encoded strings in `Text` columns (for SQLite
simplicity) and (de)serialized centrally through `app/json_utils.py`.

## Running locally (Python venv)

Requires Python 3.11+ (3.9+ should also work).

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
# Frontend
cd frontend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export API_BASE_URL=http://localhost:8000   # optional, this is the default
streamlit run Home.py
```

Open the Streamlit app (usually http://localhost:8501) and the API docs at
http://localhost:8000/docs.

> **OCR note:** running locally without the `tesseract-ocr` and `poppler-utils`
> system packages installed means the OCR fallback for scanned PDFs will log a
> warning and skip OCR rather than crash -- regular (non-scanned) PDFs and DOCX
> files are unaffected.

## Running with Docker Compose

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:8501

The backend container installs `poppler-utils` and `tesseract-ocr` so OCR works
out of the box. A named volume (`resume_data`) persists the SQLite DB and
uploaded resumes across restarts.

To configure SMTP for real email sending, set `SMTP_HOST`, `SMTP_USER`,
`SMTP_PASSWORD`, `SMTP_FROM` (and optionally `SMTP_PORT`) either in a `.env`
file at the project root (copy `.env.example`) or as shell environment
variables before running `docker compose up`.

## Environment variables

| Variable | Default | Used by | Description |
|---|---|---|---|
| `DATABASE_URL` | `sqlite:///./resume_screening.db` | backend | SQLAlchemy DB URL |
| `UPLOAD_DIR` | `./uploaded_resumes` | backend | Where uploaded resume files are stored |
| `CORS_ORIGINS` | `*` | backend | Comma-separated allowed CORS origins |
| `SMTP_HOST` | unset | backend | SMTP server host (unset = log-only mode) |
| `SMTP_PORT` | `587` | backend | SMTP server port |
| `SMTP_USER` | unset | backend | SMTP username |
| `SMTP_PASSWORD` | unset | backend | SMTP password |
| `SMTP_FROM` | unset | backend | "From" address for outgoing emails |
| `TFIDF_WEIGHT` | `0.5` | backend | Weight of TF-IDF similarity in blended match score |
| `SKILL_WEIGHT` | `0.5` | backend | Weight of skill-overlap in blended match score |
| `DUPLICATE_SHINGLE_SIZE` | `5` | backend | k-gram size for Jaccard duplicate detection |
| `DUPLICATE_SIMILARITY_THRESHOLD` | `0.6` | backend | Similarity above which a resume is flagged a duplicate |
| `API_BASE_URL` | `http://localhost:8000` | frontend | Base URL of the FastAPI backend |

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/` | Health/info |
| GET | `/health` | Health check |
| POST | `/jobs/` | Create a job |
| GET | `/jobs/` | List jobs |
| GET | `/jobs/{job_id}` | Get a job |
| POST | `/resumes/upload` | Upload & screen a resume (multipart file upload) |
| GET | `/resumes/duplicates/{candidate_id}` | Re-check duplicate status for a candidate |
| GET | `/candidates/` | List all candidates |
| GET | `/candidates/{candidate_id}` | Get a candidate |
| POST | `/matching/run` | Run/refresh matching for a job against all candidates |
| GET | `/matching/rankings/{job_id}` | Ranked candidates for a job + skill-gap resources |
| POST | `/interviews/` | Schedule an interview |
| GET | `/interviews/` | List interviews |
| GET | `/interviews/{interview_id}` | Get an interview |
| PUT | `/interviews/{interview_id}` | Update an interview |
| DELETE | `/interviews/{interview_id}` | Delete an interview |
| POST | `/notifications/send` | Send (or log) a notification email |
| GET | `/notifications/` | List notification history |
| POST | `/chatbot/query` | Ask the HR chatbot a natural-language question |

Full interactive documentation (OpenAPI/Swagger) is available at `/docs` once the
backend is running.

## Known limitations (by design, for a portfolio/demo project)

- Field extraction (name/email/phone/skills/education/certifications) is regex and
  keyword-list based, not an ML/LLM-based parser -- this is intentional per the
  project brief and works well for typical resume formats but isn't perfect for
  unusual layouts.
- OCR requires the `tesseract-ocr` and `poppler-utils` system packages. They're
  included in the backend Dockerfile; if running locally without them, OCR is
  skipped gracefully (logged, not crashed).
- Translation (`deep-translator`) requires outbound internet access; without it,
  the system falls back to using the original (untranslated) text for matching.
- No authentication/authorization layer -- out of scope for this portfolio project.
