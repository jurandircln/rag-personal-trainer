"""
Monta o prompt RAG com metodologia, contexto do aluno, catálogo de exercícios e template de saída.

Combina: instrução de sistema, metodologia RB, contexto do aluno (anamnese),
catálogo de exercícios filtrado (quando disponível), referências científicas
recuperadas do Qdrant, e template de formato de resposta.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)

# Seção base do template de saída (sempre presente)
_TEMPLATE_SAIDA_BASE = """
Estruture sua resposta EXATAMENTE neste formato:

## Resumo do Aluno
[Síntese das informações fornecidas: nome, idade, modalidade, objetivo, nível, restrições]

## Metodologia do Treino
[2-3 parágrafos explicando os princípios e decisões por trás do plano, com citações às referências científicas no formato (Fonte: [N], p. X)]

## Plano de Treino
[Treinos organizados por dia, com exercícios, séries, repetições e observações]
"""

# Seção de justificativa — incluída somente quando o catálogo está ativo
_SECAO_JUSTIFICATIVA = """
## Justificativa Personalizada
[Para cada decisão relevante: explique ao personal trainer por que aquele exercício \
foi escolhido para ESTE aluno — nível, restrição física, equipamento disponível, \
objetivo. Use linguagem direta e técnica.]
"""


def montar_prompt(
    query: str,
    resultados: list,
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

    # Catálogo de exercícios filtrado (quando disponível)
    if catalogo_filtrado is not None:
        instrucoes_catalogo = (
            "[CATÁLOGO DE EXERCÍCIOS — usar para selecionar movimentos do plano]\n"
            "Regras obrigatórias:\n"
            "- Use SOMENTE exercícios presentes nesta tabela filtrada.\n"
            "- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.\n"
            "- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício "
            "original. Nunca sugira o exercício original quando houver substituto marcado.\n"
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

    # Template de formato de saída (condicional por catálogo)
    template = _TEMPLATE_SAIDA_BASE
    if catalogo_filtrado is not None:
        template = _TEMPLATE_SAIDA_BASE + _SECAO_JUSTIFICATIVA
    secoes.append(template)

    # Pergunta do personal
    secoes.append(f"PERGUNTA: {query}")

    return "\n".join(secoes)
