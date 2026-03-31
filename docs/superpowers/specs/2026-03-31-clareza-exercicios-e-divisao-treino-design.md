# Design: Clareza na Contagem de Exercícios e Labels de Divisão de Treino

**Data:** 2026-03-31
**Branch:** feat/melhorias-formulario-anamnese

---

## Contexto

Dois problemas identificados durante testes do agente:

1. **Contagem de exercícios:** O LLM conta liberação, mobilidade e ativação como exercícios para atingir o mínimo de 12. Resultado: seção Fortalecimento com apenas 3–4 exercícios. A regra correta é que o mínimo de 12 se aplica exclusivamente à seção Fortalecimento.

2. **Labels de divisão de treino:** As opções "Superior Anterior / Inferior Anterior (Corpo todo)" e "Superior Posterior / Inferior Posterior (Corpo todo)" não comunicam o conceito de cadeia muscular completa numa sessão. O personal trainer e o LLM interpretam os labels de formas distintas.

---

## Mudança 1 — `src/generation/metodologia.txt`

**Seção 4 — ORGANIZAÇÃO DO VOLUME POR SESSÃO**

Substituir o trecho atual:

> 12 a 15 exercícios por sessão:
> - 2–3 liberações (se necessário)
> - 3–4 mobilidades (se necessário)
> - 3–4 ativações
> - 5–7 fortalecimento

Por:

> Sessão completa: 12 a 20 exercícios no total (preparação + fortalecimento).
> - Preparação (liberação, mobilidade, ativação): não conta para o mínimo de fortalecimento
>   - 2–3 liberações (se necessário)
>   - 3–4 mobilidades (se necessário)
>   - 3–4 ativações
> - Fortalecimento: mínimo obrigatório de 12 exercícios por sessão (ideal: 12–15)
>
> Liberação, mobilidade e ativação são fases de preparação — NÃO contam para o mínimo de 12.

---

## Mudança 2 — `src/generation/prompt.py`

### 2a. `_INSTRUCAO_BASE`

Substituir o trecho sobre quantidade mínima de exercícios por grupo muscular:

```python
# Antes:
"Quantidade mínima de exercícios de FORTALECIMENTO por grupo muscular em cada sessão: "
"músculos pequenos (bíceps, tríceps, ombros, panturrilha) → mínimo 3 exercícios; "
"músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
"→ mínimo 4 exercícios.\n"

# Depois:
"Quantidade mínima de exercícios na seção FORTALECIMENTO: 12 por sessão (ideal: 12–15). "
"Liberação miofascial, mobilidade e ativação são fases de PREPARAÇÃO — "
"NÃO contam para esse mínimo. "
"Dentro do Fortalecimento: músculos pequenos (bíceps, tríceps, ombros, panturrilha) "
"→ mínimo 3 exercícios cada; "
"músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
"→ mínimo 4 exercícios cada.\n"
```

### 2b. Bloco do catálogo em `montar_prompt()`

Substituir:

```python
# Antes:
"- Cada sessão deve ter 12 a 15 exercícios no total: 2-3 liberações (se necessário) + "
"3-4 mobilidades (se necessário) + 3-4 ativações + 5-8 fortalecimento "
"(respeitando o mínimo por grupo muscular definido acima). "
"Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"

# Depois:
"- Seção Fortalecimento: mínimo 12 exercícios por sessão (ideal: 12–15). "
"Liberação, mobilidade e ativação são PREPARAÇÃO e NÃO contam para esse mínimo. "
"Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
```

### 2c. Constante `_DIVISAO_TREINO_RB` (nova — conforme spec 2026-03-30)

A constante planejada no spec anterior deve incluir a explicação das cadeias musculares:

```python
_DIVISAO_TREINO_RB = (
    "[DIVISÃO DE TREINO — MÉTODO RB]\n"
    "Quando o aluno selecionar 'Deixar o agente decidir', aplique os critérios abaixo "
    "para escolher a divisão mais adequada ao perfil do aluno:\n\n"
    "- Full Body (Corpo todo) → indicado para: iniciantes, 2–3x/semana, reabilitação, "
    "alunos com pouco tempo disponível.\n"
    "- Superior + Inferior → indicado para: intermediários, 3–4x/semana. "
    "Vantagem: melhor controle de volume e maior recuperação por grupamento.\n"
    "- Cadeia Anterior (Corpo todo): numa sessão, treinar a cadeia anterior completa — "
    "Superior Anterior (Peito, Tríceps, Ombros) + Inferior Anterior (Quadríceps). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
    "- Cadeia Posterior (Corpo todo): numa sessão, treinar a cadeia posterior completa — "
    "Superior Posterior (Dorsal, Bíceps) + Inferior Posterior (Post. Coxa, Panturrilha). "
    "Indicado para intermediários e atletas. Respeita cadeias musculares.\n"
    "- Divisão completa em 4 partes (Superior Anterior, Superior Posterior, Inferior Anterior, "
    "Inferior Posterior) → indicado para: avançados, foco em hipertrofia, ≥4x/semana. "
    "Maior especificidade e volume por grupamento.\n\n"
    "REGRAS OBRIGATÓRIAS — aplicam-se a qualquer divisão:\n"
    "- Todo treino deve conter exercícios de core: anti-extensão, anti-rotação, "
    "anti-flexão lateral e estabilidade dinâmica.\n"
    "- Mínimo de 12 exercícios na seção Fortalecimento por sessão (ideal: 12–15). "
    "Liberação, mobilidade e ativação são PREPARAÇÃO — NÃO contam para esse mínimo.\n"
    "- Estrutura obrigatória da sessão: Liberação Miofascial → Mobilidade → Ativação → Fortalecimento.\n"
    "- Em treinos de membros inferiores: incluir core. "
    "Em treinos de membros superiores: incluir estabilidade escapular.\n\n"
    "JUSTIFICATIVA OBRIGATÓRIA: na seção '## Metodologia do Treino', explique sempre "
    "qual divisão foi escolhida ou seguida e por quê, com base nos dados do aluno "
    "(frequência semanal, nível de condicionamento e objetivo principal).\n"
)
```

---

## Mudança 3 — `src/interface/app.py`

Atualizar os dois labels compostos no `st.multiselect`:

| Label anterior | Novo label |
|---|---|
| `Superior Anterior / Inferior Anterior (Corpo todo)` | `Cadeia Anterior (Corpo todo) · Peito + Tríceps + Ombros + Quadríceps` |
| `Superior Posterior / Inferior Posterior (Corpo todo)` | `Cadeia Posterior (Corpo todo) · Dorsal + Bíceps + Post. Coxa + Panturrilha` |

Os demais 8 labels permanecem inalterados.

---

## Mudança 4 — Spec e plano anteriores (2026-03-30)

Atualizar `docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md` e
`docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md` para refletir:
- Novos labels das duas opções compostas
- Conteúdo atualizado de `_DIVISAO_TREINO_RB` com explicação das cadeias

---

## Arquivos modificados

| Arquivo | Tipo de mudança |
|---|---|
| `src/generation/metodologia.txt` | Clarificar seção 4 — preparação ≠ fortalecimento |
| `src/generation/prompt.py` | Atualizar `_INSTRUCAO_BASE`, bloco do catálogo e `_DIVISAO_TREINO_RB` |
| `src/interface/app.py` | Atualizar 2 labels do multiselect |
| `docs/superpowers/specs/2026-03-30-divisao-treino-metodo-rb-design.md` | Atualizar labels e `_DIVISAO_TREINO_RB` |
| `docs/superpowers/plans/2026-03-30-divisao-treino-metodo-rb.md` | Atualizar labels e código da constante |
| `tests/test_prompt.py` | Atualizar/criar testes para nova regra de contagem e nova constante |
| `tests/test_interface.py` | Atualizar testes com novos labels |

---

## Critérios de aceite

- [ ] `metodologia.txt` deixa claro que o mínimo de 12 é só para Fortalecimento
- [ ] `_INSTRUCAO_BASE` diz explicitamente que liberação, mobilidade e ativação NÃO contam para o mínimo
- [ ] Bloco do catálogo em `montar_prompt()` alinhado com a mesma regra
- [ ] `_DIVISAO_TREINO_RB` descreve Cadeia Anterior e Cadeia Posterior com músculos listados
- [ ] Formulário exibe os dois novos labels compostos com músculos listados
- [ ] Testes existentes de divisão atualizados para os novos labels
- [ ] Todos os testes da suite passando
