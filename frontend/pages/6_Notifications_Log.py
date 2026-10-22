"""Send shortlist notification emails, test the SMTP configuration, and
review the notification log."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import apply_global_styles, empty_state, page_header, section_header, status_badge

st.set_page_config(page_title="Notifications Log", page_icon="📧", layout="wide")
apply_global_styles()
page_header(
    "Notifications Log",
    "Send shortlist emails, verify your SMTP setup, and review notification history.",
    icon="📧",
)

# ---------------------------------------------------------------------------
# SMTP health check -- immediate pass/fail feedback, so email delivery is
# obviously working (or obviously not) before relying on it elsewhere.
# ---------------------------------------------------------------------------
section_header("SMTP Configuration Check", icon="🛠️")
col_test1, col_test2 = st.columns(2)

with col_test1:
    st.caption("Connect and authenticate to the configured SMTP server without sending any mail.")
    if st.button("Test SMTP Connection"):
        with st.spinner("Connecting..."):
            try:
                result = api_client.test_smtp_connection()
                st.markdown(status_badge(result["status"]), unsafe_allow_html=True)
                st.write(result["detail"])
            except ApiError as exc:
                st.error(str(exc))

with col_test2:
    st.caption("Actually send a short test email to confirm end-to-end delivery.")
    test_recipient = st.text_input(
        "Send test email to (optional -- defaults to SMTP_FROM)", key="test_email_recipient"
    )
    if st.button("Send Test Email"):
        with st.spinner("Sending..."):
            try:
                result = api_client.send_test_email(test_recipient or None)
                st.markdown(status_badge(result["status"]), unsafe_allow_html=True)
                st.write(result["detail"])
            except ApiError as exc:
                st.error(str(exc))

st.divider()
section_header("Send a notification", icon="✉️")
try:
    candidates = api_client.list_candidates()
    jobs = api_client.list_jobs()
except ApiError as exc:
    st.error(str(exc))
    candidates, jobs = [], []

if not candidates:
    empty_state("No candidates available yet. Upload and screen a resume first.", icon="✉️")
else:
    candidate_options = {
        f"[{c['id']}] {c['name'] or c['email'] or c['resume_filename']}": c["id"] for c in candidates
    }
    job_options = {"(none)": None}
    job_options.update({f"[{j['id']}] {j['title']}": j["id"] for j in jobs})

    with st.form("send_notification_form"):
        selected_candidate = st.selectbox("Candidate", list(candidate_options.keys()))
        selected_job = st.selectbox("Related job (optional)", list(job_options.keys()))
        subject = st.text_input("Subject", value="You've been shortlisted!")
        body = st.text_area(
            "Message body",
            value=(
                "Hi,\n\nCongratulations! You have been shortlisted for the next stage of our "
                "recruitment process. We will be in touch shortly with next steps.\n\nBest regards,\n"
                "Recruitment Team"
            ),
            height=200,
        )
        submitted = st.form_submit_button("Send Notification")

    if submitted:
        try:
            result = api_client.send_notification(
                candidate_id=candidate_options[selected_candidate],
                job_id=job_options[selected_job],
                subject=subject,
                body=body,
            )
            st.markdown(status_badge(result["status"]), unsafe_allow_html=True)
            if result["status"] == "sent":
                st.success("Email sent successfully.")
            elif result["status"] == "skipped_no_smtp_config":
                st.warning(
                    "SMTP is not configured in this environment, so the email was not actually sent. "
                    "The notification has been logged below instead (this is expected in a demo setup). "
                    "Use the SMTP Configuration Check above once SMTP_HOST/USER/PASSWORD/FROM are set."
                )
            else:
                st.error(f"Notification status: {result['status']}")
        except ApiError as exc:
            st.error(str(exc))

st.divider()
section_header("Notification history", icon="🗂️")
try:
    notifications = api_client.list_notifications()
    if not notifications:
        empty_state("No notifications sent yet.", icon="🗂️")
    else:
        for n in notifications:
            with st.expander(f"[{n['id']}] To candidate #{n['candidate_id']} -- {n['subject']}"):
                st.markdown(status_badge(n["status"]), unsafe_allow_html=True)
                st.write(f"**Channel:** {n['channel']}")
                st.write(f"**Job ID:** {n['job_id'] or 'N/A'}")
                st.write(f"**Sent at:** {n['created_at']}")
                st.text(n["body"])
except ApiError as exc:
    st.error(str(exc))
