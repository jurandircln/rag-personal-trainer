# Melhorias no Formulário de Anamnese e Template do LLM — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar Liberação Miofascial e Mobilidade obrigatórias no template do LLM, adicionar campo de divisão de treino no formulário, e melhorar label/placeholder do campo de texto livre.

**Architecture:** Três mudanças independentes em dois arquivos: `src/generation/prompt.py` (template do LLM) e `src/interface/app.py` (formulário e campo de texto). Cada task é isolada e commitada separadamente.

**Tech Stack:** Python 3.11+, Streamlit, pytest

---

## Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/generation/prompt.py` | Remover `(Opcional)` de 4 ocorrências em `_TEMPLATE_SAIDA` |
| `src/interface/app.py` | Novo `st.multiselect` de divisão + atualizar `formatar_contexto_aluno()` + trocar label/placeholder |
| `tests/test_interface.py` | Novos testes para `formatar_contexto_aluno` com divisão de treino + teste de template |

---

## Task 1: Tornar Liberação Miofascial e Mobilidade obrigatórias no template

**Arquivos:**
- Modify: `src/generation/prompt.py`
- Test: `tests/test_interface.py`

> Contexto: `_TEMPLATE_SAIDA` em `prompt.py` contém 4 headers marcados como `(Opcional)` — dois para Liberação Miofascial (Dia 1 e Dia 2) e dois para Mobilidade (Dia 1 e Dia 2). Isso sinaliza ao LLM que pode omiti-los. A mudança remove esses marcadores.

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao final de `tests/test_interface.py`:

```python
def test_template_saida_nao_contem_opcional():
    """Verifica que o template de saída não marca nenhuma seção como opcional."""
    from src.generation.prompt import _TEMPLATE_SAIDA

    assert "(Opcional)" not in _TEMPLATE_SAIDA
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

```bash
pytest tests/test_interface.py::test_template_saida_nao_contem_opcional -v
```

Esperado: `FAILED` — `AssertionError` porque `(Opcional)` está presente.

- [ ] **Step 3: Aplicar a mudança em `prompt.py`**

Em `src/generation/prompt.py`, localizar `_TEMPLATE_SAIDA` e substituir as 4 ocorrências:

```python
# Linha ~56: Dia 1 Liberação Miofascial
### Liberação Miofascial (Opcional)
# → substituir por:
### Liberação Miofascial

# Linha ~62: Dia 1 Mobilidade
### Mobilidade (Opcional)
# → substituir por:
### Mobilidade

# Linha ~90: Dia 2 Liberação Miofascial
### Liberação Miofascial (Opcional)
# → substituir por:
### Liberação Miofascial

# Linha ~96: Dia 2 Mobilidade
### Mobilidade (Opcional)
# → substituir por:
### Mobilidade
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

```bash
pytest tests/test_interface.py::test_template_saida_nao_contem_opcional -v
```

Esperado: `PASSED`

- [ ] **Step 5: Rodar a suite completa para garantir nenhuma regressão**

```bash
pytest tests/ -v
```

Esperado: todos `PASSED`.

- [ ] **Step 6: Commit**

```bash
git add src/generation/prompt.py tests/test_interface.py
git commit -m "feat(prompt): tornar liberação miofascial e mobilidade obrigatórias no template"
```

---

## Task 2: Adicionar campo de divisão de treino no formulário

**Arquivos:**
- Modify: `src/interface/app.py`
- Test: `tests/test_interface.py`

> Contexto: `formatar_contexto_aluno(dados)` em `app.py` recebe um dict e retorna string para o LLM. O formulário `st.form("form_anamnese")` coleta os dados do aluno. Vamos adicionar o campo `st.multiselect` no form e atualizar `formatar_contexto_aluno` para incluir a divisão condicionalmente.

### Sub-task 2a: Atualizar `formatar_contexto_aluno`

- [ ] **Step 1: Escrever os testes que falham**

Adicionar ao final de `tests/test_interface.py`:

```python
def test_formatar_contexto_aluno_com_divisao_treino():
    """Quando divisão definida, o contexto inclui 'Divisão de treino preferida'."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Ana",
        "Idade": 28,
        "Modalidade / Esporte praticado": "musculação",
        "Objetivo": "Hipertrofia",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Livre"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        "Divisão de treino": ["Fullbody"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino preferida: Fullbody" in contexto


def test_formatar_contexto_aluno_divisao_agente_decide():
    """Quando 'Deixar o agente decidir' é a única seleção, campo é omitido do contexto."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Bruno",
        "Idade": 35,
        "Modalidade / Esporte praticado": "corrida",
        "Objetivo": "Resistência",
        "Dias disponíveis por semana": 3,
        "Tempo por sessão": "45 min",
        "Equipamentos disponíveis": ["Peso Corporal"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Iniciante",
        "Divisão de treino": ["Deixar o agente decidir"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino" not in contexto


def test_formatar_contexto_aluno_divisao_multipla():
    """Quando múltiplas divisões selecionadas, todas aparecem no contexto."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Clara",
        "Idade": 22,
        "Modalidade / Esporte praticado": "natação",
        "Objetivo": "Desempenho Esportivo",
        "Dias disponíveis por semana": 5,
        "Tempo por sessão": "90 min+",
        "Equipamentos disponíveis": ["Peso Livre", "Máquinas"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Avançado",
        "Divisão de treino": ["Superior / Inferior", "Anterior / Posterior"],
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Superior / Inferior" in contexto
    assert "Anterior / Posterior" in contexto


def test_formatar_contexto_aluno_sem_campo_divisao():
    """Quando 'Divisão de treino' não está no dict (dados legados), campo é omitido."""
    from src.interface.app import formatar_contexto_aluno

    dados = {
        "Nome": "Diego",
        "Idade": 30,
        "Modalidade / Esporte praticado": "crossfit",
        "Objetivo": "Emagrecimento",
        "Dias disponíveis por semana": 4,
        "Tempo por sessão": "60 min",
        "Equipamentos disponíveis": ["Peso Corporal"],
        "Lesões ou restrições": "",
        "Nível de condicionamento": "Intermediário",
        # sem chave "Divisão de treino"
    }

    contexto = formatar_contexto_aluno(dados)

    assert "Divisão de treino" not in contexto
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

```bash
pytest tests/test_interface.py::test_formatar_contexto_aluno_com_divisao_treino \
       tests/test_interface.py::test_formatar_contexto_aluno_divisao_agente_decide \
       tests/test_interface.py::test_formatar_contexto_aluno_divisao_multipla \
       tests/test_interface.py::test_formatar_contexto_aluno_sem_campo_divisao -v
```

Esperado: 4x `FAILED` — `KeyError` ou `AssertionError`.

- [ ] **Step 3: Atualizar `formatar_contexto_aluno` em `app.py`**

Localizar a função `formatar_contexto_aluno` (linha ~25) e substituir pelo código abaixo:

```python
def formatar_contexto_aluno(dados: dict) -> str:
    """Formata os dados da anamnese como texto estruturado para o prompt.

    Args:
        dados: dicionário com os campos da anamnese.

    Returns:
        String formatada com as informações do aluno.
    """
    equipamentos = ", ".join(dados.get("Equipamentos disponíveis", [])) or "não informado"

    # Filtra a opção "Deixar o agente decidir" para não enviá-la ao LLM
    divisao_raw = dados.get("Divisão de treino", [])
    divisao_opcoes = [d for d in divisao_raw if d != "Deixar o agente decidir"]

    linhas = [
        f"Nome: {dados['Nome']}",
        f"Idade: {dados['Idade']} anos",
        f"Modalidade/esporte: {dados['Modalidade / Esporte praticado']}",
        f"Objetivo principal: {dados['Objetivo']}",
        f"Dias disponíveis por semana: {dados['Dias disponíveis por semana']}",
        f"Tempo por sessão: {dados['Tempo por sessão']}",
        f"Equipamentos disponíveis: {equipamentos}",
        f"Lesões ou restrições: {dados['Lesões ou restrições'] or 'nenhuma'}",
        f"Nível de condicionamento: {dados['Nível de condicionamento']}",
    ]

    if divisao_opcoes:
        linhas.append(f"Divisão de treino preferida: {', '.join(divisao_opcoes)}")

    return "\n".join(linhas)
