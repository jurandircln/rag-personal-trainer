"""Testes das constantes e da função montar_prompt."""
from src.config.types import ResultadoBusca, Chunk


def _resultado(conteudo: str = "referência de teste") -> ResultadoBusca:
    """Cria um ResultadoBusca mínimo para uso nos testes."""
    chunk = Chunk(
        chunk_id="c1",
        conteudo=conteudo,
        fonte="fonte.pdf",
        pagina=1,
    )
    return ResultadoBusca(chunk=chunk, score=0.9)


def test_instrucao_base_minimo_fortalecimento_explicito():
    """_INSTRUCAO_BASE deve dizer que o mínimo de 12 é para a seção Fortalecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "FORTALECIMENTO" in _INSTRUCAO_BASE
    assert "12" in _INSTRUCAO_BASE


def test_instrucao_base_preparacao_nao_conta():
    """_INSTRUCAO_BASE deve informar que liberação, mobilidade e ativação NÃO contam."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "NÃO contam" in _INSTRUCAO_BASE


def test_catalogo_block_reforça_preparacao_nao_conta():
    """Bloco do catálogo em montar_prompt() deve reforçar que preparação não conta."""
    from src.generation.prompt import montar_prompt

    prompt = montar_prompt(
        query="Gere treino",
        resultados=[_resultado()],
        catalogo_filtrado="| Exercício | Categoria |\n| Agachamento | Inferior |",
    )

    assert "NÃO contam" in prompt
    assert "Fortalecimento" in prompt
