"""Pagina 3: metas, proxima missao e progresso da jornada."""

import streamlit as st

import core as rz
from ui_theme import card_html, lead, render_theme

RZ = "rz_dados"

st.set_page_config(page_title="Jornada | Rota", page_icon="🌿", layout="wide")
render_theme()

if not st.session_state.get(RZ):
    st.warning("Primeiro preencha **Quem e suas dividas** e depois **Painel e plano**.")
    st.stop()

dados = st.session_state[RZ]
analise = rz.compute_full_analysis(dados)
diag = analise["diagnostico"]
dividas = dados["dividas"]

st.title("Sua jornada — um passo de cada vez")
lead(
    "Cada missao concluida aproxima voce da tranquilidade. "
    "A divida nao some da noite pro dia, mas some da **sua** persistencia — e isso que a gente celebra aqui."
)

fp = rz.fingerprint_cenario(dividas, float(dados.get("orcamento_mensal") or 0), float(dados["renda_mensal"]))
if st.session_state.get("jornada_fp") != fp:
    st.session_state["jornada_fp"] = fp
    for k in list(st.session_state.keys()):
        if str(k).startswith("jornada_chk_"):
            del st.session_state[k]

has_sim = analise["has_sim"]
missoes = rz.gerar_missoes_jornada(
    dividas,
    diag,
    has_sim,
    float(dados.get("valor_ativos_vendaveis") or 0),
    float(dados.get("renda_extra_mensal") or 0),
)


def _xp_e_feitos() -> tuple[int, set[str]]:
    xp = sum(
        m["xp"]
        for m in missoes
        if m.get("fixa_concluida") or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    )
    fe = {
        m["id"]
        for m in missoes
        if m.get("fixa_concluida") or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    }
    return xp, fe


st.markdown("### Marcar o que ja fez")
st.caption("Marque com honestidade — a ideia e acompanhar voce, nao julgar.")

fases_ordem = ["Base", "7 dias", "30 dias", "90 dias"]
por_fase: dict[str, list[dict]] = {f: [] for f in fases_ordem}
for m in missoes:
    if m["fase"] in por_fase:
        por_fase[m["fase"]].append(m)

for fase in fases_ordem:
    if not por_fase[fase]:
        continue
    with st.expander(fase, expanded=(fase in ("Base", "7 dias"))):
        for m in por_fase[fase]:
            if m.get("fixa_concluida"):
                st.success(f"Feito: {m['titulo']} (+{m['xp']} XP)")
            else:
                st.checkbox(
                    m["titulo"],
                    key=f"jornada_chk_{fp}_{m['id']}",
                    help=f"+{m['xp']} XP — {m['descricao']}",
                )

xp_total, feitas = _xp_e_feitos()
nv, titulo_nv, _xp_no, falta = rz.nivel_jornada(xp_total)
prog_pct = rz.progresso_jornada_pct(missoes, feitas)
prox = rz.proxima_missao_aberta(missoes, feitas)

st.divider()

st.markdown("### Seu painel neste momento")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total em dividas (cadastro)", f"R$ {diag['total_divida']:,.0f}")
with c2:
    st.metric("Nivel da jornada", f"{nv}")
with c3:
    st.metric("Titulo", titulo_nv)
with c4:
    st.metric("Trilha concluida", f"{prog_pct:.0f}%")

st.progress(min(prog_pct / 100.0, 1.0))
st.caption(
    f"XP total: {xp_total}. Proximo nivel: faltam cerca de {falta} XP. "
    "Isso acompanha seus passos aqui — nao substitui o extrato do banco."
)

st.markdown("### Proxima missao")
if prox:
    st.markdown(
        card_html(
            prox["titulo"],
            f"{prox['descricao']} · {prox['fase']} · +{prox['xp']} XP",
        ),
        unsafe_allow_html=True,
    )
else:
    st.success("Voce zerou as missoes deste cenario. Atualize os dados no Painel se a vida mudar.")

conquistas = rz.conquistas_jornada(xp_total, missoes, feitas, diag, len(dividas))
if conquistas:
    st.markdown("### Conquistas")
    for c in conquistas:
        st.info(c)

st.caption(
    "Quando mudar valores no Painel, a trilha pode recalcular — e normal, como na vida real."
)
