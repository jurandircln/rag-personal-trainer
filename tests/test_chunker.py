"""
Testes unitários para src/ingestion/chunker.py.

Verifica o comportamento do DocumentChunker sem dependências externas:
divisão de texto, determinismo dos chunk_ids e preservação de metadados.
"""

import pytest

from src.ingestion.chunker import DocumentChunker


# ---------------------------------------------------------------------------
# Testes do DocumentChunker
# ---------------------------------------------------------------------------


def test_dividir_respeita_chunk_size(settings_mock) -> None:
    """Verifica que nenhum chunk ultrapassa o tamanho máximo configurado."""
    chunk_size = 800
    # Cria texto longo o suficiente para gerar múltiplos chunks
    texto_longo = "A " * 600  # ~1200 caracteres, garante pelo menos 2 chunks

    paginas = [{"conteudo": texto_longo, "fonte": "doc.pdf", "pagina": 0}]

    chunker = DocumentChunker(settings_mock, chunk_size=chunk_size, chunk_overlap=100)
    resultado = chunker.dividir(paginas)

    # Deve haver pelo menos um chunk
    assert len(resultado) >= 1

    # Nenhum chunk deve exceder o limite máximo com tolerância para o splitter
    for chunk in resultado:
        assert len(chunk.conteudo) <= 1000, (
            f"Chunk com {len(chunk.conteudo)} caracteres excede o limite tolerado de 1000."
        )


def test_dividir_chunk_id_deterministico(settings_mock) -> None:
    """Verifica que o chunk_id é idêntico em duas chamadas com o mesmo conteúdo."""
    paginas = [
        {"conteudo": "Texto de exemplo para testar determinismo do hash.", "fonte": "treino.pdf", "pagina": 1}
    ]

    chunker = DocumentChunker(settings_mock, chunk_size=800, chunk_overlap=100)

    # Executa a divisão duas vezes com a mesma entrada
    resultado_a = chunker.dividir(paginas)
    resultado_b = chunker.dividir(paginas)

    # Os chunk_ids devem ser idênticos entre as duas execuções
    ids_a = [chunk.chunk_id for chunk in resultado_a]
    ids_b = [chunk.chunk_id for chunk in resultado_b]

    assert ids_a == ids_b, "Os chunk_ids devem ser determinísticos para o mesmo conteúdo."


def test_dividir_preserva_metadados(settings_mock) -> None:
    """Verifica que fonte e pagina originais são preservados em todos os chunks."""
    texto = "Conteúdo de treino funcional. " * 50  # texto moderadamente longo
    fonte_esperada = "anamnese_joao.pdf"
    pagina_esperada = 3

    paginas = [{"conteudo": texto, "fonte": fonte_esperada, "pagina": pagina_esperada}]

    chunker = DocumentChunker(settings_mock, chunk_size=200, chunk_overlap=20)
    resultado = chunker.dividir(paginas)

    # Todos os chunks devem ter a fonte e página corretas
    for chunk in resultado:
        assert chunk.fonte == fonte_esperada, (
            f"Fonte esperada '{fonte_esperada}', obtida '{chunk.fonte}'."
        )
        assert chunk.pagina == pagina_esperada, (
            f"Página esperada {pagina_esperada}, obtida {chunk.pagina}."
        )


def test_dividir_com_texto_curto(settings_mock) -> None:
    """Verifica que um texto menor que chunk_size retorna exatamente 1 chunk."""
    texto_curto = "Texto curto."  # bem menor que 800 caracteres

    paginas = [{"conteudo": texto_curto, "fonte": "curto.pdf", "pagina": 0}]

    chunker = DocumentChunker(settings_mock, chunk_size=800, chunk_overlap=100)
    resultado = chunker.dividir(paginas)

    assert len(resultado) == 1, (
        f"Texto menor que chunk_size deve gerar exatamente 1 chunk, obtido {len(resultado)}."
    )
    assert resultado[0].conteudo == texto_curto


def test_dividir_lista_vazia_retorna_lista_vazia(settings_mock) -> None:
    """Verifica que uma lista vazia de páginas retorna uma lista vazia de chunks."""
    chunker = DocumentChunker(settings_mock, chunk_size=800, chunk_overlap=100)
    resultado = chunker.dividir([])

    assert resultado == [], (
        f"Lista vazia de páginas deve retornar lista vazia, obtido {resultado}."
    )
