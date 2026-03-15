# /finalizar-tarefa

Finaliza a tarefa atual: verifica qualidade, realiza commit e opcionalmente abre PR.

## Uso

```
/finalizar-tarefa
```

## Passos

### 1. Verificar estado do repositório

Execute e analise:

```bash
git status
git diff --stat
```

Identifique arquivos que **não devem** ser commitados:
- `.env` ou qualquer arquivo com credenciais
- Arquivos de cache (`__pycache__/`, `*.pyc`)
- Arquivos temporários não rastreados pelo `.gitignore`

Se encontrar `.env` no diff, **pare imediatamente** e alerte o dev.

### 2. Checklist de qualidade

Verifique cada item antes de prosseguir:

- [ ] **Comentários em PT-BR?** — nenhum comentário ou docstring em inglês
- [ ] **Testes presentes?** — toda função não-trivial tem teste correspondente
- [ ] **Sem `print()` de debug?** — remover antes de commitar
- [ ] **Sem `.env` no diff?** — segredos nunca vão para o repositório
- [ ] **Nomenclatura correta?** — snake_case para arquivos/variáveis, PascalCase para classes

Reporte o resultado do checklist. Se houver falhas, liste-as e pergunte se o dev quer corrigir antes de continuar.

### 3. Propor mensagem de commit

Siga o formato Conventional Commits:

```
<tipo>(<escopo>): <descrição curta em português>

[corpo opcional — o quê e por quê, não o como]

[rodapé opcional — referências, breaking changes]
```

Tipos válidos: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`

Exemplo:
```
feat(ingestion): adicionar carregador de documentos PDF

Implementa a função carregar_documento() no módulo ingestion/
usando PyMuPDF para extrair texto de PDFs com metadados preservados.
```

Apresente a mensagem proposta e **aguarde aprovação** do dev antes de commitar.

### 4. Executar commit

Após aprovação:

```bash
git add <arquivos específicos>
git commit -m "<mensagem aprovada>"
```

Nunca usar `git add .` ou `git add -A` sem verificar o conteúdo primeiro.

### 5. Perguntar sobre push e PR

Após o commit, pergunte:

```
O que fazer agora?

  [sim]  — push + abrir PR no GitHub
  [push] — só push (sem PR ainda)
  [não]  — manter apenas local
```

### 6. Se PR: exibir template de descrição

Se o dev escolher `sim`, carregue o `GH_TOKEN` do `.env` antes de executar o comando:

```bash
export GH_TOKEN=$(grep -oP '(?<=GH_TOKEN=)\S+' .env 2>/dev/null || echo "")
```

Se `GH_TOKEN` estiver vazio ou o `.env` não existir, **alerte o dev** com a mensagem:
> "GH_TOKEN não encontrado no .env. Configure o token em https://github.com/settings/tokens e adicione GH_TOKEN=<seu_token> ao .env antes de continuar."

Caso contrário, gere o comando `gh pr create` com o template:

```markdown
## O que foi feito

<descrição clara do que foi implementado>

## Por que

<motivação — problema resolvido ou feature adicionada>

## Checklist

- [ ] Comentários em português (pt-BR)
- [ ] Testes adicionados/atualizados
- [ ] Documentos SDD consultados antes de implementar
- [ ] Sem `.env` ou segredos no diff
- [ ] Sem `print()` de debug
- [ ] Nomenclatura seguindo as convenções do projeto

## Contexto adicional

<links, screenshots, referências relevantes>
```

Execute `gh pr create` com título e corpo gerados, aguardando confirmação final.
