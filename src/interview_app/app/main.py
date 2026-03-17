from __future__ import annotations

import streamlit as st

from interview_app.app.controls import render_sidebar_controls
from interview_app.app.layout import render_header, render_instructions, render_tabs


def run() -> None:
    st.set_page_config(page_title="Interview Practice App", layout="wide")

    render_header()
    settings = render_sidebar_controls()
    render_instructions()
    render_tabs(settings)

