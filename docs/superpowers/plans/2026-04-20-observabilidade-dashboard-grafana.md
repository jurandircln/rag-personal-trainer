# Observabilidade com Grafana Cloud + Supabase — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar observabilidade ao Jarvis — captura de tempo de resposta do LLM e feedback do usuário (Satisfeito/Não Satisfeito), com dashboard no Grafana Cloud alimentado por dados armazenados no Supabase.

**Architecture:** O app Streamlit envia métricas (response time, feedback) ao Supabase via `supabase-py` após cada evento, com falha silenciosa para não degradar a experiência do usuário. O Grafana Cloud usa um data source PostgreSQL apontando para o Supabase para alimentar 5 painéis de observabilidade. Um Supabase MCP é configurado no Claude Code para debug e inspeção das métricas durante o desenvolvimento.

**Tech Stack:** `supabase-py`, Supabase (Postgres free tier), Grafana Cloud (PostgreSQL data source), `pytest`, `unittest.mock`

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/observability/__init__.py` | Criar | Exporta `registrar_resposta` e `registrar_feedback` |
| `src/observability/metrics.py` | Criar | Lógica de conexão Supabase + inserts best-effort |
| `tests/test_observability.py` | Criar | Testes unitários do módulo de métricas |
| `supabase/migrations/create_metrics_tables.sql` | Criar | DDL das tabelas `jarvis_respostas` e `jarvis_feedbacks` |
| `src/interface/app.py` | Modificar | Captura de tempo de resposta + botões de feedback |
| `grafana/dashboard.json` | Criar | Template importável do dashboard Grafana |
| `.claude/skills/supabase-jarvis.md` | Criar | Skill que descreve quando e como usar o Supabase MCP |
| `.claude/settings.local.json` | Modificar | Adiciona configuração do Supabase MCP |
| `requirements.txt` | Modificar | Adiciona `supabase>=2.0` |
| `.env.example` | Modificar | Adiciona `SUPABASE_URL` e `SUPABASE_KEY` |
| `README.md` | Modificar | Adiciona seção de Observabilidade |

---

## Task 1: Módulo de Observabilidade

**Files:**
- Create: `src/observability/__init__.py`
- Create: `src/observability/metrics.py`
- Create: `tests/test_observability.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Adicionar `supabase` ao requirements.txt**

Abra `requirements.txt` e adicione a linha abaixo (após `streamlit>=1.30`):

```
supabase>=2.0
```

- [ ] **Step 2: Escrever o teste para `registrar_resposta` com cliente disponível**

Crie `tests/test_observability.py` com o seguinte conteúdo:

```python
"""Testes unitários do módulo de observabilidade."""
from unittest.mock import MagicMock, patch

import pytest


class TestRegistrarResposta:
    """Testes para a função registrar_resposta."""

    def test_insere_linha_quando_cliente_disponivel(self, monkeypatch):
        """Quando SUPABASE_URL e SUPABASE_KEY estão definidas, insere em jarvis_respostas."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import importlib
            import src.observability.metrics as mod
            mod._cliente = None  # garante estado limpo

            from src.observability.metrics import registrar_resposta
            registrar_resposta(1.23)

        mock_cliente.table.assert_called_once_with("jarvis_respostas")
        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"tempo_resposta_segundos": 1.23}
        )

    def test_nao_levanta_excecao_quando_variaveis_ausentes(self, monkeypatch):
        """Quando SUPABASE_URL não está definida, a função retorna silenciosamente."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("src.observability.metrics._cliente", None):
            from src.observability.metrics import registrar_resposta
            registrar_resposta(0.5)  # não deve lançar exceção

    def test_nao_levanta_excecao_quando_insert_falha(self, monkeypatch):
        """Falha no insert é capturada silenciosamente."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.side_effect = (
            RuntimeError("timeout")
        )

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_resposta
            registrar_resposta(0.8)  # não deve lançar exceção


class TestRegistrarFeedback:
    """Testes para a função registrar_feedback."""

    def test_insere_satisfeito_true(self, monkeypatch):
        """Feedback positivo insere satisfeito=True em jarvis_feedbacks."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=True)

        mock_cliente.table.assert_called_once_with("jarvis_feedbacks")
        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"satisfeito": True}
        )

    def test_insere_satisfeito_false(self, monkeypatch):
        """Feedback negativo insere satisfeito=False em jarvis_feedbacks."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=False)

        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"satisfeito": False}
        )

    def test_nao_levanta_excecao_quando_variaveis_ausentes(self, monkeypatch):
        """Sem variáveis de ambiente, retorna silenciosamente."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("src.observability.metrics._cliente", None):
            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=True)  # não deve lançar exceção
```

