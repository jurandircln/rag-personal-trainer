"""
Gera embeddings usando sentence-transformers e indexa os chunks no Qdrant.

Este módulo é responsável por transformar chunks de texto em vetores numéricos
e armazená-los na coleção configurada do Qdrant para buscas semânticas.
"""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from src.config.settings import Settings
from src.config.types import Chunk

logger = logging.getLogger(__name__)


def _criar_cliente_qdrant(settings: Settings) -> QdrantClient:
    """Cria o cliente Qdrant no modo local (host:port) ou cloud (url + api_key)."""
    if settings.usar_qdrant_cloud:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


class VectorIndexer:
    """Gera embeddings e indexa chunks de texto no Qdrant."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o indexador vetorial.

        Args:
            settings: instância de configurações do sistema.
        """
        self.settings = settings
        # Carrega o modelo de embeddings multilingual
        self.modelo = SentenceTransformer(settings.embedding_model)
        # Conecta ao Qdrant no modo local ou cloud conforme a configuração
        self.cliente = _criar_cliente_qdrant(settings)
        # Obtém a dimensão dos vetores gerados pelo modelo
        self._dim = self.modelo.get_sentence_embedding_dimension()
        logger.debug(
            "VectorIndexer inicializado com modelo '%s' (dim=%d, cloud=%s).",
            settings.embedding_model,
            self._dim,
            settings.usar_qdrant_cloud,
        )

    def criar_colecao_se_necessario(self) -> None:
        """Cria a coleção no Qdrant se ela ainda não existir.

        Utiliza similaridade por cosseno, adequada para embeddings de texto.
        """
        nome_colecao = self.settings.qdrant_collection

        # Verifica se a coleção já existe para evitar recriação desnecessária
        if self.cliente.collection_exists(nome_colecao):
            logger.info("Coleção '%s' já existe. Nenhuma ação necessária.", nome_colecao)
            return

        logger.info("Criando coleção '%s' no Qdrant.", nome_colecao)
        self.cliente.create_collection(
            collection_name=nome_colecao,
            vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
        )
        logger.info("Coleção '%s' criada com sucesso.", nome_colecao)

    def indexar(self, chunks: list[Chunk]) -> int:
        """Indexa chunks no Qdrant. Retorna a quantidade de chunks indexados.

        Args:
            chunks: lista de objetos Chunk a serem indexados.

        Returns:
            Número de chunks efetivamente indexados.
        """
        if not chunks:
            logger.warning("Nenhum chunk recebido para indexação.")
            return 0

        # Gera embeddings para todos os chunks em lote
        textos = [chunk.conteudo for chunk in chunks]
        embeddings = self.modelo.encode(textos)
        logger.debug("Embeddings gerados para %d chunks.", len(chunks))

        # Monta os pontos no formato esperado pelo Qdrant
        pontos = [
            PointStruct(
                id=indice,
                vector=list(embedding),
                payload={
                    "conteudo": chunk.conteudo,
                    "fonte": chunk.fonte,
                    "pagina": chunk.pagina,
                    "chunk_id": chunk.chunk_id,
                },
            )
            for indice, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]

        # Realiza o upsert em lotes menores para não exceder o limite de payload do Qdrant
        tamanho_lote = 100
        for inicio in range(0, len(pontos), tamanho_lote):
            lote = pontos[inicio : inicio + tamanho_lote]
            self.cliente.upsert(
                collection_name=self.settings.qdrant_collection,
                points=lote,
            )
        logger.info("%d chunks indexados na coleção '%s'.", len(chunks), self.settings.qdrant_collection)

        return len(chunks)
