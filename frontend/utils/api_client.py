"""Thin wrapper around `requests` for talking to the FastAPI backend.

API_BASE_URL is read from the environment (default http://localhost:8000) so
the same code works both locally and inside docker-compose (where it is set
to http://backend:8000).
"""
import os

import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT = 30


class ApiError(Exception):
    """Raised when the backend returns a non-2xx response or is unreachable."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _handle_response(response: requests.Response):
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise ApiError(f"API error ({response.status_code}): {detail}", response.status_code)
    if response.content:
        return response.json()
    return None


def _get(path: str, params: dict | None = None):
    try:
        resp = requests.get(f"{API_BASE_URL}{path}", params=params, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Could not reach backend at {API_BASE_URL}: {exc}")
    return _handle_response(resp)


def _post(path: str, json_body: dict | None = None, files=None, data=None):
    try:
        resp = requests.post(
            f"{API_BASE_URL}{path}", json=json_body, files=files, data=data, timeout=DEFAULT_TIMEOUT
        )
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Could not reach backend at {API_BASE_URL}: {exc}")
    return _handle_response(resp)


def _put(path: str, json_body: dict | None = None):
    try:
        resp = requests.put(f"{API_BASE_URL}{path}", json=json_body, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Could not reach backend at {API_BASE_URL}: {exc}")
    return _handle_response(resp)


def _delete(path: str):
    try:
        resp = requests.delete(f"{API_BASE_URL}{path}", timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise ApiError(f"Could not reach backend at {API_BASE_URL}: {exc}")
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------
def create_job(title, description, required_skills, required_experience, required_education):
    return _post(
        "/jobs/",
        json_body={
            "title": title,
            "description": description,
            "required_skills": required_skills,
            "required_experience": required_experience,
            "required_education": required_education,
        },
    )


def list_jobs():
    return _get("/jobs/")


def get_job(job_id: int):
    return _get(f"/jobs/{job_id}")


# ---------------------------------------------------------------------------
# Resumes / candidates
# ---------------------------------------------------------------------------
def upload_resume(file_bytes: bytes, filename: str, content_type: str):
    files = {"file": (filename, file_bytes, content_type)}
    return _post("/resumes/upload", files=files)


def check_duplicate(candidate_id: int):
    return _get(f"/resumes/duplicates/{candidate_id}")


def list_candidates():
    return _get("/candidates/")


def get_candidate(candidate_id: int):
    return _get(f"/candidates/{candidate_id}")


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------
def run_matching(job_id: int):
    return _post("/matching/run", json_body={"job_id": job_id})


def get_rankings(job_id: int):
    return _get(f"/matching/rankings/{job_id}")


def list_all_match_scores():
    return _get("/matching/scores")


# ---------------------------------------------------------------------------
# Interviews
# ---------------------------------------------------------------------------
def create_interview(candidate_id, job_id, scheduled_at_iso, interviewer, status, notes):
    return _post(
        "/interviews/",
        json_body={
            "candidate_id": candidate_id,
            "job_id": job_id,
            "scheduled_at": scheduled_at_iso,
            "interviewer": interviewer,
            "status": status,
            "notes": notes,
        },
    )


def list_interviews():
    return _get("/interviews/")


def update_interview(interview_id, **kwargs):
    body = {k: v for k, v in kwargs.items() if v is not None}
    return _put(f"/interviews/{interview_id}", json_body=body)


def delete_interview(interview_id):
    return _delete(f"/interviews/{interview_id}")


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
def send_notification(candidate_id, job_id, subject, body):
    return _post(
        "/notifications/send",
        json_body={"candidate_id": candidate_id, "job_id": job_id, "subject": subject, "body": body},
    )


def list_notifications():
    return _get("/notifications/")


def test_smtp_connection():
    return _post("/notifications/test-connection")


def send_test_email(to_email: str | None = None):
    return _post("/notifications/send-test", json_body={"to_email": to_email})


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------
def chatbot_query(query: str):
    return _post("/chatbot/query", json_body={"query": query})
