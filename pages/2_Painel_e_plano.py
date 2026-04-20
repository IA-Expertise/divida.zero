"""Pagina 2: dashboard da situacao e plano de ataque."""

import os

import pandas as pd
import streamlit as st

import core as rz
from ui_theme import lead, render_theme

RZ = "rz_dados"

st.set_page_config(page_title="Painel e plano | Rota", page_icon="🌿", layout="wide")
render_theme()

if not st.session_state.get(RZ):
    st.warning("Primeiro preencha **Quem e suas dividas** no menu ao lado.")
    st.stop()

dados = st.session_state[RZ]

st.title("Sua situacao hoje")
lead(
    "Aqui entra o quanto voce pode colocar nas dividas por mes e, se quiser, um cenario de renegociacao. "
    "Os numeros abaixo sao estimativas — nao promessa de prazo."
)

with st.form("form_painel"):
    st.subheader("Quanto pode dedicar as dividas por mes?")
    orcamento_mensal = st.number_input(
        "Valor por mes para abater dividas (R$)",
        min_value=0.0,
        step=100.0,
        value=float(dados.get("orcamento_mensal") or 0),
    )
    st.subheader("Cenario de renegociacao (opcional)")
    st.caption("Se ainda nao sabe, deixe em zero.")
    reducao_juros_pct = st.slider(
        "Se negociar, quanto % de reducao de juros imagina?",
        0,
        100,
        int(dados.get("reducao_juros_pct") or 0),
    )
    entrada_inicial = st.number_input(
        "Entrada unica que poderia dar (R$)",
        min_value=0.0,
        step=100.0,
        value=float(dados.get("entrada_inicial") or 0),
    )
    nova_parcela_alvo = st.number_input(
        "Nova parcela total mensal depois da negociacao (R$)",
        min_value=0.0,
        step=100.0,
        value=float(dados.get("nova_parcela_alvo") or orcamento_mensal),
    )
    gerar_ia = st.checkbox(
        "Quero um texto com IA comentando minha situacao (usa OPENAI_API_KEY no servidor)",
        value=False,
    )
    sub = st.form_submit_button("Atualizar painel")

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

analise = rz.compute_full_analysis(st.session_state[RZ])
dados = st.session_state[RZ]
diag = analise["diagnostico"]
dividas = dados["dividas"]

st.markdown("### Visao geral")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total que voce registrou de dividas", f"R$ {diag['total_divida']:,.2f}")
with m2:
    st.metric("Sobra no mes (apos despesas fixas)", f"R$ {diag['capacidade_pagamento']:,.2f}")
with m3:
    st.metric("Risco (visao simples)", diag["risco"])

if diag["capacidade_pagamento"] <= diag["custo_juros_mensal"]:
    st.error(
        "Atencao: no modelo, os juros podem comer quase toda a sobra. "
        "Priorize negociar e revisar despesas — isso e comum e tem saida com calma."
    )

st.markdown("### Ordem sugerida para atacar")
ordem = sorted(dividas, key=lambda d: (-rz.prioridade_efetiva(d), -d["juros_mensal"], d["nome"]))
rows = []
for i, d in enumerate(ordem, start=1):
    sinais = []
    if d.get("risco_negativa_certidao"):
        sinais.append("certidao")
    if d.get("risco_acao_judicial"):
        sinais.append("acao")
    if d.get("atraso"):
        sinais.append("atraso")
    rows.append(
        {
            "#": i,
            "Credor": d["nome"],
            "Saldo": f"R$ {d['saldo']:,.0f}",
            "Urgencia": d.get("prioridade", "Normal"),
            "Sinais": ", ".join(sinais) if sinais else "-",
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.markdown("### Tres jeitos de simular a quitação")
st.caption("Referencias matematicas — a vida real pode pedir ajustes.")

if not analise["has_sim"]:
    st.info("Informe um valor mensal acima para ver prazos estimados.")
else:
    ra, rs, rp = (
        analise["resultado_avalanche"],
        analise["resultado_snowball"],
        analise["resultado_prioridade"],
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Menor juros no total**")
        if ra["quitado"]:
            st.metric("Prazo estimado", f"~{ra['meses']} meses")
            st.caption(f"Juros pagos no modelo: R$ {ra['juros_totais']:,.0f}")
        else:
            st.warning("Cenario nao fechou no horizonte calculado.")
    with c2:
        st.markdown("**Menor divida primeiro**")
        if rs["quitado"]:
            st.metric("Prazo estimado", f"~{rs['meses']} meses")
            st.caption(f"Juros pagos no modelo: R$ {rs['juros_totais']:,.0f}")
        else:
            st.warning("Cenario nao fechou no horizonte calculado.")
    with c3:
        st.markdown("**Pelo que voce marcou como urgente**")
        if rp["quitado"]:
            st.metric("Prazo estimado", f"~{rp['meses']} meses")
            st.caption(f"Juros pagos no modelo: R$ {rp['juros_totais']:,.0f}")
        else:
            st.warning("Cenario nao fechou no horizonte calculado.")

st.markdown("### Plano de ataque (resumo)")
primeiro = ordem[0]["nome"] if ordem else "—"
st.markdown(
    f"""
1. **Primeiro foco:** tratar **{primeiro}** com o que couber no mes.  
2. **Manter o minimo** nas outras para nao piorar.  
3. **Revisar em 30 dias** o que funcionou — a rota pode mudar.  
"""
)

if dados.get("valor_ativos_vendaveis", 0) > 0 or dados.get("renda_extra_mensal", 0) > 0:
    st.markdown("### Se voce usar renda extra ou venda de bens")
    alt = analise["alternativas"]
    if dados.get("renda_extra_mensal", 0) > 0 and alt["avalanche_extra"].get("quitado"):
        a = alt["avalanche_extra"]
        st.success(
            f"Com a renda extra informada: prazo estimado ~{a['meses']} meses "
            f"(juros totais no modelo R$ {a['juros_totais']:,.0f})."
        )
    if dados.get("valor_ativos_vendaveis", 0) > 0 and alt.get("pos_venda") and alt["pos_venda"].get("quitado"):
        st.success(
            f"Com a venda simulada: prazo estimado ~{alt['pos_venda']['meses']} meses "
            f"(juros totais R$ {alt['pos_venda']['juros_totais']:,.0f})."
        )

st.markdown("### Renegociacao (o que voce preencheu)")
st.write(analise["resumo_renegociacao"])

st.divider()
st.markdown("### Conversa com IA (opcional)")
if sub and gerar_ia:
    ctx = rz.montar_contexto_para_ia(
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
    with st.expander("Ver o que foi enviado ao modelo"):
        st.text(ctx)
    if not os.getenv("OPENAI_API_KEY"):
        st.warning("Configure OPENAI_API_KEY no servidor.")
    else:
        with st.spinner("Gerando texto..."):
            texto, err = rz.gerar_estrategia_com_ia(ctx)
        if err:
            st.error(err)
        elif texto:
            st.session_state["estrategia_ia"] = texto

if st.session_state.get("estrategia_ia"):
    st.markdown(st.session_state["estrategia_ia"])
else:
    st.caption("Marque a opcao no formulario acima e clique em Atualizar painel para gerar.")

st.success("Pronto para **Jornada e metas** no menu ao lado — la voce marca passos e ve a proxima missao.")
