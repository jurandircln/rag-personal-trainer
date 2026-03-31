# Template Fortalecimento — Ancoragem do Mínimo de 12 Exercícios

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Goal:** Corrigir o comportamento do LLM que retorna entre 6 e 8 exercícios na seção Fortalecimento, ancorando o template para exibir 14 exercícios de exemplo e adicionando uma nota de mínimo obrigatório inline.

**Architecture:** Duas alterações cirúrgicas na constante `_TEMPLATE_SAIDA` em `src/generation/prompt.py`: (1) adicionar um aviso `[MÍNIMO OBRIGATÓRIO: 12 exercícios...]` imediatamente abaixo de cada `### Fortalecimento`; (2) expandir o exemplo de 2 grupos musculares (1 exercício cada) para 4 grupos musculares com seus mínimos reais (14 exercícios totais). As mudanças são feitas via TDD: escrever testes que falham, implementar, confirmar que passam.

**Tech Stack:** Python 3.11+, pytest

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `tests/test_prompt.py` | Modificar | Adicionar 2 novos testes para a nota inline e contagem de exercícios no template |
| `src/generation/prompt.py` | Modificar | Expandir `_TEMPLATE_SAIDA`: nota inline + blocos de Fortalecimento com 14 exercícios de exemplo |

---

## Task 1: Adicionar nota inline e expandir template de Fortalecimento

**Files:**
- Modify: `tests/test_prompt.py`
- Modify: `src/generation/prompt.py`

---

### Passo 1.1 — Escrever os testes que devem falhar

Abrir `tests/test_prompt.py` e acrescentar as duas funções abaixo ao final do arquivo:

```python
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
```

---

### Passo 1.2 — Confirmar que os testes falham

```bash
python3 -m pytest tests/test_prompt.py::test_template_contem_aviso_minimo_fortalecimento tests/test_prompt.py::test_template_fortalecimento_tem_14_exercicios_por_secao -v
```

Saída esperada: **2 FAILED** — `AssertionError` porque o template atual não tem o aviso nem os 14 exercícios.

---

### Passo 1.3 — Atualizar `_TEMPLATE_SAIDA` em `src/generation/prompt.py`

#### Substituição 1 — Bloco Fortalecimento do Dia 1

Localizar exatamente este trecho (dentro da string `_TEMPLATE_SAIDA`):

```
### Fortalecimento

#### [Músculo Grande, ex: Peitoral]

* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Tríceps]

* [nome do exercício]
  [N séries × N–N reps (método)]
```

Substituir por:

```
### Fortalecimento
[MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção — Liberação, Mobilidade e Ativação NÃO contam. Adicione mais grupos musculares se necessário antes de fechar este dia.]

#### [Músculo Grande, ex: Peitoral]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Grande, ex: Dorsal]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Tríceps]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Bíceps]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
```

#### Substituição 2 — Bloco Fortalecimento do Dia 2

Localizar exatamente este trecho:

```
### Fortalecimento

#### [Músculo Grande]

* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno]

* [nome do exercício]
  [N séries × N–N reps (método)]
```

Substituir por:

```
### Fortalecimento
[MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção — Liberação, Mobilidade e Ativação NÃO contam. Adicione mais grupos musculares se necessário antes de fechar este dia.]

#### [Músculo Grande]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Grande]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
```

---

### Passo 1.4 — Confirmar que os novos testes passam

```bash
python3 -m pytest tests/test_prompt.py::test_template_contem_aviso_minimo_fortalecimento tests/test_prompt.py::test_template_fortalecimento_tem_14_exercicios_por_secao -v
```

Saída esperada: **2 PASSED**

---

### Passo 1.5 — Rodar a suite completa

```bash
python3 -m pytest tests/ -q
```

Saída esperada: todos os testes passando, 0 falhas.

---

### Passo 1.6 — Commit

```bash
git add tests/test_prompt.py src/generation/prompt.py
git commit -m "feat(prompt): ancorar mínimo de 12 exercícios no template de fortalecimento"
```

---

## Verificação Final

- [ ] `_TEMPLATE_SAIDA` contém `"MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção"` em ambos os dias
- [ ] Cada bloco `### Fortalecimento` do template exibe 14 exercícios de exemplo (`* [nome do exercício]`)
- [ ] `python3 -m pytest tests/ -q` → 0 falhas
