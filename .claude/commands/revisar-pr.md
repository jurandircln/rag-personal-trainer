# /revisar-pr

Revisão estruturada de código antes de abrir ou mergear um PR.

## Uso

```
/revisar-pr [branch-base]
```

Se `branch-base` não for informado, usa `main`.

## Passos

### 1. Coletar o diff

```bash
git diff <branch-base>...HEAD
git log <branch-base>...HEAD --oneline
```

Analise todos os arquivos modificados, adicionados e removidos.

### 2. Classificar issues encontradas

#### BLOQUEADOR — impede o merge

- Comentário ou docstring em inglês (viola regra obrigatória do projeto)
- `.env` ou qualquer arquivo com credencial no diff
- Segredo ou API key exposta em qualquer arquivo
- Código não-trivial sem testes correspondentes
- Violação de business rules documentadas em `docs/product-context/`
- Decisão arquitetural que contradiz um ADR em `docs/technical-context/`

#### AVISO — deve ser corrigido antes do merge, mas não bloqueia sozinho

- Mensagem de commit fora do formato Conventional Commits
- Nomenclatura de arquivo, variável ou classe fora das convenções
- Nome de branch fora do padrão `<tipo>/<descricao-em-ingles>`
- `print()` de debug deixado no código
- TODO sem referência a issue ou contexto

#### SUGESTÃO — melhoria desejável, não obrigatória

- Docstring ausente em função pública
- Função muito longa (> 50 linhas) que poderia ser dividida
- Import não utilizado
- Constante hardcoded que poderia ser configurável

### 3. Gerar relatório formatado

```
═══════════════════════════════════════
  REVISÃO DE PR — Jarvis Personal Trainer
  Branch : <branch atual>
  Base   : <branch-base>
  Commits: <n>
═══════════════════════════════════════

BLOQUEADORES (<n>)
──────────────────
[BL-1] <arquivo>:<linha> — <descrição do problema>
...

AVISOS (<n>)
─────────────
[AV-1] <arquivo>:<linha> — <descrição>
...

SUGESTÕES (<n>)
────────────────
[SG-1] <arquivo>:<linha> — <descrição>
...

═══════════════════════════════════════
VEREDICTO: REPROVADO | APROVADO
═══════════════════════════════════════
```

### 4. Se bloqueadores existirem

Pergunte:

```
Encontrei X bloqueador(es). Quer que eu corrija agora, um por um?
```

Se sim, corrija cada bloqueador sequencialmente, mostrando a alteração antes de aplicar.

### 5. Se aprovado

Sugira o próximo passo:

```
PR aprovado para merge. Execute /finalizar-tarefa para commitar e abrir o PR.
```

---

> **Nota:** Se você tiver o plugin Superpowers instalado, o skill `requesting-code-review`
> oferece revisão via subagente dedicado — mais profunda para PRs críticos ou com muitos
> arquivos alterados.
