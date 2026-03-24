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

Abordagem híbrida: o código filtra o catálogo por equipamento e nível (determinístico); o LLM decide os detalhes de substituição para restrições e gera a justificativa personalizada.

### Fluxo

```
[Contexto do aluno: nível, equipamentos, restrições]
       │
       ▼
CatalogoExercicios.filtrar(equipamentos, nivel, restricoes)
       │ → tabela markdown filtrada com flags [PRIORIZAR] e [SUBSTITUTO OBRIGATÓRIO]
       │   (ou None se nenhum exercício passar)
       ▼
montar_prompt(query, resultados_qdrant, metodologia, contexto_aluno, catalogo_filtrado)
       │
       ▼
LLM → resposta com Justificativa Personalizada (somente quando catálogo presente)
```

---

## Arquivos Afetados

| Arquivo | Ação |
|---|---|
| `data/raw/reference.md` | **Modificar** (sobrescrever conteúdo binário com Markdown válido) — passo manual antes da implementação de código; arquivo existe no repositório mas contém DOCX binário |
| `src/generation/catalogo.py` | **Criar** novo módulo com classe `CatalogoExercicios` |
| `src/generation/prompt.py` | **Modificar**: nova seção `[CATÁLOGO DE EXERCÍCIOS]`; nova seção condicional no `_TEMPLATE_SAIDA`; nova assinatura de `montar_prompt()` |
| `src/generation/llm.py` | **Modificar**: carregar e filtrar catálogo antes de montar prompt; nova assinatura de `gerar()` |
| `src/interface/app.py` | **Modificar**: persistir `dados_aluno` no `session_state`; passar equipamentos, nível e restrições ao `gerar()` |
| `tests/test_catalogo.py` | **Criar** novos testes para o módulo de catálogo |
| `tests/test_interface.py` | **Modificar**: atualizar mocks do `session_state` e da chamada a `gerar()` |
| `tests/test_llm.py` | **Modificar**: adicionar cenário de integração para `gerar()` com os novos parâmetros |

---

## Pré-requisito Manual: Sobrescrever `data/raw/reference.md`

**Responsável:** desenvolvedor, antes de iniciar a implementação de código.

O arquivo `data/raw/reference.md` existe no repositório mas contém conteúdo binário DOCX (verificado pelo cabeçalho ZIP). Deve ser sobrescrito com Markdown válido usando a estrutura abaixo.

Enquanto o arquivo não for convertido, `CatalogoExercicios.__init__` lança `ValueError("Arquivo de catálogo não é texto Markdown válido: <caminho>")` — o `UnicodeDecodeError` ao tentar decodificar o binário como UTF-8 é capturado e relançado como `ValueError`.

### Estrutura do `data/raw/reference.md`

5 colunas, organizado por grupo muscular como headers `##`:

```markdown
## Tronco e Core

| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |
|---|---|---|---|---|
| Prancha Abdominal | Transverso do abdome, Reto abd. | Deadbug, Prancha Lateral | Dor lombar aguda (se o quadril "cair"). | Peso Corporal |
| Abdominal Supra (Crunch) | Reto Abdominal | Abdominal na Máquina, Hollow Body | Protusões discais cervicais (evitar puxar o pescoço). | Peso Corporal |

## Membros Inferiores

| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |
|---|---|---|---|---|
| Agachamento Livre | Quadríceps, Glúteo | Hack Squat na Máquina, Leg Press | Dor aguda no joelho; lombar instável. | Peso Livre |
| Leg Press | Quadríceps, Glúteo | Agachamento na Máquina, Cadeira Extensora | Dor lombar com carga axial. | Máquina |
```

**Tags de equipamento válidas no catálogo:** `Peso Corporal`, `Peso Livre`, `Máquina`, `Elástico`

---

## Módulo `CatalogoExercicios` (`src/generation/catalogo.py`)

### Normalização de Equipamentos

O `st.multiselect` em `app.py` usa valores com plural/variações. O mapeamento é aplicado dentro de `filtrar()`:

