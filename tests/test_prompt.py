"""Testes da função montar_prompt e das constantes do módulo de prompt."""
import pytest

from src.config.types import ResultadoBusca, Chunk


def _chunk(conteudo: str = "texto de referência") -> ResultadoBusca:
    """Cria um ResultadoBusca mínimo para uso nos testes."""
    chunk = Chunk(
        chunk_id="c1",
        conteudo=conteudo,
        fonte="fonte.pdf",
        pagina=1,
    )
    return ResultadoBusca(chunk=chunk, score=0.9)


def test_divisao_treino_rb_presente_no_prompt():
    """_DIVISAO_TREINO_RB deve aparecer em todo prompt gerado por montar_prompt."""
    from src.generation.prompt import montar_prompt

    prompt = montar_prompt(
        query="Gere um treino",
        resultados=[_chunk()],
        contexto_aluno="Nome: Ana",
    )

    assert "[DIVISÃO DE TREINO — MÉTODO RB]" in prompt


def test_divisao_treino_rb_antes_da_metodologia():
    """Bloco de divisão deve aparecer antes do bloco de metodologia no prompt."""
    from src.generation.prompt import montar_prompt

    prompt = montar_prompt(
        query="Gere um treino",
        resultados=[_chunk()],
        metodologia="Metodologia RB completa",
        contexto_aluno="Nome: Ana",
    )

    pos_divisao = prompt.index("[DIVISÃO DE TREINO — MÉTODO RB]")
    pos_metodologia = prompt.index("[METODOLOGIA")

    assert pos_divisao < pos_metodologia


def test_instrucao_base_referencia_divisao():
    """_INSTRUCAO_BASE deve conter referência ao bloco de divisão de treino."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "DIVISÃO DE TREINO" in _INSTRUCAO_BASE


def test_divisao_treino_rb_contem_criterios_full_body():
    """_DIVISAO_TREINO_RB deve conter critérios para Full Body."""
    from src.generation.prompt import _DIVISAO_TREINO_RB

    assert "Full Body" in _DIVISAO_TREINO_RB
    assert "iniciantes" in _DIVISAO_TREINO_RB


def test_divisao_treino_rb_contem_regras_obrigatorias():
    """_DIVISAO_TREINO_RB deve conter as regras obrigatórias do método."""
    from src.generation.prompt import _DIVISAO_TREINO_RB

    assert "core" in _DIVISAO_TREINO_RB
    assert "12" in _DIVISAO_TREINO_RB
    assert "Metodologia do Treino" in _DIVISAO_TREINO_RB