- [ ] **Step 3: Executar os testes para confirmar que falham**

```bash
pytest tests/test_observability.py -v
```

Esperado: `ModuleNotFoundError` para `src.observability.metrics` — o módulo ainda não existe.

- [ ] **Step 4: Criar `src/observability/__init__.py`**

```python
"""Módulo de observabilidade do Jarvis — coleta de métricas de desempenho do LLM."""
from src.observability.metrics import registrar_feedback, registrar_resposta

__all__ = ["registrar_resposta", "registrar_feedback"]
```

- [ ] **Step 5: Criar `src/observability/metrics.py`**

```python
"""
Registra métricas de desempenho do Jarvis no Supabase (Postgres).

Todas as funções são best-effort: falhas de rede ou configuração ausente
são logadas como WARNING e descartadas — o app continua normalmente.
"""
import logging
import os

from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Singleton do cliente — inicializado na primeira chamada bem-sucedida
_cliente: Client | None = None


def _obter_cliente() -> Client | None:
    """Retorna o cliente Supabase ou None se as variáveis não estiverem configuradas.

    Não cacheia None nem erros: tenta reconectar a cada chamada quando
    o cliente ainda não foi inicializado com sucesso.

    Returns:
        Instância do cliente Supabase ou None.
    """
    global _cliente
    if _cliente is not None:
        return _cliente

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not key:
        logger.warning(
            "SUPABASE_URL ou SUPABASE_KEY não configurados — métricas desativadas."
        )
        return None

    try:
        _cliente = create_client(url, key)
        logger.debug("Cliente Supabase inicializado com sucesso.")
    except Exception as exc:
        logger.warning("Falha ao criar cliente Supabase: %s", exc)

    return _cliente


def registrar_resposta(tempo_segundos: float) -> None:
    """Insere uma linha em jarvis_respostas. Falha silenciosa com log warning.

    Args:
        tempo_segundos: tempo total de geração da resposta pelo LLM, em segundos.
    """
    cliente = _obter_cliente()
    if cliente is None:
        return
    try:
        cliente.table("jarvis_respostas").insert(
            {"tempo_resposta_segundos": tempo_segundos}
        ).execute()
        logger.debug("Resposta registrada: %.2fs.", tempo_segundos)
    except Exception as exc:
        logger.warning("Falha ao registrar resposta no Supabase: %s", exc)


def registrar_feedback(satisfeito: bool) -> None:
    """Insere uma linha em jarvis_feedbacks. Falha silenciosa com log warning.

    Args:
        satisfeito: True se o usuário marcou 'Satisfeito', False caso contrário.
    """
    cliente = _obter_cliente()
    if cliente is None:
        return
    try:
        cliente.table("jarvis_feedbacks").insert(
            {"satisfeito": satisfeito}
        ).execute()
        logger.debug("Feedback registrado: satisfeito=%s.", satisfeito)
    except Exception as exc:
        logger.warning("Falha ao registrar feedback no Supabase: %s", exc)
```

- [ ] **Step 6: Executar os testes e confirmar que passam**

```bash
pytest tests/test_observability.py -v
```

Esperado: todos os testes `PASSED`.

- [ ] **Step 7: Commit**

