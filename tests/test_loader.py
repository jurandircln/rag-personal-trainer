"""
Testes unitários para src/ingestion/loader.py.

Utiliza mocks para simular PyPDFLoader e glob, garantindo que os testes
não dependam de arquivos PDF reais ou de serviços externos.
"""

import pytest

from src.ingestion.loader import DocumentLoader


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------


def _criar_documento_falso(conteudo: str, pagina: int):
    """Cria um objeto Document simulado com os atributos mínimos necessários."""

    class DocumentoFalso:
        def __init__(self, page_content: str, metadata: dict):
            self.page_content = page_content
            self.metadata = metadata

    return DocumentoFalso(page_content=conteudo, metadata={"page": pagina})


# ---------------------------------------------------------------------------
# Testes de carregar_arquivo
# ---------------------------------------------------------------------------


class TestCarregarArquivo:
    """Testes para o método DocumentLoader.carregar_arquivo."""

    def test_carregar_arquivo_retorna_lista_de_paginas(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que o método retorna uma lista com um dicionário por página."""
        # Configura o mock do PyPDFLoader para retornar 2 documentos falsos
        documentos_falsos = [
            _criar_documento_falso("Conteúdo da página 1", 0),
            _criar_documento_falso("Conteúdo da página 2", 1),
        ]
        mock_loader = mocker.MagicMock()
        mock_loader.load.return_value = documentos_falsos
        mocker.patch(
            "src.ingestion.loader.PyPDFLoader", return_value=mock_loader
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_arquivo("/caminho/falso/documento.pdf")

        # Deve retornar exatamente 2 itens
        assert len(resultado) == 2

        # Cada item deve possuir as chaves esperadas
        for item in resultado:
            assert "conteudo" in item
            assert "fonte" in item
            assert "pagina" in item

    def test_carregar_arquivo_fonte_e_nome_do_arquivo(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que 'fonte' contém apenas o nome do arquivo, sem o caminho completo."""
        documentos_falsos = [
            _criar_documento_falso("Texto qualquer", 0),
        ]
        mock_loader = mocker.MagicMock()
        mock_loader.load.return_value = documentos_falsos
        mocker.patch(
            "src.ingestion.loader.PyPDFLoader", return_value=mock_loader
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_arquivo("/caminho/muito/longo/treinamento.pdf")

        # A fonte deve ser apenas o nome do arquivo, sem barras ou diretórios
        assert resultado[0]["fonte"] == "treinamento.pdf"

    def test_carregar_arquivo_mapeia_conteudo_e_pagina(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que conteudo e pagina são corretamente extraídos dos documentos."""
        documentos_falsos = [
            _criar_documento_falso("Texto da primeira página", 0),
            _criar_documento_falso("Texto da segunda página", 1),
        ]
        mock_loader = mocker.MagicMock()
        mock_loader.load.return_value = documentos_falsos
        mocker.patch(
            "src.ingestion.loader.PyPDFLoader", return_value=mock_loader
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_arquivo("/qualquer/arquivo.pdf")

        assert resultado[0]["conteudo"] == "Texto da primeira página"
        assert resultado[0]["pagina"] == 0
        assert resultado[1]["conteudo"] == "Texto da segunda página"
        assert resultado[1]["pagina"] == 1

    def test_carregar_arquivo_usa_pagina_zero_quando_metadado_ausente(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que pagina assume 0 quando o metadado 'page' não está presente."""

        class DocumentoSemPagina:
            """Documento simulado sem metadado de página."""
            page_content = "Texto sem metadado de página"
            metadata: dict = {}

        mock_loader = mocker.MagicMock()
        mock_loader.load.return_value = [DocumentoSemPagina()]
        mocker.patch(
            "src.ingestion.loader.PyPDFLoader", return_value=mock_loader
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_arquivo("/qualquer/sem_pagina.pdf")

        assert resultado[0]["pagina"] == 0


# ---------------------------------------------------------------------------
# Testes de carregar_diretorio
# ---------------------------------------------------------------------------


class TestCarregarDiretorio:
    """Testes para o método DocumentLoader.carregar_diretorio."""

    def test_carregar_diretorio_carrega_multiplos_pdfs(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que o método combina páginas de múltiplos PDFs encontrados."""
        # Simula o glob retornando 2 arquivos PDF
        mocker.patch(
            "src.ingestion.loader.glob.glob",
            return_value=[
                "/dados/arquivo_a.pdf",
                "/dados/arquivo_b.pdf",
            ],
        )

        # Simula PyPDFLoader retornando 1 página por arquivo
        documentos_falsos = [_criar_documento_falso("Página única", 0)]
        mock_loader = mocker.MagicMock()
        mock_loader.load.return_value = documentos_falsos
        mocker.patch(
            "src.ingestion.loader.PyPDFLoader", return_value=mock_loader
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_diretorio("/dados")

        # Dois arquivos × 1 página cada = 2 itens no total
        assert len(resultado) == 2

    def test_carregar_diretorio_sem_pdfs_retorna_lista_vazia(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que uma lista vazia é retornada quando não há PDFs no diretório."""
        # Simula glob sem resultados
        mocker.patch(
            "src.ingestion.loader.glob.glob",
            return_value=[],
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_diretorio("/diretorio/vazio")

        assert resultado == []

    def test_carregar_diretorio_concatena_todas_as_paginas(
        self, settings_mock, mocker
    ) -> None:
        """Verifica que páginas de todos os arquivos são combinadas em uma só lista."""
        mocker.patch(
            "src.ingestion.loader.glob.glob",
            return_value=[
                "/docs/manual.pdf",
                "/docs/anamnese.pdf",
            ],
        )

        # Primeiro arquivo tem 2 páginas, segundo tem 3 páginas
        paginas_arquivo_a = [
            _criar_documento_falso("Pág 1 do manual", 0),
            _criar_documento_falso("Pág 2 do manual", 1),
        ]
        paginas_arquivo_b = [
            _criar_documento_falso("Pág 1 da anamnese", 0),
            _criar_documento_falso("Pág 2 da anamnese", 1),
            _criar_documento_falso("Pág 3 da anamnese", 2),
        ]

        mock_loader_a = mocker.MagicMock()
        mock_loader_a.load.return_value = paginas_arquivo_a
        mock_loader_b = mocker.MagicMock()
        mock_loader_b.load.return_value = paginas_arquivo_b

        mocker.patch(
            "src.ingestion.loader.PyPDFLoader",
            side_effect=[mock_loader_a, mock_loader_b],
        )

        loader = DocumentLoader(settings_mock)
        resultado = loader.carregar_diretorio("/docs")

        # 2 + 3 = 5 páginas no total
        assert len(resultado) == 5
