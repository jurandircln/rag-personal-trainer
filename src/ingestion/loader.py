"""
Carrega documentos PDF do sistema de arquivos usando loaders do LangChain.

Responsável pela etapa inicial do pipeline de ingestão: leitura dos arquivos
PDF e extração do conteúdo textual página a página.
"""

import glob
import logging
import os

from langchain_community.document_loaders import PyPDFLoader

from src.config.settings import Settings

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Carrega documentos PDF e retorna o conteúdo estruturado por página."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o carregador de documentos.

        Args:
            settings: instância de Settings com as configurações do sistema.
        """
        # Guarda as configurações para uso futuro (ex: limites, filtros)
        self._settings = settings

    def carregar_arquivo(self, caminho: str) -> list[dict]:
        """Carrega um arquivo PDF e retorna lista de páginas.

        Cada item da lista representa uma página do documento com as chaves:
        - ``conteudo``: texto extraído da página
        - ``fonte``: nome do arquivo (sem o caminho completo)
        - ``pagina``: número da página conforme metadados do LangChain

        Args:
            caminho: caminho absoluto ou relativo para o arquivo PDF.

        Returns:
            Lista de dicionários, um por página do documento.
        """
        # Extrai apenas o nome do arquivo, sem o caminho completo
        nome_arquivo = os.path.basename(caminho)

        logger.info("Carregando arquivo: %s", nome_arquivo)

        # Usa o loader do LangChain para extrair as páginas do PDF
        loader = PyPDFLoader(caminho)
        paginas = loader.load()

        resultado = []
        for documento in paginas:
            # Obtém o número da página a partir dos metadados; usa 0 como padrão
            numero_pagina = documento.metadata.get("page", 0)
            resultado.append(
                {
                    "conteudo": documento.page_content,
                    "fonte": nome_arquivo,
                    "pagina": numero_pagina,
                }
            )

        logger.info(
            "Arquivo '%s' carregado com %d página(s).", nome_arquivo, len(resultado)
        )
        return resultado

    def carregar_diretorio(self, caminho: str) -> list[dict]:
        """Carrega todos os PDFs encontrados em um diretório.

        Percorre o diretório em busca de arquivos com extensão ``.pdf`` e
        chama :meth:`carregar_arquivo` para cada um deles.

        Args:
            caminho: caminho para o diretório que contém os arquivos PDF.

        Returns:
            Lista concatenada de páginas de todos os PDFs encontrados.
            Retorna lista vazia se nenhum PDF for encontrado.
        """
        # Monta o padrão de busca para arquivos PDF no diretório informado
        padrao = os.path.join(caminho, "*.pdf")
        arquivos_pdf = glob.glob(padrao)

        if not arquivos_pdf:
            logger.warning("Nenhum arquivo PDF encontrado em: %s", caminho)
            return []

        logger.info(
            "Encontrado(s) %d arquivo(s) PDF em '%s'. Iniciando carregamento.",
            len(arquivos_pdf),
            caminho,
        )

        resultado_total: list[dict] = []
        for arquivo in arquivos_pdf:
            paginas = self.carregar_arquivo(arquivo)
            resultado_total.extend(paginas)

        logger.info(
            "Diretório '%s' processado: %d página(s) no total.",
            caminho,
            len(resultado_total),
        )
        return resultado_total
