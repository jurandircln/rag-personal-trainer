# Treinos Conjugados e Aquecimento Cardiovascular — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar suporte a treinos conjugados (bi-set/tri-set com notação `[CONJUGADO]`) e seção de aquecimento cardiovascular condicional ao gerador de treinos do Jarvis.

**Architecture:** Todas as mudanças ficam na camada de prompt (`src/generation/prompt.py`) e no formulário de anamnese (`src/interface/app.py`). Nenhum novo módulo ou infraestrutura é necessário. Task 1 cobre treinos conjugados no prompt; Task 2 cobre aquecimento no prompt; Task 3 cobre o campo de cardio no formulário.

**Tech Stack:** Python 3.11, Streamlit, pytest

---

## Contexto para o implementador

O `_INSTRUCAO_BASE` em `src/generation/prompt.py` é uma string Python com `\n` no final de cada sentença. Cada linha do arquivo de prompt é uma string entre aspas duplas, concatenada com o próximo par de aspas pelo Python (sem vírgula). A variável `_TEMPLATE_SAIDA` é uma f-string (na verdade uma string com `"""..."""`) que serve de template estrutural enviado ao LLM.

Nos testes:
- `tests/test_prompt.py` importa `_INSTRUCAO_BASE` e `_TEMPLATE_SAIDA` diretamente.
- `tests/test_interface.py` chama `formatar_contexto_aluno(dados)` com um dict — todos os campos novos devem usar `.get(..., [])` para não quebrar testes existentes que não passam `"Equipamentos cardiovasculares"`.

---

## Task 1: Treinos Conjugados — prompt.py

**Files:**
- Modify: `src/generation/prompt.py:16-43` (`_INSTRUCAO_BASE`) e `:72-232` (`_TEMPLATE_SAIDA`)
- Test: `tests/test_prompt.py`

- [ ] **Step 1: Escrever os testes com falha**

Adicionar ao final de `tests/test_prompt.py`:

```python
def test_instrucao_base_contem_regra_conjugado():
    """_INSTRUCAO_BASE deve conter a instrução de notação [CONJUGADO]."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "[CONJUGADO" in _INSTRUCAO_BASE


def test_template_saida_contem_exemplo_conjugado():
    """_TEMPLATE_SAIDA deve conter exemplo de bloco [CONJUGADO A1] / [CONJUGADO A2]."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert "[CONJUGADO A1]" in _TEMPLATE_SAIDA
    assert "[CONJUGADO A2]" in _TEMPLATE_SAIDA
```

- [ ] **Step 2: Verificar que os testes falham**

```bash
pytest tests/test_prompt.py::test_instrucao_base_contem_regra_conjugado tests/test_prompt.py::test_template_saida_contem_exemplo_conjugado -v
```

Esperado: 2 FAILs com `AssertionError`.

- [ ] **Step 3: Implementar — adicionar parágrafo de conjugado em `_INSTRUCAO_BASE`**

Em `src/generation/prompt.py`, localizar a última linha de `_INSTRUCAO_BASE` (antes do fechamento `)`):

```python
    "A escolha e justificativa da divisão muscular seguem obrigatoriamente os critérios "
    "do bloco [DIVISÃO DE TREINO — MÉTODO RB] presente neste prompt.\n"
)
```

Substituir pelo bloco abaixo (adicionando o parágrafo de conjugado antes do `)`):

```python
    "A escolha e justificativa da divisão muscular seguem obrigatoriamente os critérios "
    "do bloco [DIVISÃO DE TREINO — MÉTODO RB] presente neste prompt.\n"
    "Quando o personal solicitar treinos conjugados (supersets), use a notação "
    "[CONJUGADO X1] / [CONJUGADO X2] (onde X é uma letra sequencial: A, B, C…). "
    "Blocos com 2 exercícios = bi-set; com 3 exercícios = tri-set. "
    "Não há descanso entre os exercícios de um mesmo bloco. "
    "O tempo de descanso é indicado uma única vez, após o último exercício do bloco. "
    "Máximo de 3 exercícios por bloco. "
    "Aplique conjugado SOMENTE quando o personal solicitar explicitamente.\n"
)
```