```bash
git add requirements.txt src/observability/ tests/test_observability.py
git commit -m "feat(observabilidade): criar módulo de métricas com Supabase"
```

---

## Task 2: DDL das Tabelas no Supabase

**Files:**
- Create: `supabase/migrations/create_metrics_tables.sql`

> **Nota:** Este task cria o script SQL que deve ser executado manualmente no Supabase SQL Editor (supabase.com → projeto → SQL Editor). Não há código Python aqui.

- [ ] **Step 1: Criar o diretório e o arquivo SQL**

Crie `supabase/migrations/create_metrics_tables.sql`:

```sql
-- Tabelas de observabilidade do Jarvis
-- Executar no Supabase SQL Editor: supabase.com → projeto → SQL Editor

-- Registra cada resposta gerada pelo LLM
CREATE TABLE IF NOT EXISTS jarvis_respostas (
    id                      BIGSERIAL PRIMARY KEY,
    criado_em               TIMESTAMPTZ NOT NULL DEFAULT now(),
    tempo_resposta_segundos FLOAT NOT NULL
);

-- Registra cada feedback dado pelo usuário
CREATE TABLE IF NOT EXISTS jarvis_feedbacks (
    id         BIGSERIAL PRIMARY KEY,
    criado_em  TIMESTAMPTZ NOT NULL DEFAULT now(),
    satisfeito BOOLEAN NOT NULL
);

-- Índices para as queries do dashboard Grafana
CREATE INDEX IF NOT EXISTS idx_respostas_criado_em ON jarvis_respostas (criado_em);
CREATE INDEX IF NOT EXISTS idx_feedbacks_criado_em ON jarvis_feedbacks (criado_em);
```

- [ ] **Step 2: Executar o script no Supabase**

1. Acesse `supabase.com` → seu projeto → aba **SQL Editor**
2. Cole o conteúdo do arquivo acima e clique em **Run**
3. Confirme que as tabelas aparecem em **Table Editor**

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/create_metrics_tables.sql
git commit -m "feat(supabase): adicionar DDL das tabelas de observabilidade"
```

---

## Task 3: Instrumentar `app.py` — Tempo de Resposta + Botões de Feedback

**Files:**
- Modify: `src/interface/app.py`

- [ ] **Step 1: Adicionar imports ao topo de `app.py`**

Localize a linha `import re` (linha 7 aproximadamente) e adicione após ela:

```python
import time
```

Localize o bloco de imports locais (após `from src.generation.llm import RAGGenerator`) e adicione:

```python
from src.observability.metrics import registrar_feedback, registrar_resposta
```

- [ ] **Step 2: Inicializar `feedback_enviado` no session_state**

Localize o bloco de inicialização do `session_state` (por volta da linha 118). Após a última inicialização (`if "dados_aluno" not in st.session_state:`), adicione:

```python
if "feedback_enviado" not in st.session_state:
    st.session_state["feedback_enviado"] = False
```

- [ ] **Step 3: Capturar tempo de resposta do LLM**

Localize o bloco com `st.spinner("🤖 Aguarde enquanto estou estudando o seu caso...")` (por volta da linha 300). Modifique-o para capturar o tempo apenas da geração:

Substitua:
```python
            with st.spinner("🤖 Aguarde enquanto estou estudando o seu caso..."):
                resultados = searcher.buscar(historico[0]["content"], top_k=10, max_por_fonte=3)
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

Por:
```python
            with st.spinner("🤖 Aguarde enquanto estou estudando o seu caso..."):
                resultados = searcher.buscar(historico[0]["content"], top_k=10, max_por_fonte=3)
                dados_aluno = st.session_state.get("dados_aluno", {})
                inicio_geracao = time.perf_counter()
                resposta = generator.gerar(
                    query=query_completa,
                    resultados=resultados,
                    contexto_aluno=st.session_state["contexto_aluno"],
                    equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
                    nivel=dados_aluno.get("Nível de condicionamento", ""),
                    restricoes=dados_aluno.get("Lesões ou restrições", ""),
                )
                registrar_resposta(tempo_segundos=time.perf_counter() - inicio_geracao)
```

