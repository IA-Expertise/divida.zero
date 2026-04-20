"""Rota de Quitacao — pagina inicial."""

import streamlit as st

from ui_theme import lead, render_theme

st.set_page_config(
    page_title="Rota de Quitacao",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_theme()

st.title("Rota de Quitacao")
lead(
    "Um lugar para enxergar sua situacao com calma, montar um plano de ataque e "
    "acompanhar sua jornada — como naquela conversa com o ChatGPT, mas organizada em passos."
)

st.markdown(
    '<p class="rz-muted">Apoio educacional. Nao substitui orientacao contabil ou juridica.</p>',
    unsafe_allow_html=True,
)

st.divider()

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 1 · Quem e e suas dividas")
    st.caption("Seu perfil, entrada e saida de dinheiro, e a lista do que voce deve.")
with c2:
    st.markdown("### 2 · Painel e plano")
    st.caption("Quanto cabe no mes, simulacoes e um plano claro — sem excesso de jargao.")
with c3:
    st.markdown("### 3 · Metas da jornada")
    st.caption("Passo a passo gamificado: a proxima missao aparece quando voce avanca.")

st.info(
    "Use o menu **à esquerda** para abrir cada etapa. Comece por **Quem e suas dividas**."
)
