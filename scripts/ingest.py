"""Script CLI para indexar documentos no Qdrant."""

import argparse
import logging
import os
import sys

# Adiciona a raiz do projeto ao path para que as importações de src/ funcionem
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.ingestion.loader import DocumentLoader
from src.ingestion.chunker import DocumentChunker
from src.ingestion.embedder import VectorIndexer


def main():
    """Ponto de entrada do script de indexação."""
    # 1. Faz o parse dos argumentos da linha de comando
    parser = argparse.ArgumentParser(
        description="Indexa documentos PDF no Qdrant para busca semântica."
    )
    parser.add_argument(
        "--caminho",
        required=True,
        help="Caminho para um arquivo PDF ou diretório contendo PDFs a serem indexados.",
    )
    args = parser.parse_args()
    caminho = args.caminho

    # 2. Configura o logging com formato padrão
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # 3. Carrega as configurações do sistema
    settings = Settings()

    # 4. Inicializa os componentes do pipeline de ingestão
    loader = DocumentLoader(settings)
    chunker = DocumentChunker(settings)
    indexer = VectorIndexer(settings)

    # 5. Cria a coleção no Qdrant caso não exista
    indexer.criar_colecao_se_necessario()

    # 6. Determina se o caminho é um arquivo ou diretório e carrega os documentos
    if os.path.isfile(caminho):
        logger.info("Processando arquivo: %s", caminho)
        paginas = loader.carregar_arquivo(caminho)
    else:
        logger.info("Processando diretório: %s", caminho)
        paginas = loader.carregar_diretorio(caminho)

    # 7. Log do número de páginas carregadas
    logger.info("Carregados %d páginas de documentos", len(paginas))

    # 8. Divide as páginas em chunks menores
    chunks = chunker.dividir(paginas)

    # 9. Log do número de chunks gerados
    logger.info("Gerados %d chunks", len(chunks))

    # 10. Indexa os chunks no Qdrant
    total = indexer.indexar(chunks)

    # 11. Log de conclusão da indexação
    logger.info("Indexação concluída: %d chunks indexados com sucesso", total)


if __name__ == "__main__":
    main()
