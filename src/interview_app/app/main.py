from __future__ import annotations

"""
Top-level Streamlit app runner.

This module is the "composition root" for the UI:
- configures the Streamlit page (title, layout)
- renders the header and sidebar controls
- renders the main tabs and wires buttons to service functions

Entry chain:
`streamlit_app.py` → `interview_app.app.main.run()`
"""

import streamlit as st

from interview_app.app.controls import render_sidebar_controls
from interview_app.app.layout import render_header, render_instructions, render_tabs


def run() -> None:
    """Build and render the Streamlit page."""
    st.set_page_config(page_title="Interview Practice App", layout="wide")

    render_header()
    settings = render_sidebar_controls()
    render_instructions()
    render_tabs(settings)

