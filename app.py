import streamlit as st


def calcular_diagnostico(renda_mensal: float, despesas_fixas: float, reserva: float, dividas: list[dict]) -> dict:
    capacidade_pagamento = max(renda_mensal - despesas_fixas, 0.0)
    comprometimento_renda = (despesas_fixas / renda_mensal * 100) if renda_mensal > 0 else 0.0
    total_divida = sum(item["saldo"] for item in dividas)
    custo_juros_mensal = sum(item["saldo"] * (item["juros_mensal"] / 100) for item in dividas)
    total_minimos = sum(item["parcela_minima"] for item in dividas)

    if comprometimento_renda < 50:
        risco = "Baixo"
    elif comprometimento_renda <= 80:
        risco = "Medio"
    else:
        risco = "Alto"

    return {
        "capacidade_pagamento": capacidade_pagamento,
        "comprometimento_renda": comprometimento_renda,
        "reserva": reserva,
        "risco": risco,
        "total_divida": total_divida,
        "custo_juros_mensal": custo_juros_mensal,
        "total_minimos": total_minimos,
    }


def _indice_prioritario(saldos: list[float], taxas: list[float], estrategia: str) -> int | None:
    ativos = [i for i, saldo in enumerate(saldos) if saldo > 0.01]
    if not ativos:
        return None

    if estrategia == "avalanche":
        return max(ativos, key=lambda i: (taxas[i], saldos[i]))
    return min(ativos, key=lambda i: (saldos[i], -taxas[i]))


def simular_quitacao(dividas: list[dict], orcamento_mensal: float, estrategia: str, max_meses: int = 600) -> dict:
    saldos = [item["saldo"] for item in dividas]
    taxas = [item["juros_mensal"] / 100 for item in dividas]
    minimos = [item["parcela_minima"] for item in dividas]
    juros_totais = 0.0

    if orcamento_mensal <= 0:
        return {"quitado": False, "meses": None, "juros_totais": None}

    for mes in range(1, max_meses + 1):
        juros_mes = 0.0
        for i, saldo in enumerate(saldos):
            if saldo <= 0.01:
                continue
            juros = saldo * taxas[i]
            juros_mes += juros
            saldos[i] += juros

        juros_totais += juros_mes
        disponivel = orcamento_mensal
        total_pago_mes = 0.0

        for i, saldo in enumerate(saldos):
            if saldo <= 0.01 or disponivel <= 0:
                continue
            pagamento = min(minimos[i], saldo, disponivel)
            saldos[i] -= pagamento
            disponivel -= pagamento
            total_pago_mes += pagamento

        while disponivel > 0.01:
            alvo = _indice_prioritario(saldos, taxas, estrategia)
            if alvo is None:
                break
            pagamento_extra = min(disponivel, saldos[alvo])
            saldos[alvo] -= pagamento_extra
            disponivel -= pagamento_extra
            total_pago_mes += pagamento_extra

        if all(saldo <= 0.01 for saldo in saldos):
            return {"quitado": True, "meses": mes, "juros_totais": juros_totais}

        if total_pago_mes <= juros_mes * 0.05:
            return {"quitado": False, "meses": None, "juros_totais": None}

    return {"quitado": False, "meses": None, "juros_totais": None}


def aplicar_renegociacao(
    dividas: list[dict], reducao_juros_pct: float, entrada_inicial: float, nova_parcela_alvo: float
) -> tuple[list[dict], float]:
    fator_juros = max(0.0, 1 - (reducao_juros_pct / 100))
    dividas_renegociadas = []

    saldo_total = sum(item["saldo"] for item in dividas)
    entrada_utilizada = min(max(entrada_inicial, 0.0), saldo_total)

    for item in dividas:
        proporcao = (item["saldo"] / saldo_total) if saldo_total > 0 else 0.0
        abatimento = entrada_utilizada * proporcao
        novo_saldo = max(item["saldo"] - abatimento, 0.0)
        novos_juros = item["juros_mensal"] * fator_juros
        nova_parcela = min(max(nova_parcela_alvo * proporcao, 0.0), novo_saldo) if novo_saldo > 0 else 0.0

        dividas_renegociadas.append(
            {
                "nome": item["nome"],
                "saldo": novo_saldo,
                "juros_mensal": novos_juros,
                "parcela_minima": nova_parcela,
                "atraso": item["atraso"],
            }
        )

    return dividas_renegociadas, entrada_utilizada


