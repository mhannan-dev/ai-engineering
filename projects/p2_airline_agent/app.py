"""
Airline Customer Support Agent - Streamlit Application
======================================================
Interactive web interface for bilingual airline support, boarding pass
image upload, and live audit inspection.
"""

from __future__ import annotations

import io
import json
from PIL import Image
import streamlit as st

try:
    from .agent import execute_agent_loop, sanitize_text
    from .config import DEFAULT_MODEL, OPENAI_BASE_URL, SYSTEM_PROMPT
    from .database import get_audit_log
    from .vision import parse_boarding_pass_vision
except ImportError:
    from agent import execute_agent_loop, sanitize_text
    from config import DEFAULT_MODEL, OPENAI_BASE_URL, SYSTEM_PROMPT
    from database import get_audit_log
    from vision import parse_boarding_pass_vision


def run_app():
    """Main Streamlit application lifecycle."""
    st.set_page_config(page_title="Airline Support Agent", page_icon="✈️", layout="wide")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if "chat_view" not in st.session_state:
        st.session_state.chat_view = []

    # ========================== SIDEBAR ==========================
    with st.sidebar:
        st.header("✈️ Airline Support")
        st.caption("Bilingual (বাংলা / English) multi-modal agent")

        st.markdown(f"**Current Model:** `{DEFAULT_MODEL}`")
        if OPENAI_BASE_URL:
            st.caption(f"Endpoint: `{OPENAI_BASE_URL}`")

        uploaded = st.file_uploader(
            "Upload boarding pass (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            help="Upload a digital boarding pass image to automatically extract your PNR",
        )
        if uploaded is not None:
            image_bytes = uploaded.getvalue()
            try:
                Image.open(io.BytesIO(image_bytes)).verify()
            except Exception:
                st.error("Invalid image format.")
            else:
                st.image(image_bytes, caption="Boarding pass", use_container_width=True)
                if st.button("🔍 Scan & Lookup", use_container_width=True):
                    with st.spinner("Extracting fields with vision…"):
                        try:
                            parsed = parse_boarding_pass_vision(image_bytes)
                            pnr = parsed.pnr
                            st.session_state.chat_view.append({
                                "role": "user",
                                "content": f"[Scanned boarding pass] PNR: {pnr}",
                            })
                            st.session_state.messages.append({
                                "role": "user",
                                "content": sanitize_text(
                                    f"My boarding pass PNR is {pnr}. Please show my flight details."
                                ),
                            })
                            with st.spinner("Checking flight details…"):
                                reply = execute_agent_loop(st.session_state.messages, model_name=DEFAULT_MODEL)
                            st.session_state.chat_view.append({"role": "assistant", "content": reply})
                            st.success(f"PNR {pnr} loaded successfully!")
                        except Exception as e:
                            st.error(f"Vision parse failed: {e}")
                            st.info("Tip: If using DeepSeek, image parsing requires an OpenAI-compatible vision model. You can type the PNR directly in the chat below.")

        st.divider()
        with st.expander("🔒 Live Audit Log"):
            audit_records = get_audit_log()
            if not audit_records:
                st.caption("No audit entries yet.")
            else:
                for entry in reversed(audit_records[-20:]):
                    st.code(json.dumps(entry, indent=2), language="json")

        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.chat_view = []
            st.rerun()

    # ========================== MAIN CHAT ==========================
    st.title("✈️ Multi-Modal Airline Support Agent")
    st.caption(f"Powered by {DEFAULT_MODEL} · Deterministic refund engine · 2FA-gated cancellations")

    for turn in st.session_state.chat_view:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    user_input = st.chat_input("Ask in English or বাংলা… (e.g. 'Cancel ABC123, token 7788')")

    if user_input:
        clean = sanitize_text(user_input)
        st.session_state.chat_view.append({"role": "user", "content": clean})
        st.session_state.messages.append({"role": "user", "content": clean})

        with st.chat_message("user"):
            st.markdown(clean)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = execute_agent_loop(st.session_state.messages, model_name=DEFAULT_MODEL)
            st.markdown(reply)

        st.session_state.chat_view.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    run_app()
