# Divisão de Treino — Método RB no System Prompt — Plano de Implementação

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: Use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa por tarefa. Os passos usam sintaxe de checkbox (`- [ ]`) para rastreamento.

**Goal:** Adicionar a lógica de divisão de treino do Método RB ao system prompt e expandir as opções do formulário de anamnese de 4 para 10 opções granulares.

**Architecture:** Nova constante `_DIVISAO_TREINO_RB` em `prompt.py` é injetada como segunda seção em todo prompt gerado. O formulário substitui as opções atuais pelas 9 divisões do Método RB mais "Deixar o agente decidir". A lógica de filtragem em `formatar_contexto_aluno()` permanece inalterada.

**Tech Stack:** Python 3.11+, Streamlit, pytest

**Worktree:** `.worktrees/feat/divisao-treino-metodo-rb`

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/generation/prompt.py` | Modificar | Nova constante + injeção em `montar_prompt()` + linha em `_INSTRUCAO_BASE` |
| `src/interface/app.py` | Modificar | Substituir opções do `st.multiselect` |
| `tests/test_interface.py` | Modificar | Atualizar testes existentes com novas opções |
| `tests/test_prompt.py` | Criar | Novos testes para `_DIVISAO_TREINO_RB` |

---

## Task 1: Adicionar `_DIVISAO_TREINO_RB` e injetar em `montar_prompt()`

**Files:**
- Modify: `src/generation/prompt.py`
- Create: `tests/test_prompt.py`

### Passo 1.1 — Escrever o teste que falha

Criar `tests/test_prompt.py` com o conteúdo abaixo:

```python
"""Testes da função montar_prompt e das constantes do módulo de prompt."""
import pytest

from src.config.types import ResultadoBusca, ChunkDocumento


