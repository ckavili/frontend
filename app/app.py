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
@st.cache_data(ttl=30)  # Cache for 30 seconds (checks more frequently)
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
st.sidebar.image(logo, width='stretch')
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
    if not feature_flags.get("summarization", True):
        st.info("This feature is coming soon. Stay tuned!")
    else:
        st.header("🌱 Chat with Summarizer")
        st.markdown("Have a conversation with the AI. Ask questions, request summaries, or continue the discussion!")

        # Initialize chat history and flags in session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "awaiting_response" not in st.session_state:
            st.session_state.awaiting_response = False

        # Initialize A/B testing state
        if "ab_response_a" not in st.session_state:
            st.session_state.ab_response_a = None
        if "ab_response_b" not in st.session_state:
            st.session_state.ab_response_b = None
        if "ab_mapping" not in st.session_state:
            st.session_state.ab_mapping = None
        if "ab_input" not in st.session_state:
            st.session_state.ab_input = None

        # Initialize feedback state
        if "chat_feedback" not in st.session_state:
            st.session_state.chat_feedback = {}

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

                    # Show feedback buttons under each assistant message if feedback is enabled
                    if feature_flags.get("feedback", False):
                        feedback_key = f"feedback_{i}"
                        if feedback_key in st.session_state.chat_feedback:
                            rating = st.session_state.chat_feedback[feedback_key]
                            st.markdown(f"<span style='font-size: 0.8em; color: #888;'>{'👍 Thanks for the feedback!' if rating == 'thumbs_up' else '👎 Thanks for the feedback!'}</span>", unsafe_allow_html=True)
                        else:
                            # Find the corresponding user message (previous message)
                            user_msg = st.session_state.chat_history[i - 1]["content"] if i > 0 else ""
                            col_up, col_down, _ = st.columns([1, 1, 10])
                            with col_up:
                                if st.button("👍", key=f"up_{i}"):
                                    result = submit_feedback(user_msg, msg["content"], "thumbs_up")
                                    if "error" not in result:
                                        st.session_state.chat_feedback[feedback_key] = "thumbs_up"
                                        st.rerun()
                            with col_down:
                                if st.button("👎", key=f"down_{i}"):
                                    result = submit_feedback(user_msg, msg["content"], "thumbs_down")
                                    if "error" not in result:
                                        st.session_state.chat_feedback[feedback_key] = "thumbs_down"
                                        st.rerun()

            # Show completed A/B responses and preference buttons (before streaming starts)
            if (feature_flags.get("ab_testing", False)
                    and st.session_state.get("ab_response_a")
                    and st.session_state.get("ab_response_b")):
                col_a, col_b = st.columns(2)
                with col_a:
                    safe_a = st.session_state.ab_response_a.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", "<br>")
                    st.markdown(f"""
                    <div style='background-color: #f1f8e9; padding: 12px 15px; border-radius: 15px; margin: 8px 0;'>
                        <strong style='color: #558b2f;'>Response A</strong><br>
                        <span style='color: #000000;'>{safe_a}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("A is better", key="ab_pref_a"):
                        result = submit_ab_feedback(
                            st.session_state["ab_input"],
                            st.session_state["ab_response_a"],
                            st.session_state["ab_response_b"],
                            "a",
                            st.session_state["ab_mapping"],
                        )
                        if "error" not in result:
                            st.session_state.chat_history.append({"role": "assistant", "content": st.session_state["ab_response_a"]})
                            st.session_state.ab_response_a = None
                            st.session_state.ab_response_b = None
                            st.session_state.ab_mapping = None
                            st.session_state.ab_input = None
                            st.toast("Thanks! Response A added to the conversation.")
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")
                with col_b:
                    safe_b = st.session_state.ab_response_b.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", "<br>")
                    st.markdown(f"""
                    <div style='background-color: #e8f4f8; padding: 12px 15px; border-radius: 15px; margin: 8px 0;'>
                        <strong style='color: #1e88e5;'>Response B</strong><br>
                        <span style='color: #000000;'>{safe_b}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("B is better", key="ab_pref_b"):
                        result = submit_ab_feedback(
                            st.session_state["ab_input"],
                            st.session_state["ab_response_a"],
                            st.session_state["ab_response_b"],
                            "b",
                            st.session_state["ab_mapping"],
                        )
                        if "error" not in result:
                            st.session_state.chat_history.append({"role": "assistant", "content": st.session_state["ab_response_b"]})
                            st.session_state.ab_response_a = None
                            st.session_state.ab_response_b = None
                            st.session_state.ab_mapping = None
                            st.session_state.ab_input = None
                            st.toast("Thanks! Response B added to the conversation.")
                            st.rerun()
                        else:
                            st.error(f"Failed to send feedback: {result['error']}")

            # Handle streaming response if awaiting
            if st.session_state.awaiting_response:
                if feature_flags.get("ab_testing", False):
                    # A/B mode: stream two responses side by side from /summarize/ab
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown("**Response A**")
                        placeholder_a = st.empty()
                    with col_b:
                        st.markdown("**Response B**")
                        placeholder_b = st.empty()

                    try:
                        last_user_msg = next(
                            (msg["content"] for msg in reversed(st.session_state.chat_history) if msg["role"] == "user"),
                            ""
                        )
                        payload = {"prompt": last_user_msg}
                        headers = {"Content-Type": "application/json"}

                        response_a = ""
                        response_b = ""
                        ab_mapping = {}

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/summarize/ab"),
                            json=payload,
                            headers=headers,
                            stream=True,
                            timeout=120
                        ) as response:
                            response.raise_for_status()

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

                                        if data.get("type") == "ab_config":
                                            ab_mapping = data.get("mapping", {})
                                            continue

                                        if data.get("error"):
                                            st.error(f"Error in response {data.get('variant', '').upper()}: {data.get('error')}")
                                            continue

                                        variant = data.get("variant")
                                        delta = data.get("delta")

                                        if variant == "a" and delta:
                                            response_a += delta
                                            safe_a = response_a.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", "<br>")
                                            placeholder_a.markdown(f"""
                                            <div style='background-color: #f1f8e9; padding: 12px 15px; border-radius: 15px; margin: 8px 0; min-height: 50px;'>
                                                <strong style='color: #558b2f;'>Response A</strong><br>
                                                <span style='color: #000000;'>{safe_a}</span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        elif variant == "b" and delta:
                                            response_b += delta
                                            safe_b = response_b.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;").replace("\n", "<br>")
                                            placeholder_b.markdown(f"""
                                            <div style='background-color: #e8f4f8; padding: 12px 15px; border-radius: 15px; margin: 8px 0; min-height: 50px;'>
                                                <strong style='color: #1e88e5;'>Response B</strong><br>
                                                <span style='color: #000000;'>{safe_b}</span>
                                            </div>
                                            """, unsafe_allow_html=True)

                        if response_a or response_b:
                            st.session_state.ab_response_a = response_a
                            st.session_state.ab_response_b = response_b
                            st.session_state.ab_mapping = ab_mapping
                            st.session_state.ab_input = last_user_msg
                        st.session_state.awaiting_response = False
                        st.rerun()

                    except Exception as e:
                        st.error(f"Something went wrong: {e}")
                        st.session_state.awaiting_response = False
                        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
                            st.session_state.chat_history.pop()
                        st.rerun()

                else:
                    streaming_placeholder = st.empty()

                    # Fetch the response
                    try:
                        messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.chat_history]
                        payload = {"messages": messages}
                        headers = {"Content-Type": "application/json"}

                        with requests.post(
                            urljoin(BACKEND_ENDPOINT, "/summarize/chat"),
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

                                        if data.get("type") == "shield_violation":
                                            assistant_response = f"🛡️ {data.get('message', 'Content blocked by safety shields')}"
                                            break

                                        if data.get("error"):
                                            assistant_response = f"Error: {data.get('error')}"
                                            break

                                        delta = data.get("delta")
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
                st.session_state.ab_response_a = None
                st.session_state.ab_response_b = None
                st.session_state.ab_mapping = None
                st.session_state.ab_input = None
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
            elif not BACKEND_ENDPOINT:
                st.error("BACKEND_ENDPOINT not configured in environment variables.")
            elif tokens_left <= 0:
                st.error("Your message is too long. Please shorten it to stay within the token limit.")
            else:
                # If an A/B response is pending and user didn't choose, default to A silently
                if feature_flags.get("ab_testing", False) and st.session_state.get("ab_response_a"):
                    st.session_state.chat_history.append({"role": "assistant", "content": st.session_state["ab_response_a"]})
                    st.session_state.ab_response_a = None
                    st.session_state.ab_response_b = None
                    st.session_state.ab_mapping = None
                    st.session_state.ab_input = None
                # Phase 1: Add message and clear input
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.input_key += 1
                st.session_state.start_streaming = True
                # Rerun to show empty input
                st.rerun()


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