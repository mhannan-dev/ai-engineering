# Streamlit UI application entry point conforming strictly to service-only layer imports.
"""Streamlit web application for the airline customer support agent.

Layering rule strictly obeyed: imports only from services/ and ui/components.
Never touches domain/ or infra/ directly.
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path when executed directly via 'streamlit run'
SRC_DIR = Path(__file__).resolve().parent.parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st

try:
    from airline_agent.services.agent_service import (
        execute_agent_loop,
        get_active_model_info,
        get_audit_records,
        get_system_prompt,
        sanitize_text,
    )
    from airline_agent.services.vision_service import parse_boarding_pass_vision
    from airline_agent.ui.components import render_chat_history, render_sidebar
except (ImportError, ValueError):
    from ..services.agent_service import (
        execute_agent_loop,
        get_active_model_info,
        get_audit_records,
        get_system_prompt,
        sanitize_text,
    )
    from ..services.vision_service import parse_boarding_pass_vision
    from .components import render_chat_history, render_sidebar



def main() -> None:
    """Streamlit application lifecycle and presentation controller."""
    st.set_page_config(page_title="Airline Support Agent", page_icon="✈️", layout="wide")

    # Fetch configuration & system prompt via service layer
    system_prompt = get_system_prompt()
    model_info = get_active_model_info()
    current_model = str(model_info.get("model") or "gpt-4o")
    base_url = model_info.get("base_url")

    # Initialize session state stores
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
    if "chat_view" not in st.session_state:
        st.session_state.chat_view = []

    # Callbacks
    def handle_image_uploaded(image_bytes: bytes) -> None:
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
                    reply = execute_agent_loop(st.session_state.messages, model_name=current_model)
                st.session_state.chat_view.append({"role": "assistant", "content": reply})
                st.success(f"PNR {pnr} loaded successfully!")
            except Exception as exc:
                st.error(f"Vision parse failed: {exc}")
                st.info(
                    "Tip: If using DeepSeek, image parsing requires an OpenAI-compatible vision model. "
                    "You can type the PNR directly in the chat below."
                )

    def handle_reset() -> None:
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.chat_view = []
        st.rerun()

    # 1. Render Sidebar
    audit_entries = get_audit_records()
    render_sidebar(
        current_model=current_model,
        base_url=base_url,
        audit_records=audit_entries,
        on_image_uploaded=handle_image_uploaded,
        on_reset=handle_reset,
    )

    # 2. Render Main Chat Area
    st.title("✈️ Multi-Modal Airline Support Agent")
    st.caption(
        f"Powered by {current_model} · Deterministic refund engine · 2FA-gated cancellations"
    )

    render_chat_history(st.session_state.chat_view)

    # 3. Handle User Chat Input
    user_input = st.chat_input("Ask in English or বাংলা… (e.g. 'Cancel ABC123, token 7788')")
    if user_input:
        clean_prompt = sanitize_text(user_input)
        st.session_state.chat_view.append({"role": "user", "content": clean_prompt})
        st.session_state.messages.append({"role": "user", "content": clean_prompt})

        with st.chat_message("user"):
            st.markdown(clean_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                reply = execute_agent_loop(st.session_state.messages, model_name=current_model)
            st.markdown(reply)

        st.session_state.chat_view.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