def _chunk(conteudo: str = "texto de referência") -> ResultadoBusca:
    """Cria um ResultadoBusca mínimo para uso nos testes."""
    chunk = ChunkDocumento(
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
```

- [ ] **Passo 1.2 — Rodar o teste para confirmar falha**

```bash
cd .worktrees/feat/divisao-treino-metodo-rb
python3 -m pytest tests/test_prompt.py -v
```

Saída esperada: 5 erros `ImportError` ou `AttributeError` — `_DIVISAO_TREINO_RB` ainda não existe.

- [ ] **Passo 1.3 — Implementar em `prompt.py`**

Em `src/generation/prompt.py`, fazer três alterações:

**a) Adicionar linha ao final de `_INSTRUCAO_BASE`** (logo antes do fechamento do parêntese):

```python
_INSTRUCAO_BASE = (
    # ... linhas existentes mantidas integralmente ...
    "A escolha e justificativa da divisão muscular seguem obrigatoriamente os critérios "
    "do bloco [DIVISÃO DE TREINO — MÉTODO RB] presente neste prompt.\n"
)
```

**b) Adicionar nova constante `_DIVISAO_TREINO_RB` após `_INSTRUCAO_BASE`:**

```python
# Critérios do Método RB para divisão de treino — injetado em todo prompt
_DIVISAO_TREINO_RB = (
    "[DIVISÃO DE TREINO — MÉTODO RB]\n"
    "Quando o aluno selecionar 'Deixar o agente decidir', aplique os critérios abaixo "
    "para escolher a divisão mais adequada ao perfil do aluno:\n\n"
    "- Full Body (Corpo todo) → indicado para: iniciantes, 2–3x/semana, reabilitação, "
    "alunos com pouco tempo disponível.\n"
    "- Superior + Inferior → indicado para: intermediários, 3–4x/semana. "
    "Vantagem: melhor controle de volume e maior recuperação por grupamento.\n"
    "- Superior Anterior/Inferior Anterior ou Superior Posterior/Inferior Posterior (Corpo todo) → "
    "indicado para: intermediários e atletas. Respeita cadeias musculares e melhora equilíbrio.\n"
    "- Divisão completa em 4 partes (Superior Anterior, Superior Posterior, Inferior Anterior, "
    "Inferior Posterior) → indicado para: avançados, foco em hipertrofia, ≥4x/semana. "
    "Maior especificidade e volume por grupamento.\n\n"
    "REGRAS OBRIGATÓRIAS — aplicam-se a qualquer divisão:\n"
    "- Todo treino deve conter exercícios de core: anti-extensão, anti-rotação, "
    "anti-flexão lateral e estabilidade dinâmica.\n"
    "- Mínimo de 12 exercícios por sessão (ideal: 12–15; máximo: 18–20).\n"
    "- Estrutura obrigatória da sessão: Liberação Miofascial → Mobilidade → Ativação → Fortalecimento.\n"
    "- Em treinos de membros inferiores: incluir core. "
    "Em treinos de membros superiores: incluir estabilidade escapular.\n\n"
    "JUSTIFICATIVA OBRIGATÓRIA: na seção '## Metodologia do Treino', explique sempre "
    "qual divisão foi escolhida ou seguida e por quê, com base nos dados do aluno "
    "(frequência semanal, nível de condicionamento e objetivo principal).\n"
)
```

**c) Em `montar_prompt()`, injetar `_DIVISAO_TREINO_RB` como segunda seção:**

```python
    # Instrução base do sistema
    secoes.append(_INSTRUCAO_BASE)

    # Critérios de divisão de treino do Método RB
    secoes.append(_DIVISAO_TREINO_RB)

    # Metodologia RB (quando disponível)
    if metodologia.strip():
```

- [ ] **Passo 1.4 — Rodar os testes e confirmar aprovação**

```bash
python3 -m pytest tests/test_prompt.py -v
```

Saída esperada: `5 passed`.

- [ ] **Passo 1.5 — Rodar toda a suite para confirmar que nada quebrou**

```bash
python3 -m pytest tests/ -q
```

Saída esperada: `106+ passed, 0 failed`.

- [ ] **Passo 1.6 — Commit**

```bash
git add src/generation/prompt.py tests/test_prompt.py
git commit -m "feat(prompt): adicionar critérios de divisão de treino do Método RB"
```

---

## Task 2: Atualizar opções do multiselect em `app.py`

**Files:**
- Modify: `src/interface/app.py`

- [ ] **Passo 2.1 — Localizar e substituir o multiselect**

Em `src/interface/app.py`, localizar o trecho atual (linha ~176):

```python
        divisao_treino = st.multiselect(
            "Divisão de treino",
            ["Deixar o agente decidir", "Fullbody", "Superior / Inferior", "Anterior / Posterior"],
            default=["Deixar o agente decidir"],
        )
```

Substituir por:

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

- [ ] **Passo 2.2 — Rodar os testes não relacionados a divisão para confirmar que nada quebrou**

```bash
python3 -m pytest tests/test_interface.py -v -k "not divisao"
```

Saída esperada: todos os testes sem "divisao" no nome passam.

- [ ] **Passo 2.3 — Commit parcial**

```bash
git add src/interface/app.py
git commit -m "feat(interface): expandir opções de divisão de treino para 10 opções do Método RB"
```

---

## Task 3: Atualizar testes existentes de divisão em `test_interface.py`

**Files:**
- Modify: `tests/test_interface.py`

Os testes abaixo referenciam opções antigas que foram renomeadas ou removidas. Cada passo atualiza um teste por vez.

- [ ] **Passo 3.1 — Atualizar `test_formatar_contexto_aluno_com_divisao_treino`**

Localizar (linha ~305):

```python
        "Divisão de treino": ["Fullbody"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Fullbody" in contexto
```

Substituir por:

```python
        "Divisão de treino": ["Full Body (Corpo todo)"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Full Body (Corpo todo)" in contexto
```

- [ ] **Passo 3.2 — Atualizar `test_formatar_contexto_aluno_divisao_multipla`**

Localizar (linha ~349):

```python
        "Divisão de treino": ["Superior / Inferior", "Anterior / Posterior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior / Inferior" in contexto
    assert "Anterior / Posterior" in contexto
```

Substituir por:

```python
        "Divisão de treino": ["Superior Anterior", "Inferior Posterior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior Anterior" in contexto
    assert "Inferior Posterior" in contexto
```

- [ ] **Passo 3.3 — Atualizar `test_formatar_contexto_aluno_divisao_mista_filtra_agente`**

Localizar (linha ~394):

```python
        "Divisão de treino": ["Deixar o agente decidir", "Fullbody"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Fullbody" in contexto
    assert "Deixar o agente decidir" not in contexto
```

Substituir por:

```python
        "Divisão de treino": ["Deixar o agente decidir", "Full Body (Corpo todo)"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Full Body (Corpo todo)" in contexto
    assert "Deixar o agente decidir" not in contexto
```

- [ ] **Passo 3.4 — Rodar os testes de divisão para confirmar aprovação**

```bash
python3 -m pytest tests/test_interface.py -v -k "divisao"
```

Saída esperada: todos os testes de divisão passam.

- [ ] **Passo 3.5 — Commit**

```bash
git add tests/test_interface.py
git commit -m "test(interface): atualizar testes de divisão de treino para novas opções"
```

---

## Task 4: Adicionar novos testes de divisão para as 9 opções granulares

**Files:**
- Modify: `tests/test_interface.py`

- [ ] **Passo 4.1 — Adicionar novos testes ao final de `test_interface.py`**

Adicionar ao final do arquivo:

```python
def test_formatar_contexto_aluno_divisao_superior():
    """Opção 'Superior' isolada é enviada corretamente ao LLM."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Fábio",
        "Idade": 32,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Livre"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Divisão de treino": ["Superior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Superior" in contexto


def test_formatar_contexto_aluno_divisao_inferior():
    """Opção 'Inferior' isolada é enviada corretamente ao LLM."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Gabi",
        "Idade": 25,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Livre"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Divisão de treino": ["Inferior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Inferior" in contexto


def test_formatar_contexto_aluno_divisao_superior_inferior_combinados():
    """Combinação 'Superior' + 'Inferior' aparece completa no contexto."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Hugo",
        "Idade": 27,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Livre"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Divisão de treino": ["Superior", "Inferior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior" in contexto
    assert "Inferior" in contexto


def test_formatar_contexto_aluno_divisao_quatro_partes():
    """Divisão completa em 4 partes aparece íntegra no contexto."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Irene",
        "Idade": 34,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 5,
        "Tempo por sessão": "90 min+",
        "Equipamentos disponíveis": ["Peso Livre", "Máquinas"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Avançado",
        "Divisão de treino": [
            "Superior Anterior",
            "Superior Posterior",
            "Inferior Anterior",
            "Inferior Posterior",
        ],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior Anterior" in contexto
    assert "Superior Posterior" in contexto
    assert "Inferior Anterior" in contexto
    assert "Inferior Posterior" in contexto


def test_formatar_contexto_aluno_divisao_corpo_todo_anterior():
    """Opção composta 'Superior Anterior / Inferior Anterior (Corpo todo)' é enviada corretamente."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Jonas",
        "Idade": 29,
        "Modalidade / Esporte praticado": "atletismo",
        "Objetivo": "Desempenho Esportivo",
        "Dias disponíveis por semana": 3,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Corporal"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Divisão de treino": ["Superior Anterior / Inferior Anterior (Corpo todo)"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior Anterior / Inferior Anterior (Corpo todo)" in contexto
```

- [ ] **Passo 4.2 — Rodar os novos testes**

```bash
python3 -m pytest tests/test_interface.py -v -k "divisao"
```

Saída esperada: todos os testes de divisão passam (antigos + novos).

- [ ] **Passo 4.3 — Rodar toda a suite**

```bash
python3 -m pytest tests/ -q
```

Saída esperada: `111+ passed, 0 failed`.

- [ ] **Passo 4.4 — Commit**

```bash
git add tests/test_interface.py
git commit -m "test(interface): adicionar testes para as 9 opções granulares de divisão"
```

---

## Verificação Final

- [ ] **Confirmar critérios de aceite do spec**

```bash
python3 -m pytest tests/ -v
```

Checklist:
- [ ] Formulário exibe 10 opções (verificar visualmente com `streamlit run src/interface/app.py`)
- [ ] `_DIVISAO_TREINO_RB` presente em todo prompt (`test_divisao_treino_rb_presente_no_prompt`)
- [ ] Bloco de divisão antes da metodologia (`test_divisao_treino_rb_antes_da_metodologia`)
- [ ] `_INSTRUCAO_BASE` referencia o bloco (`test_instrucao_base_referencia_divisao`)
- [ ] Testes de divisão antigos atualizados e passando
- [ ] Novos testes das 9 opções passando
- [ ] Todos os testes da suite passando
