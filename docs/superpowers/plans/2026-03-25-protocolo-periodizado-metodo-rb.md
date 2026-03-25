# Protocolo Periodizado com Método RB — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Melhorar a geração de treinos do Jarvis para sempre produzir protocolos periodizados de 4-5 semanas com 12-15 exercícios por sessão, método de treino por exercício, citações apenas ao final, e exibição em abas Streamlit por semana.

**Architecture:** Quatro mudanças coordenadas em três arquivos: (1) nova `metodologia.txt` consolidada com guia de decisão do Método RB; (2) novo template de saída em `prompt.py` com marcadores `## SEMANA N` parseáveis pela interface; (3) `_parsear_semanas()` + `st.tabs()` em `app.py`; (4) `top_k=10` explícito na chamada `searcher.buscar()`.

**Tech Stack:** Python 3.11+, Streamlit, pytest, re (stdlib), LangChain + NVIDIA NIM

---

## File Map

| Arquivo | Tipo | O que muda |
|---|---|---|
| `src/generation/metodologia.txt` | Modificar | Substituição completa — fusão do manual atual com guia de decisão do Método RB |
| `src/generation/prompt.py` | Modificar | Novo `_INSTRUCAO_BASE`, novo `_TEMPLATE_SAIDA` com `## SEMANA N`, remove `_SECAO_JUSTIFICATIVA` |
| `src/interface/app.py` | Modificar | Nova `_parsear_semanas()`, renderização com `st.tabs()`, `top_k=10` explícito |
| `tests/test_llm.py` | Modificar | Atualizar testes que verificam template antigo, adicionar testes para novo template |
| `tests/test_interface.py` | Modificar | Adicionar testes para `_parsear_semanas()` |

---

## Task 1: Atualizar testes do prompt (TDD — testes que devem falhar primeiro)

**Files:**
- Modify: `tests/test_llm.py`

Dois testes existentes vão quebrar com a nova implementação e precisam ser atualizados antes:
- `TestMontarPromptComMetodologia::test_prompt_contem_template_de_saida` — verifica `"Plano de Treino"` que será removido
- `TestMontarPromptComCatalogo::test_prompt_com_catalogo_inclui_justificativa` — verifica `"Justificativa Personalizada"` que será removida

Três testes novos precisam ser adicionados para guiar a implementação.

- [ ] **Step 1: Atualizar `test_prompt_contem_template_de_saida`**

Localizar o teste na linha ~252 de `tests/test_llm.py` e substituir:

```python
def test_prompt_contem_template_de_saida(self, resultados_exemplo) -> None:
    """Verifica que o template de saída estruturada com semanas está no prompt."""
    prompt = montar_prompt(
        query="Criar treino",
        resultados=resultados_exemplo,
        metodologia="",
        contexto_aluno="",
    )

    assert "Resumo do Aluno" in prompt
    assert "Metodologia do Treino" in prompt
    assert "SEMANA" in prompt
    assert "Fontes Consultadas" in prompt
```

- [ ] **Step 2: Atualizar `test_prompt_com_catalogo_inclui_justificativa`**

Localizar o teste na linha ~287 de `tests/test_llm.py` e substituir pelo seguinte (o template unificado não tem mais `_SECAO_JUSTIFICATIVA`, mas o catálogo ainda injeta a seção `[CATÁLOGO DE EXERCÍCIOS]`):

```python
def test_prompt_com_catalogo_contem_instrucao_volume(self, resultados_exemplo) -> None:
    """Template com catálogo contém instrução de 12-15 exercícios por sessão."""
    catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
    prompt = montar_prompt(
        query="Criar treino",
        resultados=resultados_exemplo,
        metodologia="",
        contexto_aluno="",
        catalogo_filtrado=catalogo_md,
    )
    assert "12 a 15" in prompt
```

- [ ] **Step 3: Adicionar novos testes ao final da classe `TestMontarPromptComMetodologia`**

Adicionar após o último método da classe (linha ~263):

