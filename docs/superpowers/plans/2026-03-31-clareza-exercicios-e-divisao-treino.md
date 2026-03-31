# Clareza na Contagem de Exercícios e Labels de Divisão — Plano de Implementação

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Goal:** Corrigir dois problemas identificados em testes: (1) o LLM conta liberação/mobilidade/ativação como exercícios para atingir o mínimo de 12 — a regra correta é que esse mínimo se aplica só à seção Fortalecimento; (2) os labels "corpo todo" das divisões de treino serão atualizados para descrever explicitamente as cadeias musculares de cada sessão.

**Architecture:** Task 1 aplica o fix diretamente no código existente (`metodologia.txt` e `prompt.py`) com testes novos. Task 2 atualiza os documentos de spec e plano de 2026-03-30 para que, quando aquele plano for executado, já use os novos labels e o conteúdo correto de `_DIVISAO_TREINO_RB`. Os testes de `test_interface.py` existentes (`Fullbody`, etc.) permanecem válidos porque as opções atuais do formulário ainda não foram trocadas — isso ocorrerá na execução do plano 2026-03-30.

**Tech Stack:** Python 3.11+, pytest

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/generation/metodologia.txt` | Modificar | Clarificar seção 4: preparação ≠ fortalecimento |
| `src/generation/prompt.py` | Modificar | Atualizar `_INSTRUCAO_BASE` e bloco do catálogo em `montar_prompt()` |
| `tests/test_prompt.py` | Criar | Testes para a nova regra de contagem |
| `docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md` | Modificar | Atualizar labels "corpo todo" e conteúdo de `_DIVISAO_TREINO_RB` |
| `docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md` | Modificar | Atualizar labels e código da constante `_DIVISAO_TREINO_RB` |

---

## Task 1: Corrigir regra do mínimo de 12 no código

**Files:**
- Modify: `src/generation/metodologia.txt`
- Modify: `src/generation/prompt.py`
- Create: `tests/test_prompt.py`

### Passo 1.1 — Criar `tests/test_prompt.py` com os testes que falham

```python
"""Testes das constantes e da função montar_prompt."""
from src.config.types import ResultadoBusca, ChunkDocumento