- [ ] **Step 4: Adicionar reset de `feedback_enviado` após nova resposta gerada**

Logo após a linha `st.session_state["ultimas_fontes"] = resposta.fontes` (dentro do bloco try, antes do `st.rerun()`), adicione:

```python
            st.session_state["feedback_enviado"] = False
```

- [ ] **Step 5: Adicionar os botões de feedback no branch `else`**

Localize o início do branch `else:` (linha ~336, após `if ultima_mensagem and ultima_mensagem["role"] == "user":`). Adicione o bloco de feedback como **primeira coisa** no `else`, antes da lógica de follow-up:

Substitua o início do `else:`:
```python
    else:
        rodadas = st.session_state["rodadas_followup"]
```

Por:
```python
    else:
        # Botões de feedback — exibidos após cada resposta do assistente
        ultima_resposta_assistente = next(
            (m for m in reversed(historico) if m["role"] == "assistant"), None
        )
        if ultima_resposta_assistente and not st.session_state["feedback_enviado"]:
            st.markdown("**Como você avalia esta resposta?**")
            col_sat, col_nsat, _ = st.columns([1, 1, 4])
            with col_sat:
                if st.button("👍 Satisfeito", key="btn_satisfeito"):
                    registrar_feedback(satisfeito=True)
                    st.session_state["feedback_enviado"] = True
                    st.rerun()
            with col_nsat:
                if st.button("👎 Não Satisfeito", key="btn_nao_satisfeito"):
                    registrar_feedback(satisfeito=False)
                    st.session_state["feedback_enviado"] = True
                    st.rerun()
        elif st.session_state["feedback_enviado"]:
            st.success("Obrigado pelo feedback!")

        rodadas = st.session_state["rodadas_followup"]
```

- [ ] **Step 6: Resetar `feedback_enviado` ao submeter follow-up**

Localize o bloco do botão `"Responder"` dentro da lógica de follow-up:

```python
            if st.button("Responder", key=f"btn_followup_{rodadas}"):
                if followup.strip():
                    historico.append({"role": "user", "content": followup.strip()})
                    st.session_state["historico_conversa"] = historico
                    st.session_state["rodadas_followup"] = rodadas + 1
                    st.rerun()
```

Substitua por:
```python
            if st.button("Responder", key=f"btn_followup_{rodadas}"):
                if followup.strip():
                    historico.append({"role": "user", "content": followup.strip()})
                    st.session_state["historico_conversa"] = historico
                    st.session_state["rodadas_followup"] = rodadas + 1
                    st.session_state["feedback_enviado"] = False
                    st.rerun()
```

- [ ] **Step 7: Resetar `feedback_enviado` no botão "Nova consulta"**

Localize o bloco do botão `"Nova consulta"`:

```python
        if st.button("Nova consulta"):
            st.session_state["estado"] = "anamnese"
            st.session_state["contexto_aluno"] = ""
            st.session_state["historico_conversa"] = []
            st.session_state["rodadas_followup"] = 0
            st.rerun()
```

Substitua por:
```python
        if st.button("Nova consulta"):
            st.session_state["estado"] = "anamnese"
            st.session_state["contexto_aluno"] = ""
            st.session_state["historico_conversa"] = []
            st.session_state["rodadas_followup"] = 0
            st.session_state["feedback_enviado"] = False
            st.rerun()
```

- [ ] **Step 8: Executar a suite de testes para confirmar sem regressões**

```bash
pytest tests/ -v
```

Esperado: todos os testes existentes `PASSED` (os novos testes de observabilidade também).

- [ ] **Step 9: Commit**

```bash
git add src/interface/app.py
git commit -m "feat(interface): adicionar captura de tempo de resposta e botões de feedback"
```

---

## Task 4: Template do Dashboard Grafana

**Files:**
- Create: `grafana/dashboard.json`

- [ ] **Step 1: Criar o diretório `grafana/`**

