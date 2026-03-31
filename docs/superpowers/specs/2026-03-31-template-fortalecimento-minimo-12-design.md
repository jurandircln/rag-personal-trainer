# Design: Ancoragem do Mínimo de 12 Exercícios no Template de Fortalecimento

**Data:** 2026-03-31
**Branch:** feat/melhorias-formulario-anamnese

---

## Contexto

As instruções no prompt (`_INSTRUCAO_BASE` e bloco do catálogo) já informam que o mínimo de 12 exercícios se aplica exclusivamente à seção Fortalecimento. Mesmo assim, o LLM continua retornando entre 6 e 8 exercícios nessa seção.

O problema raiz é que LLMs seguem a estrutura do template mais fielmente do que instruções em prosa. O `_TEMPLATE_SAIDA` atual mostra apenas 2 grupos musculares com 1 exercício cada na seção Fortalecimento — o LLM ancora seu comportamento nesse exemplo mínimo.

---

## Solução: Abordagem C (Template expandido + nota inline)

Dois ajustes no `_TEMPLATE_SAIDA` em `src/generation/prompt.py`:

### Mudança 1 — Nota de contagem inline no cabeçalho de `### Fortalecimento`

Adicionar uma linha de aviso imediatamente abaixo do header `### Fortalecimento` em **Dia 1 e Dia 2** do template:

```
### Fortalecimento
[MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção — Liberação, Mobilidade e Ativação NÃO contam. Adicione mais grupos musculares se necessário antes de fechar este dia.]
```

Essa nota é um gatilho contextual: aparece exatamente no ponto em que o LLM começa a gerar a seção de fortalecimento.

### Mudança 2 — Expandir o exemplo de Fortalecimento para 14 exercícios

O template atual mostra:
- 1 músculo grande (1 exercício)
- 1 músculo pequeno (1 exercício)

O novo template mostrará:
- 2 músculos grandes (4 exercícios cada = 8)
- 2 músculos pequenos (3 exercícios cada = 6)
- Total: **14 exercícios** — ancora o LLM acima do mínimo de 12

Estrutura expandida para cada dia do template:

```markdown
### Fortalecimento
[MÍNIMO OBRIGATÓRIO: 12 exercícios nesta seção — Liberação, Mobilidade e Ativação NÃO contam. Adicione mais grupos musculares se necessário antes de fechar este dia.]

#### [Músculo Grande, ex: Peitoral]

- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Grande, ex: Dorsal]

- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Tríceps]

- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Bíceps]

- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
- [nome do exercício]
  [N séries × N–N reps (método)]
```

---

## Arquivo modificado

| Arquivo | Tipo de mudança |
|---|---|
| `src/generation/prompt.py` | Atualizar `_TEMPLATE_SAIDA`: nota inline + expansão do Fortalecimento em Dia 1 e Dia 2 |

---

## Critérios de aceite

- [ ] `_TEMPLATE_SAIDA` exibe nota `[MÍNIMO OBRIGATÓRIO: 12 exercícios...]` abaixo de cada `### Fortalecimento`
- [ ] Dia 1 do template mostra 4 grupos musculares com exercícios múltiplos (≥14 no total)
- [ ] Dia 2 do template tem a mesma estrutura expandida
- [ ] Todos os testes existentes continuam passando após a mudança
