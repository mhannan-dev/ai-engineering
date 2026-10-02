# Streamlit presentation components for sidebar, chat, and audit viewers.
"""Reusable visual UI components for Streamlit interface.

Does not import domain models or infra clients directly.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List
import streamlit as st


def render_sidebar(
    current_model: str,
    base_url: str | None,
    audit_records: List[Dict[str, Any]],
    on_image_uploaded: Callable[[bytes], None],
    on_reset: Callable[[], None],
) -> None:
    """Render the configuration, image upload, and audit inspection sidebar.
    
    Args:
        current_model: Name of active LLM model.
        base_url: Optional base endpoint URL string.
        audit_records: List of audit entry dictionaries.
        on_image_uploaded: Callback invoked with uploaded raw image bytes.
        on_reset: Callback invoked to reset conversation state.
    """
    with st.sidebar:
        st.header("✈️ Airline Support")
        st.caption("Bilingual (বাংলা / English) multi-modal agent")

        st.markdown(f"**Current Model:** `{current_model}`")
        if base_url:
            st.caption(f"Endpoint: `{base_url}`")

        uploaded = st.file_uploader(
            "Upload boarding pass (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
            help="Upload a digital boarding pass image to automatically extract your PNR",
        )
        if uploaded is not None:
            image_bytes = uploaded.getvalue()
            st.image(image_bytes, caption="Boarding pass preview", use_container_width=True)
            if st.button("🔍 Scan & Lookup", use_container_width=True):
                on_image_uploaded(image_bytes)

        st.divider()
        with st.expander("🔒 Live Audit Log"):
            render_audit_log(audit_records)

        if st.button("🔄 Reset Conversation", use_container_width=True):
            on_reset()


def render_chat_history(chat_view: List[Dict[str, str]]) -> None:
    """Render chronological chat turns for user and assistant messages.
    
    Args:
        chat_view: List of dictionaries with 'role' and 'content'.
    """
    for turn in chat_view:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])


def render_audit_log(audit_records: List[Dict[str, Any]]) -> None:
    """Render formatted JSON code blocks for audit records.
    
    Args:
        audit_records: List of audit dictionaries.
    """
    if not audit_records:
        st.caption("No audit entries recorded yet.")
        return

    for entry in reversed(audit_records[-20:]):
        st.code(json.dumps(entry, indent=2), language="json")
