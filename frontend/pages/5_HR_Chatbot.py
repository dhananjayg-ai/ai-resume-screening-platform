"""Chat with the rule-based HR chatbot."""
import streamlit as st

from utils import api_client
from utils.api_client import ApiError
from utils.styling import apply_global_styles, page_header

st.set_page_config(page_title="HR Chatbot", page_icon="💬", layout="wide")
apply_global_styles()
page_header(
    "HR Chatbot",
    "Ask questions like 'top 3 candidates for job Data Analyst', 'how many resumes were "
    "uploaded today', or 'show candidates with Python skills'.",
    icon="💬",
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.write(message)

user_query = st.chat_input("Ask the HR chatbot a question...")

if user_query:
    st.session_state.chat_history.append(("user", user_query))
    with st.chat_message("user"):
        st.write(user_query)

    try:
        result = api_client.chatbot_query(user_query)
        response_text = result["response"]
    except ApiError as exc:
        response_text = f"Error reaching the chatbot backend: {exc}"

    st.session_state.chat_history.append(("assistant", response_text))
    with st.chat_message("assistant"):
        st.write(response_text)

if st.button("Clear chat history"):
    st.session_state.chat_history = []
    st.rerun()