| Valor do app.py | Tag normalizada |
|---|---|
| `"Máquinas"` | `"Máquina"` |
| `"Elásticos"` | `"Elástico"` |
| `"Peso Livre"` | `"Peso Livre"` |
| `"Peso Corporal"` | `"Peso Corporal"` |
| `"Sem Equipamento"` | `"Peso Corporal"` (fallback) |

Após o mapeamento: **deduplicar e ordenar** com `sorted(set(...))` para resultado determinístico.

### Classe `CatalogoExercicios`

```python
class CatalogoExercicios:
    def __init__(self, caminho: str) -> None: ...
    # Lança FileNotFoundError se o arquivo não existir.
    # Captura UnicodeDecodeError e relança como ValueError com mensagem clara
    # se o arquivo não for texto UTF-8 válido.

    def filtrar(
        self,
        equipamentos: list[str],  # valores brutos do app.py
        nivel: str,               # "Iniciante" | "Intermediário" | "Avançado"
        restricoes: str,          # texto livre do campo "Lesões ou restrições"
    ) -> str | None: ...
    # Retorna tabela markdown filtrada com flags,
    # ou None se nenhum exercício passar pelos filtros.
```

### Regras de Filtragem — Ordem de Aplicação

**Regra 4 (contraindicação) tem precedência absoluta sobre Regra 3 (prioridade de nível).** Um exercício com `[PRIORIZAR]` é removido se tiver contraindicação ativa.

1. **Normalização de equipamentos:** converte com o mapeamento acima e aplica `sorted(set(...))`.

2. **Filtro de equipamento:** mantém apenas exercícios cuja `Tag de Equipamento` está na lista normalizada. Comparação case-insensitive.

3. **Sinalização de nível** (aplicada após filtro de equipamento, antes da detecção de contraindicação):
   - `"Iniciante"` → marca exercícios com tag `Máquina` com `[PRIORIZAR]`
   - `"Avançado"` → marca exercícios com tag `Peso Livre` com `[PRIORIZAR]`
   - `"Intermediário"` → sem marcação de prioridade (Regra 4 ainda atua normalmente)

4. **Detecção de contraindicação** (todos os níveis; remove mesmo se `[PRIORIZAR]`):
   - **Normalização ASCII:** aplica `unicodedata.normalize('NFKD', restricoes).encode('ascii', 'ignore').decode('ascii')` antes de tokenizar, para que "não" → "nao" e os tokens sejam comparados sem dependência de acentuação.
   - **Tokenização:** split por espaços, lowercase, mantém tokens com **4+ caracteres**, remove o conjunto fixo de stopwords: `{"tenho", "sinto", "tenha", "para", "minha", "meus", "mais", "muito", "pouco", "quando", "pela", "pelo", "com", "nao", "numa", "esse", "esta", "isso", "pois"}`.
   - Para cada exercício ainda na tabela: verifica se algum token está contido na coluna `Contraindicações / Alertas` (substring match, case-insensitive, após mesma normalização ASCII da coluna).
   - **Quando há correspondência:**
     - Remove o exercício (mesmo que marcado com `[PRIORIZAR]`).
     - Obtém os substitutos da coluna `Substitutos` (split por vírgula, strip de espaços).
     - **Os substitutos passam pelo filtro de equipamento** (lista normalizada já calculada). Substitutos com tag indisponível são descartados.
     - **Os substitutos NÃO passam pelo filtro de contraindicação** (v1: assume-se que os substitutos definidos no catálogo já são adequados para as restrições do exercício que substituem).
     - Substitutos elegíveis entram na tabela com flag `[SUBSTITUTO OBRIGATÓRIO]`.
     - Se nenhum substituto for elegível, o exercício é simplesmente removido sem flag.

5. **Retorno:**
   - Retorna a tabela filtrada como string Markdown (headers `##` preservados apenas para grupos com ao menos um exercício).
   - Retorna `None` se nenhum exercício passar pelos filtros.

---

