# Design: Protocolo Periodizado com Método RB

**Data**: 2026-03-25
**Branch alvo**: `feat/protocolo-periodizado-metodo-rb`
**Arquivos afetados**: `src/generation/metodologia.txt`, `src/generation/prompt.py`, `src/interface/app.py`

---

## Contexto e Motivação

O sistema Jarvis atualmente gera treinos com problemas estruturais:
1. O LLM retorna poucos exercícios por sessão (instrução diz "6-8", Método RB requer 12-15)
2. As citações aparecem inline no texto, poluindo a leitura
3. O sistema não gera protocolos periodizados — apenas sessões avulsas
4. A busca semântica retorna apenas 5 resultados com máximo 2 por fonte — fontes insuficientes
5. A metodologia no `metodologia.txt` não incorpora o guia de decisão operacional do Método RB

---

## Escopo da Solução

Quatro mudanças coordenadas em três arquivos, sem criação de novos arquivos ou dependências.

---

## 1. Metodologia Consolidada (`src/generation/metodologia.txt`)

### O que muda
Substituição completa do arquivo por uma versão fundida em duas partes:

**Parte 1 — Filosofia e Princípios** (base do manual atual):
- Três pilares: individualização, integração, progressão
- Função primária das articulações (Região → Função: Pé→Estabilidade, Tornozelo→Mobilidade, Joelho→Estabilidade, Quadril→Mobilidade, Lombar→Estabilidade, Torácica→Mobilidade, Escápula→Estabilidade, Ombro→Mobilidade)
- Raciocínio de compensação (falta mobilidade → compensação; falta estabilidade → sobrecarga)
- Protocolos de reabilitação por região (joelho, lombar, ombro, pé/fascite, canelite)

**Parte 2 — Guia de Decisão Operacional** (material novo do Método RB):
- Fluxograma de 13 etapas: triagem → avaliação de movimento → identificação de prioridade → classificação do aluno → definição do objetivo → análise da rotina → definição da estrutura → montagem da sessão → seleção dos exercícios → definição do método → controle de carga → ajuste final → acompanhamento
- Distribuição inteligente da sessão por nível: iniciante (50% preparação / 50% força), intermediário (30/70), avançado (10-20% / 80-90%)
- Controle de fadiga e gestão de interferência entre capacidades
- Critérios de progressão (bilateral→unilateral, máquina→livre, estável→instável) e regressão (dor, perda de padrão, instabilidade)
- Checklists operacionais: antes de montar, definição da estrutura, montagem, escolha dos exercícios, intensidade/volume, método de treino, verificação final

### Por que
O LLM precisa do raciocínio decisório explícito para selecionar exercícios e estruturar sessões com inteligência. O arquivo atual contém apenas prosa descritiva; o novo contém o processo de tomada de decisão que guia a prescrição.

### Critério de aceitação verificável
O novo `metodologia.txt` deve conter: (a) as 13 etapas do fluxograma numeradas, (b) a tabela de função articular, (c) os checklists operacionais (antes/durante/após).

---

## 2. Template de Saída e Instruções do Prompt (`src/generation/prompt.py`)

### O que muda

**Instrução base do sistema** — 4 ajustes:
- Remove: `"Cite a fonte após cada afirmação relevante."` → citações vão apenas ao final
- Remove: instrução de perguntar sobre divisão muscular antes de gerar → o sistema gera o protocolo completo diretamente
- Adiciona: instrução de sempre gerar protocolo periodizado completo (N semanas adaptado ao contexto do aluno, conforme periodização do Método RB: iniciante tipicamente 4 semanas, intermediário/avançado 5 semanas)
- Adiciona: cada exercício de força deve incluir o método no formato `Exercício — séries×reps (método, ex: bi-set com Exercício Y)`

**Instrução do catálogo de exercícios** — 1 ajuste:
- Substitui: `"60 min comporta tipicamente 6 a 8 exercícios"` → `"Cada sessão deve ter 12 a 15 exercícios no total: 2-3 liberações + 3-4 mobilidades + 3-4 ativações + 5-7 força"`

**Novo template de saída obrigatório** — os marcadores `## SEMANA N` são delimitadores parseáveis pela interface:

```
## Resumo do Aluno
[Síntese: nome, idade, modalidade, objetivo, nível, restrições, dias/semana, tempo/sessão]

## Metodologia do Treino
[Raciocínio clínico aplicado a este aluno: divisão escolhida, calibragem de volume/intensidade,
considerações sobre restrições físicas. Sem citações inline.]

## SEMANA 1 — [nome descritivo, ex: Adaptação e Técnica]
### Dia 1 — [foco do dia]
**Liberação** (se necessário)
- [exercício — duração/séries]

**Mobilidade** (se necessário)
- [exercício — séries×reps]

**Ativação**
- [exercício — séries×reps]

**Fortalecimento**
- [exercício — séries×reps (método, ex: bi-set com Exercício Y)]

### Dia 2 — [foco do dia]
...

## SEMANA 2 — [nome descritivo]
...

## Fontes Consultadas
[lista numerada: [N] Fonte, p. X — trecho relevante]
```

### Por que
O template estruturado com marcadores `## SEMANA N` permite parsing confiável na interface sem exigir JSON. A remoção das citações inline melhora a legibilidade do plano. O aumento do volume de exercícios alinha com o Método RB.

