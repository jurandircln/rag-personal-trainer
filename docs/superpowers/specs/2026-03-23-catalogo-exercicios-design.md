# Spec: Catálogo de Exercícios + Justificativa Personalizada

**Data:** 2026-03-23
**Status:** Aprovado
**Autor:** Jurandir Neto

---

## Problema

O agente Jarvis comete erros na composição do treino porque não tem acesso a um catálogo estruturado de exercícios. Ele escolhe movimentos sem considerar:

- Nível do aluno (iniciante → priorizar máquinas; avançado → pode usar peso livre)
- Equipamentos disponíveis (treino em casa → peso corporal e halteres)
- Contraindicações físicas (ex: dor no joelho → substituir exercícios que agravam)

Além disso, o resumo entregue ao personal trainer é genérico e não explica o raciocínio por trás das escolhas feitas para aquele aluno específico.

---

## Solução

Abordagem híbrida (C): o código filtra o catálogo por equipamento e nível; o LLM decide os detalhes de substituição para restrições e gera a justificativa.

### Fluxo

```
[Contexto do aluno: nível, equipamentos, restrições]
       │
       ▼
CatalogoExercicios.filtrar(equipamentos, nivel, restricoes)
       │ → tabela markdown filtrada com flags [PRIORIZAR] e [SUBSTITUTO OBRIGATÓRIO]
       ▼
montar_prompt(query, resultados_qdrant, metodologia, contexto_aluno, catalogo_filtrado)
       │
       ▼
LLM → resposta com Justificativa Personalizada
```

---

## Arquivos Afetados

| Arquivo | Ação |
|---|---|
| `data/raw/reference.md` | Reescrever como tabela Markdown real (o arquivo atual é um DOCX com extensão errada) |
| `src/generation/catalogo.py` | Novo módulo com classe `CatalogoExercicios` |
| `src/generation/prompt.py` | Nova seção `[CATÁLOGO DE EXERCÍCIOS]` + nova seção no `_TEMPLATE_SAIDA` |
| `src/generation/llm.py` | Carregar e filtrar catálogo antes de montar o prompt |
| `src/interface/app.py` | Passar equipamentos, nível e restrições para o `RAGGenerator` |
| `tests/test_catalogo.py` | Novos testes para o módulo de catálogo |

---

## Módulo `CatalogoExercicios` (`src/generation/catalogo.py`)

### Estrutura do `data/raw/reference.md`

O arquivo será organizado por grupo muscular como headers `##`, com tabela de 5 colunas:

```markdown
## Tronco e Core

| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |
|---|---|---|---|---|
| Prancha Abdominal | Transverso do abdome, Reto abd. | Deadbug, Prancha Lateral | Dor lombar aguda (se o quadril "cair"). | Peso Corporal |
| Abdominal Supra (Crunch) | Reto Abdominal | Abdominal na Máquina, Hollow Body | Protusões discais cervicais (evitar puxar o pescoço). | Peso Corporal |
```

**Tags de equipamento válidas:** `Peso Corporal`, `Peso Livre`, `Máquina`, `Elástico`

### Classe `CatalogoExercicios`

```python
class CatalogoExercicios:
    def __init__(self, caminho: str) -> None: ...

    def filtrar(
        self,
        equipamentos: list[str],
        nivel: str,           # "Iniciante" | "Intermediário" | "Avançado"
        restricoes: str,      # texto livre do campo "Lesões ou restrições"
    ) -> str: ...             # tabela markdown filtrada
```

### Regras de Filtragem (Python — determinísticas)

1. **Filtro de equipamento:** mantém apenas exercícios cuja `Tag de Equipamento` está presente na lista `equipamentos` do aluno.
2. **Sinalização de nível:**
   - Iniciante → marca exercícios `Máquina` com `[PRIORIZAR]`
   - Avançado sem restrições → marca exercícios `Peso Livre` com `[PRIORIZAR]`
   - Intermediário → sem marcação de prioridade
3. **Detecção de contraindicação:** cruza palavras-chave do campo `restricoes` com a coluna `Contraindicações / Alertas` (case-insensitive). Quando há correspondência:
   - Remove o exercício contraindicated da tabela
   - Inclui os exercícios da coluna `Substitutos` com flag `[SUBSTITUTO OBRIGATÓRIO]`
4. Retorna a tabela filtrada como string Markdown.

---

## Mudanças em `prompt.py`

### Nova seção `[CATÁLOGO DE EXERCÍCIOS]`

Inserida entre `[METODOLOGIA]` e `REFERÊNCIAS`. Injetada apenas quando o catálogo filtrado não for vazio:

```
[CATÁLOGO DE EXERCÍCIOS — usar para selecionar movimentos do plano]
Regras obrigatórias:
- Use SOMENTE exercícios presentes nesta tabela filtrada.
- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.
- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício
  original. Nunca sugira o exercício original quando houver substituto marcado.
<tabela filtrada>
```

### Mudança no `_TEMPLATE_SAIDA`

Adicionar seção **"Justificativa Personalizada"** após o Plano de Treino:

```
## Justificativa Personalizada
[Para cada decisão relevante: explique ao personal trainer por que aquele exercício
foi escolhido para ESTE aluno — nível, restrição física, equipamento disponível,
objetivo. Use linguagem direta e técnica. Ex: "O Hack Squat na máquina foi escolhido
no lugar do agachamento livre pois João é iniciante e relatou dor anterior no joelho,
contraindicando carga axial livre nos joelhos neste momento."]
```

---

## Mudanças em `llm.py`

`RAGGenerator.__init__` carrega o `CatalogoExercicios` uma única vez (assim como a metodologia).

`RAGGenerator.gerar` recebe os novos parâmetros `equipamentos: list[str]`, `nivel: str`, `restricoes: str` e aplica `catalogo.filtrar(...)` antes de chamar `montar_prompt`.

**Assinatura atualizada:**

```python
def gerar(
    self,
    query: str,
    resultados: list[ResultadoBusca],
    contexto_aluno: str = "",
    equipamentos: list[str] | None = None,
    nivel: str = "",
    restricoes: str = "",
) -> RespostaRAG: ...
```

---

## Mudanças em `app.py`

`carregar_componentes()` continua igual. A chamada a `generator.gerar(...)` no estado `resposta` passa os novos campos extraídos do `session_state["dados_aluno"]`.

Para isso, `app.py` precisa manter `dados_aluno` no `session_state` além do `contexto_aluno` em texto — os campos `equipamentos`, `nivel` e `restricoes` precisam estar acessíveis como valores estruturados (não apenas como string formatada).

---

## Testes (`tests/test_catalogo.py`)

Cenários obrigatórios:
- Filtragem por equipamento: exercícios com tag ausente na lista são removidos
- Priorização iniciante: exercícios `Máquina` recebem flag `[PRIORIZAR]`
- Priorização avançado: exercícios `Peso Livre` recebem flag `[PRIORIZAR]`
- Contraindicação detectada: exercício é removido e substituto aparece com `[SUBSTITUTO OBRIGATÓRIO]`
- Catálogo vazio após filtro: retorna string vazia sem erros
- Arquivo não encontrado: lança `FileNotFoundError` com mensagem clara

---

## Restrições e Decisões

- O catálogo não é indexado no Qdrant — é acessado diretamente como arquivo `.md` em disco.
- A filtragem é puramente Python (sem LLM). O LLM só decide dentro do conjunto já filtrado.
- O `RAGGenerator` não quebra retrocompatibilidade: os novos parâmetros são opcionais com defaults.
- Comentários de código em português (pt-BR), conforme convenção do projeto.
