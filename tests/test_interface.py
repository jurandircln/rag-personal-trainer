"""Testes de integração do fluxo da interface (searcher → generator)."""
from unittest.mock import MagicMock, patch

from src.config.types import RespostaRAG


def test_fluxo_busca_e_geracao(settings_mock, resultados_exemplo):
    """Garante que searcher e generator se integram corretamente."""
    from src.retrieval.searcher import SemanticSearcher
    from src.generation.llm import RAGGenerator

    with patch('src.retrieval.searcher.SentenceTransformer'), \
         patch('src.retrieval.searcher.QdrantClient') as mock_qdrant, \
         patch('src.generation.llm.ChatNVIDIA') as mock_llm:

        mock_qdrant.return_value.query_points.return_value.points = [
            MagicMock(payload={
                'conteudo': r.chunk.conteudo,
                'fonte': r.chunk.fonte,
                'pagina': r.chunk.pagina,
                'chunk_id': r.chunk.chunk_id,
            }, score=r.score)
            for r in resultados_exemplo
        ]
        mock_llm.return_value.invoke.return_value = MagicMock(
            content="Resposta gerada pelo LLM."
        )

        searcher = SemanticSearcher(settings_mock)
        generator = RAGGenerator(settings_mock)

        resultados = searcher.buscar("como montar um treino de força?")
        resposta = generator.gerar("como montar um treino de força?", resultados)

        assert isinstance(resposta, RespostaRAG)
        assert resposta.texto == "Resposta gerada pelo LLM."
        assert len(resposta.fontes) > 0


def test_resposta_sem_resultados(settings_mock):
    """Garante que o generator lida com lista vazia de resultados."""
    from src.generation.llm import RAGGenerator

    with patch('src.generation.llm.ChatNVIDIA') as mock_llm:
        mock_llm.return_value.invoke.return_value = MagicMock(
            content="Não encontrei referências sobre esse tema."
        )
        generator = RAGGenerator(settings_mock)
        resposta = generator.gerar("pergunta sem contexto", [])

        assert isinstance(resposta, RespostaRAG)
        assert resposta.fontes == []
