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
        "Nome": "João",
        "Idade": 32,
        "Modalidade / Esporte praticado": "jiu-jitsu",
        "Objetivo": "Desempenho Esportivo",
        "Dias disponíveis por semana": 4,
        "Equipamentos disponíveis": ["Peso Livre", "Peso Corporal"],
        "Lesões ou restrições": "nenhuma",
        "Nível de condicionamento": "Intermediário",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "João" in contexto
    assert "32" in contexto
    assert "jiu-jitsu" in contexto
    assert "Desempenho Esportivo" in contexto
    assert "Peso Livre" in contexto


def test_formatar_contexto_aluno_sem_equipamentos():
    """Verifica que equipamentos vazio exibe 'não informado'."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Maria",
        "Idade": 25,
        "Modalidade / Esporte praticado": "corrida",
        "Objetivo": "Resistência",
        "Dias disponíveis por semana": 3,
        "Equipamentos disponíveis": [],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Iniciante",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "não informado" in contexto


def test_formatar_contexto_aluno_sem_lesoes():
    """Verifica que lesões vazia exibe 'nenhuma'."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Carlos",
        "Idade": 40,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 5,
        "Equipamentos disponíveis": ["Máquinas"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Avançado",
    }

    contexto = formatar_contexto_aluno(dados)

    assert "nenhuma" in contexto


def test_fluxo_busca_e_geracao_com_dados_aluno(settings_mock, resultados_exemplo):
    """Garante que gerar() é chamado com equipamentos, nivel e restricoes do session_state."""
    from src.retrieval.searcher import SemanticSearcher
    from src.generation.llm import RAGGenerator

    with patch('src.retrieval.searcher.SentenceTransformer'), \
         patch('src.retrieval.searcher.QdrantClient') as mock_qdrant, \
         patch('src.generation.llm.ChatNVIDIA') as mock_llm, \
         patch('src.generation.llm._carregar_metodologia', return_value=""), \
         patch('src.generation.llm.CatalogoExercicios'):

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
            content="Resposta com catálogo."
        )

        searcher = SemanticSearcher(settings_mock)
        generator = RAGGenerator(settings_mock)

        dados_aluno = {
            "Equipamentos disponíveis": ["Máquinas"],
            "Nível de condicionamento": "Iniciante",
            "Lesões ou restrições": "dor no joelho",
        }

        resultados = searcher.buscar("como montar treino?")
        resposta = generator.gerar(
            "como montar treino?",
            resultados,
            contexto_aluno="Aluno: João",
            equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
            nivel=dados_aluno.get("Nível de condicionamento", ""),
            restricoes=dados_aluno.get("Lesões ou restrições", ""),
        )

        assert isinstance(resposta, RespostaRAG)
        assert resposta.texto == "Resposta com catálogo."
