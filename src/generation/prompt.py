"""
Monta o prompt RAG com metodologia, contexto do aluno e template de saída estruturada.

Combina: instrução de sistema, metodologia RB, contexto do aluno (anamnese),
referências científicas recuperadas do Qdrant, e template de formato de resposta.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)

# Template obrigatório de saída que o LLM deve seguir
_TEMPLATE_SAIDA = """
Estruture sua resposta EXATAMENTE neste formato:

## Resumo do Aluno
[Síntese das informações fornecidas: nome, idade, modalidade, objetivo, nível, restrições]

## Metodologia do Treino
[2-3 parágrafos explicando os princípios e decisões por trás do plano, com citações às referências científicas no formato (Fonte: [N], p. X)]

## Plano de Treino
[Treinos organizados por dia, com exercícios, séries, repetições e observações]
"""


def montar_prompt(
    query: str,
    resultados: list[ResultadoBusca],
    metodologia: str = "",
    contexto_aluno: str = "",
) -> str:
    """Monta o prompt RAG completo com todos os contextos disponíveis.

    Args:
        query: pergunta ou instrução do personal trainer.
        resultados: chunks recuperados do Qdrant.
        metodologia: texto da metodologia RB (system instruction).
        contexto_aluno: dados da anamnese formatados como texto.

    Returns:
        String do prompt completo pronto para o LLM.
    """
    secoes = []

    # Instrução base do sistema
    secoes.append(
        "Você é um assistente especializado em personal training.\n"
        "Use APENAS as referências abaixo para embasar cientificamente o treino.\n"
        "Cite a fonte após cada afirmação relevante.\n"
        "Se o contexto do aluno for insuficiente para personalizar o treino, "
        "faça UMA pergunta objetiva antes de responder (máx. 3 rodadas).\n"
    )

    # Metodologia RB (quando disponível)
    if metodologia.strip():
        secoes.append(
            f"[METODOLOGIA — seguir sempre na estruturação do treino]\n{metodologia.strip()}\n"
        )
        logger.debug("Metodologia incluída no prompt (%d chars).", len(metodologia))

    # Contexto do aluno (anamnese)
    if contexto_aluno.strip():
        secoes.append(f"[CONTEXTO DO ALUNO]\n{contexto_aluno.strip()}\n")

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

    # Template de formato de saída
    secoes.append(_TEMPLATE_SAIDA)

    # Pergunta do personal
    secoes.append(f"PERGUNTA: {query}")

    return "\n".join(secoes)
