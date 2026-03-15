"""
Realiza chamadas ao Llama 3.x via NVIDIA NIM API usando LangChain.

Expõe a classe RAGGenerator, responsável por montar o prompt,
invocar o modelo e retornar uma RespostaRAG estruturada.
"""

import logging

from langchain_core.messages import HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from src.config.settings import Settings
from src.config.types import RespostaRAG, ResultadoBusca
from src.generation.prompt import montar_prompt

logger = logging.getLogger(__name__)


class RAGGenerator:
    """Gerador de respostas RAG utilizando o Llama 3.x via NVIDIA NIM API."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o gerador RAG com as configurações fornecidas.

        Args:
            settings: instância de Settings com as credenciais e parâmetros do modelo.
        """
        self.settings = settings
        # Inicializa o cliente LangChain para a API NVIDIA NIM
        self.llm = ChatNVIDIA(
            model=settings.llm_model,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        )
        logger.debug("RAGGenerator inicializado com o modelo '%s'.", settings.llm_model)

    def gerar(self, query: str, resultados: list[ResultadoBusca]) -> RespostaRAG:
        """Gera uma resposta RAG com base na query e nos resultados de busca.

        Monta o prompt com as referências recuperadas, invoca o LLM e
        retorna uma RespostaRAG com o texto gerado e a lista de fontes únicas.

        Args:
            query: pergunta ou instrução enviada pelo usuário.
            resultados: lista de resultados retornados pela busca semântica.

        Returns:
            RespostaRAG contendo o texto gerado e as fontes utilizadas.
        """
        # Monta o prompt RAG combinando query e referências
        prompt = montar_prompt(query, resultados)
        logger.debug("Enviando prompt ao LLM com %d referência(s).", len(resultados))

        # Invoca o modelo via LangChain
        resposta = self.llm.invoke([HumanMessage(content=prompt)])
        texto = resposta.content

        # Coleta as fontes únicas a partir dos chunks retornados
        fontes = list({r.chunk.fonte for r in resultados})

        logger.info("Resposta gerada com %d fonte(s) referenciada(s).", len(fontes))
        return RespostaRAG(texto=texto, fontes=fontes)
