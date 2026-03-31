# Design: Regra de Contagem de Exercícios v2 — Fortalecimento ≥ 8 + Total ≥ 12

**Data:** 2026-03-31
**Branch:** feat/melhorias-formulario-anamnese

---

## Contexto

A regra anterior exigia mínimo de 12 exercícios exclusivamente na seção Fortalecimento, excluindo mobilidade e ativação da contagem. A nova regra é uma dupla restrição:

1. **Fortalecimento:** mínimo 8 exercícios por sessão (mínimo isolado)
2. **Total (Mobilidade + Ativação + Fortalecimento):** mínimo 12 por sessão
3. **Liberação miofascial:** obrigatória, mas NÃO conta para nenhum mínimo

Todos os pilares da sessão são obrigatórios (nada é opcional).

---

## Mudança 1 — `_INSTRUCAO_BASE` em `src/generation/prompt.py`

Localizar o trecho:

```python
"Quantidade mínima de exercícios na seção FORTALECIMENTO: 12 por sessão (ideal: 12–15). "
"Liberação miofascial, mobilidade e ativação são fases de PREPARAÇÃO — "
"NÃO contam para esse mínimo. "
"Dentro do Fortalecimento: músculos pequenos (bíceps, tríceps, ombros, panturrilha) "
"→ mínimo 3 exercícios cada; "
"músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
"→ mínimo 4 exercícios cada.\n"
```

Substituir por:

```python
"Seção Fortalecimento: mínimo 8 exercícios por sessão. "
"Mobilidade e ativação CONTAM para o total mínimo da sessão: "
"Mobilidade + Ativação + Fortalecimento ≥ 12 por sessão. "
"Liberação miofascial NÃO conta para nenhum mínimo. "
"Dentro do Fortalecimento: músculos pequenos (bíceps, tríceps, ombros, panturrilha) "
"→ mínimo 3 exercícios cada; "
"músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
"→ mínimo 4 exercícios cada.\n"
```

---

## Mudança 2 — Bloco do catálogo em `montar_prompt()` em `src/generation/prompt.py`

Localizar o trecho (dentro de `instrucoes_catalogo`):

```python
"- Seção Fortalecimento: mínimo 12 exercícios por sessão (ideal: 12–15). "
"Liberação, mobilidade e ativação são PREPARAÇÃO e NÃO contam para esse mínimo. "
"Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
```

Substituir por:

```python
"- Fortalecimento: mínimo 8 exercícios por sessão. "
"Mobilidade e ativação contam para o total mínimo: Mobilidade + Ativação + Fortalecimento ≥ 12. "
"Liberação NÃO conta para nenhum mínimo. "
"Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
```

---

## Mudança 3 — `_TEMPLATE_SAIDA` em `src/generation/prompt.py`

### 3a. Nota inline do Dia 1

Localizar a nota atual abaixo de `### Fortalecimento` no Dia 1:

```
### Fortalecimento
[MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção — Liberação, Mobilidade e Ativação NÃO contam. Adicione mais grupos musculares se necessário antes de fechar este dia.]
```

Substituir por:

```
### Fortalecimento
[Fortalecimento: mínimo 8 exercícios nesta seção]
[Total (Mobilidade + Ativação + Fortalecimento): mínimo 12 — Liberação NÃO conta]
```

### 3b. Nota inline do Dia 2

Mesma substituição no bloco `### Fortalecimento` do Dia 2.

O restante do template (14 exercícios de exemplo por bloco) permanece inalterado.

---

## Mudança 4 — `src/generation/metodologia.txt` — Seção 4

Localizar o bloco atual da seção 4:

```
Sessão completa: 12 a 20 exercícios no total (preparação + fortalecimento).
Preparação (não conta para o mínimo de fortalecimento):
- 2–3 liberações (se necessário)
- 3–4 mobilidades (se necessário)
- 3–4 ativações
Fortalecimento: mínimo obrigatório de 12 exercícios por sessão (ideal: 12–15).
Liberação, mobilidade e ativação são fases de preparação — NÃO contam para o mínimo de 12.
```

Substituir por:

```
Sessão completa — mínimos obrigatórios:
- Fortalecimento: mínimo 8 exercícios por sessão
- Total (Mobilidade + Ativação + Fortalecimento): mínimo 12 por sessão
- Liberação miofascial: obrigatória, mas NÃO conta para nenhum mínimo

Volume típico por pilar:
- 2–3 liberações
- 3–4 mobilidades
- 3–4 ativações
- 8–12 fortalecimento
```

---

## Mudança 5 — Testes em `tests/test_prompt.py`

### Testes a atualizar

| Teste atual | O que muda |
|---|---|
| `test_instrucao_base_minimo_fortalecimento_explicito` | Assertar `"Fortalecimento: mínimo 8"` em vez de `"FORTALECIMENTO: 12"` |
| `test_instrucao_base_preparacao_nao_conta` | Assertar que liberação NÃO conta (`"Liberação miofascial NÃO conta"`) |
| `test_catalogo_block_reforça_preparacao_nao_conta` | Assertar nova string do bloco do catálogo |
| `test_template_contem_aviso_minimo_fortalecimento` | Assertar nova string `"Fortalecimento: mínimo 8 exercícios nesta seção"` (count == 2) |

### Testes novos a adicionar

```python
def test_instrucao_base_total_minimo_12():
    """_INSTRUCAO_BASE deve exigir Mobilidade + Ativação + Fortalecimento >= 12."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Mobilidade + Ativação + Fortalecimento ≥ 12" in _INSTRUCAO_BASE


def test_template_contem_nota_total_minimo_12():
    """_TEMPLATE_SAIDA deve conter nota de total mínimo de 12 em cada bloco Fortalecimento."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("Total (Mobilidade + Ativação + Fortalecimento): mínimo 12") == 2
```

---

## Arquivos modificados

| Arquivo | Tipo de mudança |
|---|---|
| `src/generation/prompt.py` | Atualizar `_INSTRUCAO_BASE`, bloco do catálogo e `_TEMPLATE_SAIDA` |
| `src/generation/metodologia.txt` | Atualizar seção 4 com nova regra dupla |
| `tests/test_prompt.py` | Atualizar 4 testes existentes + adicionar 2 novos |

---

## Critérios de aceite

- [ ] `_INSTRUCAO_BASE` contém `"Fortalecimento: mínimo 8"` e `"Mobilidade + Ativação + Fortalecimento ≥ 12"`
- [ ] `_INSTRUCAO_BASE` contém `"Liberação miofascial NÃO conta"`
- [ ] Bloco do catálogo alinhado com a mesma regra dupla
- [ ] `_TEMPLATE_SAIDA` contém a nota `"Fortalecimento: mínimo 8 exercícios nesta seção"` exatamente 2 vezes
- [ ] `_TEMPLATE_SAIDA` contém a nota `"Total (Mobilidade + Ativação + Fortalecimento): mínimo 12"` exatamente 2 vezes
- [ ] `metodologia.txt` seção 4 reflete a regra dupla
- [ ] Todos os testes passando
