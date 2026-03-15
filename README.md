# Jarvis — Assistente para Personal Trainers

## O que é o Jarvis

Personal trainers que trabalham com personalização real gastam entre 1 e 2 horas para montar cada plano de treino. O processo é manual: abrir a anamnese do aluno, consultar PDFs de metodologias, cruzar com protocolos de restrições físicas, verificar referências científicas e montar tudo numa planilha. É um trabalho qualificado, mas repetitivo — e cada hora gasta aqui é uma hora a menos atendendo alunos.

O Jarvis resolve esse problema com RAG (Retrieval-Augmented Generation). O profissional indexa seus próprios materiais — PDFs de metodologias, artigos, protocolos, anamneses — e passa a consultá-los via linguagem natural. O agente recupera os trechos mais relevantes, cruza as informações e entrega um rascunho de plano de treino em minutos, sempre citando as fontes que embasaram cada decisão.

O diferencial não é só velocidade: é rastreabilidade. Cada exercício, cada protocolo e cada adaptação no plano gerado vem acompanhado da referência exata do documento que o sustenta. O personal revisa, ajusta o que quiser e exporta o PDF pronto para enviar ao aluno.

---

## Como funciona

```
1. Personal descreve o aluno
   └─ Objetivo, restrições, histórico, disponibilidade de treino

2. Jarvis recupera os materiais relevantes
   └─ Busca semântica nos PDFs e documentos indexados (Qdrant)

3. Agente faz perguntas complementares (se necessário)
   └─ Até 3 rodadas para garantir contexto suficiente

4. Jarvis entrega o plano + fontes + download em PDF
   └─ Exercícios organizados por sessão, com referências documentais
```

---

## Stack

| Componente | Tecnologia |
|---|---|
| LLM | Llama 3.x via NVIDIA NIM API |
| Vector Store | Qdrant (local via Docker) |
| Orquestração | Python 3.11+ com LangChain |
| Interface | Streamlit |
| Embeddings | sentence-transformers (multilingual) |

---

## Estrutura de Pastas

```
jarvis-personal-trainer/
├── src/
│   ├── ingestion/      # Carregamento, chunking e indexação de documentos no Qdrant
│   ├── retrieval/      # Busca semântica contra o Qdrant
│   ├── generation/     # Chamadas ao LLM via NVIDIA NIM API
│   ├── interface/      # Aplicação Streamlit
│   └── config/         # Configurações e carregamento de variáveis de ambiente
├── docs/
│   ├── business-context/   # Visão, personas, KPIs, jornadas, análise competitiva
│   ├── product-context/    # Regras de negócio, glossário, especificações de features
│   └── technical-context/  # Stack, guia do codebase, ADRs
├── tests/              # Testes por módulo (espelhando src/)
├── .claude/            # Configuração do Claude Code (comandos, agentes)
├── .env.example        # Template de variáveis de ambiente (nunca commitar .env)
└── CLAUDE.md           # Instruções para agentes de IA que trabalham neste repositório
```

---

## Setup

**Pré-requisitos:**
- Python 3.11+
- Docker (para rodar o Qdrant localmente)
- Chave de API NVIDIA NIM (`NVIDIA_NIM_API_KEY`)

**Passo a passo:**

```bash
# 1. Clone o repositório
git clone <url-do-repositorio>
cd jarvis-personal-trainer

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env e preencha NVIDIA_NIM_API_KEY, QDRANT_HOST, QDRANT_PORT

# 3. Suba o Qdrant via Docker
docker run -p 6333:6333 qdrant/qdrant

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute a aplicação
streamlit run src/interface/app.py
```

---

## Uso

> _[Screenshot da interface — a ser adicionado]_

**Fluxo básico na interface:**

1. Abra o Jarvis no navegador (`http://localhost:8501`)
2. Na caixa de mensagem, descreva o aluno: objetivos, restrições, histórico, frequência de treino
3. O agente pode fazer perguntas complementares — responda na mesma caixa
4. Receba o plano de treino com exercícios, séries e as fontes que embasaram cada decisão
5. Clique em **Baixar PDF** para exportar o plano formatado

---

## Desenvolvimento

Este projeto segue **SDD (Spec-Driven Development)**: toda implementação começa pela leitura dos documentos de contexto em `docs/`. Leia o [`CLAUDE.md`](.claude/CLAUDE.md) antes de qualquer contribuição — ele descreve o workflow de slash commands, as convenções de código e as regras de qualidade.

```
/nova-tarefa <descrição>  →  implementação  →  /revisar-pr  →  /finalizar-tarefa
```