- [ ] **Step 4: Implementar — adicionar exemplo de conjugado em `_TEMPLATE_SAIDA`**

Em `_TEMPLATE_SAIDA`, localizar o bloco do primeiro `#### [Músculo Grande, ex: Peitoral]` (no Dia 1 do template). Encontre a sequência exata:

```
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
```

Substituir por (adicionando o bloco de exemplo conjugado após o 4º exercício):

```
#### [Músculo Grande, ex: Peitoral]

* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
* [nome do exercício]
  [N séries × N–N reps (método)]
[Quando solicitado pelo personal, inserir blocos conjugados com esta notação:]
* [CONJUGADO A1] [nome do exercício]
  N séries × N–N reps
* [CONJUGADO A2] [nome do exercício]
  N séries × N–N reps
  Descanso após bloco A: Xs

#### [Músculo Grande, ex: Dorsal]
```

- [ ] **Step 5: Verificar que os testes passam**

```bash
pytest tests/test_prompt.py -v
```

Esperado: todos os testes PASS, incluindo os dois novos. Verificar especialmente que `test_template_saida_nao_contem_opcional` ainda passa (não inserimos a string `(Opcional)`).

- [ ] **Step 6: Commit**

```bash
git add src/generation/prompt.py tests/test_prompt.py
git commit -m "feat(prompt): suporte a treinos conjugados com notação [CONJUGADO]"
```

---

## Task 2: Aquecimento Cardiovascular — prompt.py

**Files:**
- Modify: `src/generation/prompt.py:16-43` (`_INSTRUCAO_BASE`) e `:72-232` (`_TEMPLATE_SAIDA`)
- Test: `tests/test_prompt.py`

- [ ] **Step 1: Escrever os testes com falha**

Adicionar ao final de `tests/test_prompt.py`:

```python
def test_instrucao_base_contem_regra_aquecimento():
    """_INSTRUCAO_BASE deve conter a instrução condicional de ### Aquecimento."""
    from src.generation.prompt import _INSTRUCAO_BASE

    assert "### Aquecimento" in _INSTRUCAO_BASE
    assert "equipamentos cardiovasculares" in _INSTRUCAO_BASE


def test_template_saida_contem_secao_aquecimento():
    """_TEMPLATE_SAIDA deve conter a seção ### Aquecimento antes de ### Liberação Miofascial."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    pos_aquecimento = _TEMPLATE_SAIDA.find("### Aquecimento")
    pos_liberacao = _TEMPLATE_SAIDA.find("### Liberação Miofascial")
    assert pos_aquecimento != -1, "### Aquecimento não encontrado no template"
    assert pos_aquecimento < pos_liberacao, "### Aquecimento deve aparecer antes de ### Liberação Miofascial"
```

- [ ] **Step 2: Verificar que os testes falham**

```bash
pytest tests/test_prompt.py::test_instrucao_base_contem_regra_aquecimento tests/test_prompt.py::test_template_saida_contem_secao_aquecimento -v
```

Esperado: 2 FAILs com `AssertionError`.

- [ ] **Step 3: Implementar — adicionar parágrafo de aquecimento em `_INSTRUCAO_BASE`**

Em `src/generation/prompt.py`, localizar a linha que acabou de ser adicionada na Task 1 (última linha do bloco de conjugado, antes de `)`):

```python
    "Aplique conjugado SOMENTE quando o personal solicitar explicitamente.\n"
)
```

Substituir por (adicionando o parágrafo de aquecimento antes do `)`):

```python
    "Aplique conjugado SOMENTE quando o personal solicitar explicitamente.\n"
    "Se o personal solicitar aquecimento e o contexto do aluno listar equipamentos "
    "cardiovasculares disponíveis, gere a seção ### Aquecimento no início da sessão, "
    "imediatamente antes de ### Liberação Miofascial. "
    "Inclua: modalidade (ex: Esteira), duração (8–15 min) e intensidade sugerida "
    "(leve a moderada, 60–70% FCmáx). "
    "Se nenhum equipamento cardiovascular estiver disponível no contexto do aluno "
    "ou o personal não solicitar aquecimento, omita completamente a seção.\n"
)
```