def _resultado(conteudo: str = "referência de teste") -> ResultadoBusca:
    """Cria um ResultadoBusca mínimo para uso nos testes."""
    chunk = ChunkDocumento(
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
```

- [ ] **Passo 1.2 — Rodar os testes para confirmar falha**

```bash
python3 -m pytest tests/test_prompt.py -v
```

Saída esperada: 3 falhas — `AssertionError` porque `_INSTRUCAO_BASE` ainda não contém "NÃO contam".

- [ ] **Passo 1.3 — Atualizar `_INSTRUCAO_BASE` em `src/generation/prompt.py`**

Localizar as 4 linhas (aproximadamente linha 27–30):

```python
    "Quantidade mínima de exercícios de FORTALECIMENTO por grupo muscular em cada sessão: "
    "músculos pequenos (bíceps, tríceps, ombros, panturrilha) → mínimo 3 exercícios; "
    "músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
    "→ mínimo 4 exercícios.\n"
```

Substituir por:

```python
    "Quantidade mínima de exercícios na seção FORTALECIMENTO: 12 por sessão (ideal: 12–15). "
    "Liberação miofascial, mobilidade e ativação são fases de PREPARAÇÃO — "
    "NÃO contam para esse mínimo. "
    "Dentro do Fortalecimento: músculos pequenos (bíceps, tríceps, ombros, panturrilha) "
    "→ mínimo 3 exercícios cada; "
    "músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
    "→ mínimo 4 exercícios cada.\n"
```

- [ ] **Passo 1.4 — Atualizar bloco do catálogo em `montar_prompt()` em `src/generation/prompt.py`**

Localizar as 4 linhas (aproximadamente linha 190–193):

```python
            "- Cada sessão deve ter 12 a 15 exercícios no total: 2-3 liberações (se necessário) + "
            "3-4 mobilidades (se necessário) + 3-4 ativações + 5-8 fortalecimento "
            "(respeitando o mínimo por grupo muscular definido acima). "
            "Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
```

Substituir por:

```python
            "- Seção Fortalecimento: mínimo 12 exercícios por sessão (ideal: 12–15). "
            "Liberação, mobilidade e ativação são PREPARAÇÃO e NÃO contam para esse mínimo. "
            "Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
```

- [ ] **Passo 1.5 — Rodar os testes e confirmar aprovação**

```bash
python3 -m pytest tests/test_prompt.py -v
```

Saída esperada: `3 passed`.

- [ ] **Passo 1.6 — Atualizar seção 4 em `src/generation/metodologia.txt`**

Localizar o bloco (linhas 58–62):

```
12 a 15 exercícios por sessão:
- 2–3 liberações (se necessário)
- 3–4 mobilidades (se necessário)
- 3–4 ativações
- 5–7 fortalecimento
```

Substituir por:

```
Sessão completa: 12 a 20 exercícios no total (preparação + fortalecimento).
Preparação (não conta para o mínimo de fortalecimento):
- 2–3 liberações (se necessário)
- 3–4 mobilidades (se necessário)
- 3–4 ativações
Fortalecimento: mínimo obrigatório de 12 exercícios por sessão (ideal: 12–15).
Liberação, mobilidade e ativação são fases de preparação — NÃO contam para o mínimo de 12.
```

- [ ] **Passo 1.7 — Rodar suite completa**

```bash
python3 -m pytest tests/ -q
```

Saída esperada: todos os testes passando (número exato varia; 0 falhas).

- [ ] **Passo 1.8 — Commit**

```bash
git add src/generation/metodologia.txt src/generation/prompt.py tests/test_prompt.py
git commit -m "fix(prompt): esclarecer que mínimo de 12 exercícios se aplica só ao Fortalecimento"
```

---

## Task 2: Atualizar documentos de spec e plano de 2026-03-30

**Contexto:** O plano de 2026-03-30 ainda não foi executado e usa os labels antigos ("Superior Anterior / Inferior Anterior (Corpo todo)" e "Superior Posterior / Inferior Posterior (Corpo todo)") e o conteúdo original de `_DIVISAO_TREINO_RB`. Este task atualiza os docs para que, quando executados, já usem os novos labels e a regra correta do mínimo de 12.

**Files:**
- Modify: `docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md`
- Modify: `docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md`

### Passo 2.1 — Atualizar labels no spec de 2026-03-30

Em `docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md`, na seção "Mudança 1 — Opções de divisão no formulário", localizar as duas linhas:

```python
        "Superior Anterior / Inferior Anterior (Corpo todo)",
        "Superior Posterior / Inferior Posterior (Corpo todo)",
```

Substituir por:

```python
        "Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps",
        "Cadeia Posterior (Corpo todo) · Dorsal + Bíceps + Post. Coxa + Panturrilha",
```

Também atualizar a tabela de mapeamento no mesmo spec — localizar as linhas:

```
| Superior Anterior / Inferior Anterior (Corpo todo) | Anterior / Posterior (Full Body) |
| Superior Posterior / Inferior Posterior (Corpo todo) | Anterior / Posterior (Full Body) |
```

Substituir por:

```
| Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps | Anterior / Posterior (Full Body) |
| Cadeia Posterior (Corpo todo) · Dorsal + Bíceps + Post. Coxa + Panturrilha | Anterior / Posterior (Full Body) |
```

### Passo 2.2 — Atualizar `_DIVISAO_TREINO_RB` no spec de 2026-03-30

Na seção "Conteúdo da constante", localizar as duas linhas que descrevem as divisões de corpo todo:

```python
    "- Superior Anterior/Inferior Anterior ou Superior Posterior/Inferior Posterior (Corpo todo) → "
    "indicado para: intermediários e atletas. Respeita cadeias musculares e melhora equilíbrio.\n"
```

Substituir por:

```python
    "- Cadeia Anterior (Corpo todo): numa sessão, treinar a cadeia anterior completa — "
    "Superior Anterior (Peito, Tríceps, Ombros) + Inferior Anterior (Quadríceps). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
    "- Cadeia Posterior (Corpo todo): numa sessão, treinar a cadeia posterior completa — "
    "Superior Posterior (Dorsal, Bíceps) + Inferior Posterior (Post. Coxa, Panturrilha). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
```

Também atualizar a linha do mínimo de exercícios na constante, localizar:

```python
    "- Mínimo de 12 exercícios por sessão (ideal: 12–15; máximo: 18–20).\n"
```

Substituir por:

```python
    "- Mínimo de 12 exercícios na seção Fortalecimento por sessão (ideal: 12–15). "
    "Liberação, mobilidade e ativação são PREPARAÇÃO — NÃO contam para esse mínimo.\n"
```

### Passo 2.3 — Atualizar labels no plano de 2026-03-30

Em `docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md`, na seção "Task 2: Atualizar opções do multiselect em `app.py`", localizar o bloco "Substituir por":

```python
        divisao_treino = st.multiselect(
            "Divisão de treino",
            [
                "Deixar o agente decidir",
                "Full Body (Corpo todo)",
                "Superior",
                "Inferior",
                "Superior Anterior / Inferior Anterior (Corpo todo)",
                "Superior Posterior / Inferior Posterior (Corpo todo)",
                "Superior Anterior",
                "Superior Posterior",
                "Inferior Anterior",
                "Inferior Posterior",
            ],
            default=["Deixar o agente decidir"],
        )
```

Substituir as duas linhas dos labels "corpo todo":

```python
                "Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps",
                "Cadeia Posterior (Corpo todo) · Dorsal + Bíceps + Post. Coxa + Panturrilha",
```

### Passo 2.4 — Atualizar `_DIVISAO_TREINO_RB` no plano de 2026-03-30

Na seção "Passo 1.3 — Implementar em `prompt.py`", localizar o conteúdo da constante `_DIVISAO_TREINO_RB` e aplicar as mesmas substituições do Passo 2.2:

Localizar:
```python
    "- Superior Anterior/Inferior Anterior ou Superior Posterior/Inferior Posterior (Corpo todo) → "
    "indicado para: intermediários e atletas. Respeita cadeias musculares e melhora equilíbrio.\n"
```

Substituir por:
```python
    "- Cadeia Anterior (Corpo todo): numa sessão, treinar a cadeia anterior completa — "
    "Superior Anterior (Peito, Tríceps, Ombros) + Inferior Anterior (Quadríceps). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
    "- Cadeia Posterior (Corpo todo): numa sessão, treinar a cadeia posterior completa — "
    "Superior Posterior (Dorsal, Bíceps) + Inferior Posterior (Post. Coxa, Panturrilha). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
```

E a linha do mínimo de exercícios, localizar:
```python
    "- Mínimo de 12 exercícios por sessão (ideal: 12–15; máximo: 18–20).\n"
```

Substituir por:
```python
    "- Mínimo de 12 exercícios na seção Fortalecimento por sessão (ideal: 12–15). "
    "Liberação, mobilidade e ativação são PREPARAÇÃO — NÃO contam para esse mínimo.\n"
```

### Passo 2.5 — Atualizar testes referenciados no plano de 2026-03-30

No plano de 2026-03-30, a Task 3 atualiza `test_interface.py` e usa "Full Body (Corpo todo)" como label principal (os labels "corpo todo" compostos estão só em testes novos da Task 4). Localizar o teste `test_formatar_contexto_aluno_divisao_corpo_todo_anterior` na Task 4 do plano de 2026-03-30 e atualizar o valor do campo:

Localizar:
```python
        "Divisão de treino": ["Superior Anterior / Inferior Anterior (Corpo todo)"],
```

Substituir por:
```python
        "Divisão de treino": ["Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps"],
```

E o assert correspondente, localizar:
```python
    assert "Superior Anterior / Inferior Anterior (Corpo todo)" in contexto
```

Substituir por:
```python
    assert "Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps" in contexto
```

- [ ] **Passo 2.6 — Commit**

```bash
git add docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md \
        docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md
git commit -m "docs: atualizar labels de cadeia anterior/posterior e regra de 12 exercícios nos docs de 2026-03-30"
```

---

## Verificação Final

- [ ] `pytest tests/ -q` — 0 falhas
- [ ] `_INSTRUCAO_BASE` contém "NÃO contam" e "12"
- [ ] Bloco do catálogo em `montar_prompt()` contém "NÃO contam"
- [ ] `metodologia.txt` seção 4 descreve preparação separada de fortalecimento
- [ ] Plano 2026-03-30 usa "Cadeia Anterior" e "Cadeia Posterior" nos dois lugares
- [ ] Spec 2026-03-30 usa "Cadeia Anterior" e "Cadeia Posterior" na tabela e na constante
