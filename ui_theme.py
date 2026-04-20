"""Estilo visual comum (fundo suave, tipografia, cartoes)."""

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
            background: linear-gradient(165deg, #f7f5f2 0%, #eef3f0 45%, #e8f0ec 100%);
        }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: rgba(255,255,255,0.55);
            border-right: 1px solid rgba(45,106,79,0.12);
        }
        h1 {
            color: #1b4332;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        h2, h3 {
            color: #2d6a4f;
            font-weight: 600;
        }
        .rz-card {
            background: rgba(255,255,255,0.85);
            border: 1px solid rgba(45,106,79,0.15);
            border-radius: 16px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 8px 24px rgba(27, 67, 50, 0.06);
        }
        .rz-lead {
            font-size: 1.15rem;
            color: #344e41;
            line-height: 1.55;
        }
        .rz-muted {
            color: #52796f;
            font-size: 0.95rem;
        }
        div[data-testid="stMetricValue"] {
            color: #1b4332;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def card_html(title: str, body: str) -> str:
    return f'<div class="rz-card"><strong style="color:#2d6a4f">{title}</strong><p class="rz-muted" style="margin:0.5rem 0 0 0">{body}</p></div>'


def lead(text: str) -> None:
    st.markdown(f'<p class="rz-lead">{text}</p>', unsafe_allow_html=True)
