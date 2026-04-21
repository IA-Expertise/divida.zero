"""Tema visual dark futurista para o app."""

import streamlit as st


def render_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,600;0,9..40,700;1,9..40,400&display=swap');
        html, body, [class*="stApp"] {
            font-family: 'DM Sans', system-ui, sans-serif;
        }
        .stApp {
            background: radial-gradient(circle at 0% 0%, #11305f 0%, #0c1f3a 42%, #080f1f 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        [data-testid="stToolbar"] { right: 0.7rem; }
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.55);
            border-right: 1px solid rgba(45,106,79,0.12);
        }
        h1 {
            color: #ffffff !important;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        h2, h3 {
            color: #ffffff !important;
            font-weight: 600;
        }
        h4, h5, h6 {
            color: #ffffff !important;
        }
        .rz-card {
            background: linear-gradient(180deg, rgba(18,37,71,0.86), rgba(13,26,50,0.88));
            border: 1px solid rgba(94,151,255,0.28);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 14px 34px rgba(3, 9, 22, 0.38);
        }
        .rz-lead {
            font-size: 1.15rem;
            color: #ffffff !important;
            line-height: 1.55;
        }
        .rz-muted {
            color: #ffffff !important;
            font-size: 0.95rem;
        }
        div[data-testid="stMetricValue"] {
            color: #f4f8ff;
        }
        div[data-testid="stMetricLabel"] {
            color: #b9ccee;
        }
        .stMarkdown p, .stMarkdown li, .stMarkdown span, .stCaption, label {
            color: #ffffff !important;
        }
        [data-testid="stForm"] p,
        [data-testid="stForm"] label,
        [data-testid="stForm"] span,
        [data-testid="stForm"] div {
            color: #ffffff !important;
        }
        [data-baseweb="radio"] label,
        [data-baseweb="checkbox"] label,
        [data-baseweb="select"] * {
            color: #ffffff !important;
        }
        .stRadio label, .stCheckbox label, .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label {
            color: #ffffff !important;
        }
        .stButton > button {
            background: linear-gradient(135deg, #2779ff, #5b8cff);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 600;
            box-shadow: 0 8px 18px rgba(39, 121, 255, 0.35);
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #3f8bff, #79a4ff);
            color: white;
        }
        .rz-navline {
            color: #ffffff;
            font-weight: 600;
            letter-spacing: .01em;
            margin: 0.1rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card_html(title: str, body: str) -> str:
    return f'<div class="rz-card"><strong style="color:#f4f8ff">{title}</strong><p class="rz-muted" style="margin:0.5rem 0 0 0">{body}</p></div>'


def lead(text: str) -> None:
    st.markdown(f'<p class="rz-lead">{text}</p>', unsafe_allow_html=True)