```bash
mkdir -p grafana
```

- [ ] **Step 2: Criar `grafana/dashboard.json`**

Crie o arquivo com o seguinte conteúdo (template importável no Grafana Cloud via *Dashboards → Import*):

```json
{
  "__inputs": [
    {
      "name": "DS_POSTGRESQL",
      "label": "PostgreSQL (Supabase)",
      "description": "Conexão PostgreSQL com o banco Supabase do Jarvis",
      "type": "datasource",
      "pluginId": "postgres",
      "pluginName": "PostgreSQL"
    }
  ],
  "__requires": [
    {
      "type": "grafana",
      "id": "grafana",
      "name": "Grafana",
      "version": "10.0.0"
    },
    {
      "type": "datasource",
      "id": "postgres",
      "name": "PostgreSQL",
      "version": "1.0.0"
    },
    {
      "type": "panel",
      "id": "stat",
      "name": "Stat",
      "version": ""
    },
    {
      "type": "panel",
      "id": "timeseries",
      "name": "Time series",
      "version": ""
    }
  ],
  "annotations": {
    "list": []
  },
  "description": "Observabilidade do Jarvis — métricas de desempenho do LLM",
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "panels": [
    {
      "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": null }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
      "id": 1,
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "center",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": ["lastNotNull"],
          "fields": "",
          "values": false
        },
        "textMode": "value"
      },
      "targets": [
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "table",
          "rawSql": "SELECT COUNT(*) AS value FROM jarvis_respostas",
          "refId": "A"
        }
      ],
      "title": "Total de Perguntas Respondidas",
      "type": "stat"
    },
    {
      "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "green", "value": null }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
      "id": 2,
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "center",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": ["lastNotNull"],
          "fields": "",
          "values": false
        },
        "textMode": "value"
      },
      "targets": [
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "table",
          "rawSql": "SELECT COUNT(*) AS value FROM jarvis_feedbacks",
          "refId": "A"
        }
      ],
      "title": "Feedbacks Preenchidos pelos Usuários",
      "type": "stat"
    },
    {
      "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "thresholds" },
          "decimals": 3,
          "mappings": [],
          "max": 1,
          "min": 0,
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "color": "red", "value": null },
              { "color": "yellow", "value": 0.5 },
              { "color": "green", "value": 0.8 }
            ]
          },
          "unit": "percentunit"
        },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
      "id": 3,
      "options": {
        "colorMode": "value",
        "graphMode": "none",
        "justifyMode": "center",
        "orientation": "auto",
        "reduceOptions": {
          "calcs": ["lastNotNull"],
          "fields": "",
          "values": false
        },
        "textMode": "value"
      },
      "targets": [
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "table",
          "rawSql": "SELECT ROUND(AVG(satisfeito::int)::numeric, 3) AS value FROM jarvis_feedbacks",
          "refId": "A"
        }
      ],
      "title": "Taxa de Satisfação dos Usuários com o LLM",
      "type": "stat"
    },
    {
      "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "segundos",
            "axisPlacement": "auto",
            "fillOpacity": 20,
            "gradientMode": "none",
            "lineWidth": 2,
            "showPoints": "auto",
            "spanNulls": false
          },
          "mappings": [],
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 8 },
      "id": 4,
      "options": {
        "legend": { "calcs": ["mean", "max"], "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single", "sort": "none" }
      },
      "targets": [
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "time_series",
          "rawSql": "SELECT date_trunc('minute', criado_em) AS time, AVG(tempo_resposta_segundos) AS \"Tempo Médio (s)\" FROM jarvis_respostas WHERE $__timeFilter(criado_em) GROUP BY 1 ORDER BY 1",
          "refId": "A"
        }
      ],
      "title": "Tempo de Resposta do LLM",
      "type": "timeseries"
    },
    {
      "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
      "fieldConfig": {
        "defaults": {
          "color": { "mode": "palette-classic" },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisPlacement": "auto",
            "fillOpacity": 0,
            "gradientMode": "none",
            "lineWidth": 2,
            "showPoints": "auto",
            "spanNulls": false
          },
          "mappings": [],
          "max": 1,
          "min": 0
        },
        "overrides": []
      },
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 16 },
      "id": 5,
      "options": {
        "legend": { "calcs": ["mean"], "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "multi", "sort": "none" }
      },
      "targets": [
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "time_series",
          "rawSql": "SELECT date_trunc('hour', criado_em) AS time, ROUND(AVG(satisfeito::int)::numeric, 3) AS \"Taxa de Satisfação\" FROM jarvis_feedbacks WHERE $__timeFilter(criado_em) GROUP BY 1 ORDER BY 1",
          "refId": "A"
        },
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "time_series",
          "rawSql": "SELECT date_trunc('hour', r.criado_em) AS time, ROUND(COUNT(f.id)::numeric / NULLIF(COUNT(r.id), 0), 3) AS \"Proporção c/ Feedback\" FROM jarvis_respostas r LEFT JOIN jarvis_feedbacks f ON date_trunc('hour', f.criado_em) = date_trunc('hour', r.criado_em) WHERE $__timeFilter(r.criado_em) GROUP BY 1 ORDER BY 1",
          "refId": "B"
        },
        {
          "datasource": { "type": "postgres", "uid": "${DS_POSTGRESQL}" },
          "format": "time_series",
          "rawSql": "SELECT date_trunc('hour', criado_em) AS time, ROUND(LEAST(1.0 / NULLIF(AVG(tempo_resposta_segundos), 0) / 2.0, 1.0)::numeric, 3) AS \"Velocidade Normalizada\" FROM jarvis_respostas WHERE $__timeFilter(criado_em) GROUP BY 1 ORDER BY 1",
          "refId": "C"
        }
      ],
      "title": "Score de Performance do LLM",
      "type": "timeseries"
    }
  ],
  "refresh": "5s",
  "schemaVersion": 38,
  "tags": ["jarvis", "llm", "observabilidade"],
  "time": { "from": "now-1h", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "Jarvis — Desempenho do LLM",
  "uid": "jarvis-llm-performance",
  "version": 1
}
```

