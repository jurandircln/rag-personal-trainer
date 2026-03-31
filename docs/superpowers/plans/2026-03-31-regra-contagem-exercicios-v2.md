# Regra de Contagem de Exercícios v2 — Fortalecimento ≥ 8 + Total ≥ 12

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Goal:** Substituir a regra antiga (Fortalecimento ≥ 12, mobilidade/ativação não contam) pela nova regra dupla: Fortalecimento ≥ 8 por sessão E Mobilidade + Ativação + Fortalecimento ≥ 12 no total; Liberação continua fora da contagem.

**Architecture:** Duas tarefas independentes. Task 1 aplica a regra nos três pontos do prompt (`_INSTRUCAO_BASE`, bloco do catálogo e `_TEMPLATE_SAIDA`) via TDD, atualizando também os testes em `test_prompt.py` e `test_llm.py`. Task 2 atualiza `metodologia.txt` (sem testes automatizados) e fecha com commit.

**Tech Stack:** Python 3.11+, pytest

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `tests/test_prompt.py` | Modificar | Atualizar 4 testes existentes + adicionar 2 novos |
| `tests/test_llm.py` | Modificar | Atualizar 1 teste existente |
| `src/generation/prompt.py` | Modificar | Atualizar `_INSTRUCAO_BASE`, bloco do catálogo e notas do `_TEMPLATE_SAIDA` |
| `src/generation/metodologia.txt` | Modificar | Atualizar seção 4 com nova regra dupla |

---

## Task 1: Atualizar `prompt.py`, `test_prompt.py` e `test_llm.py`

**Files:**
- Modify: `tests/test_prompt.py`
- Modify: `tests/test_llm.py`
- Modify: `src/generation/prompt.py`

---

### Passo 1.1 — Atualizar os 4 testes existentes em `tests/test_prompt.py`

Substituir o conteúdo completo das 4 funções abaixo (manter o helper `_resultado` e os imports intactos):

**Função 1** — localizar:
```python
def test_instrucao_base_minimo_fortalecimento_explicito():
    """_INSTRUCAO_BASE deve associar o mínimo de 12 exercícios à seção Fortalecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Quantidade mínima de exercícios na seção FORTALECIMENTO: 12" in _INSTRUCAO_BASE
```
Substituir por:
```python
def test_instrucao_base_minimo_fortalecimento_explicito():
    """_INSTRUCAO_BASE deve associar o mínimo de 8 exercícios à seção Fortalecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Fortalecimento: mínimo 8 exercícios por sessão" in _INSTRUCAO_BASE
```

**Função 2** — localizar:
```python
def test_instrucao_base_preparacao_nao_conta():
    """_INSTRUCAO_BASE deve informar que liberação, mobilidade e ativação NÃO contam."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "NÃO contam" in _INSTRUCAO_BASE
```
Substituir por:
```python
def test_instrucao_base_preparacao_nao_conta():
    """_INSTRUCAO_BASE deve informar que liberação miofascial NÃO conta para nenhum mínimo."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Liberação miofascial NÃO conta" in _INSTRUCAO_BASE
```

**Função 3** — localizar:
```python
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
```
Substituir por:
```python
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
```

**Função 4** — localizar:
```python
def test_template_contem_aviso_minimo_fortalecimento():
    """_TEMPLATE_SAIDA deve conter aviso de mínimo obrigatório em cada Fortalecimento."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção") == 2
```
Substituir por:
```python
def test_template_contem_aviso_minimo_fortalecimento():
    """_TEMPLATE_SAIDA deve conter aviso de mínimo de fortalecimento em cada bloco."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("Fortalecimento: mínimo 8 exercícios nesta seção") == 2
```

---

### Passo 1.2 — Adicionar 2 novos testes ao final de `tests/test_prompt.py`

```python
def test_instrucao_base_total_minimo_12():
    """_INSTRUCAO_BASE deve exigir Mobilidade + Ativação + Fortalecimento >= 12."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "Mobilidade + Ativação + Fortalecimento ≥ 12" in _INSTRUCAO_BASE


def test_template_contem_nota_total_minimo_12():
    """_TEMPLATE_SAIDA deve conter nota de total mínimo 12 em cada bloco Fortalecimento."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert _TEMPLATE_SAIDA.count("Total (Mobilidade + Ativação + Fortalecimento): mínimo 12") == 2
```

