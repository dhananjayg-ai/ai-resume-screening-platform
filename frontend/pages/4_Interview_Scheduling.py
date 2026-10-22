"""Schedule, view and update candidate interviews."""
from datetime import datetime, time

import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import apply_global_styles, empty_state, page_header, section_header, status_badge

st.set_page_config(page_title="Interview Scheduling", page_icon="🗓️", layout="wide")
apply_global_styles()
page_header("Interview Scheduling", "Schedule, view and update candidate interviews.", icon="🗓️")

try:
    jobs = api_client.list_jobs()
    candidates = api_client.list_candidates()
except ApiError as exc:
    st.error(str(exc))
    jobs, candidates = [], []

section_header("Schedule a new interview", icon="➕")
if not jobs or not candidates:
    empty_state("You need at least one job and one screened candidate before scheduling an interview.", icon="🗓️")
else:
    job_options = {f"[{j['id']}] {j['title']}": j["id"] for j in jobs}
    candidate_options = {
        f"[{c['id']}] {c['name'] or c['email'] or c['resume_filename']}": c["id"] for c in candidates
    }

    with st.form("schedule_interview_form"):
        selected_candidate = st.selectbox("Candidate", list(candidate_options.keys()))
        selected_job = st.selectbox("Job", list(job_options.keys()))
        col1, col2 = st.columns(2)
        interview_date = col1.date_input("Interview date")
        interview_time = col2.time_input("Interview time", value=time(10, 0))
        interviewer = st.text_input("Interviewer name")
        notes = st.text_area("Notes", placeholder="Optional notes about the interview")
        submitted = st.form_submit_button("Schedule Interview")

    if submitted:
        scheduled_at = datetime.combine(interview_date, interview_time)
        try:
            api_client.create_interview(
                candidate_id=candidate_options[selected_candidate],
                job_id=job_options[selected_job],
                scheduled_at_iso=scheduled_at.isoformat(),
                interviewer=interviewer,
                status="scheduled",
                notes=notes or None,
            )
            st.success("Interview scheduled successfully.")
        except ApiError as exc:
            st.error(str(exc))

st.divider()
section_header("All interviews", icon="📋")
try:
    interviews = api_client.list_interviews()
except ApiError as exc:
    st.error(str(exc))
    interviews = []

if not interviews:
    empty_state("No interviews scheduled yet -- use the form above to schedule one.", icon="🗓️")
else:
    candidate_lookup = {c["id"]: c for c in candidates}
    job_lookup = {j["id"]: j for j in jobs}

    for interview in interviews:
        cand = candidate_lookup.get(interview["candidate_id"])
        job = job_lookup.get(interview["job_id"])
        cand_label = cand["name"] or cand["email"] if cand else f"Candidate #{interview['candidate_id']}"
        job_label = job["title"] if job else f"Job #{interview['job_id']}"

        with st.expander(
            f"[{interview['id']}] {cand_label} -- {job_label} -- {interview['scheduled_at']}"
        ):
            st.markdown(status_badge(interview["status"]), unsafe_allow_html=True)
            st.write(f"**Interviewer:** {interview['interviewer'] or 'N/A'}")
            st.write(f"**Notes:** {interview['notes'] or 'N/A'}")

            new_status = st.selectbox(
                "Update status",
                ["scheduled", "completed", "cancelled", "rescheduled", "no_show"],
                index=["scheduled", "completed", "cancelled", "rescheduled", "no_show"].index(interview["status"])
                if interview["status"] in ["scheduled", "completed", "cancelled", "rescheduled", "no_show"]
                else 0,
                key=f"status_{interview['id']}",
            )
            col1, col2 = st.columns(2)
            if col1.button("Update Status", key=f"update_{interview['id']}"):
                try:
                    api_client.update_interview(interview["id"], status=new_status)
                    st.success("Status updated. Refresh the page to see changes.")
                except ApiError as exc:
                    st.error(str(exc))
            if col2.button("Delete Interview", key=f"delete_{interview['id']}"):
                try:
                    api_client.delete_interview(interview["id"])
                    st.success("Interview deleted. Refresh the page to see changes.")
                except ApiError as exc:
                    st.error(str(exc))
