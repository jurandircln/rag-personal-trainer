# Spec: Observabilidade com Grafana Cloud + Supabase

**Data:** 2026-04-20
**Status:** Aprovado
**Escopo:** Sistema de métricas de desempenho do LLM com dashboard no Grafana Cloud e feedback do usuário na interface Streamlit

---

## 1. Contexto e Motivação

O Jarvis não possui hoje nenhum mecanismo de observabilidade. Não é possível saber quantas consultas foram realizadas, quanto tempo o LLM leva para responder, nem se os personal trainers estão satisfeitos com as respostas geradas.

Este sistema resolve isso com três partes:
1. **Instrumentação** — captura de tempo de resposta após cada chamada ao LLM
2. **Feedback do usuário** — botões Satisfeito/Não Satisfeito exibidos após cada resposta
3. **Dashboard Grafana** — visualização das métricas em tempo real

---

## 2. Restrições

- O app roda no **Streamlit Cloud free tier**: sem Docker Compose em produção, sem serviços extras, sem portas customizadas
- Métricas precisam ser **empurradas** do app para um serviço externo
- A gravação de métricas é **best-effort**: falhas não afetam a experiência do usuário
- Dados são **estritamente agregados** — sem identificação de aluno, sessão ou conteúdo da consulta
- Credenciais do Supabase ficam nos **Secrets do Streamlit Cloud**, nunca no código-fonte

---

## 3. Arquitetura

```
Streamlit Cloud (app.py)
    │
    ├─ a cada resposta LLM ──► INSERT em jarvis_respostas (Supabase Postgres)
    └─ a cada feedback ──────► INSERT em jarvis_feedbacks (Supabase Postgres)
                                         │
                              Grafana Cloud (data source PostgreSQL)
                                         │
                                   Dashboard com 5 painéis
```

O módulo `src/observability/metrics.py` encapsula toda a lógica de gravação. O `app.py` chama apenas funções de alto nível — sem conhecer detalhes de banco.

---

## 4. Schema do Banco (Supabase)

```sql
-- Registra cada resposta gerada pelo LLM
CREATE TABLE jarvis_respostas (
    id                      BIGSERIAL PRIMARY KEY,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    tempo_resposta_segundos FLOAT NOT NULL
);

-- Registra cada feedback dado pelo usuário
CREATE TABLE jarvis_feedbacks (
    id         BIGSERIAL PRIMARY KEY,
    criado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    satisfeito BOOLEAN NOT NULL
);
```

---

## 5. Módulo de Observabilidade

**Novo subpacote:** `src/observability/`

```
src/observability/
    __init__.py    # exporta registrar_resposta e registrar_feedback
    metrics.py     # lógica de conexão Supabase e inserts
```

### Interface pública

```python
def registrar_resposta(tempo_segundos: float) -> None:
    """Insere uma linha em jarvis_respostas. Falha silenciosa com log warning."""

def registrar_feedback(satisfeito: bool) -> None:
    """Insere uma linha em jarvis_feedbacks. Falha silenciosa com log warning."""
```

### Comportamento de erro

Qualquer exceção na gravação é capturada, logada como `WARNING` e descartada. O app continua normalmente — o usuário nunca vê erros de observabilidade.

### Dependência

`supabase` adicionado ao `requirements.txt`. Conexão inicializada via variáveis de ambiente:
- `SUPABASE_URL`
- `SUPABASE_KEY`

---

## 6. Alterações no `app.py`

### 6a — Captura de tempo de resposta

No estado `resposta`, após a chamada ao gerador (linha ~300), o tempo é medido com `time.perf_counter()` e `registrar_resposta()` é chamado:

```python
import time
from src.observability.metrics import registrar_resposta

inicio = time.perf_counter()
resposta = generator.gerar(...)
registrar_resposta(tempo_segundos=time.perf_counter() - inicio)
```

### 6b — Botões de feedback

Após o assistente exibir uma resposta (última mensagem do histórico com `role == "assistant"`), os botões são renderizados uma única vez por resposta. Um flag `feedback_enviado` no `session_state` impede duplo registro.

```
┌─────────────────────────────────────────┐
│  Como você avalia esta resposta?        │
│  [ 👍 Satisfeito ]  [ 👎 Não Satisfeito ] │
└─────────────────────────────────────────┘
```

