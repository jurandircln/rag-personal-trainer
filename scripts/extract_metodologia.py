"""Script para extrair o texto do metodo_rb PDF e salvar como instrução do sistema.

Uso: python scripts/extract_metodologia.py
"""

import os
import sys

# Adiciona a raiz do projeto ao path para permitir imports locais
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from langchain_community.document_loaders import PyPDFLoader


def main():
    """Extrai texto do PDF da metodologia e salva em src/generation/metodologia.txt."""
    caminho_pdf = os.path.join(RAIZ, "data", "raw", "metodo_rb_treinamento_integrado_manual.pdf")
    caminho_saida = os.path.join(RAIZ, "src", "generation", "metodologia.txt")

    if not os.path.exists(caminho_pdf):
        print(f"ERRO: PDF não encontrado em '{caminho_pdf}'")
        sys.exit(1)

    # Carrega as páginas do PDF
    try:
        loader = PyPDFLoader(caminho_pdf)
        paginas = loader.load()
    except Exception as e:
        print(f"ERRO: Falha ao ler o PDF '{caminho_pdf}': {e}")
        sys.exit(1)

    if not paginas:
        print("AVISO: Nenhum texto extraído do PDF. O arquivo pode ser baseado em imagem.")
        sys.exit(1)

    texto = "\n\n".join(pagina.page_content for pagina in paginas)

    if not texto.strip():
        print("AVISO: Texto extraído está vazio. Verifique se o PDF contém texto selecionável.")
        sys.exit(1)

    # Salva o texto extraído no arquivo de destino
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    try:
        with open(caminho_saida, "w", encoding="utf-8") as f:
            f.write(texto)
    except OSError as e:
        print(f"ERRO: Não foi possível salvar o arquivo '{caminho_saida}': {e}")
        sys.exit(1)

    print(f"Metodologia extraída: {len(paginas)} páginas → '{caminho_saida}'")


if __name__ == "__main__":
    main()
