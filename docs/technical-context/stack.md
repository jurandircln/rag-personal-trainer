# Stack Técnica — Jarvis Personal Trainer

## Visão Geral

Este documento descreve a stack tecnológica adotada no projeto Jarvis, as versões recomendadas e as convenções de código que devem ser seguidas por todos os contribuidores (humanos e agentes de IA).

---

## Stack

| Camada | Tecnologia | Versão / Notas |
|---|---|---|
| LLM | Llama 3.x via NVIDIA NIM API | meta/llama-3.1-70b-instruct |
| Vector Store | Qdrant | Local via Docker |
| Backend / Orquestração | Python + LangChain | Python 3.11+, LangChain latest |
| Interface | Streamlit | latest |
| Embeddings | sentence-transformers | paraphrase-multilingual-mpnet-base-v2 |
| Env management | python-dotenv | latest |

---

## Convenções de Código

### Nomenclatura

| Tipo | Convenção | Exemplo |
|---|---|---|
| Arquivos e módulos | snake_case | `document_loader.py` |
| Variáveis e funções | snake_case | `load_documents()` |
| Classes | PascalCase | `DocumentLoader` |
| Constantes | UPPER_SNAKE_CASE | `MAX_CHUNK_SIZE` |

### Estrutura de Módulos

```
src/
├── ingestion/   — carregamento, chunking, embeddings
├── retrieval/   — busca semântica no Qdrant
├── generation/  — chamadas ao LLM via NVIDIA NIM
├── interface/   — Streamlit app
└── config/      — settings, variáveis de ambiente
```

### Branches

| Tipo | Padrão | Exemplo |
|---|---|---|
| Principal | `main` | — |
| Feature | `feat/*` | `feat/document-ingestion` |
| Bug fix | `fix/*` | `fix/qdrant-connection` |
| Docs | `docs/*` | `docs/update-adr` |
| Chores | `chore/*` | `chore/update-deps` |

### Commits

Seguir [Conventional Commits](https://www.conventionalcommits.org/):

| Tipo | Uso |
|---|---|
| `feat:` | nova funcionalidade |
| `fix:` | correção de bug |
| `docs:` | documentação |
| `chore:` | manutenção, deps, configs |
| `refactor:` | refatoração sem mudança de comportamento |
| `test:` | testes |

Exemplo: `feat: add PDF loader with LangChain`

---

## Decisões de Arquitetura

Ver pasta `adr/` para Architecture Decision Records (ADRs).
