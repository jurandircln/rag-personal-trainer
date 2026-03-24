# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# CLAUDE.md — Jarvis Personal Trainer

## Project Description

Jarvis is a RAG (Retrieval-Augmented Generation) system built for personal trainers. An LLM (Llama 3.x via NVIDIA NIM API) queries indexed materials — training PDFs, methodologies, and anamneses — to answer questions and generate personalized training plans.

This file is the primary instruction source for AI agents (Claude Code and others) working on this codebase. Read it before doing anything else.

---

## Development Methodology: SDD (Spec-Driven Development)

All implementation must be preceded by reading the relevant context documents. There are three context layers:

### Layer 1 — Business Context (`docs/business-context/`)
Vision, personas, user journeys, KPIs, and competitive analysis. Read this before touching anything that affects product direction or user-facing behavior.

### Layer 2 — Product Context (`docs/product-context/`)
Business rules, glossary, and product feature specifications. Read this before implementing any feature or changing behavior that users interact with.

### Layer 3 — Technical Context (`docs/technical-context/`)
Stack decisions, codebase guide, API specifications, and Architecture Decision Records (ADRs). Read this before writing any code, choosing libraries, or making architectural decisions.

**Rule: never implement without reading the relevant context docs first.**

---

## Stack

| Concern | Technology |
|---|---|
| LLM | Llama 3.x via NVIDIA NIM API |
| Vector Store | Qdrant (local via Docker) |
| Backend / Orchestration | Python 3.11+ with LangChain |
| Interface | Streamlit |
| Embeddings | sentence-transformers (multilingual) |
| Env management | python-dotenv |

---

## Module Structure

```
src/
  ingestion/    # Document loading, chunking, and embedding into Qdrant
  retrieval/    # Semantic search queries against Qdrant
  generation/   # LLM calls via NVIDIA NIM API
  interface/    # Streamlit application
  config/       # Settings, environment variable loading
```

---

## Code Conventions

- **Files and variables**: snake_case
- **Classes**: PascalCase
- **Branches**: `main`, `feat/*`, `fix/*`
- **Commits**: Conventional Commits — `feat:`, `fix:`, `docs:`, `chore:`

### Idioma dos Comentários

**Todos os comentários de código devem ser escritos em português (pt-BR), sem exceção.**
Esta regra se aplica a desenvolvedores humanos e a agentes de IA.

- Docstrings de funções e classes: em português
- Comentários inline (`#`): em português
- Nomes de variáveis e type hints: mantêm snake_case em inglês (são código, não prosa)
- Mensagens de log dirigidas ao usuário: em português

Correto:
```python
def carregar_documento(caminho: str) -> list:
    """Carrega um documento PDF e retorna uma lista de páginas."""
    # Verifica se o arquivo existe antes de abrir
```
Incorreto: docstring ou comentário em inglês.

---

## Quality Rules

1. **Never implement without reading context docs first** (see SDD section above).
2. **Human review is required before merging** any branch into `main`.
3. **Never commit `.env`** — use `.env.example` as the template. Secrets stay local.
4. **No functional code without tests** — every non-trivial function must have corresponding test coverage.
5. **Comentários obrigatoriamente em português (pt-BR)** — ver seção "Idioma dos Comentários".

---

## Commands

```bash
# Rodar todos os testes
pytest tests/ -v

# Rodar um único teste
pytest tests/test_loader.py -v -k "test_carregar_arquivo"

# Subir Qdrant + app via Docker Compose
docker-compose up --build
# Qdrant: http://localhost:6333/dashboard  |  App: http://localhost:8501

# Indexar documentos (requer Qdrant em execução)
python scripts/ingest.py --caminho data/raw/
```

Os testes usam mocks e **não exigem** Qdrant nem NVIDIA NIM em execução.

---

## Environment Setup

Copy `.env.example` to `.env` and fill in the required values. Never add `.env` to version control.

The application expects the following environment variables (see `.env.example` for the full list):
- `NVIDIA_API_KEY` — API key for the NVIDIA NIM endpoint
- **Modo local (Docker):** `QDRANT_HOST` + `QDRANT_PORT`
- **Modo cloud:** `QDRANT_URL` + `QDRANT_API_KEY` — quando `QDRANT_URL` está definida, `Settings.usar_qdrant_cloud` retorna `True` e `QDRANT_HOST` é ignorado

Run Qdrant locally via Docker before starting the application.

---

## Fluxo de Trabalho com Claude Code

Use os slash commands abaixo como workflow padrão para toda tarefa de desenvolvimento.

### Ciclo de Vida de uma Tarefa

```
/nova-tarefa <descrição>   →   implementação   →   /revisar-pr   →   /finalizar-tarefa
```

### Slash Commands Disponíveis

| Comando | Quando usar |
|---|---|
| `/nova-tarefa <descrição>` | Ao iniciar qualquer tarefa nova — cria branch e orienta o contexto SDD |
| `/revisar-pr [branch-base]` | Antes de todo PR — revisão estruturada com BLOQUEADORES / AVISOS / SUGESTÕES |
| `/finalizar-tarefa` | Ao concluir a implementação — commit, push e abertura de PR |
| `/debug <descrição>` | Ao encontrar qualquer bug não trivial — diagnóstico sistemático em 6 fases |

### Superpowers × Comandos Nativos

Devs **sem** Superpowers usam os slash commands como workflow padrão.
Devs **com** Superpowers usam as skills nativas, que oferecem orquestração de subagentes.

| Skill Superpowers | Equivalente nativo | Quando usar |
|---|---|---|
| `finishing-a-development-branch` | `/finalizar-tarefa` | Ao terminar desenvolvimento |
| `requesting-code-review` | `/revisar-pr` | Antes de todo PR |
| `systematic-debugging` | `/debug` | Bug não trivial |
| `test-driven-development` | Testes antes + `/revisar-pr` para verificar | Toda função nova |
| `subagent-driven-development` | Implementação direta + `/revisar-pr` | Features complexas |
| `writing-plans` | Documentar plano antes de implementar | Features novas |

---

## Notes for AI Agents

- Always check `docs/technical-context/` for ADRs before proposing a new library or architecture change.
- Always check `docs/product-context/` for the glossary before naming new concepts in code or documentation.
- When in doubt about scope or priority, check `docs/business-context/` for KPIs and personas.
- Prefer editing existing files over creating new ones.
- Do not create markdown documentation files unless explicitly requested.
