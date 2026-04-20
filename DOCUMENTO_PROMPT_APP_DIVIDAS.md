# Documento de Prompt — App de Diagnóstico e Plano de Dívidas

## Objetivo

Criar um novo app web simples (MVP), em português-BR, para ajudar pessoas e pequenas empresas no Brasil a:

1. Dimensionar o tamanho do endividamento.
2. Entender o impacto dos juros no fluxo mensal.
3. Simular cenários de renegociação e quitação.
4. Receber um plano de ação prático, sem promessas irreais.

---

## Prompt mestre (para usar com IA no novo projeto)

```text
Atue como um AI Solutions Architect sênior, Product Manager e Engenheiro Full Stack Python.

Quero que você construa um MVP de um app chamado "Rota de Quitação" (nome provisório), focado no público brasileiro (pessoa física e pequena empresa), com linguagem clara e acolhedora, para diagnóstico financeiro e plano de quitação de dívidas.

### Contexto de negócio
- O usuário está endividado e precisa de clareza.
- O app NÃO promete milagre.
- O app deve mostrar "tamanho do buraco", prioridades e plano executável.
- O app deve permitir comparar estratégias de pagamento:
  1) Avalanche (maior juros primeiro)
  2) Snowball (menor saldo primeiro)

### Requisitos de produto (MVP)
1. Tela de entrada com explicação curta e botão "Começar diagnóstico".
2. Formulário com dados básicos:
   - Tipo de perfil: pessoa física ou empresa.
   - Renda/faturamento mensal.
   - Despesas fixas mensais.
   - Reserva disponível.
3. Cadastro de múltiplas dívidas (lista dinâmica), cada uma com:
   - Nome da dívida/credor.
   - Saldo devedor.
   - Taxa de juros mensal (%).
   - Parcela mínima.
   - Está em atraso? (sim/não).
4. Diagnóstico automático com indicadores:
   - Total da dívida.
   - Comprometimento da renda (%).
   - Custo mensal estimado dos juros.
   - Capacidade de pagamento mensal.
   - Nível de risco (baixo/médio/alto) com regra transparente.
5. Simulação de estratégias:
   - Avalanche
   - Snowball
   Exibir tempo estimado para quitação e total de juros pagos em cada método.
6. Simulação de renegociação:
   - Redução de juros (%)
   - Entrada inicial (valor opcional)
   - Nova parcela alvo
   Mostrar impacto no prazo e no custo total.
7. Plano de ação final:
   - Ações imediatas (7 dias)
   - Ações de 30 dias
   - Ações de 90 dias
   - Alertas de disciplina financeira
8. Exportar relatório em HTML (e instrução para salvar em PDF pelo navegador).

### Requisitos técnicos
- Stack: Python + Streamlit + Plotly.
- Persistência: PostgreSQL (Supabase) com fallback em CSV.
- Deploy target: Railway.
- Usar variáveis de ambiente com os.getenv para segredos.
- Nunca hardcode de chaves/API.
- Código organizado em funções legíveis.
- Tratar erros de entrada de dados com mensagens amigáveis.

### Variáveis de ambiente esperadas
- DATABASE_URL
- OPENAI_API_KEY (opcional para gerar texto explicativo do plano)
- OPENAI_MODEL (opcional)

### Regras de cálculo (transparência)
- Explicite as fórmulas usadas para:
  - comprometimento da renda
  - custo de juros mensal
  - prazo estimado de quitação
- Se capacidade de pagamento <= juros mensais, avisar que há "risco de bola de neve".
- Não usar linguagem de garantia ("você vai quitar em X meses com certeza").

### UX e comunicação
- Tom empático, sem julgamento.
- Frases curtas e objetivas.
- Explicar termos financeiros em linguagem simples.
- Exibir avisos legais:
  - "Este app oferece apoio educacional e de planejamento financeiro."
  - "Não substitui orientação profissional contábil/jurídica."

### Entregáveis que você deve gerar
1. Estrutura de arquivos sugerida para o projeto.
2. Código inicial funcional (app.py e auxiliares).
3. requirements.txt completo.
4. Procfile para Railway.
5. Script SQL para criar tabela principal no Supabase.
6. Checklist de deploy passo a passo no Railway.
7. Sugestão de próximos incrementos (login, histórico mensal, alertas WhatsApp, etc.).

### Critérios de qualidade
- App deve rodar localmente sem erro.
- Fluxo completo: entrada -> diagnóstico -> simulação -> plano -> exportação.
- Interface limpa e profissional.
- Mensagens de erro e estado bem tratadas.
```

---

## Prompt curto (versão rápida)

```text
Crie um app Streamlit em português-BR chamado "Rota de Quitação" para pessoa física e pequena empresa, que receba renda, despesas e múltiplas dívidas, calcule o tamanho do endividamento, simule métodos Avalanche e Snowball, permita cenário de renegociação (juros menores, entrada, nova parcela) e gere plano de ação em 7/30/90 dias com relatório em HTML. Use PostgreSQL (Supabase) com fallback CSV, deploy no Railway, sem hardcode de segredos (os.getenv), e inclua SQL da tabela + Procfile + checklist de deploy.
```

---

## Escopo recomendado do primeiro ciclo (1 semana)

- Dia 1: Estrutura base do app + formulário + validações.
- Dia 2: Motor de cálculo (indicadores + avalanche/snowball).
- Dia 3: Simulador de renegociação.
- Dia 4: Relatório HTML + ajustes de UX.
- Dia 5: Persistência Supabase + fallback CSV.
- Dia 6: Deploy Railway + testes completos.
- Dia 7: Revisão final, checklist LGPD e backlog de melhorias.

---

## Nome e posicionamento (sugestões)

- Nome: `Rota de Quitação`
- Subtítulo: `Clareza financeira para sair do vermelho com plano realista`
- Proposta de valor: `Você entende o tamanho da dívida, escolhe a melhor rota e executa com disciplina.`