---

### Passo 1.3 — Atualizar o teste em `tests/test_llm.py`

Localizar o método (aproximadamente linha 380):
```python
    def test_prompt_com_catalogo_contem_instrucao_volume(self, resultados_exemplo) -> None:
        """Template com catálogo contém instrução de mínimo 12 exercícios de Fortalecimento."""
        catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado=catalogo_md,
        )
        assert "12" in prompt
        assert "NÃO contam" in prompt
```
Substituir por:
```python
    def test_prompt_com_catalogo_contem_instrucao_volume(self, resultados_exemplo) -> None:
        """Template com catálogo contém instrução de mínimo 8 fortalecimento e total >= 12."""
        catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado=catalogo_md,
        )
        assert "Fortalecimento: mínimo 8" in prompt
        assert "Mobilidade + Ativação + Fortalecimento ≥ 12" in prompt
```

---

### Passo 1.4 — Confirmar que os 7 testes falham

```bash
python3 -m pytest tests/test_prompt.py tests/test_llm.py::TestMontarPromptComCatalogo::test_prompt_com_catalogo_contem_instrucao_volume -v
```

Saída esperada: **7 FAILED** (4 atualizados + 2 novos + 1 de test_llm).

---

### Passo 1.5 — Atualizar `_INSTRUCAO_BASE` em `src/generation/prompt.py`

Localizar o trecho (aproximadamente linhas 26–32):
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

### Passo 1.6 — Atualizar bloco do catálogo em `montar_prompt()` em `src/generation/prompt.py`

Localizar o trecho (aproximadamente linhas 193–196):
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

### Passo 1.7 — Atualizar notas inline do `_TEMPLATE_SAIDA` em `src/generation/prompt.py`

**Nota do Dia 1** — localizar:
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

**Nota do Dia 2** — localizar a mesma string antiga no segundo bloco Fortalecimento e aplicar a mesma substituição.

---

### Passo 1.8 — Confirmar que todos os 7 testes passam

```bash
python3 -m pytest tests/test_prompt.py tests/test_llm.py::TestMontarPromptComCatalogo::test_prompt_com_catalogo_contem_instrucao_volume -v
```

Saída esperada: **7 PASSED**

---

### Passo 1.9 — Rodar a suite completa

```bash
python3 -m pytest tests/ -q
```

Saída esperada: todos os testes passando, 0 falhas.

---

### Passo 1.10 — Commit

```bash
git add tests/test_prompt.py tests/test_llm.py src/generation/prompt.py
git commit -m "feat(prompt): regra de contagem v2 — fortalecimento >= 8 e total >= 12"
```

---

## Task 2: Atualizar `src/generation/metodologia.txt`

**Files:**
- Modify: `src/generation/metodologia.txt`

---

### Passo 2.1 — Atualizar seção 4 em `src/generation/metodologia.txt`

Localizar o bloco (aproximadamente linhas 57–64):
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

### Passo 2.2 — Rodar a suite completa

```bash
python3 -m pytest tests/ -q
```

Saída esperada: todos os testes passando, 0 falhas.

---

### Passo 2.3 — Commit

```bash
git add src/generation/metodologia.txt
git commit -m "docs(metodologia): atualizar seção 4 com regra de contagem v2"
```

---

## Verificação Final

- [ ] `_INSTRUCAO_BASE` contém `"Fortalecimento: mínimo 8 exercícios por sessão"`
- [ ] `_INSTRUCAO_BASE` contém `"Mobilidade + Ativação + Fortalecimento ≥ 12"`
- [ ] `_INSTRUCAO_BASE` contém `"Liberação miofascial NÃO conta"`
- [ ] Bloco do catálogo alinhado com as mesmas regras
- [ ] `_TEMPLATE_SAIDA` contém `"Fortalecimento: mínimo 8 exercícios nesta seção"` exatamente 2 vezes
- [ ] `_TEMPLATE_SAIDA` contém `"Total (Mobilidade + Ativação + Fortalecimento): mínimo 12"` exatamente 2 vezes
- [ ] `metodologia.txt` seção 4 reflete a regra dupla
- [ ] `python3 -m pytest tests/ -q` → 0 falhas