```

- [ ] **Step 4: Rodar os 4 novos testes para confirmar que passam**

```bash
pytest tests/test_interface.py::test_formatar_contexto_aluno_com_divisao_treino \
       tests/test_interface.py::test_formatar_contexto_aluno_divisao_agente_decide \
       tests/test_interface.py::test_formatar_contexto_aluno_divisao_multipla \
       tests/test_interface.py::test_formatar_contexto_aluno_sem_campo_divisao -v
```

Esperado: 4x `PASSED`

- [ ] **Step 5: Rodar a suite completa para garantir nenhuma regressão**

```bash
pytest tests/ -v
```

Esperado: todos `PASSED`.

### Sub-task 2b: Adicionar o `st.multiselect` no formulário

- [ ] **Step 6: Adicionar o campo no `st.form` em `app.py`**

Localizar o bloco `col3, col4` (linhas ~154–164) e adicionar o multiselect logo após o fechamento das colunas (antes de `equipamentos = st.multiselect`):

```python
        col3, col4 = st.columns(2)
        with col3:
            tempo_sessao = st.selectbox(
                "Tempo disponível por sessão",
                ["30 min", "45 min", "60 min", "90 min+"],
            )
        with col4:
            nivel = st.selectbox(
                "Nível de condicionamento",
                ["Iniciante", "Intermediário", "Avançado"],
            )

        # NOVO CAMPO — inserir aqui:
        divisao_treino = st.multiselect(
            "Divisão de treino",
            ["Deixar o agente decidir", "Fullbody", "Superior / Inferior", "Anterior / Posterior"],
            default=["Deixar o agente decidir"],
        )

        equipamentos = st.multiselect(
            "Equipamentos disponíveis",
            ["Peso Livre", "Máquinas", "Peso Corporal", "Elásticos", "Sem Equipamento"],
            default=["Peso Corporal"],
        )
```

- [ ] **Step 7: Adicionar `"Divisão de treino"` no dicionário `dados`**

Localizar o bloco `dados = { ... }` dentro do `if enviado:` (linha ~181) e adicionar a chave:

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

- [ ] **Step 8: Rodar a suite completa**

```bash
pytest tests/ -v
```

Esperado: todos `PASSED`.

- [ ] **Step 9: Commit**

```bash
git add src/interface/app.py tests/test_interface.py
git commit -m "feat(interface): adicionar campo de divisão de treino no formulário de anamnese"
```

---

## Task 3: Atualizar label e placeholder do campo de texto livre

**Arquivos:**
- Modify: `src/interface/app.py` — ESTADO 2 (Pergunta)

> Contexto: O campo `st.text_area` no ESTADO 2 (linha ~207) tem label `"Sua pergunta:"` e placeholder de exemplo de treino. A mudança é apenas visual — sem alteração de lógica ou validação.

- [ ] **Step 1: Localizar e atualizar o `st.text_area` em `app.py`**

Localizar (linha ~207):

```python
    pergunta = st.text_area(
        label="Sua pergunta:",
        placeholder="Ex.: Monte um programa de força para 3 dias por semana.",
        height=100,
    )
```

Substituir por:

```python
    pergunta = st.text_area(
        label="Adicione mais informações (opcional)",
        placeholder=(
            'Ex.: "Prefiro exercícios compostos no início. Evitar agachamento por limitação de tornozelo."\n'
            '"Aluno ex-atleta de natação — priorizar mobilidade de ombro e volume de costas."\n'
            '"Monte o treino com progressão de carga semana a semana."'
        ),
        height=100,
    )
```

- [ ] **Step 2: Rodar a suite completa**

```bash
pytest tests/ -v
```

Esperado: todos `PASSED`.

- [ ] **Step 3: Commit**

```bash
git add src/interface/app.py
git commit -m "feat(interface): atualizar label e placeholder do campo de informações adicionais"
```

---

## Checklist de critérios de aceite

- [ ] `(Opcional)` não aparece em nenhum header do `_TEMPLATE_SAIDA`
- [ ] Formulário exibe campo "Divisão de treino" com as 4 opções corretas
- [ ] Quando "Deixar o agente decidir" é a única seleção, campo não aparece no contexto do LLM
- [ ] Quando outras opções são selecionadas, contexto inclui `Divisão de treino preferida: ...`
- [ ] Label do campo de texto livre exibe "Adicione mais informações (opcional)"
- [ ] Placeholder do campo exibe os 3 exemplos definidos
- [ ] `pytest tests/ -v` passa integralmente
