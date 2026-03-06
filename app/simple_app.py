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
    [data-testid="stSidebarNav"] {display: none;}
    /* Force chat message text to be black */
    .stTextArea textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
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
    st.header("🌱 Chat with Summarizer")
    st.markdown("Have a conversation with the AI. Ask questions, request summaries, or continue the discussion!")

    # Initialize chat history and flags in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "awaiting_response" not in st.session_state:
        st.session_state.awaiting_response = False

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                # Escape HTML and ensure black text
                safe_content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
                safe_content = safe_content.replace("\n", "<br>")
                st.markdown(f"""
                <div style='background-color: #e3f2fd; padding: 12px 15px; border-radius: 15px; margin: 8px 0; max-width: 80%; margin-left: auto;'>
                    <strong style='color: #1565c0;'>You</strong><br>
                    <span style='color: #000000;'>{safe_content}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Escape HTML characters and ensure black text
                safe_content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;")
                safe_content = safe_content.replace("\n", "<br>")
                st.markdown(f"""
                <div style='background-color: #f1f8e9; padding: 12px 15px; border-radius: 15px; margin: 8px 0; max-width: 80%;'>
                    <strong style='color: #558b2f;'>Assistant</strong><br>
                    <span style='color: #000000;'>{safe_content}</span>
                </div>
                """, unsafe_allow_html=True)

        # Handle streaming response if awaiting
        if st.session_state.awaiting_response:
            streaming_placeholder = st.empty()

            # Fetch the response
            try:
                # Build messages with conversation history
                messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for msg in st.session_state.chat_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                payload = {
                    "model": MODEL_NAME,
                    "messages": messages,
                    "max_tokens": 2048,
                    "temperature": 0.9,
                    "stream": True
                }
                headers = {"Content-Type": "application/json"}

                with requests.post(
                    urljoin(LLM_ENDPOINT, "/v1/chat/completions"),
                    json=payload,
                    headers=headers,
                    stream=True,
                    timeout=120
                ) as response:
                    response.raise_for_status()
                    assistant_response = ""

                    for line in response.iter_lines():
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data_str = line.removeprefix("data: ")
                                if data_str == "[DONE]":
                                    break

                                try:
                                    data = json.loads(data_str)
                                except json.JSONDecodeError:
                                    continue

                                delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
                                if delta:
                                    assistant_response += delta
                                    # Escape HTML and show in green bubble
                                    safe_content = assistant_response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", "<br>")
                                    streaming_placeholder.markdown(f"""
                                    <div style='background-color: #f1f8e9; padding: 12px 15px; border-radius: 15px; margin: 8px 0; max-width: 80%; min-height: 50px;'>
                                        <strong style='color: #558b2f;'>Assistant</strong><br>
                                        <span style='color: #000000;'>{safe_content}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                    # Save complete response
                    if assistant_response:
                        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
                    st.session_state.awaiting_response = False
                    st.rerun()

            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.session_state.awaiting_response = False
                # Remove the user message if there was an error
                if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
                    st.session_state.chat_history.pop()
                st.rerun()

    # Add some spacing
    st.markdown("---")

    # Input section at the bottom (always shown)
    MAX_TOKENS = 4096

    # Use session state for input clearing
    if "input_key" not in st.session_state:
        st.session_state.input_key = 0

    user_input = st.text_area("Your message:", height=100, key=f"chat_input_{st.session_state.input_key}", placeholder="Type your message here...")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Calculate tokens based on entire conversation + current message
        total_conversation = "\n".join([msg["content"] for msg in st.session_state.chat_history])
        total_text = total_conversation + "\n" + user_input
        approx_token_count = len(total_text) // 4
        tokens_left = MAX_TOKENS - approx_token_count - 50
        color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")
        st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left (conversation): {tokens_left}</span>", unsafe_allow_html=True)

    with col2:
        clear_chat = st.button("🗑️ Clear Chat", key="clear_chat")
        if clear_chat:
            st.session_state.chat_history = []
            st.session_state.awaiting_response = False
            st.session_state.input_key += 1
            st.rerun()

    with col3:
        send_button = st.button("Send 💬", key="send_message", type="primary")

    # Check if we need to start streaming (phase 2)
    if st.session_state.get("start_streaming", False):
        st.session_state.start_streaming = False
        st.session_state.awaiting_response = True
        st.rerun()

    if send_button and not st.session_state.get("awaiting_response", False):
        if not user_input.strip():
            st.warning("Please enter a message.")
        elif not LLM_ENDPOINT:
            st.error("LLM_ENDPOINT not configured in environment variables.")
        elif tokens_left <= 0:
            st.error("Your message is too long. Please shorten it to stay within the token limit.")
        else:
            # Phase 1: Add message and clear input
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.input_key += 1
            st.session_state.start_streaming = True
            # Rerun to show empty input
            st.rerun()
else:
    st.info("This feature is coming soon. Stay tuned!")