```python
def test_prompt_nao_instrui_citacao_inline(self) -> None:
    """Verifica que o prompt não instrui citação inline após cada afirmação."""
    prompt = montar_prompt(
        query="Criar treino",
        resultados=[],
        metodologia="",
        contexto_aluno="",
    )
    assert "Cite a fonte após cada afirmação" not in prompt

def test_prompt_instrui_protocolo_periodizado(self) -> None:
    """Verifica que o prompt instrui geração de protocolo com múltiplas semanas."""
    prompt = montar_prompt(
        query="Criar treino",
        resultados=[],
        metodologia="",
        contexto_aluno="",
    )
    assert "semanas" in prompt.lower()

def test_prompt_instrui_metodo_por_exercicio(self) -> None:
    """Verifica que o prompt instrui incluir método por exercício no formato correto."""
    prompt = montar_prompt(
        query="Criar treino",
        resultados=[],
        metodologia="",
        contexto_aluno="",
    )
    assert "bi-set" in prompt.lower() or "método" in prompt.lower()
```

- [ ] **Step 4: Rodar os testes para confirmar que falham**

```bash
pytest tests/test_llm.py::TestMontarPromptComMetodologia tests/test_llm.py::TestMontarPromptComCatalogo -v
```

Esperado: `test_prompt_contem_template_de_saida` → FAIL (o novo assert verifica "SEMANA" que ainda não existe), os 3 novos testes → FAIL com `AssertionError`, e `test_prompt_com_catalogo_contem_instrucao_volume` → FAIL pois ainda não há "12 a 15" no prompt.

- [ ] **Step 5: Commit dos testes**

```bash
git add tests/test_llm.py
git commit -m "test(prompt): atualizar testes para novo template periodizado"
```

---

## Task 2: Implementar novo template em `prompt.py`

**Files:**
- Modify: `src/generation/prompt.py`

- [ ] **Step 1: Substituir `_TEMPLATE_SAIDA_BASE` e `_SECAO_JUSTIFICATIVA` por `_TEMPLATE_SAIDA`**

Substituir as constantes existentes (linhas 16-39) por:

```python
# Instrução base do sistema
_INSTRUCAO_BASE = (
    "Você é um assistente especializado em personal training.\n"
    "Use APENAS as referências abaixo para embasar cientificamente o treino.\n"
    "NÃO inclua citações de fontes de forma inline no texto — todas as referências "
    "devem aparecer apenas na seção '## Fontes Consultadas' ao final da resposta.\n"
    "Gere SEMPRE um protocolo completo periodizado com múltiplas semanas adaptado ao "
    "contexto do aluno: iniciante → tipicamente 4 semanas; "
    "intermediário/avançado → tipicamente 5 semanas.\n"
    "Para cada exercício de fortalecimento, inclua o método no formato: "
    "Exercício — séries×reps (método, ex: bi-set com Exercício Y).\n"
)

# Template de saída unificado — os marcadores ## SEMANA N são parseados pela interface
_TEMPLATE_SAIDA = """
Estruture sua resposta EXATAMENTE neste formato. Use os marcadores de seção exatamente como indicado.

## Resumo do Aluno
[Síntese: nome, idade, modalidade, objetivo, nível, restrições, dias/semana, tempo/sessão]

## Metodologia do Treino
[Raciocínio clínico para este aluno: divisão muscular escolhida, calibragem de volume/intensidade \
por nível, como as restrições físicas foram consideradas na seleção dos exercícios.]

## SEMANA 1 — [nome descritivo, ex: Adaptação e Técnica]
### Dia 1 — [foco do dia]
**Liberação** (se necessário)
- [exercício — duração]

**Mobilidade** (se necessário)
- [exercício — séries×reps]

**Ativação**
- [exercício — séries×reps]

**Fortalecimento**
- [exercício — séries×reps (método, ex: bi-set com Exercício Y)]

### Dia 2 — [foco do dia]
...

## SEMANA 2 — [nome descritivo]
...

## Fontes Consultadas
[lista numerada com as referências utilizadas: [N] Fonte, p. X — trecho relevante]
"""
```

- [ ] **Step 2: Atualizar a função `montar_prompt()`**

Substituir o corpo da função para usar as novas constantes (linhas 42-132):