## Mudanças em `prompt.py`

### Nova assinatura de `montar_prompt()`

```python
def montar_prompt(
    query: str,
    resultados: list[ResultadoBusca],
    metodologia: str = "",
    contexto_aluno: str = "",
    catalogo_filtrado: str | None = None,  # None = não injetar seção
) -> str: ...
```

**Distinção importante:** `None` significa "sem catálogo" (omite a seção). `""` nunca é passado — `filtrar()` retorna `None` quando vazio, não `""`.

### Nova seção `[CATÁLOGO DE EXERCÍCIOS]`

Inserida entre `[METODOLOGIA]` e `REFERÊNCIAS`. **Injetada somente quando `catalogo_filtrado is not None`:**

```
[CATÁLOGO DE EXERCÍCIOS — usar para selecionar movimentos do plano]
Regras obrigatórias:
- Use SOMENTE exercícios presentes nesta tabela filtrada.
- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.
- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício
  original. Nunca sugira o exercício original quando houver substituto marcado.
<tabela filtrada>
```

Quando `catalogo_filtrado is not None` mas a tabela ficou vazia (este caso não ocorre com o contrato atual — `filtrar()` retorna `None` quando vazio), a seção injeta aviso: `"Nenhum exercício compatível encontrado. Informe o personal trainer e sugira revisar equipamentos ou restrições."`.

**Guard interno:** `montar_prompt()` trata `catalogo_filtrado == ""` como `None` (converte internamente). Isso protege contra passagem acidental de string vazia pelo chamador.

### Mudança no `_TEMPLATE_SAIDA`

A seção `## Justificativa Personalizada` é **condicional**: adicionada ao template somente quando `catalogo_filtrado is not None`. Implementar com duas constantes:

```python
_TEMPLATE_SAIDA_BASE = """...(Resumo, Metodologia, Plano)..."""

_SECAO_JUSTIFICATIVA = """
## Justificativa Personalizada
[Para cada decisão relevante: explique ao personal trainer por que aquele exercício
foi escolhido para ESTE aluno — nível, restrição física, equipamento disponível,
objetivo. Use linguagem direta e técnica.]
"""
```

Em `montar_prompt()`: quando `catalogo_filtrado is not None`, usa `_TEMPLATE_SAIDA_BASE + _SECAO_JUSTIFICATIVA`; caso contrário, usa apenas `_TEMPLATE_SAIDA_BASE`.

---

## Mudanças em `llm.py`

`RAGGenerator.__init__` carrega o `CatalogoExercicios` uma única vez (assim como a metodologia).

**Nova assinatura de `gerar()`:**

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

Lógica de ativação do catálogo: quando `equipamentos is not None` **e** `nivel != ""`, chama `catalogo.filtrar(equipamentos, nivel, restricoes)` e passa o resultado (que pode ser `str` ou `None`) para `montar_prompt()`. Caso contrário, chama `montar_prompt()` sem o parâmetro `catalogo_filtrado` (retrocompatível — seção omitida).

---

## Mudanças em `app.py`

### Inicialização do `session_state`

```python
if "dados_aluno" not in st.session_state:
    st.session_state["dados_aluno"] = {}
```

### Persistência de `dados_aluno`

No bloco `if enviado:` (após validação de nome/modalidade):

```python
st.session_state["dados_aluno"] = dados  # dicionário estruturado com todos os campos
```

### Chamada ao `generator.gerar` (estado `resposta`)

Os dados estruturados são lidos de `st.session_state["dados_aluno"]` (não de variáveis locais do bloco de anamnese, que não existem no estado `resposta`):

```python
dados_aluno = st.session_state.get("dados_aluno", {})
resposta = generator.gerar(
    query=query_completa,
    resultados=resultados,
    contexto_aluno=st.session_state["contexto_aluno"],
    equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
    nivel=dados_aluno.get("Nível de condicionamento", ""),
    restricoes=dados_aluno.get("Lesões ou restrições", ""),
)
```

