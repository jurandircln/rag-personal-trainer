"""
Testes unitários para src/ingestion/embedder.py.

Utiliza mocks para simular SentenceTransformer e QdrantClient, garantindo
que os testes não dependam de modelos reais ou de serviços externos.
"""

import pytest

from src.config.types import Chunk


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sentence_transformer(mocker):
    """Simula o SentenceTransformer para evitar download de modelos reais."""
    mock = mocker.patch("src.ingestion.embedder.SentenceTransformer")
    instancia = mock.return_value
    # Retorna dimensão fixa compatível com modelos multilingual
    instancia.get_sentence_embedding_dimension.return_value = 768
    # Retorna dois embeddings falsos para testes com 2 chunks
    instancia.encode.return_value = [[0.1] * 768, [0.2] * 768]
    return instancia


@pytest.fixture
def mock_qdrant_client(mocker):
    """Simula o QdrantClient para evitar dependência de um servidor Qdrant em execução."""
    mock = mocker.patch("src.ingestion.embedder.QdrantClient")
    instancia = mock.return_value
    # Por padrão, simula que a coleção ainda não existe
    instancia.collection_exists.return_value = False
    return instancia


# ---------------------------------------------------------------------------
# Testes de criar_colecao_se_necessario
# ---------------------------------------------------------------------------


class TestCriarColecaoSeNecessario:
    """Testes para o método VectorIndexer.criar_colecao_se_necessario."""

    def test_criar_colecao_chama_create_collection_quando_nao_existe(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client
    ) -> None:
        """Verifica que create_collection é chamado quando a coleção não existe."""
        from src.ingestion.embedder import VectorIndexer

        # Garante que collection_exists retorna False
        mock_qdrant_client.collection_exists.return_value = False

        indexador = VectorIndexer(settings_mock)
        indexador.criar_colecao_se_necessario()

        # create_collection deve ser chamado exatamente uma vez com o nome correto
        mock_qdrant_client.create_collection.assert_called_once()
        args, kwargs = mock_qdrant_client.create_collection.call_args
        nome_passado = kwargs.get("collection_name") or args[0]
        assert nome_passado == settings_mock.qdrant_collection

    def test_criar_colecao_nao_recria_se_ja_existe(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client
    ) -> None:
        """Verifica que create_collection NÃO é chamado quando a coleção já existe."""
        from src.ingestion.embedder import VectorIndexer

        # Simula que a coleção já existe
        mock_qdrant_client.collection_exists.return_value = True

        indexador = VectorIndexer(settings_mock)
        indexador.criar_colecao_se_necessario()

        # create_collection não deve ser chamado
        mock_qdrant_client.create_collection.assert_not_called()


# ---------------------------------------------------------------------------
# Testes de indexar
# ---------------------------------------------------------------------------


class TestIndexar:
    """Testes para o método VectorIndexer.indexar."""

    def _criar_chunks_teste(self) -> list[Chunk]:
        """Cria dois chunks de teste com dados representativos."""
        return [
            Chunk(
                conteudo="Texto do primeiro chunk de treino",
                fonte="treino_forca.pdf",
                pagina=1,
                chunk_id="abc123",
            ),
            Chunk(
                conteudo="Texto do segundo chunk de anamnese",
                fonte="anamnese_cliente.pdf",
                pagina=2,
                chunk_id="def456",
            ),
        ]

    def test_indexar_chama_upsert_com_payload_correto(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client
    ) -> None:
        """Verifica que upsert é chamado com collection_name correto e payload completo."""
        from src.ingestion.embedder import VectorIndexer

        chunks = self._criar_chunks_teste()
        indexador = VectorIndexer(settings_mock)
        indexador.indexar(chunks)

        # upsert deve ter sido chamado uma vez
        mock_qdrant_client.upsert.assert_called_once()

        args, kwargs = mock_qdrant_client.upsert.call_args

        # Verifica o nome da coleção passado
        nome_colecao = kwargs.get("collection_name") or args[0]
        assert nome_colecao == settings_mock.qdrant_collection

        # Verifica que os pontos contêm os campos obrigatórios no payload
        pontos = kwargs.get("points") or args[1]
        assert len(pontos) == 2

        for ponto, chunk in zip(pontos, chunks):
            payload = ponto.payload
            assert "conteudo" in payload
            assert "fonte" in payload
            assert "pagina" in payload
            assert "chunk_id" in payload
            assert payload["conteudo"] == chunk.conteudo
            assert payload["fonte"] == chunk.fonte
            assert payload["pagina"] == chunk.pagina
            assert payload["chunk_id"] == chunk.chunk_id

    def test_indexar_retorna_quantidade_correta(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client
    ) -> None:
        """Verifica que indexar retorna a quantidade exata de chunks processados."""
        from src.ingestion.embedder import VectorIndexer

        chunks = self._criar_chunks_teste()
        indexador = VectorIndexer(settings_mock)
        resultado = indexador.indexar(chunks)

        assert resultado == len(chunks)
