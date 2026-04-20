"""Pagina 1: perfil e historico de dividas."""

import streamlit as st

from ui_theme import lead, render_theme

RZ = "rz_dados"

st.set_page_config(page_title="Quem e suas dividas | Rota", page_icon="🌿", layout="wide")
render_theme()

st.title("Quem e voce e o que deve")
lead(
    "Aqui a gente so levanta a situacao real — como quando voce colava tudo num chat. "
    "Sem julgamento: quanto entra, quanto sai, e cada divida com nome e tamanho."
)

if RZ not in st.session_state:
    st.session_state[RZ] = None

with st.form("form_perfil"):
    st.subheader("Sobre voce")
    perfil = st.radio(
        "Voce esta registrando como",
        ["Pessoa fisica", "Empresa"],
        horizontal=True,
    )
    renda_mensal = st.number_input(
        "Quanto entra por mes (renda ou faturamento)? (R$)",
        min_value=0.0,
        step=100.0,
        help="Valor medio do mes.",
    )
    despesas_fixas = st.number_input(
        "Despesas fixas do mes (moradia, luz, escola...) (R$)",
        min_value=0.0,
        step=100.0,
    )
    reserva = st.number_input(
        "Dinheiro que voce ja tem separado (reserva) (R$)",
        min_value=0.0,
        step=100.0,
    )

    st.subheader("Opcional: outras fontes de alivio")
    st.caption("Venda de coisas, freelas — ajuda a pensar cenarios depois.")
    valor_ativos_vendaveis = st.number_input(
        "Quanto acha que poderia levantar vendendo algo (moveis, colecao, carro...)? (R$)",
        min_value=0.0,
        step=100.0,
    )
    renda_extra_mensal = st.number_input(
        "Renda extra por mes que conseguiria usar nas dividas (R$)",
        min_value=0.0,
        step=50.0,
    )
    ideias_criativas = st.text_area(
        "Ideias que ja passaram pela cabeca",
        placeholder="Ex.: vender discos aos poucos, dar aula, bico no fim de semana...",
        height=90,
    )

    st.subheader("Suas dividas — uma por uma")
    qtd_dividas = st.number_input("Quantas dividas quer registrar agora?", 1, 20, 1, 1)
    dividas = []
    for i in range(int(qtd_dividas)):
        st.markdown(f"**Divida {i + 1}**")
        nome = st.text_input("Nome ou credor", value=f"Divida {i + 1}", key=f"nome_{i}")
        col1, col2 = st.columns(2)
        with col1:
            saldo = st.number_input("Quanto falta pagar? (R$)", min_value=0.0, step=100.0, key=f"saldo_{i}")
            juros_mensal = st.number_input(
                "Juros ao mes (aprox., %)",
                min_value=0.0,
                step=0.1,
                key=f"juros_{i}",
                help="Se n souber, chute baixo ou deixe 0.",
            )
        with col2:
            parcela_minima = st.number_input(
                "Parcela minima ou o que paga hoje (R$)",
                min_value=0.0,
                step=50.0,
                key=f"min_{i}",
            )
            atraso = st.selectbox("Esta atrasada?", ["Nao", "Sim"], key=f"atraso_{i}")

        prioridade = st.selectbox(
            "Quao urgente isso e pra voce?",
            ["Urgente", "Alta", "Normal", "Baixa"],
            index=2,
            key=f"prior_{i}",
            help="Urgente: risco grande. Baixa: da pra segurar o minimo um tempo.",
        )
        cbf1, cbf2 = st.columns(2)
        with cbf1:
            risco_negativa_certidao = st.checkbox(
                "Afeta certidoes ou cadastros (CND, banco, etc.)?",
                key=f"neg_{i}",
            )
        with cbf2:
            risco_acao_judicial = st.checkbox(
                "Tem acao ou execucao em andamento?",
                key=f"acao_{i}",
            )

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

    save = st.form_submit_button("Salvar e ir para o painel")

if save:
    if renda_mensal <= 0:
        st.error("Informe quanto entra por mes (maior que zero).")
    elif any(d["saldo"] <= 0 for d in dividas):
        st.error("Cada divida precisa de um valor a pagar maior que zero.")
    else:
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
        st.session_state.pop("estrategia_ia", None)
        for k in list(st.session_state.keys()):
            if str(k).startswith("jornada_chk_"):
                del st.session_state[k]
        st.session_state.pop("jornada_fp", None)
        st.success("Salvo! Abra **Painel e plano** no menu ao lado.")
elif st.session_state.get(RZ):
    st.caption("Voce ja tem dados salvos. Envie o formulario de novo para atualizar.")
