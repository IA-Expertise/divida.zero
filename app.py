import hashlib
import json
import os

import pandas as pd
import streamlit as st

NIVEL_PRIORIDADE = {"Urgente": 4, "Alta": 3, "Normal": 2, "Baixa": 1}


def prioridade_efetiva(item: dict) -> int:
    base = NIVEL_PRIORIDADE.get(item.get("prioridade", "Normal"), 2)
    if item.get("risco_negativa_certidao"):
        base = max(base, 3)
    if item.get("risco_acao_judicial"):
        base = max(base, 3)
    return min(base, 4)


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


def _indice_prioritario(
    saldos: list[float],
    taxas: list[float],
    estrategia: str,
    prioridades: list[int] | None = None,
) -> int | None:
    ativos = [i for i, saldo in enumerate(saldos) if saldo > 0.01]
    if not ativos:
        return None

    if estrategia == "prioridade" and prioridades is not None:
        return max(ativos, key=lambda i: (prioridades[i], taxas[i], saldos[i]))
    if estrategia == "avalanche":
        return max(ativos, key=lambda i: (taxas[i], saldos[i]))
    return min(ativos, key=lambda i: (saldos[i], -taxas[i]))


def simular_quitacao(dividas: list[dict], orcamento_mensal: float, estrategia: str, max_meses: int = 600) -> dict:
    saldos = [item["saldo"] for item in dividas]
    taxas = [item["juros_mensal"] / 100 for item in dividas]
    minimos = [item["parcela_minima"] for item in dividas]
    prioridades = [prioridade_efetiva(item) for item in dividas] if estrategia == "prioridade" else None
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
            alvo = _indice_prioritario(saldos, taxas, estrategia, prioridades)
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


def abater_saldo_proporcional(dividas: list[dict], entrada: float) -> tuple[list[dict], float]:
    saldo_total = sum(item["saldo"] for item in dividas)
    entrada_utilizada = min(max(entrada, 0.0), saldo_total)
    dividas_abatidas = []

    for item in dividas:
        proporcao = (item["saldo"] / saldo_total) if saldo_total > 0 else 0.0
        abatimento = entrada_utilizada * proporcao
        novo_saldo = max(item["saldo"] - abatimento, 0.0)
        dividas_abatidas.append(
            {
                "nome": item["nome"],
                "saldo": novo_saldo,
                "juros_mensal": item["juros_mensal"],
                "parcela_minima": item["parcela_minima"],
                "atraso": item["atraso"],
                "prioridade": item.get("prioridade", "Normal"),
                "risco_negativa_certidao": item.get("risco_negativa_certidao", False),
                "risco_acao_judicial": item.get("risco_acao_judicial", False),
            }
        )

    return dividas_abatidas, entrada_utilizada


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
                "prioridade": item.get("prioridade", "Normal"),
                "risco_negativa_certidao": item.get("risco_negativa_certidao", False),
                "risco_acao_judicial": item.get("risco_acao_judicial", False),
            }
        )

    return dividas_renegociadas, entrada_utilizada


