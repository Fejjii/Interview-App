"""
Custom CSS theme for the Interview Coach UI.

Light/dark mode uses :root variables for custom HTML (hero, pills, cards).
Streamlit/Base Web widgets require dedicated dark-mode overrides (see _dark_mode_streamlit_overrides).
"""

from __future__ import annotations

import html

import streamlit as st

from interview_app.app.ui_settings import UISettings

_FONT_IMPORT = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
</style>"""

_LIGHT_VARS = """
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --bg-card: #ffffff;
    --bg-sidebar: #fafbfc;
    --bg-input: #ffffff;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-tertiary: #94a3b8;
    --border-primary: #e2e8f0;
    --border-secondary: #f1f5f9;
    --accent: #0f766e;
    --accent-light: #14b8a6;
    --accent-bg: #f0fdfa;
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
    --success: #059669;
    --success-bg: #ecfdf5;
    --warning: #d97706;
    --warning-bg: #fffbeb;
    --error: #dc2626;
    --error-bg: #fef2f2;
    --info: #2563eb;
    --info-bg: #eff6ff;
    --header-gradient: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);
    --card-gradient: linear-gradient(135deg, rgba(15,118,110,0.03), rgba(20,184,166,0.02));
"""

# App shell + semantic tokens for Streamlit widget overrides (dark only).
_DARK_VARS = """
    --bg-primary: #0b1220;
    --bg-secondary: #151f32;
    --bg-tertiary: #243045;
    --bg-card: #1a2332;
    --bg-sidebar: #0d1424;
    --bg-input: #1a2332;
    --text-primary: #f1f5f9;
    --text-secondary: #cbd5e1;
    --text-tertiary: #a8b9d1;
    --border-primary: #3d4f66;
    --border-secondary: #243045;
    --accent: #2dd4bf;
    --accent-light: #5eead4;
    --accent-bg: rgba(45,212,191,0.12);
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.25);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.35);
    --success: #4ade80;
    --success-bg: rgba(74,222,128,0.12);
    --warning: #fbbf24;
    --warning-bg: rgba(251,191,36,0.12);
    --error: #f87171;
    --error-bg: rgba(248,113,113,0.12);
    --info: #60a5fa;
    --info-bg: rgba(96,165,250,0.12);
    --header-gradient: linear-gradient(135deg, #0d3d38 0%, #134e48 50%, #115e56 100%);
    --card-gradient: linear-gradient(135deg, rgba(20,184,166,0.06), rgba(15,118,110,0.03));
    --st-surface: #1a2332;
    --st-surface-elevated: #243045;
    --st-input-bg: #1a2332;
    --st-input-border: #5b6c82;
    --st-input-border-focus: #2dd4bf;
    --st-input-text: #f8fafc;
    --st-placeholder: #9eb0c9;
    --st-label: #e8eef7;
    --st-caption: #b6c4d8;
    --st-muted: #9eb0c9;
    --st-dropdown-bg: #1a2332;
    --st-dropdown-border: #5b6c82;
    --st-dropdown-hover: #2c3b52;
    --st-dropdown-text: #f8fafc;
    --st-btn-primary-bg: #0f766e;
    --st-btn-primary-text: #f8fafc;
    --st-btn-secondary-bg: #243045;
    --st-btn-secondary-text: #f1f5f9;
    --st-btn-secondary-border: #5b6c82;
    --st-focus-ring: rgba(45,212,191,0.45);
"""


def _dark_mode_streamlit_overrides() -> str:
    """
    Dark-mode-only rules for Streamlit + Base Web.

    Uses :root semantic tokens (--st-*) so contrast can be tuned in one place.
    Includes global [data-baseweb="popover"] rules because dropdown menus are often
    portaled outside the sidebar DOM.
    """
    return """
/* ----- Typography: labels, captions, help (sidebar + main) ----- */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] label,
[data-testid="stMain"] [data-testid="stWidgetLabel"] p,
[data-testid="stMain"] [data-testid="stWidgetLabel"] label,
[data-testid="stMain"] label:not([data-baseweb="radio"]) {
    color: var(--st-label) !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stCaptionContainer"] p,
[data-testid="stMain"] [data-testid="stCaptionContainer"] {
    color: var(--st-caption) !important;
}
[data-testid="stSidebar"] .stMarkdown,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stMain"] .stMarkdown,
[data-testid="stMain"] .stMarkdown p {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .stMarkdown strong {
    color: var(--st-input-text) !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] a {
    color: var(--accent-light) !important;
}

/* ----- Text inputs & textareas (all) ----- */
[data-testid="stSidebar"] input:not([type="checkbox"]):not([type="radio"]),
[data-testid="stMain"] input:not([type="checkbox"]):not([type="radio"]),
[data-testid="stSidebar"] textarea,
[data-testid="stMain"] textarea {
    background-color: var(--st-input-bg) !important;
    color: var(--st-input-text) !important;
    border-color: var(--st-input-border) !important;
    caret-color: var(--st-input-text) !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stMain"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder,
[data-testid="stMain"] textarea::placeholder {
    color: var(--st-placeholder) !important;
    opacity: 1 !important;
}
[data-testid="stSidebar"] [data-baseweb="input"],
[data-testid="stMain"] [data-baseweb="input"] {
    background-color: var(--st-input-bg) !important;
    border-color: var(--st-input-border) !important;
}
[data-testid="stSidebar"] [data-baseweb="input"]:focus-within,
[data-testid="stMain"] [data-baseweb="input"]:focus-within,
[data-testid="stSidebar"] [data-baseweb="textarea"]:focus-within,
[data-testid="stMain"] [data-baseweb="textarea"]:focus-within {
    border-color: var(--st-input-border-focus) !important;
    box-shadow: 0 0 0 1px var(--st-input-border-focus) !important;
}

/* ----- Selectbox: closed control (sidebar + main) ----- */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stMain"] [data-baseweb="select"] > div {
    background-color: var(--st-input-bg) !important;
    border-color: var(--st-input-border) !important;
    color: var(--st-input-text) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] div[class*="value"],
[data-testid="stMain"] [data-baseweb="select"] div[class*="value"] {
    color: var(--st-input-text) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] svg,
[data-testid="stMain"] [data-baseweb="select"] svg {
    fill: var(--st-input-text) !important;
    color: var(--st-input-text) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"]:focus-within > div,
[data-testid="stMain"] [data-baseweb="select"]:focus-within > div {
    border-color: var(--st-input-border-focus) !important;
    box-shadow: 0 0 0 1px var(--st-focus-ring) !important;
}

/* ----- Dropdown menus: portaled popovers (NOT under stSidebar) ----- */
div[data-baseweb="popover"] {
    background: transparent !important;
}
div[data-baseweb="popover"] [role="listbox"],
div[data-baseweb="popover"] ul[role="listbox"] {
    background-color: var(--st-dropdown-bg) !important;
    border: 1px solid var(--st-dropdown-border) !important;
    box-shadow: var(--shadow-md) !important;
}
div[data-baseweb="popover"] [role="option"],
div[data-baseweb="popover"] li[role="option"] {
    background-color: var(--st-dropdown-bg) !important;
    color: var(--st-dropdown-text) !important;
}
div[data-baseweb="popover"] [role="option"]:hover,
div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
    background-color: var(--st-dropdown-hover) !important;
    color: var(--st-dropdown-text) !important;
}
div[data-baseweb="popover"] [role="option"] span {
    color: inherit !important;
}

/* Fallback: listbox still inside sidebar/main */
[data-testid="stSidebar"] [role="listbox"],
[data-testid="stMain"] [role="listbox"] {
    background-color: var(--st-dropdown-bg) !important;
    border: 1px solid var(--st-dropdown-border) !important;
}
[data-testid="stSidebar"] [role="option"],
[data-testid="stMain"] [role="option"] {
    background-color: var(--st-dropdown-bg) !important;
    color: var(--st-dropdown-text) !important;
}
[data-testid="stSidebar"] [role="option"]:hover,
[data-testid="stMain"] [role="option"]:hover {
    background-color: var(--st-dropdown-hover) !important;
}

/* ----- Sliders ----- */
[data-testid="stSidebar"] [data-baseweb="slider"] [data-baseweb="thumb"],
[data-testid="stMain"] [data-baseweb="slider"] [data-baseweb="thumb"] {
    background-color: var(--accent) !important;
}
[data-testid="stSidebar"] [data-baseweb="slider"] [data-baseweb="track"],
[data-testid="stMain"] [data-baseweb="slider"] [data-baseweb="track"] {
    background-color: var(--st-surface-elevated) !important;
}

/* ----- Toggle / checkbox (dark mode switch, etc.) ----- */
[data-testid="stSidebar"] [data-baseweb="checkbox"] label {
    color: var(--st-label) !important;
}
[data-testid="stSidebar"] [data-baseweb="checkbox"] > label > div:last-child,
[data-testid="stSidebar"] [data-baseweb="checkbox"] span {
    color: var(--st-label) !important;
}

/* ----- Expanders ----- */
[data-testid="stSidebar"] [data-testid="stExpander"] summary,
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] summary span,
[data-testid="stMain"] [data-testid="stExpander"] summary,
[data-testid="stMain"] [data-testid="stExpander"] summary p {
    color: var(--st-label) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] details,
[data-testid="stMain"] [data-testid="stExpander"] details {
    background-color: var(--st-surface) !important;
    border: 1px solid var(--st-input-border) !important;
    border-radius: var(--radius-sm);
}

/* ----- Alerts ----- */
[data-testid="stSidebar"] [data-testid="stAlert"],
[data-testid="stMain"] [data-testid="stAlert"] {
    background-color: var(--st-surface-elevated) !important;
    border: 1px solid var(--st-input-border) !important;
}
[data-testid="stSidebar"] [data-testid="stAlert"] p,
[data-testid="stSidebar"] [data-testid="stAlert"] div,
[data-testid="stMain"] [data-testid="stAlert"] p,
[data-testid="stMain"] [data-testid="stAlert"] div {
    color: var(--text-primary) !important;
}

/* ----- Radio (workspace) ----- */
[data-testid="stMain"] [data-testid="stRadio"] label,
[data-testid="stMain"] [data-testid="stRadio"] div[role="radiogroup"] label {
    color: var(--st-label) !important;
}
[data-testid="stMain"] [data-testid="stRadio"] [data-baseweb="radio"] {
    color: var(--accent) !important;
}

/* ----- Buttons ----- */
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stMain"] button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stMain"] .stButton > button[kind="primary"] {
    background-color: var(--st-btn-primary-bg) !important;
    color: var(--st-btn-primary-text) !important;
    border: 1px solid var(--st-btn-primary-bg) !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover,
[data-testid="stMain"] button[kind="primary"]:hover {
    filter: brightness(1.08) !important;
}
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stMain"] button[kind="secondary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"],
[data-testid="stMain"] .stButton > button[kind="secondary"] {
    background-color: var(--st-btn-secondary-bg) !important;
    color: var(--st-btn-secondary-text) !important;
    border: 1px solid var(--st-btn-secondary-border) !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover,
[data-testid="stMain"] button[kind="secondary"]:hover {
    background-color: var(--st-surface-elevated) !important;
    border-color: var(--accent-light) !important;
}
[data-testid="stSidebar"] button:disabled,
[data-testid="stMain"] button:disabled {
    opacity: 0.45 !important;
    cursor: not-allowed !important;
}

/* ----- Chat composer ----- */
[data-testid="stBottomBlockContainer"],
[data-testid="stBottom"],
section[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stChatInputContainer"] {
    background-color: var(--bg-primary) !important;
    border-top: 1px solid var(--border-primary) !important;
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="input"] {
    background-color: var(--st-input-bg) !important;
    color: var(--st-input-text) !important;
    border-color: var(--st-input-border) !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--st-placeholder) !important;
    opacity: 1 !important;
}

/* ----- Metrics (evaluation dashboard) ----- */
[data-testid="stMain"] [data-testid="stMetric"] {
    background: var(--st-surface) !important;
    border: 1px solid var(--st-input-border) !important;
}
[data-testid="stMain"] [data-testid="stMetric"] [data-testid="stMetricLabel"] {
    color: var(--st-caption) !important;
}
[data-testid="stMain"] [data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--st-input-text) !important;
}