```python
def montar_prompt(
    query: str,
    resultados: list[ResultadoBusca],
    metodologia: str = "",
    contexto_aluno: str = "",
    catalogo_filtrado=None,
) -> str:
    """Monta o prompt RAG completo com todos os contextos disponíveis.

    Args:
        query: pergunta ou instrução do personal trainer.
        resultados: chunks recuperados do Qdrant.
        metodologia: texto da metodologia RB (system instruction).
        contexto_aluno: dados da anamnese formatados como texto.
        catalogo_filtrado: tabela Markdown filtrada de exercícios, ou None para omitir a seção.
            String vazia é tratada internamente como None (guard contra passagem acidental).

    Returns:
        String do prompt completo pronto para o LLM.
    """
    # Guard: string vazia é semanticamente igual a None
    if catalogo_filtrado == "":
        catalogo_filtrado = None

    secoes = []

    # Instrução base do sistema
    secoes.append(_INSTRUCAO_BASE)

    # Metodologia RB (quando disponível)
    if metodologia.strip():
        secoes.append(
            f"[METODOLOGIA — seguir sempre na estruturação do treino]\n{metodologia.strip()}\n"
        )
        logger.debug("Metodologia incluída no prompt (%d chars).", len(metodologia))

    # Contexto do aluno (anamnese)
    if contexto_aluno.strip():
        secoes.append(f"[CONTEXTO DO ALUNO]\n{contexto_aluno.strip()}\n")

    # Catálogo de exercícios filtrado (quando disponível)
    if catalogo_filtrado is not None:
        instrucoes_catalogo = (
            "[CATÁLOGO DE EXERCÍCIOS — usar para selecionar movimentos do plano]\n"
            "Regras obrigatórias:\n"
            "- Use SOMENTE exercícios presentes nesta tabela filtrada.\n"
            "- Use o nome EXATO do exercício conforme escrito na coluna 'Exercício'. "
            "Não renomeie, abrevie nem adapte os nomes.\n"
            "- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.\n"
            "- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício "
            "original. Nunca sugira o exercício original quando houver substituto marcado.\n"
            "- Cada sessão deve ter 12 a 15 exercícios no total: 2-3 liberações (se necessário) + "
            "3-4 mobilidades (se necessário) + 3-4 ativações + 5-7 fortalecimento. "
            "Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
            f"{catalogo_filtrado}\n"
        )
        secoes.append(instrucoes_catalogo)
        logger.debug("Catálogo de exercícios incluído no prompt.")

    # Referências científicas
    if not resultados:
        secoes.append("REFERÊNCIAS: (nenhuma referência disponível)\n")
        logger.debug("Prompt gerado sem referências.")
    else:
        linhas = []
        for i, resultado in enumerate(resultados, start=1):
            chunk = resultado.chunk
            linhas.append(f"[{i}] {chunk.fonte}, p. {chunk.pagina}: {chunk.conteudo}")
        secoes.append("REFERÊNCIAS:\n" + "\n".join(linhas) + "\n")
        logger.debug("Prompt montado com %d referência(s).", len(resultados))

    # Template de saída unificado
    secoes.append(_TEMPLATE_SAIDA)

    # Pergunta do personal
    secoes.append(f"PERGUNTA: {query}")

    return "\n".join(secoes)
```

- [ ] **Step 3: Rodar os testes para confirmar que passam**

```bash
pytest tests/test_llm.py -v
```

Esperado: todos os testes passam. Verificar especialmente:
- `test_prompt_contem_template_de_saida` → PASS (verifica "SEMANA" e "Fontes Consultadas")
- `test_prompt_com_catalogo_contem_instrucao_volume` → PASS (verifica "12 a 15")
- `test_prompt_nao_instrui_citacao_inline` → PASS
- `test_prompt_instrui_protocolo_periodizado` → PASS
- `test_prompt_sem_catalogo_nao_tem_justificativa` → PASS (Justificativa não existe mais)

- [ ] **Step 4: Commit**

```bash
git add src/generation/prompt.py
git commit -m "feat(prompt): novo template periodizado com marcadores SEMANA N e citações no final"
```

---

## Task 3: Substituir `metodologia.txt` com conteúdo consolidado

**Files:**
- Modify: `src/generation/metodologia.txt`

Não há testes unitários para o conteúdo deste arquivo (é verificado pelos critérios de aceitação do spec). A substituição deve incluir obrigatoriamente: (a) tabela de função articular, (b) fluxograma de 13 etapas numeradas, (c) checklists operacionais.

- [ ] **Step 1: Substituir o conteúdo de `src/generation/metodologia.txt` pelo seguinte**