- [ ] **Step 3: Importar o dashboard no Grafana Cloud**

1. No Grafana Cloud, acesse **Dashboards → Import**
2. Clique em **Upload dashboard JSON file** e selecione `grafana/dashboard.json`
3. Na tela de mapeamento, selecione o data source PostgreSQL do Supabase
4. Clique em **Import**

> **Pré-requisito:** O data source PostgreSQL deve estar configurado antes da importação. Veja o Task 5 para as instruções de setup do data source.

- [ ] **Step 4: Configurar o data source PostgreSQL no Grafana Cloud**

1. No Grafana Cloud, acesse **Connections → Data Sources → Add new data source**
2. Selecione **PostgreSQL**
3. Preencha os campos com os dados do Supabase:
   - **Host:** `db.<SUPABASE_PROJECT_REF>.supabase.co:5432`
   - **Database:** `postgres`
   - **User:** `postgres`
   - **Password:** (senha do banco, obtida em Supabase → Settings → Database)
   - **TLS/SSL Mode:** `require`
4. Clique em **Save & Test** — deve aparecer "Database Connection OK"

- [ ] **Step 5: Commit**

```bash
git add grafana/dashboard.json
git commit -m "feat(grafana): adicionar template importável do dashboard de observabilidade"
```

---

## Task 5: Supabase MCP + Skill

**Files:**
- Modify: `.claude/settings.local.json`
- Create: `.claude/skills/supabase-jarvis.md`

- [ ] **Step 1: Obter o Personal Access Token do Supabase**

1. Acesse `supabase.com → Account → Access Tokens`
2. Clique em **Generate new token**
3. Nomeie como "Claude Code — Jarvis"
4. Copie o token gerado (só aparece uma vez)

- [ ] **Step 2: Adicionar o Supabase MCP ao `settings.local.json`**

