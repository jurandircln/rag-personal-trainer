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
    """_INSTRUCAO_BASE deve associar o mínimo de 12 exercícios à seção Fortalecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Quantidade mínima de exercícios na seção FORTALECIMENTO: 12" in _INSTRUCAO_BASE


def test_instrucao_base_preparacao_nao_conta():
    """_INSTRUCAO_BASE deve informar que liberação, mobilidade e ativação NÃO contam."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "NÃO contam" in _INSTRUCAO_BASE


def test_catalogo_block_reforça_preparacao_nao_conta():
    """Bloco do catálogo em montar_prompt() deve reforçar que preparação não conta.

    Nota: test_llm.py também verifica esta propriedade via test_prompt_com_catalogo_contem_instrucao_volume.
    A cobertura dupla é intencional: este arquivo testa a unidade prompt.py isolada;
    test_llm.py testa o fluxo integrado.
    """
    from src.generation.prompt import montar_prompt

    prompt = montar_prompt(
        query="Gere treino",
        resultados=[_resultado()],
        catalogo_filtrado="| Exercício | Categoria |\n| Agachamento | Inferior |",
    )

    assert "NÃO contam" in prompt
    assert "Fortalecimento" in prompt


def test_template_contem_aviso_minimo_fortalecimento():
    """_TEMPLATE_SAIDA deve conter aviso de mínimo obrigatório em cada Fortalecimento."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert "MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção" in _TEMPLATE_SAIDA


def test_template_fortalecimento_tem_14_exercicios_por_secao():
    """Cada bloco ### Fortalecimento do template deve exibir ao menos 14 exercícios de exemplo."""
    import re
    from src.generation.prompt import _TEMPLATE_SAIDA

    # Divide o template nos blocos de Fortalecimento (pula o texto antes do primeiro)
    blocos = re.split(r"\n### Fortalecimento\n", _TEMPLATE_SAIDA)[1:]
    assert blocos, "Nenhum bloco ### Fortalecimento encontrado no template"

    for bloco in blocos:
        # Pega o conteúdo até o próximo header de nível ### (ex: ### Observações)
        conteudo = re.split(r"\n### ", bloco)[0]
        contagem = conteudo.count("* [nome do exercício]")
        assert contagem >= 14, (
            f"Bloco Fortalecimento tem {contagem} exercício(s) de exemplo — esperado >= 14"
        )
