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