- [ ] **Step 4: Implementar — adicionar seção `### Aquecimento` em `_TEMPLATE_SAIDA`**

Em `_TEMPLATE_SAIDA`, há **duas** ocorrências de `### Liberação Miofascial` (uma por dia). Ambas devem receber a seção de aquecimento antes delas.

**Primeira ocorrência** — localizar:

```
### Dia 1 — [foco do dia]

### Liberação Miofascial
```

Substituir por:

```
### Dia 1 — [foco do dia]

### Aquecimento  *(usar somente quando solicitado e equipamento cardiovascular disponível)*

* [modalidade, ex: Esteira]
  [duração e intensidade, ex: 10 min — velocidade 6 km/h, intensidade leve]

### Liberação Miofascial
```

**Segunda ocorrência** — localizar:

```
### Dia 2 — [foco do dia]

### Liberação Miofascial
```

Substituir por:

```
### Dia 2 — [foco do dia]

### Aquecimento  *(usar somente quando solicitado e equipamento cardiovascular disponível)*

* [modalidade, ex: Esteira]
  [duração e intensidade, ex: 10 min — velocidade 6 km/h, intensidade leve]

### Liberação Miofascial
```

- [ ] **Step 5: Verificar que os testes passam**

```bash
pytest tests/test_prompt.py -v
```

Esperado: todos PASS. Verificar especialmente:
- `test_template_saida_nao_contem_opcional` — PASS (a string `(Opcional)` não foi inserida)
- `test_template_contem_aviso_minimo_fortalecimento` — PASS (count ainda == 2)
- `test_template_fortalecimento_tem_14_exercicios_por_secao` — PASS (contagem de `* [nome do exercício]` por bloco ainda >= 14)

- [ ] **Step 6: Commit**

```bash
git add src/generation/prompt.py tests/test_prompt.py
git commit -m "feat(prompt): seção ### Aquecimento condicional para equipamentos cardiovasculares"
```

---

## Task 3: Campo Cardiovascular no Formulário — app.py

**Files:**
- Modify: `src/interface/app.py:198-224` (formulário) e `:27-57` (`formatar_contexto_aluno`)
- Test: `tests/test_interface.py`

- [ ] **Step 1: Escrever os testes com falha**

Adicionar ao final de `tests/test_interface.py`:

```python
def test_formatar_contexto_aluno_com_cardio():
    """Quando equipamentos cardiovasculares preenchidos, o contexto inclui a linha."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Pedro",
        "Idade": 30,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Livre"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Equipamentos cardiovasculares": ["Esteira", "Bike estacionária"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Equipamentos cardiovasculares: Esteira, Bike estacionária" in contexto


def test_formatar_contexto_aluno_sem_cardio():
    """Quando equipamentos cardiovasculares é lista vazia, a linha não aparece no contexto."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Renata",
        "Idade": 27,
        "Modalidade / Esporte praticado": "yoga",
        "Objetivo": "Qualidade de Vida",
        "Dias disponíveis por semana": 3,
        "Tempo por sessão": "45 min",
        "Equipamentos disponíveis": ["Peso Corporal"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Iniciante",
        "Equipamentos cardiovasculares": [],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Equipamentos cardiovasculares" not in contexto
```

- [ ] **Step 2: Verificar que os testes falham**

```bash
pytest tests/test_interface.py::test_formatar_contexto_aluno_com_cardio tests/test_interface.py::test_formatar_contexto_aluno_sem_cardio -v
```

Esperado: 2 FAILs.

- [ ] **Step 3: Implementar — atualizar `formatar_contexto_aluno`**

Em `src/interface/app.py`, localizar a função `formatar_contexto_aluno`. Encontrar o bloco onde `linhas` é construído e onde a divisão de treino é adicionada condicionalmente:

