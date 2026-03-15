# /nova-tarefa

Inicia uma nova tarefa de desenvolvimento seguindo o workflow do projeto Jarvis.

## Uso

```
/nova-tarefa <descrição da tarefa>
```

## Passos

### 1. Classificar o tipo de tarefa

Com base na descrição fornecida, determine o tipo:

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade para o usuário |
| `fix` | Correção de bug |
| `docs` | Documentação apenas |
| `chore` | Manutenção, dependências, configuração |
| `refactor` | Reestruturação sem mudança de comportamento |
| `test` | Adição ou correção de testes |

Apresente o tipo sugerido e confirme com o dev antes de continuar.

### 2. Propor nome de branch

Siga o padrão: `<tipo>/<descricao-em-ingles-com-hifens>`

Exemplos:
- `feat/pdf-document-loader`
- `fix/qdrant-connection-timeout`
- `chore/update-langchain-dependency`

Apresente a branch sugerida e aguarde confirmação.

### 3. Criar a branch

Após confirmação, execute:

```bash
git checkout -b <branch>
```

### 4. Indicar contexto SDD a ler

Com base no tipo de tarefa, indique quais documentos ler **antes** de implementar:

| Tipo | Documentos obrigatórios |
|---|---|
| `feat` | `docs/product-context/` (regras de negócio, glossário) + `docs/technical-context/` (ADRs, stack) |
| `fix` | `docs/technical-context/` (stack, módulo afetado) |
| `docs` | `docs/business-context/` (contexto do que está documentando) |
| `chore` | `docs/technical-context/` (ADRs antes de mudar dependência ou config) |
| `refactor` | `docs/technical-context/` (ADRs) + `docs/product-context/` (glossário) |
| `test` | `docs/technical-context/` (módulo testado) |

### 5. Exibir resumo

Ao final, exiba:

```
✓ Nova tarefa iniciada

Tarefa  : <descrição>
Tipo    : <tipo>
Branch  : <nome-da-branch>
Módulo  : <módulo(s) do src/ envolvido(s)>
SDD     : <documentos a ler antes de implementar>

Próximo passo: leia os documentos SDD indicados antes de escrever qualquer código.
```
