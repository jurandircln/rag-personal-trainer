# Design: Divisão de Treino — Método RB no System Prompt

**Data:** 2026-03-30
**Branch:** feat/divisao-treino-metodo-rb

---

## Contexto

O formulário de anamnese atualmente oferece 4 opções de divisão de treino ("Deixar o agente decidir", "Fullbody", "Superior / Inferior", "Anterior / Posterior"). O system prompt não possui lógica estruturada do Método RB para guiar o LLM na escolha e justificativa da divisão muscular.

Este spec cobre duas mudanças complementares:
1. Expandir as opções de divisão no formulário (de 4 para 10 opções)
2. Adicionar a lógica do Método RB como constante dedicada no system prompt

---

## Mudança 1 — Opções de divisão no formulário (`app.py`)

**Arquivo:** `src/interface/app.py`

**Problema:** As opções atuais são genéricas e não refletem a granularidade do Método RB, que distingue entre dias de superior anterior, superior posterior, inferior anterior e inferior posterior.

**Solução:** Substituir as 3 opções específicas atuais pelas 9 opções granulares do Método RB:

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

**Comportamento inalterado:**
- Só "Deixar o agente decidir" selecionado → campo omitido do contexto enviado ao LLM
- Qualquer outra seleção → `Divisão de treino preferida: <opções>` no contexto
- Filtro em `formatar_contexto_aluno()` continua idêntico

**Mapeamento das opções para as divisões do Método RB:**

| Opção no formulário | Divisão no Método RB |
|---|---|
| Full Body (Corpo todo) | Full Body |
| Superior + Inferior | Superior / Inferior |
| Superior Anterior / Inferior Anterior (Corpo todo) | Anterior / Posterior (Full Body) |
| Superior Posterior / Inferior Posterior (Corpo todo) | Anterior / Posterior (Full Body) |
| Superior Anterior + Superior Posterior + Inferior Anterior + Inferior Posterior | Divisão Completa (4 partes) |
| Superior Anterior | Dia isolado — Superior Anterior |
| Superior Posterior | Dia isolado — Superior Posterior |
| Inferior Anterior | Dia isolado — Inferior Anterior |
| Inferior Posterior | Dia isolado — Inferior Posterior |

O LLM interpreta combinações de opções como intenção de divisão semanal.

---

## Mudança 2 — Constante `_DIVISAO_TREINO_RB` no system prompt (`prompt.py`)

**Arquivo:** `src/generation/prompt.py`

**Problema:** O LLM não possui critérios estruturados do Método RB para:
- Decidir automaticamente a divisão quando "Deixar o agente decidir" é selecionado
- Justificar a escolha na seção "## Metodologia do Treino"

**Solução:** Adicionar constante `_DIVISAO_TREINO_RB` com a lógica completa do método.

### Conteúdo da constante

```python
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

### Atualização em `_INSTRUCAO_BASE`

Adicionar ao final da string atual:

```
"A escolha e justificativa da divisão muscular seguem obrigatoriamente os critérios "
"do bloco [DIVISÃO DE TREINO — MÉTODO RB] presente neste prompt.\n"
```

### Atualização em `montar_prompt()`

Injetar `_DIVISAO_TREINO_RB` como segunda seção, logo após `_INSTRUCAO_BASE`:

```python
secoes.append(_INSTRUCAO_BASE)
secoes.append(_DIVISAO_TREINO_RB)  # nova linha
```

---

## Mudança 3 — Testes (`tests/test_interface.py` e `tests/test_prompt.py`)

### `test_interface.py`

Atualizar os testes existentes que referenciam as opções antigas:
- `test_formatar_contexto_aluno_com_divisao_treino` → usar `"Full Body (Corpo todo)"` no lugar de `"Fullbody"`
- `test_formatar_contexto_aluno_divisao_multipla` → substituir `"Superior / Inferior"` e `"Anterior / Posterior"` por opções da nova lista
- `test_formatar_contexto_aluno_divisao_mista_filtra_agente` → idem

Novos testes a adicionar:
- Verificar que cada uma das 9 novas opções é enviada corretamente ao LLM
- Verificar que combinações (ex: "Superior Anterior" + "Inferior Posterior") aparecem juntas no contexto

### `tests/test_prompt.py`

Novos testes:
- `_DIVISAO_TREINO_RB` está presente no prompt gerado por `montar_prompt()`
- O bloco de divisão aparece após `_INSTRUCAO_BASE` e antes da metodologia
- A referência à divisão em `_INSTRUCAO_BASE` está presente no prompt

---

## Arquivos modificados

| Arquivo | Tipo de mudança |
|---|---|
| `src/interface/app.py` | Substituir opções do multiselect |
| `src/generation/prompt.py` | Nova constante + linha em `_INSTRUCAO_BASE` + injeção em `montar_prompt()` |
| `tests/test_interface.py` | Atualizar testes existentes + novos testes |
| `tests/test_prompt.py` | Novos testes para `_DIVISAO_TREINO_RB` |

---

## Critérios de aceite

- [ ] Formulário exibe as 10 opções de divisão (incluindo "Deixar o agente decidir")
- [ ] Comportamento de omissão/inclusão no contexto do LLM mantido para "Deixar o agente decidir"
- [ ] `_DIVISAO_TREINO_RB` presente em todo prompt gerado por `montar_prompt()`
- [ ] Bloco de divisão injetado após `_INSTRUCAO_BASE`, antes da metodologia
- [ ] `_INSTRUCAO_BASE` referencia o bloco de divisão
- [ ] Testes existentes de divisão atualizados para as novas opções
- [ ] Novos testes cobrindo as 9 opções e combinações
- [ ] Todos os 106 testes existentes continuam passando