```python
    if divisao_opcoes:
        linhas.append(f"Divisão de treino preferida: {', '.join(divisao_opcoes)}")

    return "\n".join(linhas)
```

Substituir por (adicionando o bloco de cardio antes do `return`):

```python
    if divisao_opcoes:
        linhas.append(f"Divisão de treino preferida: {', '.join(divisao_opcoes)}")

    cardio_disponivel = ", ".join(dados.get("Equipamentos cardiovasculares", []))
    if cardio_disponivel:
        linhas.append(f"Equipamentos cardiovasculares: {cardio_disponivel}")

    return "\n".join(linhas)
```

- [ ] **Step 4: Verificar que os testes de `formatar_contexto_aluno` passam**

```bash
pytest tests/test_interface.py::test_formatar_contexto_aluno_com_cardio tests/test_interface.py::test_formatar_contexto_aluno_sem_cardio -v
```

Esperado: 2 PASSes.

- [ ] **Step 5: Implementar — adicionar campo no formulário de anamnese**

Em `src/interface/app.py`, localizar o campo `equipamentos` seguido de `lesoes`:

```python
        equipamentos = st.multiselect(
            "Equipamentos disponíveis",
            ["Peso Livre", "Máquinas", "Peso Corporal", "Elásticos", "Sem Equipamento"],
            default=["Peso Corporal"],
        )
        lesoes = st.text_area(
            "Lesões ou restrições (deixe em branco se nenhuma)", height=80
        )
```

Substituir por (inserindo o campo `cardio` entre `equipamentos` e `lesoes`):

```python
        equipamentos = st.multiselect(
            "Equipamentos disponíveis",
            ["Peso Livre", "Máquinas", "Peso Corporal", "Elásticos", "Sem Equipamento"],
            default=["Peso Corporal"],
        )
        cardio = st.multiselect(
            "Equipamentos cardiovasculares",
            ["Esteira", "Bike estacionária", "Remo ergométrico", "Elíptico", "Corda de pular"],
            default=[],
        )
        lesoes = st.text_area(
            "Lesões ou restrições (deixe em branco se nenhuma)", height=80
        )
```

- [ ] **Step 6: Implementar — adicionar `cardio` no dicionário de dados do aluno**

Localizar o dicionário `dados` no bloco `if enviado:`:

```python
            dados = {
                "Nome": nome.strip(),
                "Idade": idade,
                "Modalidade / Esporte praticado": modalidade.strip(),
                "Objetivo": objetivo,
                "Dias disponíveis por semana": dias_semana,
                "Tempo por sessão": tempo_sessao,
                "Equipamentos disponíveis": equipamentos,
                "Lesões ou restrições": lesoes.strip(),
                "Nível de condicionamento": nivel,
                "Divisão de treino": divisao_treino,
            }
```

Substituir por:

```python
            dados = {
                "Nome": nome.strip(),
                "Idade": idade,
                "Modalidade / Esporte praticado": modalidade.strip(),
                "Objetivo": objetivo,
                "Dias disponíveis por semana": dias_semana,
                "Tempo por sessão": tempo_sessao,
                "Equipamentos disponíveis": equipamentos,
                "Equipamentos cardiovasculares": cardio,
                "Lesões ou restrições": lesoes.strip(),
                "Nível de condicionamento": nivel,
                "Divisão de treino": divisao_treino,
            }
```

- [ ] **Step 7: Rodar a suíte completa de testes**

```bash
pytest tests/ -v
```

Esperado: todos os testes PASS. Os testes existentes de `formatar_contexto_aluno` (que não passam `"Equipamentos cardiovasculares"`) devem continuar passando porque a implementação usa `.get("Equipamentos cardiovasculares", [])`.

- [ ] **Step 8: Commit**

```bash
git add src/interface/app.py tests/test_interface.py
git commit -m "feat(interface): campo de equipamentos cardiovasculares no formulário de anamnese"
```
