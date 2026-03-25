"""
Monta o prompt RAG com metodologia, contexto do aluno, catálogo de exercícios e template de saída.

Combina: instrução de sistema, metodologia RB, contexto do aluno (anamnese),
catálogo de exercícios filtrado (quando disponível), referências científicas
recuperadas do Qdrant, e template de formato de resposta.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)

# Instrução base do sistema
_INSTRUCAO_BASE = (
    "Você é um assistente especializado em personal training.\n"
    "Use APENAS as referências abaixo para embasar cientificamente o treino.\n"
    "NÃO inclua citações de fontes de forma inline no texto — todas as referências "
    "devem aparecer apenas na seção '## Fontes Consultadas' ao final da resposta.\n"
    "Gere SEMPRE um protocolo completo periodizado com múltiplas semanas adaptado ao "
    "contexto do aluno: iniciante → tipicamente 4 semanas; "
    "intermediário/avançado → tipicamente 5 semanas.\n"
    "SEMPRE gere pelo menos 4 semanas completas — nunca abrevie ou use reticências (...).\n"
    "Quantidade mínima de exercícios de FORTALECIMENTO por grupo muscular em cada sessão: "
    "músculos pequenos (bíceps, tríceps, ombros, panturrilha) → mínimo 3 exercícios; "
    "músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
    "→ mínimo 4 exercícios.\n"
    "Para cada exercício de fortalecimento, inclua o método no formato: "
    "Exercício — séries×reps (método, ex: bi-set com Exercício Y).\n"
)

# Template de saída unificado — os marcadores ## SEMANA N são parseados pela interface
_TEMPLATE_SAIDA = """Estruture sua resposta EXATAMENTE neste formato. Use os marcadores de seção exatamente como indicado.

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
**Liberação** (se necessário)
- [exercício — duração]

**Mobilidade** (se necessário)
- [exercício — séries×reps]

**Ativação**
- [exercício — séries×reps]

**Fortalecimento**
- [exercício — séries×reps (método)]

## SEMANA 2 — [nome descritivo]
### Dia 1 — [foco do dia]
**Liberação** (se necessário)
- [exercício — duração]

**Mobilidade** (se necessário)
- [exercício — séries×reps]

**Ativação**
- [exercício — séries×reps]

**Fortalecimento**
- [exercício — séries×reps (método)]

### Dia 2 — [foco do dia]
**Liberação** (se necessário)
- [exercício — duração]

**Mobilidade** (se necessário)
- [exercício — séries×reps]

**Ativação**
- [exercício — séries×reps]

**Fortalecimento**
- [exercício — séries×reps (método)]

## SEMANA 3 — [nome descritivo]
[mesma estrutura completa — NUNCA usar reticências]

## SEMANA 4 — [nome descritivo]
[mesma estrutura completa — NUNCA usar reticências]

## Fontes Consultadas
[lista numerada com as referências utilizadas: [N] Fonte, p. X — trecho relevante]
"""


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
