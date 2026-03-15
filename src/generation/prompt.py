"""
Monta o prompt RAG utilizado nas chamadas ao LLM.

Combina a query do usuário com os resultados recuperados do Qdrant
para formar um prompt estruturado com referências numeradas.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)


def montar_prompt(query: str, resultados: list[ResultadoBusca]) -> str:
    """Monta o prompt RAG com contexto e instrução de citação de fontes.

    Formata as referências recuperadas como uma lista numerada e instrui
    o modelo a citar as fontes após cada afirmação. Caso nenhum resultado
    seja fornecido, inclui uma mensagem indicando ausência de referências.

    Args:
        query: pergunta ou instrução enviada pelo usuário.
        resultados: lista de resultados retornados pela busca semântica.

    Returns:
        String contendo o prompt completo pronto para ser enviado ao LLM.
    """
    cabecalho = (
        "Você é um assistente especializado em personal training.\n"
        "Use APENAS as referências abaixo para responder. Cite a fonte após cada afirmação.\n"
        "Se as referências forem insuficientes, informe claramente.\n"
    )

    # Constrói a seção de referências ou indica ausência de resultados
    if not resultados:
        secao_referencias = "REFERÊNCIAS: (nenhuma referência disponível)\n"
        logger.debug("Nenhum resultado de busca fornecido; prompt gerado sem referências.")
    else:
        linhas_referencias = []
        for indice, resultado in enumerate(resultados, start=1):
            chunk = resultado.chunk
            linha = f"[{indice}] {chunk.fonte}, p. {chunk.pagina}: {chunk.conteudo}"
            linhas_referencias.append(linha)
        secao_referencias = "REFERÊNCIAS:\n" + "\n".join(linhas_referencias) + "\n"
        logger.debug("Prompt montado com %d referência(s).", len(resultados))

    prompt = f"{cabecalho}\n{secao_referencias}\nPERGUNTA: {query}"
    return prompt
