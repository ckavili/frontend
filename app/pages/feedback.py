import os
import requests
import streamlit as st
from urllib.parse import urljoin

BACKEND_ENDPOINT = os.getenv("BACKEND_ENDPOINT", "http://localhost:8000")

st.set_page_config(
    page_title="Canopy - Feedback Dashboard",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
    <div style='text-align: center;'>
        <h1 style='color: #2e8b57;'>Canopy - Feedback Dashboard</h1>
        <p style='font-size: 1.2em;'>Review user feedback and export evaluation datasets 📊</p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Check if feedback feature is enabled
try:
    flags_resp = requests.get(urljoin(BACKEND_ENDPOINT, "/feature-flags"), timeout=10)
    flags_resp.raise_for_status()
    feature_flags = flags_resp.json()
except Exception:
    feature_flags = {}

if not feature_flags.get("feedback", False):
    st.warning("The feedback feature is not enabled. Enable it in the backend configuration.")
    st.stop()

# Fetch feedback data
try:
    feedback_resp = requests.get(urljoin(BACKEND_ENDPOINT, "/feedback"), timeout=10)
    feedback_resp.raise_for_status()
    feedback_data = feedback_resp.json()
except Exception as e:
    st.error(f"Failed to load feedback data: {e}")
    st.stop()

total = feedback_data.get("total", 0)
entries = feedback_data.get("feedback", [])

thumbs_up = [e for e in entries if e["rating"] == "thumbs_up"]
thumbs_down = [e for e in entries if e["rating"] == "thumbs_down"]

# Metrics row
col1, col2, col3 = st.columns(3)
col1.metric("Total Feedback", total)
col2.metric("👍 Positive", len(thumbs_up))
col3.metric("👎 Negative", len(thumbs_down))

st.markdown("---")

if not entries:
    st.info("No feedback collected yet. Use the Summarization feature and rate some responses!")
    st.stop()

# Filter
filter_option = st.radio(
    "Filter by:",
    ["All", "Positive only", "Negative only"],
    horizontal=True,
    key="feedback_filter",
)

if filter_option == "Positive only":
    display_entries = thumbs_up
elif filter_option == "Negative only":
    display_entries = thumbs_down
else:
    display_entries = entries

# Display feedback entries
if display_entries:
    for e in display_entries:
        rating_icon = "👍" if e["rating"] == "thumbs_up" else "👎"
        with st.expander(f"#{e['id']} {rating_icon} — {e['timestamp'][:19]}", expanded=False):
            st.markdown("**Prompt:**")
            st.text(e["input_text"])
            st.markdown("**Response:**")
            st.text(e["response_text"])
else:
    st.info("No feedback entries match the selected filter.")

# Export section
if thumbs_down:
    st.markdown("---")
    st.subheader("Export for Evaluation")
    st.markdown(
        f"**{len(thumbs_down)}** negative feedback entries can be exported as an evaluation dataset. "
        "Fill in the `expected_answer` field to create regression test cases."
    )
    try:
        export_resp = requests.get(urljoin(BACKEND_ENDPOINT, "/feedback/export"), timeout=10)
        export_resp.raise_for_status()
        st.download_button(
            label="Download feedback-eval-dataset.yaml",
            data=export_resp.text,
            file_name="feedback-eval-dataset.yaml",
            mime="application/x-yaml",
            key="download_eval_yaml",
        )
    except Exception as e:
        st.error(f"Failed to load export data: {e}")