---

## 3. Interface com Abas por Semana (`src/interface/app.py`)

### O que muda

**Mecanismo de follow-up**: preservado sem alteração. A remoção da instrução de perguntar sobre divisão muscular reduz a frequência de follow-up, mas o mecanismo permanece útil para outras clarificações que o LLM possa solicitar.

**Nova função utilitária** `_parsear_semanas(texto: str) -> dict`:
- Usa regex `re.split(r'(?=^## SEMANA \d+)', texto, flags=re.MULTILINE)` para detectar marcadores
- **Cabeçalho**: tudo antes da primeira ocorrência de `## SEMANA N` (inclui `## Resumo do Aluno` e `## Metodologia do Treino`)
- **Semanas**: cada bloco iniciado por `## SEMANA N` e terminado pelo início do próximo `## SEMANA N`, por `## Fontes Consultadas`, ou EOF
- **Fontes**: conteúdo a partir de `## Fontes Consultadas` até o EOF; se não houver este marcador, string vazia
- Retorna `dict` com três chaves: `"cabecalho": str`, `"semanas": list[tuple[str, str]]` onde cada tuple é `(nome_completo_da_secao, conteudo)`, `"fontes": str`

**Renderização no estado `resposta`**:
- Exibe `cabecalho` acima das abas (markdown)
- Cria `st.tabs()` dinâmico: uma aba por item em `semanas`, label = nome completo da seção (ex: "SEMANA 1 — Adaptação e Técnica")
- Exibe `fontes` abaixo das abas substituindo o bloco atual de "Fontes consultadas"
- **Fallback**: se `len(semanas) == 0`, exibe `texto` inteiro como hoje (bloco único) — sem quebrar fluxo existente

**Sem mudanças** em: formulário de anamnese, estados, follow-up, botões de navegação.

### Por que
O fallback garante que uma resposta mal formatada do LLM não quebre a interface. O parsing é feito no Streamlit, sem chamada adicional ao LLM.

---

## 4. Aumento do Retrieval (`src/interface/app.py`)

### O que muda
Na chamada `searcher.buscar(historico[0]["content"])` em `app.py` (estado `resposta`), passar os parâmetros explicitamente:

```python
# antes (mantendo o argumento posicional atual, apenas acrescentando parâmetros nomeados)
resultados = searcher.buscar(historico[0]["content"])

# depois
resultados = searcher.buscar(historico[0]["content"], top_k=10, max_por_fonte=3)
```

**Não alterar** os valores default em `searcher.py` — a mudança é local a esta chamada, preservando o comportamento padrão para outros usos futuros do `SemanticSearcher`.

### Risco: limite de contexto do LLM
A combinação de metodologia expandida + 10 referências + saída de 4-5 semanas aumenta o uso de tokens. O Llama 3.1 70B via NVIDIA NIM suporta 128K tokens de contexto — suficiente para este volume. Mitigação: o `metodologia.txt` novo deve ser estruturado e conciso (não verboso). Se o LLM truncar a resposta, o fallback da interface exibe o texto parcial como bloco único sem quebrar.

### Por que
Com `top_k=5` e `max_por_fonte=2`, a geração tem no máximo 5 chunks de no máximo 2-3 fontes. Aumentar para `top_k=10, max_por_fonte=3` enriquece o embasamento científico. A mudança é local (não afeta o default do `SemanticSearcher`).

---

## Arquivos Modificados

| Arquivo | Tipo de Mudança |
|---|---|
| `src/generation/metodologia.txt` | Substituição completa — fusão dos dois materiais do Método RB |
| `src/generation/prompt.py` | Novo template de saída + ajustes nas instruções do sistema |
| `src/interface/app.py` | `_parsear_semanas()` + `st.tabs()` dinâmico + `top_k=10` explícito |

Nenhum arquivo novo. Nenhuma dependência nova. Nenhuma mudança de arquitetura.

---

## Critérios de Aceitação

- [ ] O novo `metodologia.txt` contém as 13 etapas do fluxograma numeradas, a tabela de função articular e os checklists operacionais
- [ ] O LLM gera protocolos com 4 semanas (iniciante) ou 5 semanas (intermediário/avançado)
- [ ] Cada semana aparece em uma aba separada na interface
- [ ] Cada sessão contém 12-15 exercícios seguindo os 4 pilares do Método RB
- [ ] Cada exercício de força inclui o método no formato `Exercício — séries×reps (método)` — verificável por inspeção manual da saída gerada (padrão esperado: `r'.+ — \d+x\d+ \(.+\)'`)
- [ ] Citações aparecem apenas na seção `## Fontes Consultadas`, não inline
- [ ] A interface não quebra se o LLM não seguir o formato de marcadores (fallback ativo)
- [ ] A busca semântica retorna até 10 resultados com no máximo 3 por fonte
- [ ] O mecanismo de follow-up existente continua funcional

---

## Fora de Escopo

- Mudança na lógica de filtragem do catálogo de exercícios
- Alteração dos estados da interface (anamnese / pergunta / resposta)
- Mudança no modelo LLM ou na API NVIDIA NIM
- Criação de novos arquivos de configuração
- Alteração dos valores default de `top_k` e `max_por_fonte` em `searcher.py`