O `or None` garante que lista vazia `[]` seja tratada como `None` (sem catálogo), ativando o comportamento retrocompatível.

**Regra de negócio:** se o aluno não selecionar nenhum equipamento no formulário (lista vazia), o catálogo é **desativado** — o sistema opera sem filtro de exercícios, como se o catálogo não existisse. O personal trainer deve instruir o aluno a preencher ao menos um equipamento para ativar a seleção guiada.

A chave `"contexto_aluno"` no `session_state` é **mantida** — continua sendo persistida em paralelo com `"dados_aluno"` para não quebrar o código de exibição existente (linha `st.text(st.session_state["contexto_aluno"])`).

---

## Testes

### `tests/test_catalogo.py` — Criar

| Cenário | Comportamento esperado |
|---|---|
| Tag ausente na lista de equipamentos | Exercício removido |
| Tag presente na lista de equipamentos | Exercício mantido |
| Normalização: `"Máquinas"` (plural) | Exercício com tag `"Máquina"` é mantido |
| Deduplicação: `["Sem Equipamento", "Peso Corporal"]` | Lista normalizada sem duplicata; ordenada deterministicamente |
| Nível iniciante | Exercícios com tag `Máquina` recebem `[PRIORIZAR]` |
| Nível avançado | Exercícios com tag `Peso Livre` recebem `[PRIORIZAR]` |
| Nível intermediário | Sem flag de prioridade; contraindicações ainda atuam |
| Exercício com `[PRIORIZAR]` + contraindicação ativa | Exercício removido; substituto elegível com `[SUBSTITUTO OBRIGATÓRIO]` |
| Contraindicação + substituto sem equipamento disponível | Exercício removido; substituto descartado; sem flag |
| Substituto com contraindicação própria correspondente à restrição do aluno | Substituto é incluído com `[SUBSTITUTO OBRIGATÓRIO]` (v1: substitutos não passam por filtro de contraindicação — comportamento intencional) |
| Nenhum exercício após filtro | Retorna `None` sem erros |
| Arquivo não encontrado | `FileNotFoundError` com mensagem clara |
| Arquivo binário (não UTF-8) | `ValueError` com mensagem clara |

### `tests/test_interface.py` — Modificar

- Adicionar `"dados_aluno"` ao mock do `session_state` com os campos: `"Equipamentos disponíveis": ["Máquinas"]`, `"Nível de condicionamento": "Iniciante"`, `"Lesões ou restrições": ""`.
- Atualizar assertion da chamada a `generator.gerar()` para incluir `equipamentos`, `nivel`, `restricoes`.

### `tests/test_llm.py` — Modificar

Adicionar cenário de integração: `RAGGenerator.gerar(equipamentos=["Máquinas"], nivel="Iniciante", restricoes="dor no joelho")` deve invocar `montar_prompt()` com `catalogo_filtrado` não-`None` — usar mock de `CatalogoExercicios.filtrar` retornando uma string Markdown de exemplo.

---

## Restrições e Decisões

- O catálogo não é indexado no Qdrant — acesso direto como arquivo `.md` em disco.
- A filtragem é puramente Python (sem LLM). O LLM só decide dentro do conjunto já filtrado.
- Matching de contraindicações usa substring simples com normalização ASCII. Falsos negativos são aceitáveis para v1.
- Substitutos **não** passam pelo filtro de contraindicação (v1): assume-se que os substitutos definidos no catálogo são adequados para as restrições do exercício original.
- A regra de contraindicação tem precedência absoluta sobre a sinalização de nível.
- `montar_prompt()` usa `None` (não `""`) como sentinela para "sem catálogo" — evita ambiguidade entre catálogo ausente e catálogo vazio.
- A seção `## Justificativa Personalizada` no output do LLM é condicional — só aparece quando o catálogo está ativo.
- O `RAGGenerator` não quebra retrocompatibilidade: os novos parâmetros são opcionais com defaults que desativam a funcionalidade.
- Comentários de código em português (pt-BR), conforme convenção do projeto.
