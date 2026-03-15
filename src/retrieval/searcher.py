"""
Realiza busca semântica no Qdrant dado uma query do usuário.

Converte a query em um vetor de embeddings e recupera os chunks
mais relevantes indexados na coleção do Qdrant.
"""

import logging

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

from src.config.settings import Settings
from src.config.types import Chunk, ResultadoBusca

logger = logging.getLogger(__name__)


class SemanticSearcher:
    """Executa buscas semânticas na base de conhecimento indexada no Qdrant."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o buscador semântico com modelo de embeddings e cliente Qdrant.

        Args:
            settings: configurações do sistema carregadas do ambiente.
        """
        self.settings = settings
        # Carrega o modelo de embeddings multilingual para codificar queries
        self.modelo = SentenceTransformer(settings.embedding_model)
        # Conecta ao servidor Qdrant local
        self.cliente = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        logger.debug(
            "SemanticSearcher inicializado com modelo '%s' e Qdrant em %s:%s.",
            settings.embedding_model,
            settings.qdrant_host,
            settings.qdrant_port,
        )

    def buscar(self, query: str, top_k: int = 5) -> list[ResultadoBusca]:
        """Busca os chunks mais relevantes para a query fornecida.

        Codifica a query em um vetor de embeddings e consulta o Qdrant
        para recuperar os pontos mais similares, ordenados por score decrescente.

        Args:
            query: texto da consulta do usuário.
            top_k: número máximo de resultados a retornar.

        Returns:
            Lista de ResultadoBusca ordenada por score decrescente.
            Retorna lista vazia se nenhum resultado for encontrado.
        """
        # Codifica a query em vetor de embeddings
        vetor = self.modelo.encode(query).tolist()

        logger.debug(
            "Executando busca semântica para query de %d caracteres com top_k=%d.",
            len(query),
            top_k,
        )

        # Consulta o Qdrant com o vetor codificado
        resultados = self.cliente.search(
            collection_name=self.settings.qdrant_collection,
            query_vector=vetor,
            limit=top_k,
        )

        # Converte cada resultado do Qdrant para o tipo ResultadoBusca do sistema
        resultados_busca: list[ResultadoBusca] = []
        for resultado in resultados:
            chunk = Chunk(
                conteudo=resultado.payload["conteudo"],
                fonte=resultado.payload["fonte"],
                pagina=resultado.payload["pagina"],
                chunk_id=resultado.payload["chunk_id"],
            )
            resultados_busca.append(ResultadoBusca(chunk=chunk, score=resultado.score))

        logger.debug("Busca retornou %d resultado(s).", len(resultados_busca))
        return resultados_busca
