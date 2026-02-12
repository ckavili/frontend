import os
import requests
import json
import streamlit as st
from PIL import Image
from urllib.parse import urljoin

# Load environment variables
BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")

def submit_feedback(input_text, response_text, rating, feature="summarize"):
    """Submit feedback to the backend."""
    try:
        payload = {
            "input_text": input_text,
            "response_text": response_text,
            "rating": rating,
            "feature": feature,
        }
        resp = requests.post(
            urljoin(BACKEND_ENDPOINT, "/feedback"),
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def submit_ab_feedback(input_text, response_a, response_b, preference, prompt_mapping, feature="summarize"):
    """Submit A/B comparison feedback to the backend."""
    try:
        payload = {
            "input_text": input_text,
            "response_a": response_a,
            "response_b": response_b,
            "preference": preference,
            "prompt_mapping": prompt_mapping,
            "feature": feature,
        }
        resp = requests.post(
            urljoin(BACKEND_ENDPOINT, "/feedback/ab"),
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

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
print(feature_flags)

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

if feature_flags.get("student-assistant", False):
    feature_options.append("Student Assistant")
else:
    feature_options.append("Student Assistant (coming soon)")

if feature_flags.get("socratic-tutor", False):
    feature_options.append("Socratic Tutor")
else:
    feature_options.append("Socratic Tutor (coming soon)")

feature = st.sidebar.radio(
    "What do you want to do:",
    feature_options,
    index=0
)

# Main view depending on feature
st.markdown("""
    <style>
    * {opacity:100% !important;}
    [data-testid="stSidebarNav"] {display: none;}
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

        ab_enabled = feature_flags.get("ab_testing", False)

        if st.button("Summarize 🌿"):
            if not user_input.strip():
                st.warning("Please enter some text to summarize.")
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your text is too long. Please shorten it to stay within the token limit.")
            elif ab_enabled:
                # A/B mode: show two columns with both prompts
                with st.spinner("Running both prompts..."):
                    try:
                        payload = {"prompt": user_input}
                        headers = {"Content-Type": "application/json"}

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/summarize/ab"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Response A**")
                                box_a = st.empty()
                            with col_b:
                                st.markdown("**Response B**")
                                box_b = st.empty()

                            text_a = ""
                            text_b = ""
                            ab_mapping = {}

                            for line in response.iter_lines():
                                if line:
                                    line = line.decode("utf-8")
                                    if line.startswith("data: "):
                                        data_str = line.removeprefix("data: ")
                                        if data_str == "[DONE]":
                                            break
                                        data = json.loads(data_str)

                                        if data.get("type") == "ab_config":
                                            ab_mapping = data.get("mapping", {})
                                            continue

                                        variant = data.get("variant")
                                        delta = data.get("delta", "")
                                        if variant == "a" and delta:
                                            text_a += delta
                                            box_a.text_area("A", text_a, height=200, key=f"ab_a_{len(text_a)}")
                                        elif variant == "b" and delta:
                                            text_b += delta
                                            box_b.text_area("B", text_b, height=200, key=f"ab_b_{len(text_b)}")

                            # Save to session state
                            if text_a and text_b:
                                st.session_state["ab_response_a"] = text_a
                                st.session_state["ab_response_b"] = text_b
                                st.session_state["ab_mapping"] = ab_mapping
                                st.session_state["ab_input"] = user_input
                                st.session_state.pop("ab_feedback_sent", None)

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")
            else:
                # Standard single-prompt mode
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
                                        # Handle shield violation
                                        if data.get("type") == "shield_violation":
                                            summary_box.warning(f"🛡️ {data.get('message', 'Content blocked by safety shields')}")
                                            break
                                        # Handle error
                                        if data.get("error"):
                                            summary_box.error(f"Error: {data.get('error')}")
                                            break
                                        delta = data.get("delta")
                                        if delta:
                                            summary += delta
                                            summary_box.text_area("Summary", summary, height=200)

                            # Save to session state for feedback buttons (survive Streamlit reruns)
                            if summary:
                                st.session_state["last_summary"] = summary
                                st.session_state["last_summary_input"] = user_input
                                st.session_state.pop("summary_feedback_sent", None)

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

        # A/B preference buttons
        if ab_enabled and st.session_state.get("ab_response_a") and st.session_state.get("ab_response_b"):
            if "ab_feedback_sent" not in st.session_state:
                st.markdown("**Which response is better?**")
                pref_col1, pref_col2 = st.columns(2)
                with pref_col1:
                    if st.button("A is better", key="ab_pref_a"):
                        result = submit_ab_feedback(
                            st.session_state["ab_input"],
                            st.session_state["ab_response_a"],
                            st.session_state["ab_response_b"],
                            "a",
                            st.session_state["ab_mapping"],
                        )
                        if "error" not in result:
                            st.session_state["ab_feedback_sent"] = "a"
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")
                with pref_col2:
                    if st.button("B is better", key="ab_pref_b"):
                        result = submit_ab_feedback(
                            st.session_state["ab_input"],
                            st.session_state["ab_response_a"],
                            st.session_state["ab_response_b"],
                            "b",
                            st.session_state["ab_mapping"],
                        )
                        if "error" not in result:
                            st.session_state["ab_feedback_sent"] = "b"
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")
            else:
                pref = st.session_state["ab_feedback_sent"]
                st.success(f"Thanks! You preferred Response {pref.upper()}.")

        # Show feedback buttons if a summary exists and feedback feature is enabled (standard mode only)
        if not ab_enabled and st.session_state.get("last_summary") and feature_flags.get("feedback", False):
            st.markdown("---")
            st.markdown("**Was this summary helpful?**")

            if "summary_feedback_sent" not in st.session_state:
                col1, col2, col3 = st.columns([1, 1, 6])
                with col1:
                    if st.button("👍", key="thumbs_up_sum"):
                        result = submit_feedback(
                            st.session_state["last_summary_input"],
                            st.session_state["last_summary"],
                            "thumbs_up",
                        )
                        if "error" not in result:
                            st.session_state["summary_feedback_sent"] = "thumbs_up"
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")
                with col2:
                    if st.button("👎", key="thumbs_down_sum"):
                        result = submit_feedback(
                            st.session_state["last_summary_input"],
                            st.session_state["last_summary"],
                            "thumbs_down",
                        )
                        if "error" not in result:
                            st.session_state["summary_feedback_sent"] = "thumbs_down"
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")
            else:
                rating = st.session_state["summary_feedback_sent"]
                if rating == "thumbs_up":
                    st.success("Thanks for the positive feedback!")
                else:
                    st.info("Thanks for the feedback! We'll use it to improve.")

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

elif feature == "Student Assistant":
    if not feature_flags.get("student-assistant", False):
        st.info("This feature is coming soon. Stay tuned!")
    else:
        st.header("🎓 Student Assistant")
        st.markdown("Ask me anything! I can search the knowledge base, find professors, and help schedule meetings.")

        MAX_TOKENS = 4096
        user_input = st.text_area("Your question:", height=150, key="student_assistant_text")
        approx_token_count = len(user_input) // 4
        tokens_left = MAX_TOKENS - approx_token_count - 50

        color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")
        st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left: {tokens_left}</span>", unsafe_allow_html=True)
        if st.button("🔄 Calculate tokens left", key="calc_tokens_student_assistant", help="Calculate tokens"):
            st.rerun()

        if st.button("Ask 🎓"):
            if not user_input.strip():
                st.warning("Please enter a question.")
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your question is too long. Please shorten it to stay within the token limit.")
            else:
                with st.spinner("Thinking..."):
                    try:
                        payload = {"prompt": user_input}
                        headers = {"Content-Type": "application/json"}

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/student-assistant"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()

                            # Create containers for different sections
                            tool_calls_section = st.expander("🔧 Tool Calls & Actions", expanded=True)
                            answer_section = st.container()

                            tool_calls_list = []  # Track individual tool call entries
                            answer = ""
                            answer_box = None
                            in_final_answer = False

                            for line in response.iter_lines():
                                if line:
                                    line = line.decode("utf-8")
                                    if line.startswith("data: "):
                                        data_str = line.removeprefix("data: ")
                                        if data_str == "[DONE]":
                                            break

                                        data = json.loads(data_str)
                                        event_type = data.get("type")

                                        print(data)

                                        if event_type == "tool_call":
                                            to_add = f"🔧 **Calling tool:** `{data.get('name')}`\n   Args: `{json.dumps(data.get('args'))}`\n"
                                            tool_calls_section.markdown(to_add)

                                        elif event_type == "mcp_call":
                                            mcp_text = f"🔧 **MCP Tool:** `{data.get('name')}` (MCP server: {data.get('server_label')})\n   Args: `{json.dumps(data.get('arguments'))}`\n"
                                            if data.get('output'):
                                                output = str(data.get('output'))
                                                mcp_text += f"   Output: {output}\n"
                                            elif data.get('error'):
                                                mcp_text += f"   ⚠️ Error: {data.get('error')}\n"
                                            to_add = mcp_text
                                            tool_calls_section.markdown(to_add)

                                        elif event_type == "tool_result":
                                            content = data.get('content', '')
                                            tool_calls_section.markdown(f"📦 **Tool result** (`{data.get('name')}`):")
                                            # Use code block without height limit
                                            tool_calls_section.code(content, language=None, wrap_lines=True)

                                        elif event_type == "final_answer":
                                            in_final_answer = True
                                            answer_section.success("💡 Final Response:")
                                            answer_box = answer_section.empty()

                                        elif data.get("delta") and in_final_answer:
                                            answer += data.get("delta")
                                            if answer_box:
                                                # Calculate dynamic height based on content
                                                line_count = answer.count('\n') + 1
                                                estimated_lines = max(line_count, len(answer) // 80)  # Assume ~80 chars per line
                                                dynamic_height = min(max(estimated_lines * 25, 150), 600)  # Between 150 and 600px
                                                answer_box.markdown(f"**Response:**\n\n{answer}")

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

elif feature == "Socratic Tutor":
    if not feature_flags.get("socratic-tutor", False):
        st.info("This feature is coming soon. Stay tuned!")
    else:
        st.header("🎓 Socratic Tutor")
        st.markdown("Ask me your question and I'll guide you to discover the answer through thoughtful questioning!")

        # Token count and limit (approximate: 1 token ≈ 4 characters in English)
        MAX_TOKENS = 1500  # Matching backend max_tokens
        user_input = st.text_area("What would you like to learn about?", height=300, key="socratic_text")
        approx_token_count = len(user_input) // 4
        tokens_left = MAX_TOKENS - approx_token_count - 50  # buffer for response

        # Token display with calculate button
        color = "red" if tokens_left <= 0 else ("orange" if tokens_left < 100 else "green")

        st.markdown(f"<span style='color:{color}; font-size: 0.9em;'>🧮 Tokens left: {tokens_left}</span>", unsafe_allow_html=True)
        if st.button("🔄 Calculate tokens left", key="calc_tokens_socratic", help="Calculate tokens"):
            st.rerun()

        if st.button("Ask the Tutor 🎓"):
            if not user_input.strip():
                st.warning("Please enter your question to get started.")
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your text is too long. Please shorten it to stay within the token limit.")
            else:
                with st.spinner("Your Socratic tutor is thinking..."):
                    try:
                        payload = {
                            "prompt": user_input
                        }
                        headers = {
                            "Content-Type": "application/json",
                        }

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/socratic-tutor"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()
                            tutor_response = ""
                            st.success("Here's what your tutor has to say:")
                            response_box = st.empty()

                            for line in response.iter_lines():
                                if line:
                                    line = line.decode("utf-8")
                                    if line.startswith("data: "):
                                        data_str = line.removeprefix("data: ")
                                        if data_str == "[DONE]":
                                            break
                                        data = json.loads(data_str)
                                        # Handle error
                                        if data.get("error"):
                                            response_box.error(f"Error: {data.get('error')}")
                                            break
                                        delta = data.get("delta")
                                        if delta:
                                            tutor_response += delta
                                            response_box.text_area("Tutor Response", tutor_response, height=200)

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")

else:
    st.info("This feature is coming soon. Stay tuned!")