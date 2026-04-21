"""Bussola Inteligente - Divida Zero (single page)."""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import core as rz
from ui_theme import card_html, lead, render_theme

RZ = "rz_dados"
STEP_KEY = "rz_step"
INTRO_KEY = "rz_intro_done"


def _plotly_dark(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#eaf1ff",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def _init_state() -> None:
    if RZ not in st.session_state:
        st.session_state[RZ] = None
    if STEP_KEY not in st.session_state:
        st.session_state[STEP_KEY] = "perfil"
    if INTRO_KEY not in st.session_state:
        st.session_state[INTRO_KEY] = False


def _header_and_nav() -> None:
    top_left, _ = st.columns([1, 6])
    with top_left:
        if st.button("← Início", key="btn_top_home"):
            st.session_state[INTRO_KEY] = False
            st.rerun()
    st.markdown("## 🧭 Bússola Inteligente - Dívida Zero")
    st.markdown(
        '<p class="rz-sub">Use a Bússola Inteligente para corrigir a rota da sua empresa e organizar a quitação.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="rz-navline">(1) Perfil e Dívidas ---- (2) Dashboard e Plano ---- (3) Jornada e Metas</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("1) Perfil e Dívidas", use_container_width=True):
            st.session_state[STEP_KEY] = "perfil"
    with c2:
        if st.button("2) Dashboard e Plano", use_container_width=True):
            st.session_state[STEP_KEY] = "dashboard"
    with c3:
        if st.button("3) Jornada e Metas", use_container_width=True):
            st.session_state[STEP_KEY] = "jornada"

    st.divider()


def _render_intro() -> None:
    st.markdown('<span class="rz-topchip">IAExpertise</span>', unsafe_allow_html=True)
    st.markdown("## Bússola Inteligente 🧭")
    st.markdown(
        '<p class="rz-sub">O mapa para tirar sua vida financeira do invisível e colocar no controle.</p>',
        unsafe_allow_html=True,
    )

    video_url = os.getenv("BUSSOLA_VIDEO_URL", "").strip()
    if video_url:
        st.video(video_url)
    else:
        st.info("Configure a URL do vídeo em `BUSSOLA_VIDEO_URL` (variável de ambiente).")

    st.markdown(
        card_html(
            "Qual é o objetivo do app?",
            (
                "A Bússola Inteligente - Dívida Zero foi criada para transformar confusão em direção prática. "
                "Você informa sua situação real, entende o impacto das dívidas no mês, compara estratégias de "
                "quitação e sai com um plano executável, com prioridade do que atacar primeiro."
            ),
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        card_html(
            "Como usar em 3 passos",
            (
                "1) Preencha Perfil e Dívidas com honestidade. "
                "2) Veja o Dashboard para comparar rotas e ajustar cenário. "
                "3) Siga a Jornada de metas para manter consistência até ver a dívida desaparecer."
            ),
        ),
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("Quero analisar minha situação", use_container_width=True):
            st.session_state[INTRO_KEY] = True
            st.rerun()

    st.divider()
    st.markdown(
        "<p style='text-align:center; color:#7ea3da; font-weight:600; margin-bottom:0.2rem;'>IAExpertise</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#ffffff; margin-top:0; margin-bottom:0.4rem;'>"
        "Eduardo Augusto Sona — Jornalista e Especialista em IA"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:#cfe0ff;'>🔒 Dados protegidos (LGPD)</p>",
        unsafe_allow_html=True,
    )


def _render_perfil() -> None:
    st.markdown("### Etapa 1 · Perfil e histórico das dívidas")
    lead("Vamos levantar sua situação real, sem julgamento.")

    with st.form("form_perfil"):
        perfil = st.radio("Tipo de perfil", ["Pessoa fisica", "Empresa"], horizontal=True)
        renda_mensal = st.number_input("Quanto entra por mes (R$)", min_value=0.0, step=100.0)
        despesas_fixas = st.number_input("Despesas fixas por mes (R$)", min_value=0.0, step=100.0)
        reserva = st.number_input("Reserva disponivel (R$)", min_value=0.0, step=100.0)

        st.markdown("#### Fontes alternativas de caixa (opcional)")
        valor_ativos_vendaveis = st.number_input(
            "Valor em ativos que poderia vender (R$)", min_value=0.0, step=100.0
        )
        renda_extra_mensal = st.number_input(
            "Renda extra mensal para dividas (R$)", min_value=0.0, step=50.0
        )
        ideias_criativas = st.text_area(
            "Ideias para aliviar o caixa",
            placeholder="Ex.: vender colecao de vinil aos poucos...",
            height=90,
        )

        qtd_dividas = st.number_input("Quantidade de dividas", min_value=1, max_value=20, value=1, step=1)
        dividas = []
        for i in range(int(qtd_dividas)):
            st.markdown(f"**Divida {i + 1}**")
            nome = st.text_input("Nome da divida/credor", value=f"Divida {i + 1}", key=f"nome_{i}")
            c1, c2 = st.columns(2)
            with c1:
                saldo = st.number_input("Saldo devedor (R$)", min_value=0.0, step=100.0, key=f"saldo_{i}")
                juros_mensal = st.number_input(
                    "Juros mensal (%)", min_value=0.0, step=0.1, key=f"juros_{i}"
                )
            with c2:
                parcela_minima = st.number_input(
                    "Parcela minima (R$)", min_value=0.0, step=50.0, key=f"min_{i}"
                )
                atraso = st.selectbox("Em atraso?", ["Nao", "Sim"], key=f"atraso_{i}")
            prioridade = st.selectbox(
                "Prioridade", ["Urgente", "Alta", "Normal", "Baixa"], index=2, key=f"prior_{i}"
            )
            cc1, cc2 = st.columns(2)
            with cc1:
                risco_negativa_certidao = st.checkbox(
                    "Impacta certidoes/cadastro?", key=f"neg_{i}"
                )
            with cc2:
                risco_acao_judicial = st.checkbox("Acao judicial/execucao?", key=f"acao_{i}")
            dividas.append(
                {
                    "nome": nome,
                    "saldo": saldo,
                    "juros_mensal": juros_mensal,
                    "parcela_minima": parcela_minima,
                    "atraso": atraso == "Sim",
                    "prioridade": prioridade,
                    "risco_negativa_certidao": risco_negativa_certidao,
                    "risco_acao_judicial": risco_acao_judicial,
                }
            )

        save = st.form_submit_button("Salvar etapa 1 e seguir para o painel")

    if save:
        if renda_mensal <= 0:
            st.error("Informe uma renda/faturamento mensal maior que zero.")
            return
        if any(d["saldo"] <= 0 for d in dividas):
            st.error("Todas as dividas devem ter saldo maior que zero.")
            return
        st.session_state[RZ] = {
            "perfil": perfil,
            "renda_mensal": renda_mensal,
            "despesas_fixas": despesas_fixas,
            "reserva": reserva,
            "valor_ativos_vendaveis": valor_ativos_vendaveis,
            "renda_extra_mensal": renda_extra_mensal,
            "ideias_criativas": ideias_criativas,
            "dividas": dividas,
            "orcamento_mensal": 0.0,
            "reducao_juros_pct": 0.0,
            "entrada_inicial": 0.0,
            "nova_parcela_alvo": 0.0,
        }
        st.success("Dados salvos. Proxima acao: abrir a Etapa 2 para ver o painel.")
        st.session_state[STEP_KEY] = "dashboard"


def _render_dashboard() -> None:
    if not st.session_state.get(RZ):
        st.info("Primeira acao: preencha a Etapa 1.")
        return

    dados = st.session_state[RZ]
    st.markdown("### Etapa 2 · Dashboard da situação atual e plano de ataque")
    lead("Aqui você enxerga onde está e quais caminhos aceleram sua quitação.")

    with st.form("form_dash"):
        orcamento_mensal = st.number_input(
            "Quanto consegue pagar por mes nas dividas (R$)",
            min_value=0.0,
            step=100.0,
            value=float(dados.get("orcamento_mensal") or 0),
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            reducao_juros_pct = st.slider(
                "Reducao de juros (%)", 0, 100, int(dados.get("reducao_juros_pct") or 0)
            )
        with c2:
            entrada_inicial = st.number_input(
                "Entrada inicial (R$)",
                min_value=0.0,
                step=100.0,
                value=float(dados.get("entrada_inicial") or 0),
            )
        with c3:
            nova_parcela_alvo = st.number_input(
                "Nova parcela alvo (R$)",
                min_value=0.0,
                step=100.0,
                value=float(dados.get("nova_parcela_alvo") or orcamento_mensal),
            )
        gerar_ia = st.checkbox("Gerar texto com IA (opcional)", value=False)
        sub = st.form_submit_button("Atualizar dashboard")

    if sub:
        dados.update(
            {
                "orcamento_mensal": orcamento_mensal,
                "reducao_juros_pct": float(reducao_juros_pct),
                "entrada_inicial": entrada_inicial,
                "nova_parcela_alvo": nova_parcela_alvo,
            }
        )
        st.session_state[RZ] = dados
        st.session_state.pop("estrategia_ia", None)

    dados = st.session_state[RZ]
    analise = rz.compute_full_analysis(dados)
    diag = analise["diagnostico"]
    dividas = dados["dividas"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total da divida", f"R$ {diag['total_divida']:,.2f}")
    with m2:
        st.metric("Comprometimento da renda", f"{diag['comprometimento_renda']:.1f}%")
    with m3:
        st.metric("Capacidade mensal", f"R$ {diag['capacidade_pagamento']:,.2f}")
    with m4:
        st.metric("Nivel de risco", diag["risco"])

    # Grafico 1: composicao das dividas
    st.markdown("#### Composicao das dividas por credor")
    df_div = pd.DataFrame(dividas)
    fig_pie = px.pie(df_div, names="nome", values="saldo", hole=0.45, color_discrete_sequence=px.colors.sequential.Blues_r)
    st.plotly_chart(_plotly_dark(fig_pie), use_container_width=True)

    # Grafico 2: comparativo estrategias
    st.markdown("#### Comparativo das estrategias")
    rows = []
    for nome, res in [
        ("Avalanche", analise["resultado_avalanche"]),
        ("Snowball", analise["resultado_snowball"]),
        ("Prioridade", analise["resultado_prioridade"]),
    ]:
        rows.append(
            {
                "Estrategia": nome,
                "Meses": res["meses"] if res.get("quitado") else None,
                "Juros": res["juros_totais"] if res.get("quitado") else None,
            }
        )
    df_cmp = pd.DataFrame(rows).fillna(0)
    c1, c2 = st.columns(2)
    with c1:
        fig_meses = px.bar(df_cmp, x="Estrategia", y="Meses", color="Estrategia", color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(_plotly_dark(fig_meses), use_container_width=True)
    with c2:
        fig_juros = px.bar(df_cmp, x="Estrategia", y="Juros", color="Estrategia", color_discrete_sequence=px.colors.sequential.Purples)
        st.plotly_chart(_plotly_dark(fig_juros), use_container_width=True)

    # Grafico 3: renda x despesas x capacidade
    st.markdown("#### Renda x despesas x capacidade")
    df_fluxo = pd.DataFrame(
        [
            {"Categoria": "Renda", "Valor": dados["renda_mensal"]},
            {"Categoria": "Despesas fixas", "Valor": dados["despesas_fixas"]},
            {"Categoria": "Capacidade mensal", "Valor": diag["capacidade_pagamento"]},
        ]
    )
    fig_fluxo = px.bar(df_fluxo, x="Categoria", y="Valor", color="Categoria", color_discrete_sequence=px.colors.sequential.Tealgrn)
    st.plotly_chart(_plotly_dark(fig_fluxo), use_container_width=True)

    ordem = sorted(dividas, key=lambda d: (-rz.prioridade_efetiva(d), -d["juros_mensal"], d["nome"]))
    primeiro = ordem[0]["nome"] if ordem else "-"
    st.markdown(card_html("Proxima acao recomendada", f"Comece por **{primeiro}** e mantenha o minimo nas demais."), unsafe_allow_html=True)

    if sub and gerar_ia:
        contexto = rz.montar_contexto_para_ia(
            perfil=dados["perfil"],
            renda_mensal=dados["renda_mensal"],
            despesas_fixas=dados["despesas_fixas"],
            reserva=dados["reserva"],
            valor_ativos_vendaveis=dados["valor_ativos_vendaveis"],
            renda_extra_mensal=dados["renda_extra_mensal"],
            ideias_criativas=dados.get("ideias_criativas") or "",
            orcamento_mensal=dados["orcamento_mensal"],
            has_sim=analise["has_sim"],
            reducao_juros_pct=dados.get("reducao_juros_pct") or 0,
            entrada_inicial=dados.get("entrada_inicial") or 0,
            nova_parcela_alvo=dados.get("nova_parcela_alvo") or 0,
            dividas=dados["dividas"],
            diagnostico=diag,
            resultado_avalanche=analise["resultado_avalanche"],
            resultado_snowball=analise["resultado_snowball"],
            resultado_prioridade=analise["resultado_prioridade"],
            resumo_renegociacao=analise["resumo_renegociacao"],
        )
        if not os.getenv("OPENAI_API_KEY"):
            st.warning("OPENAI_API_KEY nao configurada.")
        else:
            with st.spinner("Gerando estrategia com IA..."):
                texto, err = rz.gerar_estrategia_com_ia(contexto)
            if err:
                st.error(err)
            elif texto:
                st.session_state["estrategia_ia"] = texto
    if st.session_state.get("estrategia_ia"):
        st.markdown("#### Estrategia sugerida")
        st.markdown(st.session_state["estrategia_ia"])

    st.info("Quando concluir, avance para a Etapa 3 para seguir a jornada.")


def _render_jornada() -> None:
    if not st.session_state.get(RZ):
        st.info("Primeira acao: preencha a Etapa 1.")
        return
    dados = st.session_state[RZ]
    analise = rz.compute_full_analysis(dados)
    diag = analise["diagnostico"]
    dividas = dados["dividas"]

    st.markdown("### Etapa 3 · Metas e jornada de execução")
    lead("Sua dívida desaparece como fruto da sua jornada, passo a passo.")

    fp = rz.fingerprint_cenario(dividas, float(dados.get("orcamento_mensal") or 0), float(dados["renda_mensal"]))
    if st.session_state.get("jornada_fp") != fp:
        st.session_state["jornada_fp"] = fp
        for k in list(st.session_state.keys()):
            if str(k).startswith("jornada_chk_"):
                del st.session_state[k]

    missoes = rz.gerar_missoes_jornada(
        dividas, diag, analise["has_sim"], float(dados.get("valor_ativos_vendaveis") or 0), float(dados.get("renda_extra_mensal") or 0)
    )

    for fase in ["Base", "7 dias", "30 dias", "90 dias"]:
        fase_missoes = [m for m in missoes if m["fase"] == fase]
        if not fase_missoes:
            continue
        with st.expander(fase, expanded=fase in ("Base", "7 dias")):
            for m in fase_missoes:
                if m.get("fixa_concluida"):
                    st.success(f"Feito: {m['titulo']} (+{m['xp']} XP)")
                else:
                    st.checkbox(m["titulo"], key=f"jornada_chk_{fp}_{m['id']}", help=m["descricao"])

    feitos = {
        m["id"]
        for m in missoes
        if m.get("fixa_concluida") or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    }
    xp = sum(
        m["xp"]
        for m in missoes
        if m.get("fixa_concluida") or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    )
    nivel, titulo, _, falta = rz.nivel_jornada(xp)
    pct = rz.progresso_jornada_pct(missoes, feitos)
    prox = rz.proxima_missao_aberta(missoes, feitos)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Nivel", f"{nivel}")
    with c2:
        st.metric("Titulo", titulo)
    with c3:
        st.metric("XP", xp)
    st.progress(min(pct / 100, 1.0))
    st.caption(f"Trilha concluida: {pct:.0f}% · faltam ~{falta} XP para o proximo nivel.")

    # Grafico 4: progresso da jornada
    df_prog = pd.DataFrame(
        [{"Etapa": "Concluido", "Percentual": pct}, {"Etapa": "Restante", "Percentual": max(0.0, 100 - pct)}]
    )
    fig_prog = px.bar(
        df_prog,
        x="Etapa",
        y="Percentual",
        color="Etapa",
        color_discrete_map={"Concluido": "#5b8cff", "Restante": "#243a64"},
    )
    st.plotly_chart(_plotly_dark(fig_prog), use_container_width=True)

    if prox:
        st.markdown(card_html("Proxima missao", f"{prox['titulo']} (+{prox['xp']} XP)"), unsafe_allow_html=True)
    else:
        st.success("Parabens: voce concluiu todas as missoes desse cenario.")

    conquistas = rz.conquistas_jornada(xp, missoes, feitos, diag, len(dividas))
    if conquistas:
        st.markdown("#### Conquistas")
        for c in conquistas:
            st.info(c)


def main() -> None:
    st.set_page_config(page_title="Bussola Inteligente - Divida Zero", page_icon="🧭", layout="wide")
    render_theme()
    _init_state()

    if not st.session_state[INTRO_KEY]:
        _render_intro()
        return

    _header_and_nav()

    step = st.session_state[STEP_KEY]
    if step == "perfil":
        _render_perfil()
    elif step == "dashboard":
        _render_dashboard()
    else:
        _render_jornada()

    st.markdown(
        '<p class="rz-muted">Apoio educacional e de planejamento financeiro. Nao substitui orientacao contabil/juridica.</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
