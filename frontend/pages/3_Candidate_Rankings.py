"""Run matching for a job, view ranked candidates with skill-gap resources,
and notify shortlisted candidates in bulk."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import (
    SCORE_BAND_HIGH,
    apply_global_styles,
    empty_state,
    page_header,
    score_badge,
    section_header,
    status_badge,
)

st.set_page_config(page_title="Candidate Rankings", page_icon="📊", layout="wide")
apply_global_styles()
page_header(
    "Candidate Rankings",
    "Run NLP (TF-IDF + skill overlap) matching and notify shortlisted candidates.",
    icon="📊",
)

try:
    jobs = api_client.list_jobs()
except ApiError as exc:
    st.error(str(exc))
    jobs = []

if not jobs:
    empty_state("No jobs posted yet. Post a job first.", icon="📊")
else:
    job_options = {f"[{j['id']}] {j['title']}": j["id"] for j in jobs}
    selected_label = st.selectbox("Select a job", list(job_options.keys()))
    job_id = job_options[selected_label]

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Run / Refresh Matching"):
            with st.spinner("Computing TF-IDF + skill-overlap match scores..."):
                try:
                    api_client.run_matching(job_id)
                    st.success("Matching complete.")
                except ApiError as exc:
                    st.error(str(exc))

    try:
        rankings = api_client.get_rankings(job_id)
    except ApiError as exc:
        st.error(str(exc))
        rankings = []

    if not rankings:
        empty_state(
            "No match scores yet for this job -- click 'Run / Refresh Matching' above.", icon="📊"
        )
    else:
        section_header(f"Ranked candidates ({len(rankings)})", icon="🏆")
        for rank, item in enumerate(rankings, start=1):
            candidate = item["candidate"]
            match = item["match"]
            name = candidate["name"] or candidate["email"] or f"Candidate #{candidate['id']}"
            with st.expander(f"#{rank} -- {name}"):
                st.markdown(score_badge(match["score"]), unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Overall score", f"{match['score']:.1f}")
                col_b.metric("TF-IDF similarity", f"{match['tfidf_score']:.1f}")
                col_c.metric("Skill overlap", f"{match['skill_overlap_score']:.1f}")

                st.write(f"**Email:** {candidate['email'] or 'N/A'} | **Phone:** {candidate['phone'] or 'N/A'}")
                st.write(f"**Candidate skills:** {', '.join(candidate['skills']) or 'None detected'}")

                if match["missing_skills"]:
                    st.write(f"**Missing skills:** {', '.join(match['missing_skills'])}")
                    st.write("**Skill-gap learning recommendations:**")
                    for skill, resources in item["learning_resources"].items():
                        resource_links = ", ".join(f"[{r['name']}]({r['url']})" for r in resources)
                        st.markdown(f"- **{skill}**: {resource_links}")
                else:
                    st.success("No missing required skills.")

        # ---------------------------------------------------------------
        # Bulk notify shortlisted candidates
        # ---------------------------------------------------------------
        st.divider()
        section_header("Notify Shortlisted Candidates", icon="📧")

        threshold = st.slider(
            "Shortlist threshold (minimum match score)",
            min_value=0.0,
            max_value=100.0,
            value=SCORE_BAND_HIGH,
            step=1.0,
            help="Candidates at or above this match score are considered shortlisted.",
        )

        shortlisted = [
            item for item in rankings if item["match"]["score"] >= threshold and item["candidate"]["email"]
        ]
        skipped_no_email = [
            item for item in rankings if item["match"]["score"] >= threshold and not item["candidate"]["email"]
        ]

        if not shortlisted and not skipped_no_email:
            empty_state(
                f"No candidates meet the {threshold:.0f}+ threshold yet -- lower the threshold or "
                "screen more candidates.",
                icon="📧",
            )
        else:
            if skipped_no_email:
                st.warning(
                    f"{len(skipped_no_email)} shortlisted candidate(s) have no email on file and will "
                    "be skipped: "
                    + ", ".join(
                        f"#{i['candidate']['id']} ({i['candidate']['name'] or 'unnamed'})"
                        for i in skipped_no_email
                    )
                )

            st.write(f"**{len(shortlisted)} candidate(s)** at or above the threshold have an email on file:")
            selected_ids = st.multiselect(
                "Recipients",
                options=[item["candidate"]["id"] for item in shortlisted],
                default=[item["candidate"]["id"] for item in shortlisted],
                format_func=lambda cid: next(
                    f"[{i['candidate']['id']}] {i['candidate']['name'] or i['candidate']['email']} "
                    f"-- {i['match']['score']:.1f}/100"
                    for i in shortlisted
                    if i["candidate"]["id"] == cid
                ),
            )

            job_title = next((j["title"] for j in jobs if j["id"] == job_id), "")
            with st.form("bulk_notify_form"):
                subject = st.text_input("Subject", value="You've been shortlisted!")
                body = st.text_area(
                    "Message body",
                    value=(
                        f"Hi,\n\nCongratulations! You have been shortlisted for the role of "
                        f"\"{job_title}\" in our recruitment process. We will be in touch shortly "
                        "with next steps.\n\nBest regards,\nRecruitment Team"
                    ),
                    height=180,
                )
                send_clicked = st.form_submit_button(f"Send to {len(selected_ids)} selected candidate(s)")

            if send_clicked:
                if not selected_ids:
                    st.warning("No recipients selected.")
                else:
                    results = []
                    progress = st.progress(0.0, text="Sending notifications...")
                    for idx, cid in enumerate(selected_ids):
                        item = next(i for i in shortlisted if i["candidate"]["id"] == cid)
                        cand = item["candidate"]
                        try:
                            resp = api_client.send_notification(
                                candidate_id=cid, job_id=job_id, subject=subject, body=body
                            )
                            results.append(
                                {
                                    "candidate": cand["name"] or cand["email"],
                                    "email": cand["email"],
                                    "status": resp["status"],
                                }
                            )
                        except ApiError as exc:
                            results.append(
                                {"candidate": cand["name"] or cand["email"], "email": cand["email"], "status": "failed", "detail": str(exc)}
                            )
                        progress.progress((idx + 1) / len(selected_ids), text=f"Sent {idx + 1}/{len(selected_ids)}")
                    progress.empty()

                    sent_count = sum(1 for r in results if r["status"] == "sent")
                    failed_count = sum(1 for r in results if r["status"] not in ("sent",))
                    if sent_count:
                        st.success(f"{sent_count} email(s) sent successfully.")
                    if failed_count:
                        st.warning(
                            f"{failed_count} notification(s) were not sent (see per-recipient status below)."
                        )

                    st.write("**Per-recipient results:**")
                    for r in results:
                        st.markdown(
                            f"{status_badge(r['status'])} &nbsp; **{r['candidate']}** "
                            f"({r['email']})" + (f" -- {r.get('detail', '')}" if r.get("detail") else ""),
                            unsafe_allow_html=True,
                        )
