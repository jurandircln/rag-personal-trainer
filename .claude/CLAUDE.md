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

---

## Quality Rules

1. **Never implement without reading context docs first** (see SDD section above).
2. **Human review is required before merging** any branch into `main`.
3. **Never commit `.env`** — use `.env.example` as the template. Secrets stay local.
4. **No functional code without tests** — every non-trivial function must have corresponding test coverage.

---

## Environment Setup

Copy `.env.example` to `.env` and fill in the required values. Never add `.env` to version control.

The application expects the following environment variables (see `.env.example` for the full list):
- `NVIDIA_NIM_API_KEY` — API key for the NVIDIA NIM endpoint
- `QDRANT_HOST` / `QDRANT_PORT` — connection details for the local Qdrant instance

Run Qdrant locally via Docker before starting the application.

---

## Notes for AI Agents

- Always check `docs/technical-context/` for ADRs before proposing a new library or architecture change.
- Always check `docs/product-context/` for the glossary before naming new concepts in code or documentation.
- When in doubt about scope or priority, check `docs/business-context/` for KPIs and personas.
- Prefer editing existing files over creating new ones.
- Do not create markdown documentation files unless explicitly requested.
