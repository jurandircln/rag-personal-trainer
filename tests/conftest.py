"""Configuração global de fixtures para os testes."""

import pytest


@pytest.fixture
def settings_mock(monkeypatch):
    """Retorna um objeto Settings com valores de teste, sem necessidade de .env real."""
    monkeypatch.setattr("dotenv.load_dotenv", lambda **kw: None)
    monkeypatch.setenv("NVIDIA_API_KEY", "test-key")
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    from src.config.settings import Settings
    return Settings()


@pytest.fixture
def chunks_exemplo():
    """Retorna uma lista de Chunks de exemplo para uso nos testes."""
    from src.config.types import Chunk
    return [
        Chunk(
            conteudo="Texto sobre treino de força e hipertrofia muscular.",
            fonte="metodologia_treino.pdf",
            pagina=1,
            chunk_id="abc123def456",
        ),
        Chunk(
            conteudo="Princípios de periodização para atletas de alto rendimento.",
            fonte="periodizacao.pdf",
            pagina=5,
            chunk_id="def456ghi789",
        ),
    ]


@pytest.fixture
def resultados_exemplo(chunks_exemplo):
    """Retorna lista de ResultadoBusca de exemplo."""
    from src.config.types import ResultadoBusca
    return [
        ResultadoBusca(chunk=chunks_exemplo[0], score=0.95),
        ResultadoBusca(chunk=chunks_exemplo[1], score=0.87),
    ]
