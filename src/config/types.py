"""
Tipos de dados compartilhados entre os módulos do sistema Jarvis.

Define as estruturas principais usadas no pipeline de RAG:
ingestão, recuperação e geração de respostas.
"""

from dataclasses import dataclass


@dataclass
class Chunk:
    """Representa um trecho extraído de um documento PDF após o processo de chunking."""

    conteudo: str
    fonte: str      # nome do arquivo PDF de origem
    pagina: int
    chunk_id: str   # hash SHA-256 do conteúdo


@dataclass
class ResultadoBusca:
    """Representa um resultado retornado pela busca semântica no Qdrant."""

    chunk: Chunk
    score: float    # pontuação de similaridade entre 0 e 1


@dataclass
class RespostaRAG:
    """Representa a resposta final gerada pelo pipeline RAG."""

    texto: str
    fontes: list[str]   # RN-001: citação obrigatória das fontes utilizadas