```
MÉTODO RB — TREINAMENTO INTEGRADO PARA PERFORMANCE E SAÚDE
Guia de Raciocínio Clínico para Prescrição de Exercícios
Rafael Bruno

=== PARTE 1: FILOSOFIA E PRINCÍPIOS ===

1. FILOSOFIA DO MÉTODO RB

Três pilares sustentam a metodologia:
- Individualização: cada aluno tem história corporal única — lesões, rotina, nível e preferências influenciam a prescrição.
- Integração: o treino respeita a interação entre mobilidade, estabilidade e produção de força. Alterações em uma articulação geram compensações em outras.
- Progressão: evolução progressiva respeitando adaptação fisiológica e controle de carga.

Essência: treino não é só exercício. É raciocínio. Não é sobre cansar — é sobre evoluir com inteligência.

2. FUNÇÃO PRIMÁRIA DAS ARTICULAÇÕES

| Região     | Função Principal |
|------------|-----------------|
| Pé         | Estabilidade     |
| Tornozelo  | Mobilidade       |
| Joelho     | Estabilidade     |
| Quadril    | Mobilidade       |
| Lombar     | Estabilidade     |
| Torácica   | Mobilidade       |
| Escápula   | Estabilidade     |
| Ombro      | Mobilidade       |

Lógica de compensação:
- Falta de mobilidade → gera compensação na articulação acima ou abaixo
- Falta de estabilidade → gera sobrecarga local
- Exemplos: tornozelo travado → sobrecarga no joelho; glúteo fraco → sobrecarga lombar; torácica rígida → sobrecarga no ombro

3. ESTRUTURA DA SESSÃO — OS 4 PILARES

Pilar 1 — LIBERAÇÃO (se necessário)
Objetivo: reduzir tensão e melhorar qualidade do movimento.
Usar somente se houver necessidade.
Exemplos: panturrilha, glúteo, quadríceps, peitoral, dorsal.

Pilar 2 — MOBILIDADE / ALONGAMENTO (se necessário)
Objetivo: recuperar amplitude e melhorar padrão de movimento.
Exemplos: mobilidade de tornozelo (joelho na parede), mobilidade de quadril (90/90), rotação torácica, alongamento de flexores de quadril, gato/camelo.

Pilar 3 — ATIVAÇÃO MUSCULAR
Objetivo: ativar músculos estabilizadores e melhorar controle motor.
Foco: core, glúteo, escápula.
Exemplos: prancha frontal, prancha lateral, dead bug, ponte de glúteo, abdução com elástico, retração escapular.

Pilar 4 — FORTALECIMENTO
Base: trabalhar padrões de movimento — agachar, hinge, empurrar, puxar, core.
Inferiores: agachamento, avanço, levantamento terra, stiff (com critério), panturrilha.
Superiores: supino, remada, puxada, desenvolvimento, elevação lateral.
Core: prancha, anti-rotação, farmer carry.

4. ORGANIZAÇÃO DO VOLUME POR SESSÃO

12 a 15 exercícios por sessão:
- 2–3 liberações (se necessário)
- 3–4 mobilidades (se necessário)
- 3–4 ativações
- 5–7 fortalecimento

Distribuição por nível do aluno:
- Iniciante ou com dor: 50% preparação / 50% força
- Intermediário: 30% preparação / 70% força
- Avançado / atleta: 10–20% preparação / 80–90% força

5. PERIODIZAÇÃO (4–5 SEMANAS)

Semana 1–2: adaptação — foco em técnica, carga moderada.
Semana 3–4: aumento de intensidade.
Semana 5: ajuste ou troca de estímulo.

Variáveis de periodização: carga, repetições, volume, intensidade, método de treino.

Para atletas:
- Fase base: mais força e carga.
- Fase competição: manutenção, mais ativação e mobilidade, evitar fadiga excessiva.

6. MÉTODOS DE TREINO

- Tradicional: séries e repetições separadas com descanso completo.
- Bi-set: dois exercícios em sequência sem descanso entre eles.
- Tri-set: três exercícios em sequência.
- Circuito: quatro ou mais exercícios em sequência.
- Drop set: redução de carga sem descanso na mesma série.

Critério de escolha: objetivo + tempo disponível + nível do aluno.

7. REABILITAÇÃO POR REGIÃO

JOELHO
Evitar: amplitude excessiva sem controle, carga alta em ângulos críticos.
Priorizar: cadeira extensora com controle de amplitude, foco em glúteo, mobilidade de tornozelo.

LOMBAR
Evitar: sobrecarga direta, stiff mal executado.
Priorizar: estabilidade de core, controle de movimento, progressão gradual.

OMBRO
Evitar: elevação acima da linha articular em dor, movimentos com compressão.
Priorizar: pegada neutra ou supinada, fortalecimento escapular.

PÉ (FASCITE / CANELITE)
Evitar: impacto e sobrecarga repetitiva.
Priorizar: musculatura intrínseca do pé, estabilidade, mobilidade de tornozelo.
Canelite (específico): tibial posterior, mobilidade de tornozelo, mobilidade de quadril, controle de carga.

=== PARTE 2: GUIA DE DECISÃO OPERACIONAL ===

8. FLUXOGRAMA DE DECISÃO (13 ETAPAS)

ETAPA 1 — TRIAGEM INICIAL
O aluno tem dor ou lesão atual?
→ SIM: priorizar protocolo de reabilitação antes de avançar.
→ NÃO: ir para avaliação de movimento.

ETAPA 2 — AVALIAÇÃO DE MOVIMENTO
Avaliar: mobilidade (tornozelo, quadril, torácica), estabilidade (core, glúteo, escápula), padrões básicos (agachar, hinge, empurrar, puxar).

ETAPA 3 — IDENTIFICAÇÃO DE PRIORIDADE
Existe limitação clara?
→ SIM: priorizar mobilidade OU ativação OU controle motor.
→ NÃO: avançar para treino direto de força.

ETAPA 4 — CLASSIFICAÇÃO DO ALUNO
Classificar como: iniciante, intermediário, avançado ou com restrição.

ETAPA 5 — DEFINIÇÃO DO OBJETIVO
Foco é: reabilitação, emagrecimento, hipertrofia, condicionamento ou performance?

ETAPA 6 — ANÁLISE DA ROTINA
Verificar: quantos dias treina, prática esportiva, nível de fadiga, tempo disponível por sessão.

ETAPA 7 — DEFINIÇÃO DA ESTRUTURA
Definir proporção preparação/força conforme nível e limitações (ver seção 4).

ETAPA 8 — MONTAGEM DA SESSÃO
Ordem obrigatória: Liberação → Mobilidade → Ativação → Fortalecimento.

ETAPA 9 — SELEÇÃO DOS EXERCÍCIOS
Basear em: padrão de movimento, segurança, capacidade do aluno, material disponível.
Critério: "qual função esse exercício cumpre?" — não "qual exercício usar?".

ETAPA 10 — DEFINIÇÃO DO MÉTODO DE TREINO
Escolher entre: tradicional, bi-set, tri-set, circuito, drop set.
Critério: objetivo + tempo + nível.

ETAPA 11 — CONTROLE DE CARGA
Definir intensidade: leve (confortável), moderado (desafiador), alto (próximo do limite).
Sempre baseado no objetivo e na qualidade de execução.

ETAPA 12 — AJUSTE FINAL
Checar: o treino está equilibrado? Não está excessivo? Respeita o momento do aluno?

ETAPA 13 — ACOMPANHAMENTO
Durante e ao longo das semanas: dor → ajustar; fadiga → reduzir; evolução → progredir.

Fluxo resumido: Dor? → tratar | Limitação? → corrigir | Estável? → fortalecer | Evoluiu? → progredir

9. CRITÉRIOS DE PROGRESSÃO E REGRESSÃO

Progressão (quando evoluir):
- bilateral → unilateral
- máquina → livre
- estável → instável
- lento → dinâmico
- simples → combinado
- aumento de carga, repetições ou volume

Regressão (quando regredir):
- dor durante execução
- perda de padrão de movimento
- instabilidade excessiva
- compensações visíveis
Regredir não é piorar o treino — é tornar o treino mais eficiente.

10. CONTROLE DE FADIGA E INTERFERÊNCIA

Tipos de fadiga a controlar: muscular, neural, articular, metabólica.

Para atletas (corrida/triatlo):
- Evitar treinos pesados de perna próximo a treinos intensos da modalidade.
- Quanto maior o volume externo → menor o volume de força.
- Alternância semanal: dia pesado, dia técnico, dia leve (recuperação ativa).

11. SELEÇÃO INTELIGENTE DE EXERCÍCIOS

Critérios: segurança, capacidade de execução, objetivo, nível, equipamento disponível.
Sempre ter variações: sem equipamento, com elástico, com máquina, com peso livre.
Iniciante: mais máquinas e exercícios guiados.
Intermediário: mistura.
Avançado: mais livre e integrado.

12. CHECKLISTS OPERACIONAIS

ANTES DE MONTAR O TREINO:
□ O aluno tem dor?
□ Tem histórico de lesão?
□ Qual o objetivo principal?
□ Quantos dias ele treina?
□ Ele pratica outro esporte?
□ Qual o nível dele?
□ Tem limitações de mobilidade?
□ Tem fraqueza de core/glúteo/escápula?

DEFINIÇÃO DA ESTRUTURA:
□ Vai precisar de liberação?
□ Vai precisar de mobilidade?
□ Vai precisar de ativação mais longa?
□ Ou pode ir mais direto para força?

MONTAGEM DO TREINO:
□ Incluí padrões de movimento?
□ O treino está equilibrado?
□ Tem exercícios de core?
□ Tem membros inferiores e superiores?

ESCOLHA DOS EXERCÍCIOS:
□ O aluno consegue executar bem?
□ É seguro para ele?
□ Está adaptado ao ambiente?
□ Existe alternativa caso não tenha equipamento?

INTENSIDADE E VOLUME:
□ A carga está adequada?
□ O volume está coerente com a rotina?
□ Não está excessivo?
□ Está alinhado com o objetivo?

MÉTODO DE TREINO:
□ Vou usar: ( ) tradicional ( ) bi-set ( ) tri-set ( ) circuito ( ) drop set
□ Faz sentido com o tempo disponível?

VERIFICAÇÃO FINAL:
□ O treino respeita o nível do aluno?
□ Está progressivo em relação à semana anterior?
□ O aluno vai conseguir executar sozinho?

Princípio operacional: você não monta treino — você toma decisões. Cada exercício tem um motivo. Cada ajuste tem uma lógica.
```

