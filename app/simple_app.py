import os
import requests
import streamlit as st
from PIL import Image
import json
from urllib.parse import urljoin

# Load environment variables
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "Summarize this text for me.")
MODEL_NAME = os.getenv("MODEL_NAME", "tinyllama")



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
feature = st.sidebar.radio(
    "What do you want to do:",
    ["Summarization", "Information Search (coming soon)", "Student Assistant (coming soon)", "Socratic Tutor (coming soon)"],
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
    st.header("🌱 Summarize My Text")

    # Token count and limit (approximate: 1 token ≈ 4 characters in English)
    MAX_TOKENS = 2048
    system_token_est = len(SYSTEM_PROMPT) // 4

    user_input = st.text_area("Paste your text here:", height=300, key="user_text")
    approx_token_count = len(user_input) // 4
    tokens_left = MAX_TOKENS - approx_token_count - system_token_est - 50  # buffer for response

    color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")
    st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left: {tokens_left}</span>", unsafe_allow_html=True)
    if st.button("🔄 Calculate tokens left", key="calc_tokens_sum", help="Calculate tokens"):
        st.rerun()

    if st.button("Summarize 🌿"):
        if not user_input.strip():
            st.warning("Please enter some text to summarize.")
        elif not LLM_ENDPOINT:
            st.error("LLM_ENDPOINT not configured in environment variables.")
        elif tokens_left <= 0:
            st.error("Your text is too long. Please shorten it to stay within the token limit.")
        else:
            with st.spinner("Talking to the forest spirits..."):
                try:
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ]

                    payload = {
                        "model": MODEL_NAME,
                        "messages": messages,
                        "max_tokens": tokens_left,
                        "temperature": 0.9,
                        "stream": True
                    }
                    headers = {
                        "Content-Type": "application/json",
                    }

                    with requests.post(urljoin(LLM_ENDPOINT, "/v1/chat/completions"), json=payload, headers=headers, stream=True, timeout=120) as response:
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
                                    delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                    if delta:
                                        summary += delta
                                        summary_box.text_area("Summary", summary, height=200)

                except Exception as e:
                    st.error(f"Something went wrong: {e}")
else:
    st.info("This feature is coming soon. Stay tuned!")
