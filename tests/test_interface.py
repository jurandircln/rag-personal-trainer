"""Testes de integração do fluxo da interface com anamnese e follow-up."""
from unittest.mock import MagicMock, patch

import pytest

from src.config.types import RespostaRAG


def test_fluxo_busca_e_geracao(settings_mock, resultados_exemplo):
    """Garante que searcher e generator se integram com contexto_aluno."""
    from src.retrieval.searcher import SemanticSearcher
    from src.generation.llm import RAGGenerator

    with patch('src.retrieval.searcher.SentenceTransformer'), \
         patch('src.retrieval.searcher.QdrantClient') as mock_qdrant, \
         patch('src.generation.llm.ChatNVIDIA') as mock_llm, \
         patch('src.generation.llm._carregar_metodologia', return_value=""):

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
        resposta = generator.gerar(
            "como montar um treino de força?",
            resultados,
            contexto_aluno="Aluno: João, 32 anos, jiu-jitsu.",
        )

        assert isinstance(resposta, RespostaRAG)
        assert resposta.texto == "Resposta gerada pelo LLM."
        assert len(resposta.fontes) > 0


def test_resposta_sem_resultados(settings_mock):
    """Garante que o generator lida com lista vazia de resultados."""
    from src.generation.llm import RAGGenerator

    with patch('src.generation.llm.ChatNVIDIA') as mock_llm, \
         patch('src.generation.llm._carregar_metodologia', return_value=""):
        mock_llm.return_value.invoke.return_value = MagicMock(
            content="Não encontrei referências sobre esse tema."
        )
        generator = RAGGenerator(settings_mock)
        resposta = generator.gerar("pergunta sem contexto", [])

        assert isinstance(resposta, RespostaRAG)
        assert resposta.fontes == []


def test_formatar_contexto_aluno():
    """Verifica que o contexto do aluno é formatado corretamente."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "nome": "João",
        "idade": 32,
        "modalidade": "jiu-jitsu",
        "objetivo": "desempenho esportivo",
        "dias_semana": 4,
        "equipamentos": ["peso livre", "peso corporal"],
        "lesoes": "nenhuma",
        "nivel": "intermediário",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "João" in contexto
    assert "32" in contexto
    assert "jiu-jitsu" in contexto
    assert "desempenho esportivo" in contexto
    assert "peso livre" in contexto


def test_formatar_contexto_aluno_sem_equipamentos():
    """Verifica que equipamentos vazio exibe 'não informado'."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "nome": "Maria",
        "idade": 25,
        "modalidade": "corrida",
        "objetivo": "resistência",
        "dias_semana": 3,
        "equipamentos": [],
        "lesoes": "",
        "nivel": "iniciante",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "não informado" in contexto


def test_formatar_contexto_aluno_sem_lesoes():
    """Verifica que lesões vazia exibe 'nenhuma'."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "nome": "Carlos",
        "idade": 40,
        "modalidade": "musculação",
        "objetivo": "hipertrofia",
        "dias_semana": 5,
        "equipamentos": ["máquinas"],
        "lesoes": "",
        "nivel": "avançado",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "nenhuma" in contexto
