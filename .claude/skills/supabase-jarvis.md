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
