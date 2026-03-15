"""
Testes unitários para src/retrieval/searcher.py.

Utiliza mocks para simular SentenceTransformer e QdrantClient, garantindo
que os testes não dependam de modelos reais ou de um servidor Qdrant em execução.
"""

import pytest

from src.config.types import ResultadoBusca, Chunk
from src.retrieval.searcher import SemanticSearcher


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_qdrant_search_result(mocker):
    """Mock de resultado retornado pelo Qdrant."""
    resultado = mocker.MagicMock()
    resultado.payload = {
        "conteudo": "Texto do chunk",
        "fonte": "arquivo.pdf",
        "pagina": 1,
        "chunk_id": "abc123",
    }
    resultado.score = 0.95
    return resultado


@pytest.fixture
def mock_sentence_transformer(mocker):
    """Simula o SentenceTransformer para evitar download de modelos reais."""
    mock = mocker.patch("src.retrieval.searcher.SentenceTransformer")
    instancia = mock.return_value
    # Retorna vetor falso de dimensão 768 ao codificar qualquer query
    instancia.encode.return_value = type(
        "FakeArray", (), {"tolist": lambda self: [0.1] * 768}
    )()
    return instancia


@pytest.fixture
def mock_qdrant_client(mocker):
    """Simula o QdrantClient para evitar dependência de um servidor Qdrant em execução."""
    mock = mocker.patch("src.retrieval.searcher.QdrantClient")
    instancia = mock.return_value
    # Por padrão, query_points retorna objeto com .points vazio
    instancia.query_points.return_value.points = []
    return instancia


# ---------------------------------------------------------------------------
# Testes de buscar
# ---------------------------------------------------------------------------


class TestBuscar:
    """Testes para o método SemanticSearcher.buscar."""

    def test_buscar_retorna_lista_de_resultado_busca(
        self,
        settings_mock,
        mock_sentence_transformer,
        mock_qdrant_client,
        mock_qdrant_search_result,
    ) -> None:
        """Verifica que buscar retorna uma lista de ResultadoBusca com score correto."""
        # Configura o mock do Qdrant para retornar um resultado
        mock_qdrant_client.query_points.return_value.points = [mock_qdrant_search_result]

        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("treino de força")

        # Deve retornar uma lista não vazia
        assert isinstance(resultados, list)
        assert len(resultados) == 1

        # O elemento deve ser do tipo ResultadoBusca com score correto
        assert isinstance(resultados[0], ResultadoBusca)
        assert resultados[0].score == 0.95

    def test_buscar_usa_top_k_correto(
        self,
        settings_mock,
        mock_sentence_transformer,
        mock_qdrant_client,
    ) -> None:
        """Verifica que top_k controla o número de resultados quando max_por_fonte=None."""
        buscador = SemanticSearcher(settings_mock)
        buscador.buscar("consulta de teste", top_k=3, max_por_fonte=None)

        # Garante que o cliente Qdrant foi chamado com limit=3
        mock_qdrant_client.query_points.assert_called_once()
        _, kwargs = mock_qdrant_client.query_points.call_args
        assert kwargs.get("limit") == 3
        assert kwargs.get("query") == [0.1] * 768

    def test_buscar_query_vazia_retorna_lista_vazia(
        self,
        settings_mock,
        mock_sentence_transformer,
        mock_qdrant_client,
    ) -> None:
        """Verifica que buscar com query vazia retorna lista vazia sem chamar o Qdrant."""
        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("")

        assert resultados == []
        mock_qdrant_client.query_points.assert_not_called()

    def test_buscar_chunk_tem_campos_corretos(
        self,
        settings_mock,
        mock_sentence_transformer,
        mock_qdrant_client,
        mock_qdrant_search_result,
    ) -> None:
        """Verifica que o Chunk dentro de ResultadoBusca contém todos os campos corretos."""
        mock_qdrant_client.query_points.return_value.points = [mock_qdrant_search_result]

        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("anamnese do cliente")

        assert len(resultados) == 1
        chunk = resultados[0].chunk

        # Verifica que o chunk é do tipo correto
        assert isinstance(chunk, Chunk)

        # Verifica que cada campo foi corretamente mapeado do payload
        assert chunk.conteudo == "Texto do chunk"
        assert chunk.fonte == "arquivo.pdf"
        assert chunk.pagina == 1
        assert chunk.chunk_id == "abc123"


class TestBuscarComDiversidade:
    """Testes para a diversidade de fontes no método buscar."""

    def _criar_resultado(self, mocker, fonte: str, score: float):
        """Helper para criar mock de resultado Qdrant."""
        resultado = mocker.MagicMock()
        resultado.payload = {
            "conteudo": f"Conteúdo de {fonte}",
            "fonte": fonte,
            "pagina": 1,
            "chunk_id": f"id_{fonte}_{score}",
        }
        resultado.score = score
        return resultado

    def test_max_por_fonte_limita_chunks_da_mesma_fonte(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client, mocker
    ) -> None:
        """Verifica que no máximo max_por_fonte chunks da mesma fonte são retornados."""
        resultados_qdrant = [
            self._criar_resultado(mocker, "livro_a.pdf", 0.99),
            self._criar_resultado(mocker, "livro_a.pdf", 0.97),
            self._criar_resultado(mocker, "livro_a.pdf", 0.95),
            self._criar_resultado(mocker, "livro_a.pdf", 0.93),
            self._criar_resultado(mocker, "livro_b.pdf", 0.91),
        ]
        mock_qdrant_client.query_points.return_value.points = resultados_qdrant

        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("treino funcional", top_k=5, max_por_fonte=2)

        fontes = [r.chunk.fonte for r in resultados]
        assert fontes.count("livro_a.pdf") <= 2
        assert "livro_b.pdf" in fontes

    def test_diversidade_retorna_multiplas_fontes(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client, mocker
    ) -> None:
        """Verifica que o resultado final contém chunks de múltiplas fontes."""
        resultados_qdrant = [
            self._criar_resultado(mocker, "nasm.pdf", 0.98),
            self._criar_resultado(mocker, "nasm.pdf", 0.96),
            self._criar_resultado(mocker, "nasm.pdf", 0.94),
            self._criar_resultado(mocker, "boyle.pdf", 0.92),
            self._criar_resultado(mocker, "cook.pdf", 0.90),
        ]
        mock_qdrant_client.query_points.return_value.points = resultados_qdrant

        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("treino funcional", top_k=4, max_por_fonte=1)

        fontes_unicas = {r.chunk.fonte for r in resultados}
        assert len(fontes_unicas) >= 3

    def test_sem_max_por_fonte_comportamento_original(
        self, settings_mock, mock_sentence_transformer, mock_qdrant_client, mocker
    ) -> None:
        """Verifica que max_por_fonte=None mantém o comportamento original."""
        resultados_qdrant = [
            self._criar_resultado(mocker, "livro_a.pdf", 0.99),
            self._criar_resultado(mocker, "livro_a.pdf", 0.97),
            self._criar_resultado(mocker, "livro_a.pdf", 0.95),
        ]
        mock_qdrant_client.query_points.return_value.points = resultados_qdrant

        buscador = SemanticSearcher(settings_mock)
        resultados = buscador.buscar("treino", top_k=3, max_por_fonte=None)

        assert len(resultados) == 3