def fingerprint_cenario(dividas: list[dict], orcamento_mensal: float, renda_mensal: float) -> str:
    payload = json.dumps(
        [{"n": d["nome"], "s": round(d["saldo"], 2)} for d in dividas]
        + [round(orcamento_mensal, 2), round(renda_mensal, 2)],
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def gerar_missoes_jornada(
    dividas: list[dict],
    diagnostico: dict,
    has_sim: bool,
    valor_ativos: float,
    renda_extra: float,
) -> list[dict]:
    ordem = sorted(dividas, key=lambda d: (-prioridade_efetiva(d), -d["juros_mensal"], d["nome"]))
    primeiro_nome = ordem[0]["nome"] if ordem else "sua divida mais urgente"
    tem_risco_legal = any(
        d.get("risco_negativa_certidao") or d.get("risco_acao_judicial") for d in dividas
    )
    maior_juros = max((d["juros_mensal"] for d in dividas), default=0.0)
    motor_ok = diagnostico["capacidade_pagamento"] > diagnostico["custo_juros_mensal"]

    missoes: list[dict] = [
        {
            "id": "clareza_numeros",
            "fase": "Base",
            "titulo": "Ter clareza dos numeros (mapa do atoleiro)",
            "descricao": "Voce ja deu o primeiro passo ao registrar renda, despesas e dividas neste formulario.",
            "xp": 25,
            "fixa_concluida": True,
        },
        {
            "id": "foco_primeiro",
            "fase": "7 dias",
            "titulo": f"Escolher o primeiro foco de ataque: {primeiro_nome}",
            "descricao": "Combine com sua rota de prioridade: ataque o que mais machuca (juros ou risco) primeiro.",
            "xp": 30,
            "fixa_concluida": False,
        },
        {
            "id": "contato_credor",
            "fase": "7 dias",
            "titulo": f"Agendar contato ou negociacao com: {primeiro_nome}",
            "descricao": "Mesmo que seja só pedir extrato ou simular renegociacao — o movimento importa.",
            "xp": 35,
            "fixa_concluida": False,
        },
    ]

    if has_sim:
        missoes.insert(
            2,
            {
                "id": "separar_caixa",
                "fase": "7 dias",
                "titulo": "Separar o valor mensal para dividas (sem misturar com o resto)",
                "descricao": "Reservar na pratica o valor que voce informou como orcamento para dividas.",
                "xp": 25,
                "fixa_concluida": False,
            },
        )

    if tem_risco_legal:
        missoes.append(
            {
                "id": "orientacao_legal",
                "fase": "7 dias",
                "titulo": "Buscar orientacao sobre negativa, acao ou execucao (profissional)",
                "descricao": "O app nao substitui advogado; priorize entender riscos reais.",
                "xp": 40,
                "fixa_concluida": False,
            }
        )

    if valor_ativos > 0:
        missoes.append(
            {
                "id": "venda_ativos",
                "fase": "30 dias",
                "titulo": "Executar plano de venda de bens (lista, precos, canais)",
                "descricao": "Transformar estimativa em acao: fotos, anuncios, prazos.",
                "xp": 30,
                "fixa_concluida": False,
            }
        )

    if renda_extra > 0:
        missoes.append(
            {
                "id": "teste_renda_extra",
                "fase": "30 dias",
                "titulo": "Rodar 2 semanas de renda extra dedicada as dívidas",
                "descricao": "Validar se o valor extra que voce estimou e sustentavel.",
                "xp": 30,
                "fixa_concluida": False,
            }
        )

    missoes.append(
        {
            "id": "revisao_30",
            "fase": "30 dias",
            "titulo": "Revisar o plano (o que funcionou, o que ajustar)",
            "descricao": "Pequena retrospectiva: juros, humor, atrasos. Ajuste a rota sem culpa.",
            "xp": 25,
            "fixa_concluida": False,
        }
    )

    missoes.append(
        {
            "id": "vitoria_pequena",
            "fase": "90 dias",
            "titulo": "Registrar uma vitoria pequena (mesmo uma parcela ou um acordo)",
            "descricao": "Progresso real combate desanimo — celebre com sobriedade.",
            "xp": 35,
            "fixa_concluida": False,
        }
    )

    if maior_juros >= 5:
        missoes.append(
            {
                "id": "estudar_refin",
                "fase": "30 dias",
                "titulo": "Estudar renegociacao ou portabilidade onde os juros forem muito altos",
                "descricao": f"Voce tem credores com juros a.m. elevados (~{maior_juros:.1f}% no cadastro).",
                "xp": 25,
                "fixa_concluida": False,
            }
        )

    if motor_ok:
        missoes.append(
            {
                "id": "manter_ritmo",
                "fase": "90 dias",
                "titulo": "Manter ritmo por 4 semanas seguidas o pagamento minimo+ do plano",
                "descricao": "No modelo, sua capacidade cobre os juros — consistência vira tracao.",
                "xp": 40,
                "fixa_concluida": False,
            }
        )

    return missoes


def nivel_jornada(xp_total: int) -> tuple[int, str, int, int]:
    """Retorna (nivel, titulo, xp dentro do nivel atual, xp que falta para o proximo nivel)."""
    xp_capped = max(0, xp_total)
    nivel = min(xp_capped // 100 + 1, 99)
    xp_no_nivel = xp_capped % 100
    falta_proximo = 100 - xp_no_nivel if xp_capped < 9900 else 0
    titulos = {
        1: "Escavador — saindo do atoleiro",
        2: "Trilheiro — primeira tracao",
        3: "Persistente — rota em movimento",
        4: "Estrategista — ajustando a rota",
        5: "Quitador em construcao",
    }
    titulo = titulos.get(min(nivel, 5), "Rota avancada")
    return nivel, titulo, xp_no_nivel, falta_proximo


def conquistas_jornada(
    xp_total: int,
    missoes: list[dict],
    feitas: set[str],
    diagnostico: dict,
    n_dividas: int,
) -> list[str]:
    out = []
    if "clareza_numeros" in feitas:
        out.append("Mapa claro — voce enxerga o terreno")
    if len(feitas) >= max(1, len(missoes) // 2):
        out.append("Metade da trilha — ritmo em andamento")
    if len(feitas) >= len(missoes):
        out.append("Rota consolidada — todas as missoes deste cenario")
    if diagnostico["capacidade_pagamento"] > diagnostico["custo_juros_mensal"]:
        out.append("Motor ligado — capacidade acima dos juros (no modelo)")
    if n_dividas >= 3:
        out.append("Multiplas frentes — varios credores no radar")
    if xp_total >= 80:
        out.append("XP 80+ — foco em acao")
    return out


def _fmt_simulacao(res: dict | None) -> str:
    if not res or not res.get("quitado"):
        return "nao calculado ou nao foi possivel estimar no modelo"
    return f"prazo estimado ~{res['meses']} meses; juros totais estimados R$ {res['juros_totais']:,.2f}"


def montar_contexto_para_ia(
    *,
    perfil: str,
    renda_mensal: float,
    despesas_fixas: float,
    reserva: float,
    valor_ativos_vendaveis: float,
    renda_extra_mensal: float,
    ideias_criativas: str,
    orcamento_mensal: float,
    has_sim: bool,
    reducao_juros_pct: float,
    entrada_inicial: float,
    nova_parcela_alvo: float,
    dividas: list[dict],
    diagnostico: dict,
    resultado_avalanche: dict,
    resultado_snowball: dict,
    resultado_prioridade: dict,
    resumo_renegociacao: str,
) -> str:
    linhas_dividas = []
    for d in dividas:
        sinais = []
        if d.get("risco_negativa_certidao"):
            sinais.append("negativa/restricao em certidoes")
        if d.get("risco_acao_judicial"):
            sinais.append("acao judicial ou execucao")
        if d.get("atraso"):
            sinais.append("atraso")
        linhas_dividas.append(
            f"- {d['nome']}: saldo R$ {d['saldo']:,.2f}; juros a.m. {d['juros_mensal']:.2f}%; "
            f"parcela minima R$ {d['parcela_minima']:,.2f}; prioridade informada: {d.get('prioridade', 'Normal')}; "
            f"prioridade efetiva (1-4): {prioridade_efetiva(d)}; "
            f"sinais: {', '.join(sinais) if sinais else 'nenhum'}"
        )

    bloco_ideias = ideias_criativas.strip() if ideias_criativas.strip() else "(nenhuma ideia livre informada)"

    return f"""## Dados levantados pelo formulario (Brasil)

### Perfil e caixa
- Tipo: {perfil}
- Renda/faturamento mensal: R$ {renda_mensal:,.2f}
- Despesas fixas mensais: R$ {despesas_fixas:,.2f}
- Reserva disponivel: R$ {reserva:,.2f}
- Orcamento mensal para dividas (informado): R$ {orcamento_mensal:,.2f}
- Simulacoes numericas rodadas neste envio: {"sim" if has_sim else "nao (orcamento zero ou fluxo incompleto)"}

### Ativos e renda extra (planos alternativos)
- Valor estimado em bens vendaveis: R$ {valor_ativos_vendaveis:,.2f}
- Renda extra mensal media: R$ {renda_extra_mensal:,.2f}

### Dividas (detalhe)
{chr(10).join(linhas_dividas)}

### Diagnostico agregado (modelo interno)
- Total da divida: R$ {diagnostico['total_divida']:,.2f}
- Comprometimento da renda: {diagnostico['comprometimento_renda']:.1f}%
- Capacidade mensal de pagamento (apos despesas fixas): R$ {diagnostico['capacidade_pagamento']:,.2f}
- Custo mensal estimado dos juros: R$ {diagnostico['custo_juros_mensal']:,.2f}
- Soma das parcelas minimas: R$ {diagnostico['total_minimos']:,.2f}
- Nivel de risco (regra simples): {diagnostico['risco']}

### Resultados das simulacoes (referencia, nao garantia)
- Avalanche: {_fmt_simulacao(resultado_avalanche)}
- Snowball: {_fmt_simulacao(resultado_snowball)}
- Por prioridade (marcada pelo usuario): {_fmt_simulacao(resultado_prioridade)}

### Renegociacao (parametros informados)
- Reducao de juros esperada: {reducao_juros_pct:.1f}%
- Entrada inicial: R$ {entrada_inicial:,.2f}
- Nova parcela total alvo: R$ {nova_parcela_alvo:,.2f}
- Resumo da simulacao de renegociacao (se houver): {resumo_renegociacao}

### Ideias criativas (texto livre do usuario)
{bloco_ideias}

---
Instrucao: use estes dados como base. Seja realista, acolhedor e encorajador sem prometer resultados juridicos ou em cadastros.
"""


def gerar_estrategia_com_ia(contexto: str) -> tuple[str | None, str | None]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "OPENAI_API_KEY nao configurada."

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = (
        "Voce e um planejador financeiro educacional para pessoas e pequenas empresas no Brasil. "
        "Responda em portugues do Brasil, com tom acolhedor e direto, sem julgar. "
        "Monte uma estrategia realista e, quando possivel, esperancosa — sem milagres, sem garantias legais "
        "ou promessas de quitacao em prazo fixo. "
        "Diferencie claramente: (1) prioridade por risco operacional/juridico quando o usuario marcou sinais; "
        "(2) prioridade matematica por juros quando fizer sentido. "
        "Inclua secoes curtas: visao geral; o que atacar primeiro e por que; proximos passos em 7, 30 e 90 dias; "
        "uma ou duas ideias fora da caixinha porem racionais (ex.: venda de ativos, renda extra), alinhadas ao que o usuario escreveu; "
        "cuidados com saude emocional e disciplina. "
        "Lembre que voce nao substitui advogado, contador ou credito-scoring."
    )

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": contexto},
            ],
            temperature=0.65,
            max_tokens=2200,
        )
        texto = completion.choices[0].message.content
        return texto, None
    except Exception as exc:
        return None, str(exc)


def main() -> None:
    st.set_page_config(page_title="Rota de Quitacao", page_icon="📊", layout="centered")

    st.title("Rota de Quitacao")
    st.subheader("Diagnostico financeiro e simulacao de quitacao")
    st.caption(
        "O formulario levanta dados reais da sua situacao; eles viram o contexto para a estrategia assistida por IA "
        "(opcional), alinhada aos numeros calculados aqui."
    )
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

        st.markdown("### 1b) Ativos, rendas extras e planos alternativos (opcional)")
        st.caption(
            "Use estes campos para simular cenarios como venda de bens, freelas ou outras fontes de caixa."
        )
        valor_ativos_vendaveis = st.number_input(
            "Valor estimado em bens que pode vender (ex.: eletronicos, colecao, veiculo) (R$)",
            min_value=0.0,
            step=100.0,
        )
        renda_extra_mensal = st.number_input(
            "Renda extra mensal media que pode dedicar as dividas (freelas, aluguel, etc.) (R$)",
            min_value=0.0,
            step=50.0,
        )
        ideias_criativas = st.text_area(
            "Ideias para gerar caixa (livre)",
            placeholder="Ex.: vender colecao de vinil aos poucos; dar aulas no fim de semana; negociar antecipacao de 13o.",
            height=100,
        )

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

            prioridade = st.selectbox(
                "Prioridade na sua rota",
                ["Urgente", "Alta", "Normal", "Baixa"],
                index=2,
                key=f"prior_{i}",
                help="Urgente: risco juridico, negativacao, cobranca critica. Baixa: pode manter o minimo por mais tempo.",
            )
            cbf1, cbf2 = st.columns(2)
            with cbf1:
                risco_negativa_certidao = st.checkbox(
                    "Negativa / restricao em certidoes ou cadastros",
                    key=f"neg_{i}",
                )
            with cbf2:
                risco_acao_judicial = st.checkbox(
                    "Acao judicial ou execucao em andamento",
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

        st.caption("---")
        gerar_ia_no_envio = st.checkbox(
            "Gerar estrategia com IA ao enviar (os dados deste formulario viram o contexto do modelo; requer OPENAI_API_KEY)",
            value=False,
            help="A IA usa apenas o que voce informou aqui, mais os numeros calculados no app, para sugerir uma rota realista e encorajadora.",
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

    st.session_state.pop("estrategia_ia", None)

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

    st.markdown("### Priorizacao das dividas")
    st.caption(
        "A ordem abaixo reflete o que voce marcou (urgencia, juros altos, negativa, acoes). "
        "Nao e parecer juridico: use para organizar a rota e converse com profissional quando houver risco legal."
    )
    ordem = sorted(
        dividas,
        key=lambda d: (-prioridade_efetiva(d), -d["juros_mensal"], d["nome"]),
    )
    tabela_prior = []
    for idx, d in enumerate(ordem, start=1):
        flags = []
        if d.get("risco_negativa_certidao"):
            flags.append("certidao/cadastro")
        if d.get("risco_acao_judicial"):
            flags.append("acao/execucao")
        if d.get("atraso"):
            flags.append("atraso")
        tabela_prior.append(
            {
                "Ordem sugerida": idx,
                "Nome": d["nome"],
                "Prioridade (voce)": d.get("prioridade", "Normal"),
                "Peso (1-4)": prioridade_efetiva(d),
                "Juros a.m. (%)": d["juros_mensal"],
                "Saldo (R$)": d["saldo"],
                "Sinais": ", ".join(flags) if flags else "-",
            }
        )
    st.dataframe(pd.DataFrame(tabela_prior), use_container_width=True, hide_index=True)

    with st.expander("Sobre prioridade vs simulacao matematica", expanded=False):
        st.write(
            "**Avalanche** minimiza juros no modelo. **Snowball** acelera vitorias psicologicas. "
            "**Por prioridade** direciona o excedente primeiro para o que voce classificou como mais urgente "
            "(e desempata por juros). Em dividas com risco juridico ou negativa, a ordem real pode precisar "
            "de ajuste com assessoria juridica ou contabil."
        )
        st.write(
            "**Estrategia com IA:** marque a opcao ao final do formulario para gerar um texto com base nestes dados — "
            "sugestoes fora da caixinha e racionais, sem prometer resultado em tribunais ou cadastros."
        )

    if orcamento_mensal <= 0:
        st.warning(
            "Orcamento mensal para dividas igual a zero: as simulacoes numericas nao serao executadas. "
            "Voce ainda pode usar a estrategia com IA com o restante dos dados."
        )
        has_sim = False
        resultado_avalanche = {"quitado": False, "meses": None, "juros_totais": None}
        resultado_snowball = {"quitado": False, "meses": None, "juros_totais": None}
        resultado_prioridade = {"quitado": False, "meses": None, "juros_totais": None}
    else:
        has_sim = True
        resultado_avalanche = simular_quitacao(dividas, orcamento_mensal, "avalanche")
        resultado_snowball = simular_quitacao(dividas, orcamento_mensal, "snowball")
        resultado_prioridade = simular_quitacao(dividas, orcamento_mensal, "prioridade")

    st.markdown("### Simulacao de estrategias")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Avalanche (maior juros primeiro)**")
        if resultado_avalanche["quitado"]:
            st.metric("Prazo estimado", f"{resultado_avalanche['meses']} meses")
            st.metric("Juros totais estimados", f"R$ {resultado_avalanche['juros_totais']:,.2f}")
        else:
            st.error("Nao foi possivel estimar quitacao no horizonte de simulacao.")

    with col2:
        st.markdown("**Snowball (menor saldo primeiro)**")
        if resultado_snowball["quitado"]:
            st.metric("Prazo estimado", f"{resultado_snowball['meses']} meses")
            st.metric("Juros totais estimados", f"R$ {resultado_snowball['juros_totais']:,.2f}")
        else:
            st.error("Nao foi possivel estimar quitacao no horizonte de simulacao.")

    with col3:
        st.markdown("**Por prioridade (o que voce marcou)**")
        if resultado_prioridade["quitado"]:
            st.metric("Prazo estimado", f"{resultado_prioridade['meses']} meses")
            st.metric("Juros totais estimados", f"R$ {resultado_prioridade['juros_totais']:,.2f}")
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

    if resultado_prioridade["quitado"] and resultado_avalanche["quitado"]:
        st.markdown("**Prioridade vs Avalanche (matematico)**")
        dj = resultado_avalanche["juros_totais"] - resultado_prioridade["juros_totais"]
        dm = resultado_avalanche["meses"] - resultado_prioridade["meses"]
        if dj > 0:
            st.info(
                f"Na simulacao, priorizar o que voce marcou pode custar cerca de R$ {dj:,.2f} a mais em juros "
                "que o Avalanche puro — troca comum entre custo financeiro e urgencia juridica/operacional."
            )
        elif dj < 0:
            st.info(
                f"Neste cenario, a rota por prioridade ficou com cerca de R$ {abs(dj):,.2f} a menos em juros "
                "que o Avalanche puro."
            )
        if dm != 0:
            st.caption(
                f"Diferenca de prazo entre Avalanche e prioridade: {abs(dm)} meses "
                f"({'Avalanche mais rapido' if dm > 0 else 'prioridade mais rapida'} neste modelo)."
            )

    st.markdown("### Planos alternativos (ativos + renda extra)")
    col_alt1, col_alt2 = st.columns(2)
    with col_alt1:
        st.metric("Renda extra mensal informada", f"R$ {renda_extra_mensal:,.2f}")
        st.metric("Valor em bens vendaveis (entrada unica simulada)", f"R$ {valor_ativos_vendaveis:,.2f}")
    with col_alt2:
        colchao_potencial = reserva + valor_ativos_vendaveis
        st.metric("Colchao potencial (reserva + venda de bens)", f"R$ {colchao_potencial:,.2f}")

    if ideias_criativas.strip():
        with st.expander("Suas ideias para a rota de quitacao", expanded=True):
            st.write(ideias_criativas.strip())

    tem_alternativa = renda_extra_mensal > 0 or valor_ativos_vendaveis > 0
    if tem_alternativa:
        orcamento_com_extra = orcamento_mensal + renda_extra_mensal
        alt_avalanche_extra = (
            simular_quitacao(dividas, orcamento_com_extra, "avalanche")
            if orcamento_com_extra > 0
            else {"quitado": False, "meses": None, "juros_totais": None}
        )

        dividas_pos_venda, entrada_ativos = abater_saldo_proporcional(dividas, valor_ativos_vendaveis)
        alt_avalanche_venda = (
            simular_quitacao(dividas_pos_venda, orcamento_mensal, "avalanche")
            if valor_ativos_vendaveis > 0 and any(d["saldo"] > 0.01 for d in dividas_pos_venda)
            else None
        )
        alt_combinado = (
            simular_quitacao(dividas_pos_venda, orcamento_com_extra, "avalanche")
            if valor_ativos_vendaveis > 0 and orcamento_com_extra > 0
            and any(d["saldo"] > 0.01 for d in dividas_pos_venda)
            else None
        )

        st.markdown("**Comparativo com cenario base (Avalanche)**")
        if resultado_avalanche["quitado"]:
            st.caption(
                f"Base: {resultado_avalanche['meses']} meses, "
                f"juros totais R$ {resultado_avalanche['juros_totais']:,.2f}"
            )

        if renda_extra_mensal > 0 and alt_avalanche_extra["quitado"]:
            st.success(
                f"Com renda extra mensal: quitacao estimada em {alt_avalanche_extra['meses']} meses "
                f"(orcamento mensal R$ {orcamento_com_extra:,.2f}), "
                f"juros totais R$ {alt_avalanche_extra['juros_totais']:,.2f}."
            )
            if resultado_avalanche["quitado"]:
                d_m = resultado_avalanche["meses"] - alt_avalanche_extra["meses"]
                d_j = resultado_avalanche["juros_totais"] - alt_avalanche_extra["juros_totais"]
                st.info(f"Diferenca aproximada vs base: {d_m} meses a menos, economia de R$ {d_j:,.2f} em juros.")

        if valor_ativos_vendaveis > 0:
            if entrada_ativos > 0 and all(d["saldo"] <= 0.01 for d in dividas_pos_venda):
                st.success(
                    f"Com a venda simulada dos bens (R$ {entrada_ativos:,.2f}), "
                    "as dividas seriam quitadas de imediato neste modelo."
                )
            elif alt_avalanche_venda and alt_avalanche_venda["quitado"]:
                st.success(
                    f"Apos entrada unica com venda de bens (R$ {entrada_ativos:,.2f}): "
                    f"quitacao em {alt_avalanche_venda['meses']} meses, "
                    f"juros totais R$ {alt_avalanche_venda['juros_totais']:,.2f}."
                )

        if (
            alt_combinado
            and alt_combinado["quitado"]
            and valor_ativos_vendaveis > 0
            and renda_extra_mensal > 0
        ):
            st.success(
                f"Cenario combinado (venda + renda extra): quitacao em {alt_combinado['meses']} meses, "
                f"juros totais R$ {alt_combinado['juros_totais']:,.2f}."
            )
    else:
        st.info(
            "Informe renda extra ou valor em bens vendaveis para ver simulacoes alternativas "
            "ao seu cenario atual."
        )

    st.markdown("### Simulacao de renegociacao")
    resumo_renegociacao = "Nenhum parametro de renegociacao preenchido ou simulacao nao executada neste envio."
    if reducao_juros_pct <= 0 and entrada_inicial <= 0 and nova_parcela_alvo <= 0:
        st.info("Preencha os campos de renegociacao para estimar o impacto no prazo e no custo total.")
    else:
        dividas_renegociadas, entrada_utilizada = aplicar_renegociacao(
            dividas=dividas,
            reducao_juros_pct=float(reducao_juros_pct),
            entrada_inicial=entrada_inicial,
            nova_parcela_alvo=nova_parcela_alvo,
        )

        if all(item["saldo"] <= 0.01 for item in dividas_renegociadas):
            st.success("Com a entrada informada, todas as dividas seriam quitadas imediatamente.")
            resumo_renegociacao = (
                "Simulacao: entrada informada quitou todos os saldos no modelo imediatamente."
            )
        else:
            orcamento_renegociado = nova_parcela_alvo if nova_parcela_alvo > 0 else orcamento_mensal
            if orcamento_renegociado <= 0:
                st.warning("Informe uma nova parcela alvo maior que zero para simular a renegociacao.")
            else:
                base_renegociacao = simular_quitacao(dividas_renegociadas, orcamento_renegociado, "avalanche")
                base_original = simular_quitacao(dividas, orcamento_mensal, "avalanche")

                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("Entrada considerada", f"R$ {entrada_utilizada:,.2f}")
                    st.metric("Orcamento mensal renegociado", f"R$ {orcamento_renegociado:,.2f}")
                with col_r2:
                    custo_juros_renegociado = sum(
                        item["saldo"] * (item["juros_mensal"] / 100) for item in dividas_renegociadas
                    )
                    st.metric("Novo custo mensal estimado dos juros", f"R$ {custo_juros_renegociado:,.2f}")
                    st.metric("Reducao de juros aplicada", f"{float(reducao_juros_pct):.1f}%")

                if base_renegociacao["quitado"]:
                    st.success(
                        f"Cenario renegociado: quitacao estimada em {base_renegociacao['meses']} meses "
                        f"com juros totais de R$ {base_renegociacao['juros_totais']:,.2f}."
                    )
                else:
                    st.error(
                        "No cenario renegociado, nao foi possivel estimar quitacao no horizonte de simulacao."
                    )

                if base_renegociacao["quitado"] and base_original["quitado"]:
                    delta_meses = base_original["meses"] - base_renegociacao["meses"]
                    delta_juros = base_original["juros_totais"] - base_renegociacao["juros_totais"]
                    st.info(
                        f"Impacto estimado vs cenario original (Avalanche): "
                        f"{delta_meses} meses a menos e economia de R$ {delta_juros:,.2f} em juros."
                    )
                    resumo_renegociacao = (
                        f"Quitacao renegociada estimada em {base_renegociacao['meses']} meses; "
                        f"juros totais R$ {base_renegociacao['juros_totais']:,.2f}. "
                        f"Vs Avalanche original: {delta_meses} meses a menos e R$ {delta_juros:,.2f} a menos em juros."
                    )
                elif base_renegociacao["quitado"]:
                    resumo_renegociacao = (
                        f"Quitacao renegociada estimada em {base_renegociacao['meses']} meses; "
                        f"juros totais R$ {base_renegociacao['juros_totais']:,.2f}."
                    )
                else:
                    resumo_renegociacao = (
                        "Cenario renegociado nao convergiu no horizonte de simulacao do modelo."
                    )

    st.markdown("### Estrategia com IA (dados reais do formulario)")
    st.caption(
        "O objetivo e transformar o que voce informou em um plano acionavel, com tom acolhedor e realista — "
        "sem substituir orientacao profissional."
    )
    if gerar_ia_no_envio:
        contexto = montar_contexto_para_ia(
            perfil=perfil,
            renda_mensal=renda_mensal,
            despesas_fixas=despesas_fixas,
            reserva=reserva,
            valor_ativos_vendaveis=valor_ativos_vendaveis,
            renda_extra_mensal=renda_extra_mensal,
            ideias_criativas=ideias_criativas,
            orcamento_mensal=orcamento_mensal,
            has_sim=has_sim,
            reducao_juros_pct=float(reducao_juros_pct),
            entrada_inicial=entrada_inicial,
            nova_parcela_alvo=nova_parcela_alvo,
            dividas=dividas,
            diagnostico=diagnostico,
            resultado_avalanche=resultado_avalanche,
            resultado_snowball=resultado_snowball,
            resultado_prioridade=resultado_prioridade,
            resumo_renegociacao=resumo_renegociacao,
        )
        with st.expander("Ver contexto enviado ao modelo (prompt de usuario)", expanded=False):
            st.text(contexto)

        if not os.getenv("OPENAI_API_KEY"):
            st.warning(
                "Defina a variavel de ambiente OPENAI_API_KEY (ex.: no Railway) para gerar o texto. "
                "Opcional: OPENAI_MODEL (padrao gpt-4o-mini)."
            )
        else:
            with st.spinner("Montando sua estrategia com IA..."):
                texto_ia, erro_ia = gerar_estrategia_com_ia(contexto)
            if erro_ia:
                st.error(f"Nao foi possivel gerar o texto agora: {erro_ia}")
            elif texto_ia:
                st.session_state["estrategia_ia"] = texto_ia

    if st.session_state.get("estrategia_ia"):
        st.markdown(st.session_state["estrategia_ia"])
    elif not gerar_ia_no_envio:
        st.info(
            "Marque a opcao no final do formulario para gerar uma estrategia com IA usando os dados reais "
            "que voce informou."
        )

    st.markdown("### Jornada gamificada — sair do atoleiro")
    st.caption(
        "Missoes geradas a partir do seu cenario real. Marque ao concluir. "
        "O progresso fica nesta sessao do navegador; com login e persistencia no futuro, vira historico e sequencia."
    )
    fp = fingerprint_cenario(dividas, orcamento_mensal, renda_mensal)
    if st.session_state.get("jornada_fp") != fp:
        st.session_state["jornada_fp"] = fp
        for k in list(st.session_state.keys()):
            if str(k).startswith("jornada_chk_"):
                del st.session_state[k]

    missoes_jornada = gerar_missoes_jornada(
        dividas, diagnostico, has_sim, valor_ativos_vendaveis, renda_extra_mensal
    )

    xp_total = sum(
        m["xp"]
        for m in missoes_jornada
        if m.get("fixa_concluida")
        or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    )
    feitas = {
        m["id"]
        for m in missoes_jornada
        if m.get("fixa_concluida")
        or st.session_state.get(f"jornada_chk_{fp}_{m['id']}", False)
    }

    nv, titulo_nv, xp_no, falta = nivel_jornada(xp_total)
    cj1, cj2, cj3 = st.columns(3)
    with cj1:
        st.metric("Nivel da jornada", nv)
    with cj2:
        st.metric("Titulo", titulo_nv)
    with cj3:
        st.metric("XP total", xp_total)
    st.progress(min(xp_no / 100.0, 1.0))
    st.caption(
        f"Proximo nivel: faltam cerca de {falta} XP (100 XP por nivel). "
        f"Missoes completas: {len(feitas)} / {len(missoes_jornada)}."
    )

    conquistas = conquistas_jornada(xp_total, missoes_jornada, feitas, diagnostico, len(dividas))
    if conquistas:
        st.markdown("**Conquistas desbloqueadas**")
        for c in conquistas:
            st.success(c)

    fases_ordem = ["Base", "7 dias", "30 dias", "90 dias"]
    por_fase: dict[str, list[dict]] = {f: [] for f in fases_ordem}
    for m in missoes_jornada:
        if m["fase"] in por_fase:
            por_fase[m["fase"]].append(m)

    for fase in fases_ordem:
        if not por_fase[fase]:
            continue
        st.markdown(f"**{fase}**")
        for m in por_fase[fase]:
            if m.get("fixa_concluida"):
                st.success(f"Concluida: {m['titulo']} (+{m['xp']} XP)")
            else:
                st.checkbox(
                    f"{m['titulo']} (+{m['xp']} XP)",
                    key=f"jornada_chk_{fp}_{m['id']}",
                    help=m["descricao"],
                )
            st.caption(m["descricao"])


if __name__ == "__main__":
    main()