O arquivo atual contém:
```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(python:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(pytest:*)"
    ]
  }
}
```

Substitua pelo seguinte (mantendo as permissões existentes e adicionando o MCP):
```json
{
  "permissions": {
    "allow": [
      "Bash(python3:*)",
      "Bash(python:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(pytest:*)"
    ]
  },
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase@latest",
        "--access-token",
        "<SEU_PERSONAL_ACCESS_TOKEN_AQUI>"
      ]
    }
  }
}
```

Substitua `<SEU_PERSONAL_ACCESS_TOKEN_AQUI>` pelo token obtido no Step 1.

> **Segurança:** O `settings.local.json` está no `.gitignore` — o token nunca vai para o repositório. Confirme com `git check-ignore -v .claude/settings.local.json` antes de commitar qualquer coisa.

- [ ] **Step 3: Verificar que `settings.local.json` está ignorado pelo git**

```bash
git check-ignore -v .claude/settings.local.json
```

Esperado: uma linha confirmando que o arquivo é ignorado. Se não for ignorado, adicione `.claude/settings.local.json` ao `.gitignore` antes de continuar.

- [ ] **Step 4: Criar o diretório de skills do projeto**

```bash
mkdir -p .claude/skills
```

- [ ] **Step 5: Criar `.claude/skills/supabase-jarvis.md`**

```markdown
---
name: supabase-jarvis
description: Consulta e inspeciona as tabelas de métricas do Jarvis no Supabase (jarvis_respostas e jarvis_feedbacks) via MCP
trigger: qualquer contexto envolvendo métricas do Jarvis, dados do Supabase, validação do dashboard Grafana ou debug de observabilidade
---

# Skill: supabase-jarvis

Use esta skill quando o contexto envolver qualquer um dos seguintes:
- Verificar se métricas estão sendo gravadas corretamente
- Inspecionar registros recentes de `jarvis_respostas` ou `jarvis_feedbacks`
- Cruzar contagens com o que o dashboard Grafana está exibindo
- Debugar problemas de observabilidade
- Checar schema ou integridade das tabelas

## Como usar o MCP

O Supabase MCP está configurado no `settings.local.json`. Use as ferramentas do MCP para executar queries SQL diretamente no banco do projeto Jarvis.

## Queries úteis

### Verificar se há dados sendo gravados

```sql
-- Últimas 5 respostas registradas
SELECT id, criado_em, tempo_resposta_segundos
FROM jarvis_respostas
ORDER BY criado_em DESC
LIMIT 5;

-- Últimos 5 feedbacks registrados
SELECT id, criado_em, satisfeito
FROM jarvis_feedbacks
ORDER BY criado_em DESC
LIMIT 5;
```

### Replicar os painéis do dashboard

```sql
-- Painel 1: Total de Perguntas
SELECT COUNT(*) FROM jarvis_respostas;

-- Painel 2: Feedbacks Preenchidos
SELECT COUNT(*) FROM jarvis_feedbacks;

-- Painel 3: Taxa de Satisfação
SELECT ROUND(AVG(satisfeito::int)::numeric, 3) FROM jarvis_feedbacks;

-- Painel 4: Tempo médio de resposta (últimas 24h)
SELECT AVG(tempo_resposta_segundos)
FROM jarvis_respostas
WHERE criado_em > now() - INTERVAL '24 hours';
```

### Verificar schema

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name IN ('jarvis_respostas', 'jarvis_feedbacks')
ORDER BY table_name, ordinal_position;
```
```

- [ ] **Step 6: Reiniciar o Claude Code para carregar o MCP**

Feche e reabra o Claude Code (ou recarregue a sessão). O MCP `supabase` deve aparecer nas ferramentas disponíveis.

- [ ] **Step 7: Commit**

```bash
git add .claude/skills/supabase-jarvis.md
git commit -m "feat(mcp): adicionar skill supabase-jarvis para debug de observabilidade"
```

> Não commite `.claude/settings.local.json` — ele contém o token de acesso.

---

## Task 6: Atualizar `.env.example` e `README.md`

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 1: Adicionar variáveis do Supabase ao `.env.example`**

Adicione ao final de `.env.example`:

```bash
# Supabase — Observabilidade (métricas de desempenho do LLM)
# Obtenha em: supabase.com → projeto → Settings → API
# SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
# SUPABASE_KEY=your_supabase_service_role_key_here
```

- [ ] **Step 2: Adicionar seção de Observabilidade ao `README.md`**

Adicione a seguinte seção ao `README.md`, após a seção **Stack** e antes de **Estrutura de Pastas**:

```markdown
## Observabilidade