/* ----- Tabs (if used) ----- */
.stTabs [data-baseweb="tab-list"] {
    background: var(--st-surface) !important;
    border: 1px solid var(--st-input-border) !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--st-caption) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--st-input-text) !important;
}

/* ----- Code / debug expanders ----- */
[data-testid="stMain"] [data-testid="stCode"] {
    background: var(--bg-primary) !important;
}
[data-testid="stMain"] pre {
    background: var(--st-surface) !important;
    color: var(--st-input-text) !important;
    border: 1px solid var(--st-input-border) !important;
}

/* ----- Notifications / toast ----- */
[data-testid="stMain"] [data-baseweb="notification"] {
    background-color: var(--st-surface-elevated) !important;
    color: var(--st-input-text) !important;
    border: 1px solid var(--st-input-border) !important;
}
"""


def _build_app_css(dark: bool = False) -> str:
    vars_block = _DARK_VARS if dark else _LIGHT_VARS
    dark_extra = _dark_mode_streamlit_overrides() if dark else ""
    return f"""<style>
:root {{
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    {vars_block}
}}
html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    color: var(--text-primary);
    background-color: var(--bg-primary);
}}
h1, h2, h3, h4 {{ color: var(--text-primary) !important; }}
.block-container {{
    padding-top: 0.75rem !important;
    padding-bottom: 1.5rem !important;
    max-width: min(1480px, 96vw) !important;
}}
[data-testid="stMain"] {{ background-color: var(--bg-primary) !important; }}
[data-testid="stSidebar"] {{
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-primary) !important;
}}
[data-testid="stHeader"] {{
    background: var(--header-gradient) !important;
}}
.ia-hero {{
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.25rem;
    background: var(--card-gradient);
    box-shadow: var(--shadow-sm);
}}
.ia-hero-compact {{
    padding: 0.85rem 1.1rem !important;
    margin-bottom: 0.75rem !important;
}}
.ia-hero-title {{
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    margin: 0 0 0.4rem 0 !important;
    letter-spacing: -0.03em;
    color: var(--text-primary) !important;
}}
.ia-hero-compact .ia-hero-title {{
    font-size: 1.28rem !important;
    font-weight: 700 !important;
    margin: 0 0 0.35rem 0 !important;
}}
.ia-hero-icon {{ margin-right: 0.4rem; }}
.ia-hero-subtitle {{
    margin: 0;
    font-size: 0.95rem;
    color: var(--text-secondary);
    line-height: 1.55;
}}
.ia-hero-compact .ia-hero-subtitle {{
    font-size: 0.86rem !important;
    line-height: 1.45 !important;
}}
.ia-config-pill-bar {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.45rem;
    padding: 0.55rem 0.75rem;
    margin-bottom: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
}}
.ia-config-pill-bar .ia-pill-label {{
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-tertiary);
    margin-right: 0.35rem;
}}
.ia-pill {{
    display: inline-flex;
    align-items: center;
    padding: 0.22rem 0.65rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--text-primary);
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    max-width: 100%;
}}
[data-testid="stSidebar"] .block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}}
[data-testid="stMain"] label {{
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}}
.ia-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    box-shadow: var(--shadow-sm);
    margin-bottom: 0.75rem;
}}
.ia-card-header {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-secondary);
}}
.ia-card-header h3 {{
    margin: 0 !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}}
