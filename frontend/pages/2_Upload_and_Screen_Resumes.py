"""Upload resumes (PDF/DOCX) and see extracted fields, quality feedback, and
duplicate warnings."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import apply_global_styles, empty_state, page_header, score_badge, section_header

st.set_page_config(page_title="Upload & Screen Resumes", page_icon="📄", layout="wide")
apply_global_styles()
page_header(
    "Upload & Screen Resumes",
    "Upload a resume to extract fields, check quality, detect duplicates and translate non-English text.",
    icon="📄",
)

uploaded_file = st.file_uploader("Upload a resume (PDF or DOCX)", type=["pdf", "docx"])

if uploaded_file is not None:
    if st.button("Upload & Screen"):
        with st.spinner("Parsing resume, extracting fields, checking for duplicates..."):
            try:
                result = api_client.upload_resume(
                    file_bytes=uploaded_file.getvalue(),
                    filename=uploaded_file.name,
                    content_type=uploaded_file.type or "application/octet-stream",
                )
            except ApiError as exc:
                st.error(str(exc))
                result = None

        if result:
            candidate = result["candidate"]

            if result["is_possible_duplicate"]:
                st.warning(
                    f"This resume looks like a possible duplicate of candidate "
                    f"#{result['duplicate_candidate_id']} "
                    f"(similarity: {result['duplicate_similarity']:.0%})."
                )
            if result["ocr_used"]:
                st.info("This looked like a scanned PDF -- OCR was used to extract text.")
            if result["translation_used"]:
                st.info(
                    f"Resume detected as non-English (language: {candidate['detected_language']}) "
                    "and was translated to English before analysis."
                )

            st.success(f"Candidate screened successfully! Candidate ID: {candidate['id']}")

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Extracted details")
                st.write(f"**Name:** {candidate['name'] or 'Not detected'}")
                st.write(f"**Email:** {candidate['email'] or 'Not detected'}")
                st.write(f"**Phone:** {candidate['phone'] or 'Not detected'}")
                st.write(f"**Detected language:** {candidate['detected_language']}")
                st.write(f"**Experience:** {candidate['experience_years']} years")
                st.write(f"**Skills:** {', '.join(candidate['skills']) or 'None detected'}")
                st.write(f"**Education:** {', '.join(candidate['education']) or 'None detected'}")
                st.write(f"**Certifications:** {', '.join(candidate['certifications']) or 'None detected'}")

            with col2:
                st.subheader("Resume quality feedback")
                st.markdown(score_badge(candidate["quality_score"]), unsafe_allow_html=True)
                for suggestion in candidate["quality_feedback"]:
                    st.write(f"- {suggestion}")

st.divider()
section_header("All screened candidates", icon="🗂️")
try:
    candidates = api_client.list_candidates()
    if not candidates:
        empty_state("No candidates screened yet -- upload a resume above to get started.", icon="🗂️")
    else:
        for c in candidates:
            label = f"[{c['id']}] {c['name'] or c['email'] or c['resume_filename']}"
            if c["duplicate_of_candidate_id"]:
                label += f"  (possible duplicate of #{c['duplicate_of_candidate_id']})"
            with st.expander(label):
                st.write(f"**Email:** {c['email'] or 'N/A'} | **Phone:** {c['phone'] or 'N/A'}")
                st.write(f"**Skills:** {', '.join(c['skills']) or 'None'}")
                st.markdown(
                    f"**Quality score:** {score_badge(c['quality_score'])}", unsafe_allow_html=True
                )
                if st.button("Re-check duplicate", key=f"dup_{c['id']}"):
                    try:
                        dup = api_client.check_duplicate(c["id"])
                        if dup["is_duplicate"]:
                            st.warning(
                                f"Likely duplicate of candidate #{dup['duplicate_of_candidate_id']} "
                                f"(similarity {dup['similarity']:.0%})"
                            )
                        else:
                            st.success("No duplicate detected.")
                    except ApiError as exc:
                        st.error(str(exc))
except ApiError as exc:
    st.error(str(exc))
