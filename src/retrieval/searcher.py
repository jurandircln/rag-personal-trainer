"""
Realiza busca semântica no Qdrant dado uma query do usuário.

Converte a query em um vetor de embeddings e recupera os chunks
mais relevantes indexados na coleção do Qdrant.
"""

import logging
from typing import Optional

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

from src.config.settings import Settings
from src.config.types import Chunk, ResultadoBusca

logger = logging.getLogger(__name__)


def _criar_cliente_qdrant(settings: Settings) -> QdrantClient:
    """Cria o cliente Qdrant no modo local (host:port) ou cloud (url + api_key)."""
    if settings.usar_qdrant_cloud:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


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
        # Conecta ao Qdrant no modo local ou cloud conforme a configuração
        self.cliente = _criar_cliente_qdrant(settings)
        logger.debug(
            "SemanticSearcher inicializado com modelo '%s' (cloud=%s).",
            settings.embedding_model,
            settings.usar_qdrant_cloud,
        )

    def buscar(
        self,
        query: str,
        top_k: int = 5,
        max_por_fonte: Optional[int] = 2,
    ) -> list[ResultadoBusca]:
        """Busca os chunks mais relevantes com diversidade de fontes.

        Busca um pool ampliado de candidatos e aplica filtro de diversidade,
        limitando o número de chunks por fonte para garantir múltiplas referências.

        Args:
            query: texto da consulta do usuário.
            top_k: número máximo de resultados a retornar.
            max_por_fonte: máximo de chunks permitidos por fonte. None desativa o filtro.

        Returns:
            Lista de ResultadoBusca ordenada por score decrescente, com diversidade de fontes.
        """
        if not query.strip():
            return []

        # Busca pool ampliado para ter candidatos suficientes após filtro de diversidade
        limite_ampliado = top_k * 4 if max_por_fonte else top_k
        vetor = self.modelo.encode(query).tolist()

        logger.debug(
            "Executando busca semântica (pool=%d, top_k=%d, max_por_fonte=%s).",
            limite_ampliado,
            top_k,
            max_por_fonte,
        )

        # Consulta o Qdrant com o vetor codificado (API atual: query_points retorna QueryResponse com .points)
        resposta = self.cliente.query_points(
            collection_name=self.settings.qdrant_collection,
            query=vetor,
            limit=limite_ampliado,
        )
        candidatos = resposta.points

        # Aplica filtro de diversidade por fonte
        if max_por_fonte is not None:
            contagem_por_fonte: dict[str, int] = {}
            candidatos_filtrados = []
            for resultado in candidatos:
                fonte = resultado.payload.get("fonte", "")
                if not fonte:
                    continue
                contagem = contagem_por_fonte.get(fonte, 0)
                if contagem < max_por_fonte:
                    candidatos_filtrados.append(resultado)
                    contagem_por_fonte[fonte] = contagem + 1
                if len(candidatos_filtrados) == top_k:
                    break
            candidatos = candidatos_filtrados

        # Converte para ResultadoBusca, ignorando registros com payload incompleto
        resultados_busca: list[ResultadoBusca] = []
        for resultado in candidatos[:top_k]:
            payload = resultado.payload
            chaves_obrigatorias = {"conteudo", "fonte", "pagina", "chunk_id"}
            if not chaves_obrigatorias.issubset(payload.keys()):
                logger.warning(
                    "Registro ignorado: payload incompleto — chaves presentes: %s",
                    list(payload.keys()),
                )
                continue
            chunk = Chunk(
                conteudo=payload["conteudo"],
                fonte=payload["fonte"],
                pagina=payload["pagina"],
                chunk_id=payload["chunk_id"],
            )
            resultados_busca.append(ResultadoBusca(chunk=chunk, score=resultado.score))

        logger.debug(
            "Busca retornou %d resultado(s).", len(resultados_busca)
        )
        return resultados_busca
