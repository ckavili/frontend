import os
import requests
import json
import streamlit as st
from PIL import Image
from urllib.parse import urljoin

# Load environment variables
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")

# Cache feature flags to avoid repeated requests
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_feature_flags():
    """Fetch feature flags from backend"""
    try:
        response = requests.get(urljoin(BACKEND_ENDPOINT, "/feature-flags"), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch feature flags: {e}")
        # Return default flags if backend is unavailable
        return {}

# Page setup
st.set_page_config(
    page_title="Canopy - Educational Assistant",
    page_icon="🌿",
    layout="wide",
)

# Sidebar navigation
logo_path = "logo.png"
logo = Image.open(logo_path)
st.sidebar.image(logo, use_container_width=True)
st.sidebar.title("Canopy 🌿")

# Get feature flags from backend
feature_flags = get_feature_flags()

# Build feature options based on feature flags
feature_options = []
if feature_flags.get("summarization", True):
    feature_options.append("Summarization")
else:
    feature_options.append("Summarization (coming soon)")

if feature_flags.get("information-search", False):
    feature_options.append("Information Search")
else:
    feature_options.append("Information Search (coming soon)")

if feature_flags.get("content-creation", False):
    feature_options.append("Content Creation")
else:
    feature_options.append("Content Creation (coming soon)")

if feature_flags.get("assignment-scoring", False):
    feature_options.append("Assignment Scoring")
else:
    feature_options.append("Assignment Scoring (coming soon)")

feature = st.sidebar.radio(
    "What do you want to do:",
    feature_options,
    index=0
)

# Main view depending on feature
st.markdown("""
    <style>
    * {opacity:100% !important;}
    </style>
    """, unsafe_allow_html=True)
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='color: #2e8b57;'>Canopy</h1>
        <p style='font-size: 1.2em;'>Your leafy smart companion for education ✨</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

if feature == "Summarization":
    if not feature_flags.get("summarization", True):
        st.info("This feature is coming soon. Stay tuned!")
    else:
        st.header("🌱 Summarize My Text")

        # Token count and limit (approximate: 1 token ≈ 4 characters in English)
        MAX_TOKENS = 4096  # Matching backend max_tokens
        user_input = st.text_area("Paste your text here:", height=300, key="user_text")
        approx_token_count = len(user_input) // 4
        tokens_left = MAX_TOKENS - approx_token_count - 50  # buffer for response

        # Token display with calculate button
        color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")

        st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left: {tokens_left}</span>", unsafe_allow_html=True)
        if st.button("🔄 Calculate tokens left", key="calc_tokens_sum", help="Calculate tokens"):
            st.rerun()

        if st.button("Summarize 🌿"):
            if not user_input.strip():
                st.warning("Please enter some text to summarize.")
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your text is too long. Please shorten it to stay within the token limit.")
            else:
                with st.spinner("Talking to the forest spirits..."):
                    try:
                        payload = {
                            "prompt": user_input
                        }
                        headers = {
                            "Content-Type": "application/json",
                        }

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/summarize"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()
                            summary = ""
                            st.success("Here's your summary:")
                            summary_box = st.empty()

                            for line in response.iter_lines():
                                if line:
                                    line = line.decode("utf-8")
                                    if line.startswith("data: "):
                                        data_str = line.removeprefix("data: ")
                                        if data_str == "[DONE]":
                                            break
                                        data = json.loads(data_str)
                                        delta = data.get("delta")
                                        if delta:
                                            summary += delta
                                            summary_box.text_area("Summary", summary, height=200)

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

elif feature == "Information Search":
    if not feature_flags.get("information-search", False):
        st.info("This feature is coming soon. Stay tuned!")
    else:
        st.header("🔍 Information Search")

        # Token count and limit
        MAX_TOKENS = 4096
        user_input = st.text_area("Ask your question:", height=150, key="rag_text")
        approx_token_count = len(user_input) // 4
        tokens_left = MAX_TOKENS - approx_token_count - 50

        # Token display with calculate button
        color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")
        st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left: {tokens_left}</span>", unsafe_allow_html=True)
        if st.button("🔄 Calculate tokens left", key="calc_tokens_rag", help="Calculate tokens"):
            st.rerun()

        if st.button("Ask Our Internal Documents 🔍"):
            if not user_input.strip():
                st.warning("Please enter a question.")
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your question is too long. Please shorten it to stay within the token limit.")
            else:
                with st.spinner("Searching through knowledge base..."):
                    try:
                        payload = {
                            "prompt": user_input
                        }
                        headers = {
                            "Content-Type": "application/json",
                        }

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/information-search"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()
                            answer = ""
                            st.success("Here's your Information Search answer:")
                            answer_box = st.empty()

                            for line in response.iter_lines():
                                if line:
                                    line = line.decode("utf-8")
                                    if line.startswith("data: "):
                                        data_str = line.removeprefix("data: ")
                                        if data_str == "[DONE]":
                                            break
                                        data = json.loads(data_str)
                                        delta = data.get("delta")
                                        if delta:
                                            answer += delta
                                            answer_box.text_area("Information Search Answer", answer, height=200)

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

elif feature in ["Content Creation", "Assignment Scoring"] or "coming soon" in feature:
    st.info("This feature is coming soon. Stay tuned!")
else:
    st.info("This feature is coming soon. Stay tuned!")