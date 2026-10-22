"""Post a new job opening."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import apply_global_styles, empty_state, page_header, section_header

st.set_page_config(page_title="Post a Job", page_icon="🧑‍💼", layout="wide")
apply_global_styles()
page_header("Post a Job", "Define a role with required skills, experience and education.", icon="🧑‍💼")

with st.form("post_job_form"):
    title = st.text_input("Job title", placeholder="e.g. Senior Backend Engineer")
    description = st.text_area(
        "Job description",
        placeholder="Describe the role, responsibilities, and context...",
        height=200,
    )
    skills_raw = st.text_input(
        "Required skills (comma-separated)", placeholder="python, sql, aws, docker"
    )
    col1, col2 = st.columns(2)
    required_experience = col1.number_input("Required experience (years)", min_value=0.0, step=0.5)
    required_education = col2.text_input("Required education", placeholder="e.g. Bachelor's degree")

    submitted = st.form_submit_button("Post Job")

if submitted:
    if not title.strip() or not description.strip():
        st.error("Job title and description are required.")
    else:
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        try:
            job = api_client.create_job(
                title=title,
                description=description,
                required_skills=skills,
                required_experience=required_experience,
                required_education=required_education,
            )
            st.success(f"Job posted successfully! Job ID: {job['id']}")
            st.json(job)
        except ApiError as exc:
            st.error(str(exc))

st.divider()
section_header("Existing jobs", icon="📋")
try:
    jobs = api_client.list_jobs()
    if not jobs:
        empty_state("No jobs posted yet -- use the form above to post the first one.", icon="📋")
    else:
        for job in jobs:
            with st.expander(f"[{job['id']}] {job['title']}"):
                st.write(job["description"])
                st.write(f"**Required skills:** {', '.join(job['required_skills']) or 'None specified'}")
                st.write(f"**Required experience:** {job['required_experience']} years")
                st.write(f"**Required education:** {job['required_education'] or 'None specified'}")
except ApiError as exc:
    st.error(str(exc))
