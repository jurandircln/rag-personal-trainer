# Design: Melhorias no Formulário de Anamnese e Template do LLM

**Data:** 2026-03-27
**Branch:** feat/volume-layout-catalogo-tempo

---

## Contexto

Este spec cobre três melhorias relacionadas à qualidade dos insumos coletados do personal trainer e à consistência do treino gerado pelo LLM.

---

## Mudança 1 — Liberação Miofascial e Mobilidade obrigatórias

**Arquivo:** `src/generation/prompt.py`

**Problema:** As seções `### Liberação Miofascial (Opcional)` e `### Mobilidade (Opcional)` no `_TEMPLATE_SAIDA` sinalizam ao LLM que pode omiti-las, gerando treinos inconsistentes.

**Solução:** Remover `(Opcional)` de todos os headers dessas seções no template. O LLM passa a tratá-las como obrigatórias, igual a Ativação e Fortalecimento.

**Ocorrências a alterar:** Dia 1 e Dia 2 (e qualquer dia adicional no template).

```
Antes: ### Liberação Miofascial (Opcional)
Depois: ### Liberação Miofascial

Antes: ### Mobilidade (Opcional)
Depois: ### Mobilidade
```

**Impacto:** Nenhuma mudança em lógica de parsing ou geração — apenas comportamento do LLM ao seguir o template.

---

## Mudança 2 — Campo de divisão de treino no formulário

**Arquivo:** `src/interface/app.py`

**Problema:** O formulário de anamnese não coleta a preferência de divisão muscular, forçando o agente a inferir ou ignorar esse aspecto importante do treino.

**Solução:** Adicionar campo `st.multiselect` com as opções:

- `"Deixar o agente decidir"` (default)
- `"Fullbody"`
- `"Superior / Inferior"`
- `"Anterior / Posterior"`

**Posicionamento:** Após `Nível de condicionamento` (col4), antes de `Equipamentos disponíveis`.

**Comportamento:**
- Default: `["Deixar o agente decidir"]`
- Se apenas "Deixar o agente decidir" selecionado → campo **omitido** do contexto enviado ao LLM
- Se outras opções selecionadas → incluir no contexto: `Divisão de treino preferida: Fullbody, Superior / Inferior`

**Alterações necessárias:**
1. Novo `st.multiselect` no `st.form("form_anamnese")`
2. Atualizar o dicionário `dados` para incluir o campo
3. Atualizar `formatar_contexto_aluno()` para renderizar a linha condicionalmente

---

## Mudança 3 — Label e placeholder do campo de texto livre

**Arquivo:** `src/interface/app.py` — ESTADO 2 (Pergunta)

**Problema:** O label "Sua pergunta:" não reflete bem o uso real do campo, que recebe tanto perguntas quanto contexto adicional e customizações de treino.

**Solução:**

**Label:**
```
Antes: "Sua pergunta:"
Depois: "Adicione mais informações (opcional)"
```

**Placeholder:**
```
Ex.: "Prefiro exercícios compostos no início. Evitar agachamento por limitação de tornozelo."
     "Aluno ex-atleta de natação — priorizar mobilidade de ombro e volume de costas."
     "Monte o treino com progressão de carga semana a semana."
```

**Validação:** Nenhuma mudança — o campo já é opcional na lógica atual.

---

## Arquivos modificados

| Arquivo | Tipo de mudança |
|---|---|
| `src/generation/prompt.py` | Remover `(Opcional)` de headers no `_TEMPLATE_SAIDA` |
| `src/interface/app.py` | Novo campo multiselect + atualização de label/placeholder |

---

## Critérios de aceite

- [ ] Treinos gerados sempre incluem seções Liberação Miofascial e Mobilidade
- [ ] Formulário exibe campo de divisão de treino com as 4 opções corretas
- [ ] Quando "Deixar o agente decidir" é a única seleção, o campo não aparece no contexto do LLM
- [ ] Quando outras opções são selecionadas, o contexto inclui `Divisão de treino preferida: ...`
- [ ] Label do campo de texto livre exibe "Adicione mais informações (opcional)"
- [ ] Placeholder do campo exibe os 3 exemplos definidos