- [ ] **Step 2: Rodar os testes gerais para confirmar que nada quebrou**

```bash
pytest tests/ -v --ignore=tests/test_searcher.py
```

(O `test_searcher.py` requer Qdrant em execução — ignorar neste contexto.)
Esperado: todos os testes passam.

- [ ] **Step 3: Commit**

```bash
git add src/generation/metodologia.txt
git commit -m "feat(metodologia): consolidar Método RB com guia de decisão operacional e checklists"
```

---

## Task 4: Adicionar testes para `_parsear_semanas()` (TDD)

**Files:**
- Modify: `tests/test_interface.py`

- [ ] **Step 1: Adicionar os seguintes testes ao final de `tests/test_interface.py`**

```python
# ---------------------------------------------------------------------------
# Testes de _parsear_semanas
# ---------------------------------------------------------------------------


class TestParsearSemanas:
    """Testes para a função _parsear_semanas da interface."""

    def test_retorna_dict_com_chaves_corretas(self) -> None:
        """Verifica que a função retorna dict com as três chaves esperadas."""
        from src.interface.app import _parsear_semanas

        resultado = _parsear_semanas("texto qualquer")

        assert isinstance(resultado, dict)
        assert "cabecalho" in resultado
        assert "semanas" in resultado
        assert "fontes" in resultado

    def test_fallback_sem_marcadores_retorna_semanas_vazia(self) -> None:
        """Texto sem marcadores ## SEMANA N retorna lista de semanas vazia."""
        from src.interface.app import _parsear_semanas

        texto = "## Resumo\nConteúdo\n\n## Metodologia\nMais conteúdo"
        resultado = _parsear_semanas(texto)

        assert resultado["semanas"] == []
        assert resultado["cabecalho"] != ""

    def test_extrai_cabecalho_antes_da_primeira_semana(self) -> None:
        """Tudo antes do primeiro ## SEMANA N vai para cabecalho."""
        from src.interface.app import _parsear_semanas

        texto = "## Resumo do Aluno\nJoão\n\n## SEMANA 1 — Adaptação\nDia 1"
        resultado = _parsear_semanas(texto)

        assert "Resumo do Aluno" in resultado["cabecalho"]
        assert "João" in resultado["cabecalho"]
        assert "SEMANA 1" not in resultado["cabecalho"]

    def test_extrai_uma_semana_como_tuple(self) -> None:
        """Uma semana é extraída como tuple (nome, conteudo)."""
        from src.interface.app import _parsear_semanas

        texto = "cabeçalho\n\n## SEMANA 1 — Adaptação e Técnica\nDia 1 conteúdo"
        resultado = _parsear_semanas(texto)

        assert len(resultado["semanas"]) == 1
        nome, conteudo = resultado["semanas"][0]
        assert "SEMANA 1" in nome
        assert "Adaptação e Técnica" in nome
        assert "Dia 1 conteúdo" in conteudo

    def test_extrai_multiplas_semanas(self) -> None:
        """Múltiplos marcadores ## SEMANA N geram múltiplas semanas."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nconteudo semana 1\n\n"
            "## SEMANA 2 — Intensificação\nconteudo semana 2\n\n"
            "## SEMANA 3 — Pico\nconteudo semana 3"
        )
        resultado = _parsear_semanas(texto)

        assert len(resultado["semanas"]) == 3
        assert "SEMANA 1" in resultado["semanas"][0][0]
        assert "SEMANA 2" in resultado["semanas"][1][0]
        assert "SEMANA 3" in resultado["semanas"][2][0]

    def test_extrai_fontes_consultadas(self) -> None:
        """Seção ## Fontes Consultadas é extraída para a chave 'fontes'."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nconteudo\n\n"
            "## Fontes Consultadas\n[1] fonte.pdf, p. 1 — trecho relevante"
        )
        resultado = _parsear_semanas(texto)

        assert "Fontes Consultadas" in resultado["fontes"]
        assert "fonte.pdf" in resultado["fontes"]

    def test_sem_fontes_retorna_string_vazia(self) -> None:
        """Texto sem ## Fontes Consultadas retorna fontes como string vazia."""
        from src.interface.app import _parsear_semanas

        texto = "cabeçalho\n\n## SEMANA 1 — Adaptação\nconteudo"
        resultado = _parsear_semanas(texto)

        assert resultado["fontes"] == ""

    def test_fontes_nao_aparecem_no_conteudo_da_semana(self) -> None:
        """O conteúdo de uma semana não deve incluir a seção de Fontes."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nDia 1\n\n"
            "## Fontes Consultadas\n[1] fonte.pdf"
        )
        resultado = _parsear_semanas(texto)

        _, conteudo_semana1 = resultado["semanas"][0]
        assert "Fontes Consultadas" not in conteudo_semana1
        assert "fonte.pdf" not in conteudo_semana1
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

```bash
pytest tests/test_interface.py::TestParsearSemanas -v
```

Esperado: todos os 8 testes FAIL com `ImportError: cannot import name '_parsear_semanas' from 'src.interface.app'`.

- [ ] **Step 3: Commit dos testes**

```bash
git add tests/test_interface.py
git commit -m "test(interface): adicionar testes TDD para _parsear_semanas"
```

---

## Task 5: Implementar `_parsear_semanas()` e atualizar interface em `app.py`

**Files:**
- Modify: `src/interface/app.py`

- [ ] **Step 1: Adicionar `import re` no topo do arquivo**

Após a linha `import logging` (linha ~5), adicionar:

```python
import re
```

- [ ] **Step 2: Adicionar a função `_parsear_semanas()` na seção de utilitários**

Adicionar após a função `formatar_contexto_aluno` (após a linha ~44), antes do bloco de cache:

```python
def _parsear_semanas(texto: str) -> dict:
    """Divide o texto gerado pelo LLM em cabeçalho, semanas e fontes.

    Args:
        texto: resposta completa do LLM.

    Returns:
        Dict com chaves 'cabecalho' (str), 'semanas' (list[tuple[str, str]]) e 'fontes' (str).
        'semanas' é vazia se nenhum marcador ## SEMANA N for encontrado (fallback).
    """
    # Divide no início de cada marcador ## SEMANA N, preservando o marcador em cada parte
    partes = re.split(r"(?=^## SEMANA \d+)", texto, flags=re.MULTILINE)

    cabecalho = partes[0].strip() if partes else ""
    semanas = []
    fontes = ""

    for parte in partes[1:]:
        # Verifica se esta parte contém a seção de fontes
        match_fontes = re.search(r"^## Fontes Consultadas", parte, re.MULTILINE)
        if match_fontes:
            corpo_semana = parte[: match_fontes.start()]
            fontes = parte[match_fontes.start() :].strip()
        else:
            corpo_semana = parte

        # Extrai nome (primeira linha) e conteúdo (restante)
        linhas = corpo_semana.strip().split("\n", 1)
        nome = linhas[0].replace("## ", "").strip()
        conteudo = linhas[1].strip() if len(linhas) > 1 else ""
        semanas.append((nome, conteudo))

    return {"cabecalho": cabecalho, "semanas": semanas, "fontes": fontes}
