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
            background: radial-gradient(circle at 0% 0%, #112b55 0%, #0b1c36 46%, #071325 100%);
        }
        .block-container {
            max-width: 860px;
            padding-top: 1.6rem;
            padding-bottom: 2rem;
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }
        [data-testid="stToolbar"] { right: 0.7rem; }
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
            border-radius: 12px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(3, 9, 22, 0.34);
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
            color: #ffffff !important;
        }
        .stMarkdown p, .stMarkdown li, .stMarkdown span, .stCaption, label {
            color: #ffffff !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] p {
            color: #dfeaff !important;
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
        [data-testid="stExpander"] summary p,
        [data-testid="stExpander"] summary span,
        [data-testid="stExpander"] label,
        [data-testid="stExpander"] p {
            color: #ffffff !important;
        }
        [data-testid="stExpander"] {
            border: 1px solid rgba(123, 165, 242, 0.22);
            border-radius: 10px;
            background: rgba(17, 36, 67, 0.35);
        }
        [data-testid="stCheckbox"] span {
            color: #f4f8ff !important;
        }
        .stAlert p, .stSuccess p, .stInfo p, .stWarning p, .stError p {
            color: #ffffff !important;
        }
        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="select"] > div {
            background: rgba(17, 36, 67, 0.72) !important;
            color: #ffffff !important;
            border: 1px solid rgba(131, 168, 231, 0.24) !important;
            border-radius: 8px !important;
        }
        [data-baseweb="input"] input::placeholder,
        [data-baseweb="textarea"] textarea::placeholder {
            color: #b7c8e8 !important;
        }
        [data-testid="stForm"] {
            background: rgba(10, 22, 42, 0.40);
            border: 1px solid rgba(92, 141, 227, 0.18);
            border-radius: 14px;
            padding: 1rem 1rem 0.4rem 1rem;
        }
        .stButton > button {
            background: linear-gradient(135deg, #2a6fe0, #5489e3);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(39, 121, 255, 0.28);
            min-height: 2.2rem;
            font-size: 0.85rem;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #3b7de8, #699ae9);
            color: white;
        }
        .rz-navline {
            color: #ffffff;
            font-weight: 500;
            font-size: 0.84rem;
            letter-spacing: .01em;
            margin: 0.1rem 0 0.7rem 0;
        }
        .rz-topchip {
            display: inline-block;
            color: #d5e6ff;
            font-size: 0.78rem;
            border: 1px solid rgba(108, 152, 233, 0.35);
            border-radius: 8px;
            padding: 0.2rem 0.5rem;
            background: rgba(28, 52, 92, 0.45);
            margin-bottom: 0.7rem;
        }
        .rz-sub {
            color: #bcd0ef !important;
            font-size: 0.88rem;
            margin-top: -0.2rem;
            margin-bottom: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card_html(title: str, body: str) -> str:
    return f'<div class="rz-card"><strong style="color:#f4f8ff">{title}</strong><p class="rz-muted" style="margin:0.5rem 0 0 0">{body}</p></div>'


def lead(text: str) -> None:
    st.markdown(f'<p class="rz-lead">{text}</p>', unsafe_allow_html=True)
