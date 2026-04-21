import hashlib
import json
import os

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
            "titulo": "Voce colocou o mapa na mesa",
            "descricao": "Registrar renda, despesas e dividas ja e um passo de coragem. Isso e seu ponto de partida.",
            "xp": 25,
            "fixa_concluida": True,
        },
        {
            "id": "foco_primeiro",
            "fase": "7 dias",
            "titulo": f"Decidir por onde comecar: {primeiro_nome}",
            "descricao": "Escolha um primeiro alvo (o que mais pesa no bolso ou no coracao). Um de cada vez.",
            "xp": 30,
            "fixa_concluida": False,
        },
        {
            "id": "contato_credor",
            "fase": "7 dias",
            "titulo": f"Agendar contato ou negociacao com: {primeiro_nome}",
            "descricao": "Pode ser so pedir extrato ou falar de renegociacao. O importante e dar o primeiro passo.",
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
                "titulo": "Separar na vida real o dinheiro das dividas",
                "descricao": "Guardar separado o valor que voce pode pagar por mes, sem misturar com o resto.",
                "xp": 25,
                "fixa_concluida": False,
            },
        )

    if tem_risco_legal:
        missoes.append(
            {
                "id": "orientacao_legal",
                "fase": "7 dias",
                "titulo": "Cuidar da parte seria (negativa, acao ou execucao)",
                "descricao": "Se marcou risco juridico, vale conversar com um profissional. Aqui so ha apoio educacional.",
                "xp": 40,
                "fixa_concluida": False,
            }
        )

    if valor_ativos > 0:
        missoes.append(
            {
                "id": "venda_ativos",
                "fase": "30 dias",
                "titulo": "Transformar venda de bens em acao concreta",
                "descricao": "Lista, precos, fotos, onde vender. Pequenos passos contam.",
                "xp": 30,
                "fixa_concluida": False,
            }
        )

    if renda_extra > 0:
        missoes.append(
            {
                "id": "teste_renda_extra",
                "fase": "30 dias",
                "titulo": "Testar por 2 semanas sua renda extra",
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
            "descricao": "Anotar uma vitória real, mesmo pequena. Isso alimenta a jornada.",
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
                "descricao": "No modelo, sua capacidade cobre os juros. Constancia vira tracao.",
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
        1: "Escavador - saindo do atoleiro",
        2: "Trilheiro - primeira tracao",
        3: "Persistente - rota em movimento",
        4: "Estrategista - ajustando a rota",
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
        out.append("Mapa claro - voce enxerga o terreno")
    if len(feitas) >= max(1, len(missoes) // 2):
        out.append("Metade da trilha - ritmo em andamento")
    if len(feitas) >= len(missoes):
        out.append("Rota consolidada - todas as missoes deste cenario")
    if diagnostico["capacidade_pagamento"] > diagnostico["custo_juros_mensal"]:
        out.append("Motor ligado - capacidade acima dos juros (no modelo)")
    if n_dividas >= 3:
        out.append("Multiplas frentes - varios credores no radar")
    if xp_total >= 80:
        out.append("XP 80+ - foco em acao")
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


def validar_openai_api_key() -> tuple[bool, str | None]:
    """Verifica se a OPENAI_API_KEY esta configurada e e aceita pela API.

    Retorna (True, None) se valida, ou (False, mensagem_de_erro) caso contrario.
    Usa uma chamada minima (max_tokens=1) para nao gerar custo significativo.
    """
    import logging

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return False, "OPENAI_API_KEY nao configurada ou vazia."

    try:
        from openai import AuthenticationError, OpenAI

        client = OpenAI(api_key=api_key)
        client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        logging.info("validar_openai_api_key: chave valida.")
        return True, None
    except AuthenticationError as exc:
        msg = f"Chave OpenAI invalida ou sem permissao (AuthenticationError): {exc}"
        logging.error("validar_openai_api_key: %s", msg)
        return False, msg
    except Exception as exc:
        msg = f"Erro ao validar chave OpenAI: {exc}"
        logging.error("validar_openai_api_key: %s", msg)
        return False, msg


def gerar_estrategia_com_ia(contexto: str) -> tuple[str | None, str | None]:
    import logging

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None, "OPENAI_API_KEY nao configurada ou vazia."

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    logging.info("gerar_estrategia_com_ia: usando modelo '%s'.", model)

    system = (
        "Voce e um planejador financeiro educacional para pessoas e pequenas empresas no Brasil. "
        "Responda em portugues do Brasil, com tom acolhedor e direto, sem julgar. "
        "Monte uma estrategia realista e, quando possivel, esperancosa - sem milagres, sem garantias legais "
        "ou promessas de quitacao em prazo fixo. "
        "Diferencie claramente: (1) prioridade por risco operacional/juridico quando o usuario marcou sinais; "
        "(2) prioridade matematica por juros quando fizer sentido. "
        "Inclua secoes curtas: visao geral; o que atacar primeiro e por que; proximos passos em 7, 30 e 90 dias; "
        "uma ou duas ideias fora da caixinha porem racionais (ex.: venda de ativos, renda extra), alinhadas ao que o usuario escreveu; "
        "cuidados com saude emocional e disciplina. "
        "Lembre que voce nao substitui advogado, contador ou credito-scoring."
    )

    try:
        from openai import (
            APIConnectionError,
            APIStatusError,
            AuthenticationError,
            OpenAI,
            RateLimitError,
        )

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
        logging.info("gerar_estrategia_com_ia: resposta recebida com sucesso.")
        return texto, None
    except AuthenticationError as exc:
        msg = f"Chave OpenAI invalida ou sem permissao. Verifique OPENAI_API_KEY. Detalhe: {exc}"
        logging.error("gerar_estrategia_com_ia: AuthenticationError — %s", exc)
        return None, msg
    except RateLimitError as exc:
        msg = f"Limite de requisicoes ou cota da OpenAI atingido. Tente novamente em instantes. Detalhe: {exc}"
        logging.error("gerar_estrategia_com_ia: RateLimitError — %s", exc)
        return None, msg
    except APIConnectionError as exc:
        msg = f"Nao foi possivel conectar a API da OpenAI. Verifique a conectividade do servidor. Detalhe: {exc}"
        logging.error("gerar_estrategia_com_ia: APIConnectionError — %s", exc)
        return None, msg
    except APIStatusError as exc:
        msg = f"Erro HTTP {exc.status_code} retornado pela API da OpenAI. Detalhe: {exc.message}"
        logging.error("gerar_estrategia_com_ia: APIStatusError %s — %s", exc.status_code, exc.message)
        return None, msg
    except Exception as exc:
        msg = f"Erro inesperado ao chamar a OpenAI (modelo: {model}): {exc}"
        logging.error("gerar_estrategia_com_ia: erro inesperado — %s", exc)
        return None, msg


def compute_full_analysis(dados: dict) -> dict:
    """Agrega diagnostico, simulacoes e resumo de renegociacao a partir de rz_dados."""
    dividas = dados["dividas"]
    renda_mensal = float(dados["renda_mensal"])
    despesas_fixas = float(dados["despesas_fixas"])
    reserva = float(dados["reserva"])
    orcamento_mensal = float(dados.get("orcamento_mensal") or 0)
    valor_ativos = float(dados.get("valor_ativos_vendaveis") or 0)
    renda_extra = float(dados.get("renda_extra_mensal") or 0)
    reducao_juros_pct = float(dados.get("reducao_juros_pct") or 0)
    entrada_inicial = float(dados.get("entrada_inicial") or 0)
    nova_parcela_alvo = float(dados.get("nova_parcela_alvo") or 0)

    diagnostico = calcular_diagnostico(renda_mensal, despesas_fixas, reserva, dividas)

    if orcamento_mensal <= 0:
        has_sim = False
        resultado_avalanche = {"quitado": False, "meses": None, "juros_totais": None}
        resultado_snowball = {"quitado": False, "meses": None, "juros_totais": None}
        resultado_prioridade = {"quitado": False, "meses": None, "juros_totais": None}
    else:
        has_sim = True
        resultado_avalanche = simular_quitacao(dividas, orcamento_mensal, "avalanche")
        resultado_snowball = simular_quitacao(dividas, orcamento_mensal, "snowball")
        resultado_prioridade = simular_quitacao(dividas, orcamento_mensal, "prioridade")

    orcamento_com_extra = orcamento_mensal + renda_extra
    if orcamento_com_extra > 0:
        alt_avalanche_extra = simular_quitacao(dividas, orcamento_com_extra, "avalanche")
    else:
        alt_avalanche_extra = {"quitado": False, "meses": None, "juros_totais": None}

    dividas_pos_venda, _entrada_ativos = abater_saldo_proporcional(dividas, valor_ativos)
    if valor_ativos > 0 and any(d["saldo"] > 0.01 for d in dividas_pos_venda):
        alt_avalanche_venda = simular_quitacao(dividas_pos_venda, orcamento_mensal, "avalanche")
        alt_combinado = (
            simular_quitacao(dividas_pos_venda, orcamento_com_extra, "avalanche")
            if orcamento_com_extra > 0
            else None
        )
    else:
        alt_avalanche_venda = None
        alt_combinado = None

    alternativas = {
        "avalanche_extra": alt_avalanche_extra,
        "pos_venda": alt_avalanche_venda,
        "combinado": alt_combinado,
    }

    resumo_renegociacao = (
        "Nenhum parametro de renegociacao preenchido ou simulacao nao executada neste envio."
    )
    base_renegociacao = None
    base_original = None

    if reducao_juros_pct > 0 or entrada_inicial > 0 or nova_parcela_alvo > 0:
        dividas_renegociadas, _eu = aplicar_renegociacao(
            dividas, reducao_juros_pct, entrada_inicial, nova_parcela_alvo
        )
        if all(item["saldo"] <= 0.01 for item in dividas_renegociadas):
            resumo_renegociacao = (
                "Simulacao: entrada informada quitou todos os saldos no modelo imediatamente."
            )
        else:
            orcamento_renegociado = nova_parcela_alvo if nova_parcela_alvo > 0 else orcamento_mensal
            if orcamento_renegociado <= 0:
                resumo_renegociacao = "Informe parcela alvo ou orcamento para simular renegociacao."
            else:
                base_renegociacao = simular_quitacao(dividas_renegociadas, orcamento_renegociado, "avalanche")
                base_original = (
                    simular_quitacao(dividas, orcamento_mensal, "avalanche")
                    if orcamento_mensal > 0
                    else {"quitado": False, "meses": None, "juros_totais": None}
                )
                if base_renegociacao["quitado"] and base_original.get("quitado"):
                    delta_meses = base_original["meses"] - base_renegociacao["meses"]
                    delta_juros = base_original["juros_totais"] - base_renegociacao["juros_totais"]
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

    return {
        "diagnostico": diagnostico,
        "has_sim": has_sim,
        "resultado_avalanche": resultado_avalanche,
        "resultado_snowball": resultado_snowball,
        "resultado_prioridade": resultado_prioridade,
        "alternativas": alternativas,
        "resumo_renegociacao": resumo_renegociacao,
        "base_renegociacao": base_renegociacao,
        "base_original": base_original,
    }


def proxima_missao_aberta(missoes: list[dict], ids_feitos: set[str]) -> dict | None:
    for m in missoes:
        if m.get("fixa_concluida"):
            continue
        if m["id"] not in ids_feitos:
            return m
    return None


def progresso_jornada_pct(missoes: list[dict], ids_feitos: set[str]) -> float:
    total = len([m for m in missoes if not m.get("fixa_concluida")])
    if total == 0:
        return 100.0
    feitas = len([m for m in missoes if not m.get("fixa_concluida") and m["id"] in ids_feitos])
    return round(100.0 * feitas / total, 1)