O Jarvis coleta métricas de desempenho do LLM e as envia ao **Supabase** (Postgres). O **Grafana Cloud** conecta ao Supabase via data source PostgreSQL e exibe um dashboard com 5 painéis:

| Painel | Descrição |
|---|---|
| Total de Perguntas Respondidas | Contador de chamadas ao LLM |
| Feedbacks Preenchidos pelos Usuários | Contador de feedbacks enviados |
| Taxa de Satisfação dos Usuários com o LLM | Razão satisfeito/total feedbacks |
| Tempo de Resposta do LLM | Série temporal do tempo de geração |
| Score de Performance do LLM | Satisfação, velocidade e cobertura de feedback ao longo do tempo |

### Setup

1. Crie o banco no Supabase: execute `supabase/migrations/create_metrics_tables.sql` no SQL Editor
2. Configure o data source PostgreSQL no Grafana Cloud (Settings → Database do Supabase)
3. Importe o dashboard: Grafana Cloud → Dashboards → Import → `grafana/dashboard.json`
4. Adicione `SUPABASE_URL` e `SUPABASE_KEY` aos Secrets do Streamlit Cloud

### Feedback na Interface

Após cada resposta gerada, o usuário vê dois botões: **👍 Satisfeito** e **👎 Não Satisfeito**. O clique registra um evento em `jarvis_feedbacks` no Supabase.

As métricas são **best-effort**: se o Supabase estiver indisponível, o app continua funcionando normalmente.
```

- [ ] **Step 3: Executar todos os testes uma última vez**

```bash
pytest tests/ -v
```

Esperado: todos `PASSED`, sem nenhuma regressão.

- [ ] **Step 4: Commit final**

```bash
git add .env.example README.md
git commit -m "docs: adicionar seção de observabilidade ao README e variáveis ao .env.example"
```

---

## Self-Review

**Cobertura da spec:**
- ✅ Seção 3 (Arquitetura): Task 1 + Task 3 cobrem o fluxo completo
- ✅ Seção 4 (Schema): Task 2 cria o DDL
- ✅ Seção 5 (Módulo de observabilidade): Task 1 implementa `metrics.py` com TDD
- ✅ Seção 6a (Captura de tempo): Task 3, Steps 1–4
- ✅ Seção 6b (Botões de feedback): Task 3, Steps 5–7
- ✅ Seção 6c (session_state `feedback_enviado`): Task 3, Step 2
- ✅ Seção 7 (Dashboard): Task 4 com template JSON completo
- ✅ Seção 8 (MCP + Skill): Task 5
- ✅ Seção 9 (Arquivos afetados): todos cobertos nos 6 tasks
- ✅ Seção 10 (Variáveis de ambiente): Task 6
- ✅ README: Task 6

**Consistência de tipos e nomes:**
- `registrar_resposta(tempo_segundos: float)` e `registrar_feedback(satisfeito: bool)` — usados consistentemente em `metrics.py`, `__init__.py`, e `app.py`
- `feedback_enviado` no `session_state` — inicializado no Task 3 Step 2, resetado nos Steps 4, 6 e 7
- Tabelas `jarvis_respostas` e `jarvis_feedbacks` — nomes consistentes entre DDL, `metrics.py`, queries do dashboard e skill

**Placeholders:** Nenhum. Todo código está completo.