```

- [ ] **Step 3: Rodar os testes de `_parsear_semanas()` para confirmar que passam**

```bash
pytest tests/test_interface.py::TestParsearSemanas -v
```

Esperado: todos os 8 testes PASS.

- [ ] **Step 4: Atualizar a renderização das mensagens do assistente no loop de histórico**

No bloco `elif st.session_state["estado"] == "resposta":`, localizar o loop de histórico (linha ~201):

```python
# Substituir:
for mensagem in st.session_state["historico_conversa"]:
    if mensagem["role"] == "user":
        st.markdown(f"**Você:** {mensagem['content']}")
    else:
        st.markdown(mensagem["content"])
        st.divider()

# Por:
for mensagem in st.session_state["historico_conversa"]:
    if mensagem["role"] == "user":
        st.markdown(f"**Você:** {mensagem['content']}")
    else:
        parsed = _parsear_semanas(mensagem["content"])
        if parsed["cabecalho"]:
            st.markdown(parsed["cabecalho"])
        if parsed["semanas"]:
            abas = st.tabs([nome for nome, _ in parsed["semanas"]])
            for aba, (_, conteudo) in zip(abas, parsed["semanas"]):
                with aba:
                    st.markdown(conteudo)
        else:
            # Fallback: exibe texto completo sem abas
            st.markdown(mensagem["content"])
        if parsed["fontes"]:
            st.divider()
            st.markdown(parsed["fontes"])
        st.divider()