.ia-card-accent {{ border-left: 3px solid var(--accent); }}
.ia-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.65rem;
    border-radius: 100px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}}
.ia-badge-active {{
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid var(--success);
}}
.ia-badge-idle {{
    background: var(--bg-tertiary);
    color: var(--text-tertiary);
    border: 1px solid var(--border-primary);
}}
.ia-badge-saved {{
    background: var(--info-bg);
    color: var(--info);
    border: 1px solid var(--info);
}}
.ia-meta {{
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
}}
.ia-meta-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0;
    border-bottom: 1px solid var(--border-secondary);
}}
.ia-meta-row:last-child {{ border-bottom: none; }}
.ia-meta-label {{
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-tertiary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}
.ia-meta-value {{
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--text-primary);
}}
.ia-empty {{
    text-align: center;
    padding: 1.5rem;
    color: var(--text-tertiary);
    font-size: 0.9rem;
}}
.eval-card {{
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-left: 4px solid var(--accent);
    padding: 1.25rem 1.5rem;
    border-radius: var(--radius-md);
    margin: 0.75rem 0;
}}
.eval-score {{
    font-size: 2rem;
    font-weight: 800;
    color: var(--accent);
}}
[data-testid="stMetric"] {{
    background: var(--bg-card);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-md);
    padding: 0.75rem;
}}
.stTabs [data-baseweb="tab-list"] {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-primary);
    border-radius: var(--radius-lg);
    padding: 0.3rem;
}}
[data-testid="stMain"] [data-testid="stRadio"] {{
    margin-bottom: 0.75rem;
}}
[data-testid="stChatMessage"] {{
    border: 1px solid var(--border-primary);
    background: var(--bg-card) !important;
    border-radius: var(--radius-md);
}}
{dark_extra}
</style>"""


def inject_theme() -> None:
    """Inject fonts + CSS for light/dark mode from session state."""
    dark = st.session_state.get("dark_mode", False)
    st.markdown(_FONT_IMPORT, unsafe_allow_html=True)
    st.markdown(_build_app_css(dark=dark), unsafe_allow_html=True)


def card_open(title: str = "", icon: str = "", accent: bool = False) -> str:
    """Opening HTML for a card wrapper."""
    cls = "ia-card ia-card-accent" if accent else "ia-card"
    header = ""
    if title:
        header = f'<div class="ia-card-header"><span>{icon}</span><h3>{title}</h3></div>'
    return f'<div class="{cls}">{header}'


def card_close() -> str:
    return "</div>"


def render_card_html(
    title: str = "", icon: str = "", content: str = "", accent: bool = False
) -> str:
    """Complete card HTML block."""
    return f"{card_open(title, icon, accent)}{content}{card_close()}"


def render_badge(text: str, variant: str = "idle") -> str:
    """Status badge HTML."""
    return f'<span class="ia-badge ia-badge-{variant}">{text}</span>'


def render_meta_row(label: str, value: str) -> str:
    """Metadata key-value row."""
    return (
        f'<div class="ia-meta-row">'
        f'<span class="ia-meta-label">{label}</span>'
        f'<span class="ia-meta-value">{value}</span>'
        f"</div>"
    )


def render_empty_state(icon: str, text: str) -> str:
    """Empty state placeholder."""
    return (
        f'<div class="ia-empty">'
        f'<div class="ia-empty-icon">{icon}</div>'
        f'<div class="ia-empty-text">{text}</div>'
        f"</div>"
    )


def _pill(text: str) -> str:
    safe = html.escape(text.strip() or "—")
    return f'<span class="ia-pill" title="{safe}">{safe}</span>'


def render_configuration_pill_bar(*, settings: UISettings) -> str:
    """
    Compact horizontal summary of active interview configuration (main area, top of workspace).
    """
    mode = settings.question_difficulty_mode
    diff_note = (
        f"Calibrated · {settings.effective_question_difficulty}"
        if mode == "Auto"
        else f"{mode} · {settings.effective_question_difficulty}"
    )
    parts = [
        '<div class="ia-config-pill-bar" aria-label="Current configuration">',
        '<span class="ia-pill-label">Current setup</span>',
        _pill(settings.role_category),
        _pill(settings.role_title or "Role title"),
        _pill(settings.seniority),
        _pill(settings.interview_round),
        _pill(settings.interview_focus),
        _pill(settings.persona),
        _pill(diff_note),
        _pill(settings.model_preset),
        "</div>",
    ]
    return "".join(parts)
