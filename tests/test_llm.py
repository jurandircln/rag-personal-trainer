"""
Testes unitários para src/generation/llm.py e src/generation/prompt.py.

Utiliza pytest-mock para isolar a dependência de ChatNVIDIA,
garantindo que os testes não necessitem de credenciais reais da API NVIDIA NIM.
"""

import pytest

from src.config.types import Chunk, RespostaRAG, ResultadoBusca
from src.generation.prompt import montar_prompt


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_chat_nvidia(mocker):
    """Substitui ChatNVIDIA por um mock que retorna uma resposta pré-definida."""
    mock = mocker.patch("src.generation.llm.ChatNVIDIA")
    instancia = mock.return_value
    resposta_mock = mocker.MagicMock()
    resposta_mock.content = "Resposta gerada pelo LLM sobre treinamento."
    instancia.invoke.return_value = resposta_mock
    return instancia


# ---------------------------------------------------------------------------
# Testes de RAGGenerator
# ---------------------------------------------------------------------------


class TestRAGGenerator:
    """Testes para a classe RAGGenerator."""

    def test_gerar_retorna_resposta_rag(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """Verifica que gerar() retorna uma instância de RespostaRAG com texto correto."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        resposta = gerador.gerar("query de teste", resultados_exemplo)

        assert isinstance(resposta, RespostaRAG)
        assert resposta.texto == "Resposta gerada pelo LLM sobre treinamento."

    def test_gerar_fontes_nao_vazias(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """Verifica que fontes não estão vazias quando resultados são fornecidos."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        resposta = gerador.gerar("query de teste", resultados_exemplo)

        assert len(resposta.fontes) > 0
        assert "metodologia_treino.pdf" in resposta.fontes

    def test_gerar_com_lista_vazia_de_resultados(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
    ) -> None:
        """Verifica que gerar() retorna RespostaRAG com fontes vazias quando não há resultados."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        resposta = gerador.gerar("query sem contexto", [])

        assert isinstance(resposta, RespostaRAG)
        assert resposta.fontes == []

    def test_gerar_fontes_sao_unicas(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
    ) -> None:
        """Verifica que fontes duplicadas são eliminadas no retorno."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        from src.generation.llm import RAGGenerator

        # Dois chunks com a mesma fonte
        chunk1 = Chunk(conteudo="Conteúdo A", fonte="mesmo_arquivo.pdf", pagina=1, chunk_id="id1")
        chunk2 = Chunk(conteudo="Conteúdo B", fonte="mesmo_arquivo.pdf", pagina=2, chunk_id="id2")
        resultados = [
            ResultadoBusca(chunk=chunk1, score=0.9),
            ResultadoBusca(chunk=chunk2, score=0.8),
        ]

        gerador = RAGGenerator(settings=settings_mock)
        resposta = gerador.gerar("query", resultados)

        # A mesma fonte deve aparecer apenas uma vez
        assert resposta.fontes.count("mesmo_arquivo.pdf") == 1

    def test_gerar_instancia_llm_com_max_tokens(
        self,
        mocker,
        settings_mock,
    ) -> None:
        """Verifica que ChatNVIDIA é instanciado com max_tokens para evitar truncamento."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        mock_nvidia_cls = mocker.patch("src.generation.llm.ChatNVIDIA")
        mock_nvidia_cls.return_value.invoke.return_value = mocker.MagicMock(
            content="resposta"
        )

        from src.generation.llm import RAGGenerator
        RAGGenerator(settings=settings_mock)

        _, kwargs = mock_nvidia_cls.call_args
        assert "max_tokens" in kwargs
        assert kwargs["max_tokens"] > 1024


# ---------------------------------------------------------------------------
# Testes de _carregar_metodologia
# ---------------------------------------------------------------------------


class TestCarregarMetodologia:
    """Testes para a função _carregar_metodologia."""

    def test_retorna_string_vazia_se_arquivo_nao_existe(self, tmp_path, mocker) -> None:
        """Verifica que retorna string vazia quando o arquivo de metodologia não existe."""
        import src.generation.llm as llm_mod

        mocker.patch.object(
            llm_mod, "_CAMINHO_METODOLOGIA",
            str(tmp_path / "metodologia_inexistente.txt"),
        )

        resultado = llm_mod._carregar_metodologia()

        assert resultado == ""

    def test_retorna_conteudo_quando_arquivo_existe(self, tmp_path, mocker) -> None:
        """Verifica que retorna o conteúdo do arquivo quando ele existe."""
        import src.generation.llm as llm_mod

        arquivo = tmp_path / "metodologia.txt"
        arquivo.write_text("Metodologia de teste: periodização linear.", encoding="utf-8")
        mocker.patch.object(
            llm_mod, "_CAMINHO_METODOLOGIA",
            str(arquivo),
        )

        resultado = llm_mod._carregar_metodologia()

        assert resultado == "Metodologia de teste: periodização linear."


# ---------------------------------------------------------------------------
# Testes de montar_prompt
# ---------------------------------------------------------------------------


class TestMontarPrompt:
    """Testes para a função montar_prompt."""

    def test_prompt_contem_query(self, resultados_exemplo: list[ResultadoBusca]) -> None:
        """Verifica que o prompt contém a query fornecida pelo usuário."""
        prompt = montar_prompt("minha query", resultados_exemplo, metodologia="", contexto_aluno="")

        assert "minha query" in prompt

    def test_prompt_contem_fontes(self, resultados_exemplo: list[ResultadoBusca]) -> None:
        """Verifica que o prompt contém o nome da fonte de cada resultado."""
        prompt = montar_prompt("query de teste", resultados_exemplo, metodologia="", contexto_aluno="")

        for resultado in resultados_exemplo:
            assert resultado.chunk.fonte in prompt

    def test_prompt_formato_referencias(self, resultados_exemplo: list[ResultadoBusca]) -> None:
        """Verifica que o prompt possui a seção REFERÊNCIAS e o formato [1] correto."""
        prompt = montar_prompt("query de teste", resultados_exemplo, metodologia="", contexto_aluno="")

        assert "REFERÊNCIAS:" in prompt
        assert "[1]" in prompt

    def test_prompt_sem_resultados_indica_ausencia(self) -> None:
        """Verifica que prompt sem resultados contém mensagem de ausência de referências."""
        prompt = montar_prompt("query sem contexto", [], metodologia="", contexto_aluno="")

        assert "REFERÊNCIAS: (nenhuma referência disponível)" in prompt
        assert "query sem contexto" in prompt

    def test_prompt_multiplos_resultados_numerados(self) -> None:
        """Verifica que múltiplos resultados são numerados corretamente no prompt."""
        chunk1 = Chunk(conteudo="Texto 1", fonte="fonte1.pdf", pagina=1, chunk_id="id1")
        chunk2 = Chunk(conteudo="Texto 2", fonte="fonte2.pdf", pagina=5, chunk_id="id2")
        resultados = [
            ResultadoBusca(chunk=chunk1, score=0.9),
            ResultadoBusca(chunk=chunk2, score=0.8),
        ]

        prompt = montar_prompt("pergunta", resultados, metodologia="", contexto_aluno="")

        assert "[1]" in prompt
        assert "[2]" in prompt
        assert "fonte1.pdf" in prompt
        assert "fonte2.pdf" in prompt

    def test_prompt_contem_numero_de_pagina(self, resultados_exemplo: list[ResultadoBusca]) -> None:
        """Verifica que o número de página do chunk está presente no prompt."""
        prompt = montar_prompt("query", resultados_exemplo, metodologia="", contexto_aluno="")

        # A página do primeiro chunk de exemplo é 1
        assert "p. 1" in prompt


# ---------------------------------------------------------------------------
# Testes de montar_prompt com metodologia e contexto do aluno
# ---------------------------------------------------------------------------


class TestMontarPromptComMetodologia:
    """Testes para prompt com metodologia e contexto do aluno."""

    def test_prompt_contem_metodologia_quando_fornecida(self) -> None:
        """Verifica que metodologia aparece no prompt quando fornecida."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="Seguir método RB: periodização ondulatória.",
            contexto_aluno="",
        )

        assert "Seguir método RB: periodização ondulatória." in prompt

    def test_prompt_contem_contexto_do_aluno(self, resultados_exemplo) -> None:
        """Verifica que o contexto do aluno está presente no prompt."""
        contexto = "Nome: João. Idade: 32. Modalidade: jiu-jitsu."
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno=contexto,
        )

        assert "João" in prompt
        assert "jiu-jitsu" in prompt

    def test_prompt_contem_template_de_saida(self, resultados_exemplo) -> None:
        """Verifica que o template de saída estruturada com semanas está no prompt."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
        )

        assert "Resumo do Aluno" in prompt
        assert "Metodologia do Treino" in prompt
        assert "SEMANA" in prompt

    def test_prompt_sem_metodologia_nao_tem_secao_metodologia(self) -> None:
        """Verifica que prompt sem metodologia não inclui marcador de metodologia."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )

        assert "[METODOLOGIA" not in prompt

    def test_prompt_nao_instrui_citacao_inline(self) -> None:
        """Verifica que o prompt não instrui citação inline após cada afirmação."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        assert "Cite a fonte após cada afirmação" not in prompt

    def test_prompt_instrui_protocolo_periodizado(self) -> None:
        """Verifica que o prompt instrui geração de protocolo com múltiplas semanas."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        assert "semanas" in prompt.lower()

    def test_prompt_instrui_metodo_por_exercicio(self) -> None:
        """Verifica que o prompt instrui incluir método de treino por exercício (ex: método)."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        # O novo formato usa "(método)" como placeholder no template de saída
        assert "método" in prompt.lower()

    def test_prompt_instrui_minimo_fortalecimento_por_grupo(self) -> None:
        """Verifica que o prompt instrui mínimo de exercícios por grupo muscular."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        assert "músculos pequenos" in prompt.lower()
        assert "músculos grandes" in prompt.lower()

    def test_prompt_instrui_semanas_completas_sem_abreviacao(self) -> None:
        """Verifica que o prompt proíbe abreviação de semanas com reticências."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        assert "4 semanas completas" in prompt.lower() and "pelo menos 4" in prompt.lower()

    def test_prompt_instrui_respeitar_dias_por_semana(self) -> None:
        """Verifica que o prompt instrui o LLM a respeitar o número de dias do aluno."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        assert "dias disponíveis por semana" in prompt.lower()

    def test_prompt_instrui_formato_duas_linhas_exercicio(self) -> None:
        """Verifica que o prompt instrui o formato de exercício em duas linhas (nome + séries)."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=[],
            metodologia="",
            contexto_aluno="",
        )
        # A instrução base deve conter a diretiva explícita de formato de duas linhas
        assert "formato obrigatório" in prompt.lower()
        assert "duas linhas" in prompt.lower()


# ---------------------------------------------------------------------------
# Testes de montar_prompt com catálogo de exercícios
# ---------------------------------------------------------------------------


class TestMontarPromptComCatalogo:
    """Testes para prompt com catálogo de exercícios filtrado."""

    def test_prompt_com_catalogo_injeta_secao_catalogo(self, resultados_exemplo) -> None:
        """Prompt com catalogo_filtrado contém seção [CATÁLOGO DE EXERCÍCIOS]."""
        catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado=catalogo_md,
        )
        assert "[CATÁLOGO DE EXERCÍCIOS" in prompt
        assert "Prancha" in prompt

    def test_prompt_com_catalogo_contem_instrucao_volume(self, resultados_exemplo) -> None:
        """Template com catálogo contém instrução de mínimo 12 exercícios de Fortalecimento."""
        catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado=catalogo_md,
        )
        assert "12" in prompt
        assert "NÃO contam" in prompt

    def test_prompt_sem_catalogo_nao_tem_justificativa(self, resultados_exemplo) -> None:
        """Template NÃO inclui Justificativa Personalizada quando catálogo ausente."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
        )
        assert "Justificativa Personalizada" not in prompt

    def test_prompt_catalogo_string_vazia_tratado_como_none(self, resultados_exemplo) -> None:
        """catalogo_filtrado='' é tratado internamente como None (sem seção)."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado="",
        )
        assert "[CATÁLOGO DE EXERCÍCIOS" not in prompt
        assert "Justificativa Personalizada" not in prompt


# ---------------------------------------------------------------------------
# Testes de RAGGenerator com catálogo
# ---------------------------------------------------------------------------


class TestRAGGeneratorComCatalogo:
    """Testes de integração do RAGGenerator com o CatalogoExercicios."""

    def test_gerar_com_equipamentos_e_nivel_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() com equipamentos e nivel chama montar_prompt com catalogo_filtrado não-None."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")

        catalogo_mock = mocker.MagicMock()
        catalogo_mock.filtrar.return_value = "## Core\n\n| Prancha | Peso Corporal |"
        mocker.patch(
            "src.generation.llm.CatalogoExercicios",
            return_value=catalogo_mock,
        )

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar(
            "Criar treino",
            resultados_exemplo,
            contexto_aluno="Aluno: João",
            equipamentos=["Máquinas"],
            nivel="Iniciante",
            restricoes="dor no joelho",
        )

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert kwargs.get("catalogo_filtrado") is not None

    def test_gerar_sem_equipamentos_nao_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() sem equipamentos não ativa o catálogo (retrocompatível)."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        mocker.patch("src.generation.llm.CatalogoExercicios")

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar("Criar treino", resultados_exemplo)

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert "catalogo_filtrado" not in kwargs or kwargs.get("catalogo_filtrado") is None

    def test_gerar_com_equipamentos_sem_nivel_nao_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() com equipamentos mas sem nivel não ativa catálogo."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        mocker.patch("src.generation.llm.CatalogoExercicios")

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar("Criar treino", resultados_exemplo, equipamentos=["Máquinas"], nivel="")

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert "catalogo_filtrado" not in kwargs or kwargs.get("catalogo_filtrado") is None