```

- [ ] **Step 5: Remover o bloco de fontes duplicado**

No bloco `else:` que exibe `ultimas_fontes` (logo após o loop de histórico, aproximadamente linha ~261 do arquivo original), remover completamente o seguinte trecho (as fontes agora vêm do LLM via `_parsear_semanas` e são exibidas no Step 4):

```python
# REMOVER este bloco inteiro:
if ultimas_fontes:
    st.markdown("**Fontes consultadas:**")
    for fonte in ultimas_fontes:
        st.markdown(f"- {fonte}")
```

Manter a variável `ultimas_fontes = st.session_state.get("ultimas_fontes", [])` e a linha `st.session_state["ultimas_fontes"] = resposta.fontes` (preservadas para uso futuro). Apenas remover a exibição do bloco acima.

- [ ] **Step 6: Atualizar a chamada `searcher.buscar()` com `top_k` e `max_por_fonte` explícitos**

Localizar a linha `resultados = searcher.buscar(historico[0]["content"])` (linha ~226) e substituir:

```python
# Substituir:
resultados = searcher.buscar(historico[0]["content"])

# Por (mantendo o argumento posicional atual, acrescentando parâmetros nomeados):
resultados = searcher.buscar(historico[0]["content"], top_k=10, max_por_fonte=3)
```

- [ ] **Step 7: Rodar todos os testes**

```bash
pytest tests/ -v --ignore=tests/test_searcher.py
```

Esperado: todos os testes passam.

- [ ] **Step 8: Commit final**

```bash
git add src/interface/app.py
git commit -m "feat(interface): adicionar _parsear_semanas, abas por semana e top_k=10 no retrieval"
```

---

## Verificação Final (Critérios de Aceitação)

Antes de criar o PR, verificar manualmente:

- [ ] `src/generation/metodologia.txt` contém as 13 etapas do fluxograma numeradas (buscar "ETAPA 1" a "ETAPA 13")
- [ ] `src/generation/metodologia.txt` contém a tabela de função articular (buscar "Tornozelo | Mobilidade")
- [ ] `src/generation/metodologia.txt` contém os checklists operacionais (buscar "ANTES DE MONTAR O TREINO")
- [ ] `pytest tests/ -v --ignore=tests/test_searcher.py` → todos PASS
- [ ] Testar manualmente no Streamlit com um aluno de nível Iniciante → verificar 4 semanas em abas
- [ ] Testar com aluno Intermediário → verificar 5 semanas em abas
- [ ] Verificar que cada sessão tem pelo menos 12 exercícios
- [ ] Verificar que exercícios de força incluem o método no formato `Exercício — séries×reps (método)`
- [ ] Verificar que não há citações inline no corpo do texto
- [ ] Verificar fallback: se o LLM não gerar SEMANA N, o texto aparece como bloco único sem erro
