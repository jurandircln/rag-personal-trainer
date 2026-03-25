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
        "Tempo por sessão": "60 min",
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
        "Tempo por sessão": "45 min",
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
        "Tempo por sessão": "90 min+",
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


# ---------------------------------------------------------------------------
# Testes de _parsear_semanas
# ---------------------------------------------------------------------------


class TestParsearSemanas:
    """Testes para a função _parsear_semanas da interface."""

    def test_retorna_dict_com_chaves_corretas(self) -> None:
        """Verifica que a função retorna dict com as três chaves esperadas."""
        from src.interface.app import _parsear_semanas

        resultado = _parsear_semanas("texto qualquer")

        assert isinstance(resultado, dict)
        assert "cabecalho" in resultado
        assert "semanas" in resultado
        assert "fontes" in resultado

    def test_fallback_sem_marcadores_retorna_semanas_vazia(self) -> None:
        """Texto sem marcadores ## SEMANA N retorna lista de semanas vazia."""
        from src.interface.app import _parsear_semanas

        texto = "## Resumo\nConteúdo\n\n## Metodologia\nMais conteúdo"
        resultado = _parsear_semanas(texto)

        assert resultado["semanas"] == []
        assert resultado["cabecalho"] != ""

    def test_extrai_cabecalho_antes_da_primeira_semana(self) -> None:
        """Tudo antes do primeiro ## SEMANA N vai para cabecalho."""
        from src.interface.app import _parsear_semanas

        texto = "## Resumo do Aluno\nJoão\n\n## SEMANA 1 — Adaptação\nDia 1"
        resultado = _parsear_semanas(texto)

        assert "Resumo do Aluno" in resultado["cabecalho"]
        assert "João" in resultado["cabecalho"]
        assert "SEMANA 1" not in resultado["cabecalho"]

    def test_extrai_uma_semana_como_tuple(self) -> None:
        """Uma semana é extraída como tuple (nome, conteudo)."""
        from src.interface.app import _parsear_semanas

        texto = "cabeçalho\n\n## SEMANA 1 — Adaptação e Técnica\nDia 1 conteúdo"
        resultado = _parsear_semanas(texto)

        assert len(resultado["semanas"]) == 1
        nome, conteudo = resultado["semanas"][0]
        assert "SEMANA 1" in nome
        assert "Adaptação e Técnica" in nome
        assert "Dia 1 conteúdo" in conteudo

    def test_extrai_multiplas_semanas(self) -> None:
        """Múltiplos marcadores ## SEMANA N geram múltiplas semanas."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nconteudo semana 1\n\n"
            "## SEMANA 2 — Intensificação\nconteudo semana 2\n\n"
            "## SEMANA 3 — Pico\nconteudo semana 3"
        )
        resultado = _parsear_semanas(texto)

        assert len(resultado["semanas"]) == 3
        assert "SEMANA 1" in resultado["semanas"][0][0]
        assert "SEMANA 2" in resultado["semanas"][1][0]
        assert "SEMANA 3" in resultado["semanas"][2][0]

    def test_extrai_fontes_consultadas(self) -> None:
        """Seção ## Fontes Consultadas é extraída para a chave 'fontes'."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nconteudo\n\n"
            "## Fontes Consultadas\n[1] fonte.pdf, p. 1 — trecho relevante"
        )
        resultado = _parsear_semanas(texto)

        assert "Fontes Consultadas" in resultado["fontes"]
        assert "fonte.pdf" in resultado["fontes"]

    def test_sem_fontes_retorna_string_vazia(self) -> None:
        """Texto sem ## Fontes Consultadas retorna fontes como string vazia."""
        from src.interface.app import _parsear_semanas

        texto = "cabeçalho\n\n## SEMANA 1 — Adaptação\nconteudo"
        resultado = _parsear_semanas(texto)

        assert resultado["fontes"] == ""

    def test_fontes_nao_aparecem_no_conteudo_da_semana(self) -> None:
        """O conteúdo de uma semana não deve incluir a seção de Fontes."""
        from src.interface.app import _parsear_semanas

        texto = (
            "cabeçalho\n\n"
            "## SEMANA 1 — Adaptação\nDia 1\n\n"
            "## Fontes Consultadas\n[1] fonte.pdf"
        )
        resultado = _parsear_semanas(texto)

        _, conteudo_semana1 = resultado["semanas"][0]
        assert "Fontes Consultadas" not in conteudo_semana1
        assert "fonte.pdf" not in conteudo_semana1

    def test_fallback_fontes_sem_semanas_exibidas_no_cabecalho(self) -> None:
        """Sem marcadores ## SEMANA N, Fontes Consultadas aparecem no cabecalho (exibidas pelo fallback)."""
        from src.interface.app import _parsear_semanas

        texto = "## Resumo\nConteúdo\n\n## Fontes Consultadas\n[1] fonte.pdf"
        resultado = _parsear_semanas(texto)

        # Sem semanas, o fallback exibe o texto completo incluindo as fontes
        assert resultado["semanas"] == []
        assert "Fontes Consultadas" in resultado["cabecalho"]
        assert resultado["fontes"] == ""  # fontes só são extraídas quando dentro de uma semana
