"""
Divide documentos em chunks para indexação vetorial.

Utiliza RecursiveCharacterTextSplitter do LangChain para fragmentar
páginas de documentos PDF em trechos menores, adequados para embeddings.
"""

import hashlib
import logging

from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.config.settings import Settings
from src.config.types import Chunk

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Divide páginas de documentos em chunks menores para indexação vetorial."""

    def __init__(
        self,
        settings: Settings,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ) -> None:
        """Inicializa o divisor de documentos em chunks.

        Args:
            settings: configurações do sistema injetadas como dependência.
            chunk_size: tamanho máximo de cada chunk em caracteres.
            chunk_overlap: número de caracteres de sobreposição entre chunks adjacentes.
        """
        self._settings = settings
        # Inicializa o divisor de texto com os parâmetros recebidos
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._chunk_size = chunk_size
        logger.debug(
            "DocumentChunker inicializado com chunk_size=%d e chunk_overlap=%d.",
            chunk_size,
            chunk_overlap,
        )

    def dividir(self, paginas: list[dict]) -> list[Chunk]:
        """Divide páginas em chunks menores para indexação.

        Cada item de `paginas` deve ter o formato:
            {"conteudo": str, "fonte": str, "pagina": int}

        O chunk_id é gerado de forma determinística usando SHA-256 do conteúdo,
        garantindo que o mesmo texto sempre produza o mesmo identificador.

        Args:
            paginas: lista de dicionários representando páginas de documentos.

        Returns:
            Lista de Chunk com conteudo, fonte, pagina e chunk_id preenchidos.
        """
        # Retorna lista vazia imediatamente se não há páginas para processar
        if not paginas:
            logger.debug("Nenhuma página recebida; retornando lista vazia.")
            return []

        chunks: list[Chunk] = []

        for pagina in paginas:
            conteudo_pagina: str = pagina["conteudo"]
            fonte: str = pagina["fonte"]
            numero_pagina: int = pagina["pagina"]

            # Divide o texto da página em fragmentos menores
            fragmentos = self._splitter.split_text(conteudo_pagina)

            for fragmento in fragmentos:
                # Gera identificador determinístico baseado no conteúdo do chunk
                chunk_id = hashlib.sha256(fragmento.encode()).hexdigest()[:16]

                chunks.append(
                    Chunk(
                        conteudo=fragmento,
                        fonte=fonte,
                        pagina=numero_pagina,
                        chunk_id=chunk_id,
                    )
                )

        logger.info(
            "Divisão concluída: %d página(s) → %d chunk(s) gerados.",
            len(paginas),
            len(chunks),
        )
        return chunks
