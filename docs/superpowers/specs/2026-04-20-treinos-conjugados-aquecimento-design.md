# Spec: Treinos Conjugados e Aquecimento Cardiovascular

**Data:** 2026-04-20
**Status:** Aprovado
**Escopo:** Duas melhorias no gerador de treinos — suporte a blocos conjugados (supersets) e seção de aquecimento cardiovascular condicional

---

## 1. Contexto e Motivação

O Jarvis gera planos de treino completos, mas ainda não suporta dois padrões comuns solicitados por personais:

1. **Treinos conjugados** — exercícios executados sem intervalo entre si (supersets / bi-sets / tri-sets). O LLM atualmente não conhece essa notação e não sabe quando ou como aplicá-la.
2. **Aquecimento cardiovascular** — esteira, bike, remo ou similares como bloco inicial de sessão. Não existe seção `### Aquecimento` no template nem campo no formulário para indicar equipamentos cardiovasculares disponíveis.

Ambas as melhorias são ativadas **somente quando o personal solicitar** — não são adicionadas a todo plano automaticamente.

---

## 2. Restrições

- Nenhuma mudança de infraestrutura: sem novos módulos, sem alterações no catálogo de exercícios (`reference.md`), sem novas tabelas de banco.
- Toda a lógica fica na camada de prompt (`prompt.py`) e no formulário de anamnese (`app.py`).
- Conjugado é uma instrução tática por consulta — não vira campo permanente da anamnese.
- Aquecimento só aparece no plano se o personal pedir E o aluno tiver equipamento cardiovascular cadastrado.

---

## 3. Arquitetura

```
app.py (formulário)
    └─ novo campo "Equipamentos cardiovasculares" (multiselect)
    └─ formatar_contexto_aluno() inclui cardio quando preenchido

prompt.py (camada de prompt)
    └─ _INSTRUCAO_BASE: instrução condicional de conjugado + instrução condicional de aquecimento
    └─ _TEMPLATE_SAIDA: exemplo de bloco [CONJUGADO] + seção ### Aquecimento condicional
```

Sem mudanças em: `llm.py`, `catalogo.py`, `retrieval/`, `ingestion/`, `config/`.

---

## 4. Feature 1 — Treinos Conjugados

### 4.1 Instrução no `_INSTRUCAO_BASE`

Adicionado ao final do bloco existente:

```
Quando o personal solicitar treinos conjugados (supersets), use a notação
[CONJUGADO X1] / [CONJUGADO X2] (onde X é uma letra sequencial: A, B, C…).
Blocos com 2 exercícios = bi-set; com 3 exercícios = tri-set.
Não há descanso entre os exercícios de um mesmo bloco.
O tempo de descanso é indicado uma única vez, após o último exercício do bloco.
Máximo de 3 exercícios por bloco.
Aplique conjugado SOMENTE quando o personal solicitar explicitamente.
```

### 4.2 Exemplo no `_TEMPLATE_SAIDA`

Dentro do bloco de `#### [Músculo]`, após os exemplos existentes de exercício simples, adicionar:

```
*(Exemplo de bloco conjugado — usar somente quando solicitado)*
* [CONJUGADO A1] Nome do exercício
  N séries × N–N reps
* [CONJUGADO A2] Nome do exercício
  N séries × N–N reps
  Descanso após bloco A: Xs
```

---

## 5. Feature 2 — Aquecimento Cardiovascular

### 5.1 Formulário de Anamnese (`app.py`)

Novo campo logo após o `st.multiselect` de "Equipamentos disponíveis":

```python
cardio = st.multiselect(
    "Equipamentos cardiovasculares",
    ["Esteira", "Bike estacionária", "Remo ergométrico", "Elíptico", "Corda de pular"],
    default=[],
)
```

Adicionado ao dicionário de dados do aluno:

```python
"Equipamentos cardiovasculares": cardio,
```

### 5.2 `formatar_contexto_aluno` (`app.py`)

Nova linha condicional no texto formatado:

```python
cardio_disponivel = ", ".join(dados.get("Equipamentos cardiovasculares", [])) or None
if cardio_disponivel:
    linhas.append(f"Equipamentos cardiovasculares: {cardio_disponivel}")
```

O campo **não aparece** no contexto enviado ao LLM quando a lista estiver vazia.

### 5.3 Instrução no `_INSTRUCAO_BASE` (`prompt.py`)

Adicionado ao final do bloco existente:

```
Se o personal solicitar aquecimento e o contexto do aluno listar equipamentos
cardiovasculares disponíveis, gere a seção ### Aquecimento no início da sessão,
imediatamente antes de ### Liberação Miofascial.
Inclua: modalidade (ex: Esteira), duração (8–15 min) e intensidade sugerida
(leve a moderada, 60–70% FCmáx).
Se nenhum equipamento cardiovascular estiver disponível no contexto do aluno,
ou o personal não solicitar aquecimento, omita completamente a seção.
```

### 5.4 Seção no `_TEMPLATE_SAIDA` (`prompt.py`)

Inserido antes de `### Liberação Miofascial`, marcado como condicional:

```
### Aquecimento  *(incluir somente quando solicitado e equipamento disponível)*

* [modalidade, ex: Esteira]
  [duração e intensidade, ex: 10 min — velocidade 6 km/h, intensidade leve]
```

---

## 6. Arquivos Afetados

| Arquivo | Mudança |
|---|---|
| `src/interface/app.py` | Novo campo "Equipamentos cardiovasculares" no formulário + linha em `formatar_contexto_aluno` |
| `src/generation/prompt.py` | `_INSTRUCAO_BASE` e `_TEMPLATE_SAIDA` atualizados para conjugado e aquecimento |
| `tests/test_prompt.py` | Novos testes para as instruções adicionadas |
| `tests/test_interface.py` | Novo teste para `formatar_contexto_aluno` com campo cardiovascular |

---

## 7. Testes

### `tests/test_prompt.py`

- `test_instrucao_base_contem_conjugado` — verifica que `_INSTRUCAO_BASE` contém `[CONJUGADO`
- `test_instrucao_base_contem_aquecimento` — verifica que `_INSTRUCAO_BASE` contém `### Aquecimento`
- `test_template_saida_contem_exemplo_conjugado` — verifica que `_TEMPLATE_SAIDA` contém `[CONJUGADO A1]`
- `test_template_saida_contem_secao_aquecimento` — verifica que `_TEMPLATE_SAIDA` contém `### Aquecimento`

### `tests/test_interface.py`

- `test_formatar_contexto_aluno_com_cardio` — verifica que `formatar_contexto_aluno` inclui linha `"Equipamentos cardiovasculares: Esteira"` quando o campo está preenchido
- `test_formatar_contexto_aluno_sem_cardio` — verifica que a linha **não aparece** quando `"Equipamentos cardiovasculares"` é lista vazia

---

## 8. Fora do Escopo

- Campo permanente na anamnese para "prefere treinos conjugados" (decisão tática, não de perfil)
- Adição de cardio ao catálogo de exercícios (`reference.md`)
- Validação estrutural de blocos conjugados no parser de semanas
- Alertas ou restrições de conjugado por nível de condicionamento
