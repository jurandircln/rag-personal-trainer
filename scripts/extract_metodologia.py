"""Script para extrair o texto do metodo_rb PDF e salvar como instrução do sistema."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader


def main():
    """Extrai texto do PDF da metodologia e salva em src/generation/metodologia.txt."""
    caminho_pdf = os.path.join("data", "raw", "metodo_rb_treinamento_integrado_manual.pdf")
    caminho_saida = os.path.join("src", "generation", "metodologia.txt")

    if not os.path.exists(caminho_pdf):
        print(f"ERRO: PDF não encontrado em '{caminho_pdf}'")
        sys.exit(1)

    loader = PyPDFLoader(caminho_pdf)
    paginas = loader.load()

    texto = "\n\n".join(pagina.page_content for pagina in paginas)

    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    with open(caminho_saida, "w", encoding="utf-8") as f:
        f.write(texto)

    print(f"Metodologia extraída: {len(paginas)} páginas → '{caminho_saida}'")


if __name__ == "__main__":
    main()