def main() -> None:
    st.set_page_config(page_title="Rota de Quitacao", page_icon="📊", layout="centered")

    st.title("Rota de Quitacao")
    st.subheader("Diagnostico financeiro e simulacao de quitacao")
    st.write(
        "Este app oferece apoio educacional e de planejamento financeiro. "
        "Nao substitui orientacao profissional contabil/juridica."
    )

    with st.form("form_diagnostico"):
        st.markdown("### 1) Dados gerais")
        perfil = st.radio("Tipo de perfil", ["Pessoa fisica", "Empresa"], horizontal=True)
        renda_mensal = st.number_input("Renda/Faturamento mensal (R$)", min_value=0.0, step=100.0)
        despesas_fixas = st.number_input("Despesas fixas mensais (R$)", min_value=0.0, step=100.0)
        reserva = st.number_input("Reserva disponivel (R$)", min_value=0.0, step=100.0)

        st.markdown("### 2) Cadastro de dividas")
        qtd_dividas = st.number_input("Quantidade de dividas", min_value=1, max_value=20, value=1, step=1)
        dividas = []
        for i in range(int(qtd_dividas)):
            st.markdown(f"**Divida {i + 1}**")
            nome = st.text_input("Nome da divida/credor", value=f"Divida {i + 1}", key=f"nome_{i}")
            col1, col2 = st.columns(2)
            with col1:
                saldo = st.number_input(
                    "Saldo devedor (R$)", min_value=0.0, step=100.0, key=f"saldo_{i}"
                )
                juros_mensal = st.number_input(
                    "Juros mensal (%)", min_value=0.0, step=0.1, key=f"juros_{i}"
                )
            with col2:
                parcela_minima = st.number_input(
                    "Parcela minima (R$)", min_value=0.0, step=50.0, key=f"min_{i}"
                )
                atraso = st.selectbox("Em atraso?", ["Nao", "Sim"], key=f"atraso_{i}")

            dividas.append(
                {
                    "nome": nome,
                    "saldo": saldo,
                    "juros_mensal": juros_mensal,
                    "parcela_minima": parcela_minima,
                    "atraso": atraso == "Sim",
                }
            )

        st.markdown("### 3) Orcamento para quitar dividas")
        orcamento_mensal = st.number_input(
            "Quanto voce consegue pagar por mes nas dividas (R$)?",
            min_value=0.0,
            step=100.0,
        )

        st.markdown("### 4) Cenario de renegociacao (opcional)")
        reducao_juros_pct = st.slider("Reducao de juros esperada (%)", min_value=0, max_value=100, value=0)
        entrada_inicial = st.number_input("Entrada inicial para abater saldo (R$)", min_value=0.0, step=100.0)
        nova_parcela_alvo = st.number_input(
            "Nova parcela total alvo apos renegociacao (R$)",
            min_value=0.0,
            step=100.0,
            value=orcamento_mensal,
        )

        submitted = st.form_submit_button("Gerar diagnostico e simulacoes")

    if not submitted:
        return

    if renda_mensal <= 0:
        st.error("Informe uma renda/faturamento mensal maior que zero.")
        return

    if any(item["saldo"] <= 0 for item in dividas):
        st.error("Todas as dividas devem ter saldo devedor maior que zero.")
        return

    diagnostico = calcular_diagnostico(
        renda_mensal=renda_mensal,
        despesas_fixas=despesas_fixas,
        reserva=reserva,
        dividas=dividas,
    )

    st.success("Diagnostico calculado com sucesso.")
    st.markdown(f"**Perfil selecionado:** {perfil}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Total da divida", f"R$ {diagnostico['total_divida']:,.2f}")
        st.metric("Capacidade mensal de pagamento", f"R$ {diagnostico['capacidade_pagamento']:,.2f}")
        st.metric("Comprometimento da renda", f"{diagnostico['comprometimento_renda']:.1f}%")
    with col_b:
        st.metric("Custo mensal estimado dos juros", f"R$ {diagnostico['custo_juros_mensal']:,.2f}")
        st.metric("Soma das parcelas minimas", f"R$ {diagnostico['total_minimos']:,.2f}")
        st.metric("Reserva informada", f"R$ {diagnostico['reserva']:,.2f}")

    st.markdown(f"**Nivel de risco atual:** {diagnostico['risco']}")

    if diagnostico["capacidade_pagamento"] <= diagnostico["custo_juros_mensal"]:
        st.warning(
            "Risco de bola de neve: sua capacidade de pagamento esta menor ou igual ao custo mensal dos juros."
        )

    if orcamento_mensal <= 0:
        st.warning("Informe um orcamento mensal para executar as simulacoes de quitacao.")
        return

    resultado_avalanche = simular_quitacao(dividas, orcamento_mensal, "avalanche")
    resultado_snowball = simular_quitacao(dividas, orcamento_mensal, "snowball")

    st.markdown("### Simulacao de estrategias")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Metodo Avalanche (maior juros primeiro)**")
        if resultado_avalanche["quitado"]:
            st.metric("Prazo estimado", f"{resultado_avalanche['meses']} meses")
            st.metric("Juros totais estimados", f"R$ {resultado_avalanche['juros_totais']:,.2f}")
        else:
            st.error("Nao foi possivel estimar quitacao no horizonte de simulacao.")

    with col2:
        st.markdown("**Metodo Snowball (menor saldo primeiro)**")
        if resultado_snowball["quitado"]:
            st.metric("Prazo estimado", f"{resultado_snowball['meses']} meses")
            st.metric("Juros totais estimados", f"R$ {resultado_snowball['juros_totais']:,.2f}")
        else:
            st.error("Nao foi possivel estimar quitacao no horizonte de simulacao.")

    if resultado_avalanche["quitado"] and resultado_snowball["quitado"]:
        juros_avalanche = resultado_avalanche["juros_totais"]
        juros_snowball = resultado_snowball["juros_totais"]
        meses_avalanche = resultado_avalanche["meses"]
        meses_snowball = resultado_snowball["meses"]

        st.markdown("### Comparativo rapido")
        if juros_avalanche < juros_snowball:
            st.info("Avalanche teve menor custo total de juros nesta simulacao.")
        elif juros_snowball < juros_avalanche:
            st.info("Snowball teve menor custo total de juros nesta simulacao.")
        else:
            st.info("As duas estrategias tiveram custo de juros equivalente nesta simulacao.")

        if meses_avalanche < meses_snowball:
            st.info("Avalanche terminou em menos tempo nesta simulacao.")
        elif meses_snowball < meses_avalanche:
            st.info("Snowball terminou em menos tempo nesta simulacao.")
        else:
            st.info("As duas estrategias terminaram no mesmo prazo nesta simulacao.")

    st.markdown("### Simulacao de renegociacao")
    if reducao_juros_pct <= 0 and entrada_inicial <= 0 and nova_parcela_alvo <= 0:
        st.info("Preencha os campos de renegociacao para estimar o impacto no prazo e no custo total.")
        return

    dividas_renegociadas, entrada_utilizada = aplicar_renegociacao(
        dividas=dividas,
        reducao_juros_pct=float(reducao_juros_pct),
        entrada_inicial=entrada_inicial,
        nova_parcela_alvo=nova_parcela_alvo,
    )

    if all(item["saldo"] <= 0.01 for item in dividas_renegociadas):
        st.success("Com a entrada informada, todas as dividas seriam quitadas imediatamente.")
        return

    orcamento_renegociado = nova_parcela_alvo if nova_parcela_alvo > 0 else orcamento_mensal
    if orcamento_renegociado <= 0:
        st.warning("Informe uma nova parcela alvo maior que zero para simular a renegociacao.")
        return

    base_renegociacao = simular_quitacao(dividas_renegociadas, orcamento_renegociado, "avalanche")
    base_original = simular_quitacao(dividas, orcamento_mensal, "avalanche")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.metric("Entrada considerada", f"R$ {entrada_utilizada:,.2f}")
        st.metric("Orcamento mensal renegociado", f"R$ {orcamento_renegociado:,.2f}")
    with col_r2:
        custo_juros_renegociado = sum(item["saldo"] * (item["juros_mensal"] / 100) for item in dividas_renegociadas)
        st.metric("Novo custo mensal estimado dos juros", f"R$ {custo_juros_renegociado:,.2f}")
        st.metric("Reducao de juros aplicada", f"{float(reducao_juros_pct):.1f}%")

    if base_renegociacao["quitado"]:
        st.success(
            f"Cenario renegociado: quitacao estimada em {base_renegociacao['meses']} meses "
            f"com juros totais de R$ {base_renegociacao['juros_totais']:,.2f}."
        )
    else:
        st.error("No cenario renegociado, nao foi possivel estimar quitacao no horizonte de simulacao.")
        return

    if base_original["quitado"]:
        delta_meses = base_original["meses"] - base_renegociacao["meses"]
        delta_juros = base_original["juros_totais"] - base_renegociacao["juros_totais"]
        st.info(
            f"Impacto estimado vs cenario original (Avalanche): "
            f"{delta_meses} meses a menos e economia de R$ {delta_juros:,.2f} em juros."
        )


if __name__ == "__main__":
    main()
