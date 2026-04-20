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
    """_INSTRUCAO_BASE deve associar o mínimo de 8 exercícios à seção Fortalecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Fortalecimento: mínimo 8 exercícios por sessão" in _INSTRUCAO_BASE


def test_instrucao_base_preparacao_nao_conta():
    """_INSTRUCAO_BASE deve informar que liberação miofascial NÃO conta para nenhum mínimo."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Liberação miofascial NÃO conta" in _INSTRUCAO_BASE


def test_catalogo_block_reforça_preparacao_nao_conta():
    """Bloco do catálogo em montar_prompt() deve reforçar que liberação não conta.

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

    assert "Liberação NÃO conta" in prompt
    assert "Fortalecimento" in prompt
    assert "Mobilidade + Ativação + Fortalecimento ≥ 12" in prompt


def test_template_contem_aviso_minimo_fortalecimento():
    """_TEMPLATE_SAIDA deve conter aviso de mínimo de fortalecimento em cada bloco."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("Fortalecimento: mínimo 8 exercícios nesta seção") == 2


def test_instrucao_base_total_minimo_12():
    """_INSTRUCAO_BASE deve exigir Mobilidade + Ativação + Fortalecimento >= 12."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Mobilidade + Ativação + Fortalecimento ≥ 12" in _INSTRUCAO_BASE


def test_template_contem_nota_total_minimo_12():
    """_TEMPLATE_SAIDA deve conter nota de total mínimo 12 em cada bloco Fortalecimento."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("Total (Mobilidade + Ativação + Fortalecimento): mínimo 12") == 2


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


def test_instrucao_base_contem_regra_conjugado():
    """_INSTRUCAO_BASE deve conter a instrução de notação [CONJUGADO X1] / [CONJUGADO X2] e a regra de aplicação exclusiva."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "[CONJUGADO X1] / [CONJUGADO X2]" in _INSTRUCAO_BASE
    assert "Aplique conjugado SOMENTE quando o personal solicitar explicitamente" in _INSTRUCAO_BASE


def test_template_saida_contem_exemplo_conjugado():
    """_TEMPLATE_SAIDA deve conter exemplo de bloco [CONJUGADO A1] / [CONJUGADO A2]."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert "[CONJUGADO A1]" in _TEMPLATE_SAIDA
    assert "[CONJUGADO A2]" in _TEMPLATE_SAIDA


def test_instrucao_base_contem_regra_aquecimento():
    """_INSTRUCAO_BASE deve conter a instrução condicional de aquecimento com condição dupla."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Se o personal solicitar aquecimento e o contexto do aluno listar equipamentos" in _INSTRUCAO_BASE
    assert "omita completamente a seção" in _INSTRUCAO_BASE


def test_template_saida_contem_secao_aquecimento():
    """_TEMPLATE_SAIDA deve conter ### Aquecimento antes de ### Liberação Miofascial nos dois dias."""
    import re
    from src.generation.prompt import _TEMPLATE_SAIDA

    pares = list(zip(
        [m.start() for m in re.finditer(r"### Aquecimento", _TEMPLATE_SAIDA)],
        [m.start() for m in re.finditer(r"### Liberação Miofascial", _TEMPLATE_SAIDA)],
    ))
    assert len(pares) == 2, f"Esperado 2 pares (Dia 1 e Dia 2), encontrado {len(pares)}"
    for i, (pos_aq, pos_lib) in enumerate(pares, start=1):
        assert pos_aq < pos_lib, f"### Aquecimento deve preceder ### Liberação Miofascial no Dia {i}"
