"""
Testes unitários para os módulos src/config/settings.py e src/config/types.py.

Utiliza monkeypatch do pytest para isolar variáveis de ambiente,
garantindo que os testes não dependam de um arquivo .env real.
"""

import pytest

from src.config.settings import Settings
from src.config.types import Chunk, RespostaRAG, ResultadoBusca


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

def _configurar_env_completo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Define todas as variáveis de ambiente necessárias para Settings."""
    monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
    monkeypatch.setenv("NVIDIA_BASE_URL", "https://api.exemplo.com/v1")
    monkeypatch.setenv("LLM_MODEL", "meta/llama-3-teste")
    monkeypatch.setenv("QDRANT_HOST", "qdrant-host-teste")
    monkeypatch.setenv("QDRANT_PORT", "9999")
    monkeypatch.setenv("QDRANT_COLLECTION", "colecao_teste")
    monkeypatch.setenv("EMBEDDING_MODEL", "modelo-embedding-teste")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


def _desabilitar_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Substitui load_dotenv por uma função no-op para evitar leitura do .env real."""
    import src.config.settings as modulo_settings
    monkeypatch.setattr(modulo_settings, "load_dotenv", lambda: None)


# ---------------------------------------------------------------------------
# Testes de Settings
# ---------------------------------------------------------------------------

class TestSettings:
    """Testes para a classe Settings."""

    def test_settings_carrega_variaveis_corretamente(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que todos os atributos são carregados corretamente do ambiente."""
        _desabilitar_dotenv(monkeypatch)
        _configurar_env_completo(monkeypatch)

        settings = Settings()

        assert settings.nvidia_api_key == "chave-nvidia-teste"
        assert settings.nvidia_base_url == "https://api.exemplo.com/v1"
        assert settings.llm_model == "meta/llama-3-teste"
        assert settings.qdrant_host == "qdrant-host-teste"
        assert settings.qdrant_port == 9999
        assert settings.qdrant_collection == "colecao_teste"
        assert settings.embedding_model == "modelo-embedding-teste"
        assert settings.log_level == "DEBUG"

    def test_settings_lanca_erro_sem_nvidia_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que ValueError é lançado quando NVIDIA_API_KEY está ausente."""
        _desabilitar_dotenv(monkeypatch)
        _configurar_env_completo(monkeypatch)
        monkeypatch.delenv("NVIDIA_API_KEY")

        with pytest.raises(ValueError, match="NVIDIA_API_KEY"):
            Settings()

    def test_settings_lanca_erro_sem_qdrant_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que ValueError é lançado quando QDRANT_HOST está ausente."""
        _desabilitar_dotenv(monkeypatch)
        _configurar_env_completo(monkeypatch)
        monkeypatch.delenv("QDRANT_HOST")

        with pytest.raises(ValueError, match="QDRANT_HOST"):
            Settings()

    def test_settings_usa_valores_padrao(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que os valores padrão são aplicados quando variáveis opcionais estão ausentes."""
        _desabilitar_dotenv(monkeypatch)

        # Define apenas as variáveis obrigatórias
        monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
        monkeypatch.setenv("QDRANT_HOST", "localhost")

        # Remove variáveis opcionais para garantir que os padrões sejam usados
        for var in (
            "NVIDIA_BASE_URL",
            "LLM_MODEL",
            "QDRANT_PORT",
            "QDRANT_COLLECTION",
            "EMBEDDING_MODEL",
            "LOG_LEVEL",
        ):
            monkeypatch.delenv(var, raising=False)

        settings = Settings()

        assert settings.nvidia_base_url == "https://integrate.api.nvidia.com/v1"
        assert settings.llm_model == "meta/llama-3.1-70b-instruct"
        assert settings.qdrant_port == 6333
        assert settings.qdrant_collection == "jarvis_knowledge"
        assert settings.embedding_model == (
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        )
        assert settings.log_level == "INFO"


# ---------------------------------------------------------------------------
# Testes de tipos (Chunk, ResultadoBusca, RespostaRAG)
# ---------------------------------------------------------------------------

class TestTipos:
    """Testes para os dataclasses definidos em types.py."""

    def test_chunk_cria_instancia_corretamente(self) -> None:
        """Verifica que Chunk armazena todos os campos corretamente."""
        chunk = Chunk(
            conteudo="Texto de exemplo",
            fonte="documento.pdf",
            pagina=3,
            chunk_id="abc123",
        )

        assert chunk.conteudo == "Texto de exemplo"
        assert chunk.fonte == "documento.pdf"
        assert chunk.pagina == 3
        assert chunk.chunk_id == "abc123"

    def test_resultado_busca_cria_instancia_corretamente(self) -> None:
        """Verifica que ResultadoBusca armazena chunk e score corretamente."""
        chunk = Chunk(conteudo="Texto", fonte="fonte.pdf", pagina=1, chunk_id="xyz")
        resultado = ResultadoBusca(chunk=chunk, score=0.95)

        assert resultado.chunk is chunk
        assert resultado.score == 0.95

    def test_resposta_rag_cria_instancia_corretamente(self) -> None:
        """Verifica que RespostaRAG armazena texto e lista de fontes corretamente."""
        resposta = RespostaRAG(
            texto="Resposta gerada pelo LLM.",
            fontes=["documento1.pdf", "documento2.pdf"],
        )

        assert resposta.texto == "Resposta gerada pelo LLM."
        assert len(resposta.fontes) == 2
        assert "documento1.pdf" in resposta.fontes