Após o clique: botões somem, mensagem `"Obrigado pelo feedback!"` aparece. O flag `feedback_enviado` é marcado como `True` no `session_state`. Na próxima consulta (nova mensagem do usuário), o flag é resetado para `False`.

### 6c — Novos campos no `session_state`

| Campo | Tipo | Valor inicial |
|---|---|---|
| `feedback_enviado` | `bool` | `False` |

---

## 7. Dashboard Grafana Cloud

### Configuração do data source

- Tipo: PostgreSQL
- Host: connection string do Supabase (painel Supabase → Settings → Database)
- SSL: obrigatório (`sslmode=require`)
- Credenciais: configuradas diretamente no Grafana Cloud — nunca no repositório

### Painéis

| # | Nome | Tipo | Query |
|---|---|---|---|
| 1 | Total de Perguntas Respondidas | Stat | `SELECT COUNT(*) FROM jarvis_respostas` |
| 2 | Feedbacks Preenchidos pelos Usuários | Stat | `SELECT COUNT(*) FROM jarvis_feedbacks` |
| 3 | Taxa de Satisfação dos Usuários com o LLM | Stat | `SELECT ROUND(AVG(satisfeito::int)::numeric, 3) FROM jarvis_feedbacks` |
| 4 | Tempo de Resposta do LLM | Time series | `SELECT date_trunc('minute', criado_em) AS time, AVG(tempo_resposta_segundos) AS value FROM jarvis_respostas GROUP BY 1 ORDER BY 1` |
| 5 | Score de Performance do LLM | Time series | 3 séries: taxa de satisfação por hora, tempo médio normalizado (1/avg_time), proporção perguntas-com-feedback |

### Layout

```
┌──────────────────┬──────────────────┬──────────────────┐
│  Total Perguntas │  Feedbacks       │  Taxa Satisfação  │
│  (Stat)          │  (Stat)          │  (Stat)           │
├──────────────────┴──────────────────┴──────────────────┤
│         Tempo de Resposta do LLM (Time series)          │
├─────────────────────────────────────────────────────────┤
│         Score de Performance do LLM (Time series)       │
└─────────────────────────────────────────────────────────┘
```

Auto-refresh: 5 segundos (padrão Grafana, configurável).

### Template versionado

O dashboard é exportado como `grafana/dashboard.json` e versionado no repositório. Permite reproduzir o dashboard em qualquer workspace Grafana sem cliques manuais.

---

## 8. Supabase MCP + Skill

### MCP

`@supabase/mcp-server-supabase` configurado no `settings.json` do Claude Code com o access token do projeto Supabase.

### Skill `supabase-jarvis`

Arquivo: `.claude/skills/supabase-jarvis.md`

**Gatilho:** qualquer contexto envolvendo métricas do Jarvis, dados do Supabase, validação do dashboard ou debug de observabilidade.

**Casos de uso cobertos pela skill:**
- Verificar se métricas estão sendo gravadas
- Inspecionar os últimos registros das tabelas
- Rodar queries de validação antes de ajustar painéis no Grafana
- Checar schema e integridade das tabelas
- Contar registros para cruzar com o dashboard

---

## 9. Arquivos Afetados

| Arquivo | Mudança |
|---|---|
| `src/observability/__init__.py` | Novo |
| `src/observability/metrics.py` | Novo |
| `src/interface/app.py` | Adiciona captura de tempo e botões de feedback |
| `grafana/dashboard.json` | Novo — template do dashboard |
| `.claude/skills/supabase-jarvis.md` | Nova skill |
| `settings.json` | Supabase MCP configurado |
| `requirements.txt` | `supabase` adicionado |
| `README.md` | Seção de Observabilidade adicionada |
| `.env.example` | `SUPABASE_URL` e `SUPABASE_KEY` adicionados |

---

## 10. Variáveis de Ambiente

| Variável | Onde configurar | Descrição |
|---|---|---|
| `SUPABASE_URL` | Streamlit Cloud Secrets + `.env` local | URL do projeto Supabase |
| `SUPABASE_KEY` | Streamlit Cloud Secrets + `.env` local | Chave de serviço (service_role) do Supabase |

Nunca commitar `.env`. Adicionar as duas variáveis ao `.env.example` como placeholders.

---

## 11. Fora do Escopo

- Identificação de usuário, sessão ou conteúdo das consultas
- Alertas automáticos (Grafana Alerting)
- Grafana MCP (pode ser adicionado numa iteração futura)
- Retenção ou purga automática de dados históricos
