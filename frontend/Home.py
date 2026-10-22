"""Home page for the AI Resume Screening and Recruitment Platform Streamlit app."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import (
    apply_global_styles,
    empty_state,
    page_header,
    section_header,
)

st.set_page_config(
    page_title="AI Resume Screening Platform",
    page_icon="👨‍💼",
    layout="wide",
)

apply_global_styles()

page_header(
    "AI Resume Screening and Recruitment Platform",
    "An end-to-end AI-assisted recruitment workflow -- from job posting to shortlist notification.",
    icon="👨‍💼",
)

st.caption(f"Backend API: {api_client.API_BASE_URL}")
section_header("Backend connection status", icon="🔌")

jobs = []
candidates = []
notifications = []
interviews = []

try:
    jobs = api_client.list_jobs() or []
    candidates = api_client.list_candidates() or []

    try:
        notifications = api_client.list_notifications() or []
    except ApiError:
        notifications = []

    try:
        interviews = api_client.list_interviews() or []
    except ApiError:
        interviews = []

    # Use native Streamlit metrics to avoid raw HTML showing as text.
    metric_columns = st.columns(4)
    metrics = [
        ("Jobs posted", len(jobs)),
        ("Candidates screened", len(candidates)),
        ("Interviews scheduled", len(interviews)),
        ("Notifications sent", len(notifications)),
    ]

    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            st.metric(label=label, value=value)

    st.success("Connected to backend successfully.")

except ApiError as exc:
    st.error(f"Could not connect to backend: {exc}")
    st.info(
        "Make sure the FastAPI backend is running and that API_BASE_URL is set "
        f"correctly (currently: {api_client.API_BASE_URL})."
    )

section_header("What you can do here", icon="🧭")

features = [
    ("💼", "Post a Job", "Define a role with required skills, experience and education."),
    (
        "📄",
        "Upload & Screen Resumes",
        "Upload PDF/DOCX resumes; fields are extracted automatically, with OCR fallback "
        "for scanned PDFs, multi-language detection/translation, duplicate detection, "
        "and resume quality feedback.",
    ),
    (
        "📊",
        "Candidate Rankings",
        "Run NLP (TF-IDF + skill overlap) matching, view ranked candidates per job, "
        "get skill-gap learning recommendations, and notify shortlisted candidates.",
    ),
    ("🗓️", "Interview Scheduling", "Schedule, view and update interviews."),
    ("💬", "HR Chatbot", "Ask natural-language questions about jobs and candidates."),
    (
        "📧",
        "Notifications Log",
        "Send shortlist emails, test SMTP configuration, and review notification history.",
    ),
]

columns = st.columns(3)
for index, (icon, title, description) in enumerate(features):
    with columns[index % 3]:
        with st.container(border=True):
            st.markdown(f"### {icon} {title}")
            st.write(description)

if not jobs and not candidates:
    empty_state(
        "Get started by posting a job, then upload a resume to screen it.",
        icon="🚀",
    )
