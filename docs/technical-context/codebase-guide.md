# Guia da Codebase — Jarvis Personal Trainer

## Visão Geral da Estrutura

```
src/
├── ingestion/   — Pipeline de ingestão de documentos
├── retrieval/   — Busca semântica
├── generation/  — Geração de texto via LLM
├── interface/   — Interface Streamlit
└── config/      — Configurações centralizadas
```

## Fluxo Principal

O sistema opera em duas fases distintas:

**Fase 1 — Indexação (offline, executada via `scripts/ingest.py`):**
```
data/raw/*.pdf → DocumentLoader → DocumentChunker → VectorIndexer → Qdrant
```

**Fase 2 — Consulta (online, chamada pelo Streamlit):**
```
query → SemanticSearcher → Qdrant → RAGGenerator → NVIDIA NIM → RespostaRAG
```

---

## Módulos

### config/

**`types.py`** — Dataclasses centrais do sistema:
- `Chunk(conteudo, fonte, pagina, chunk_id)` — unidade de texto indexada
- `ResultadoBusca(chunk, score)` — resultado de busca com score de similaridade
- `RespostaRAG(texto, fontes)` — resposta final com citações

**`settings.py`** — Classe `Settings`:
- Carrega variáveis de ambiente via `python-dotenv`
- Variáveis obrigatórias: `NVIDIA_API_KEY`, `QDRANT_HOST`
- Lança `ValueError` se variável obrigatória estiver ausente

---

### ingestion/

**`loader.py`** — Classe `DocumentLoader`:
- `carregar_arquivo(caminho: str) -> list[dict]` — carrega um PDF
- `carregar_diretorio(caminho: str) -> list[dict]` — carrega todos os PDFs de um diretório
- Usa `PyPDFLoader` do `langchain-community`
- Cada item retornado: `{"conteudo": str, "fonte": str, "pagina": int}`

**`chunker.py`** — Classe `DocumentChunker`:
- `dividir(paginas: list[dict]) -> list[Chunk]` — divide páginas em chunks
- Usa `RecursiveCharacterTextSplitter` com `chunk_size=800`, `chunk_overlap=100`
- `chunk_id` = primeiros 16 caracteres do SHA-256 do conteúdo

**`embedder.py`** — Classe `VectorIndexer`:
- `indexar(chunks: list[Chunk]) -> int` — gera embeddings e persiste no Qdrant
- Usa `SentenceTransformer` para gerar embeddings
- Faz upsert no Qdrant com payload `{conteudo, fonte, pagina, chunk_id}`
- `criar_colecao_se_necessario()` — verifica existência antes de criar (distância COSINE)

---

### retrieval/

**`searcher.py`** — Classe `SemanticSearcher`:
- `buscar(query: str, top_k: int = 5) -> list[ResultadoBusca]` — busca semântica
- Codifica a query com o mesmo modelo de embeddings da indexação
- Busca por similaridade coseno no Qdrant
- Reconstrói objetos `Chunk` a partir do payload retornado

---

### generation/

**`prompt.py`** — Função `montar_prompt(query, resultados) -> str`:
- Monta prompt com seção `REFERÊNCIAS:` numerada `[N] fonte, p. pagina: conteudo`
- Inclui instrução de citação obrigatória (regra de negócio RN-001)
- Fallback para "(nenhuma referência disponível)" quando sem resultados

**`llm.py`** — Classe `RAGGenerator`:
- `gerar(query: str, resultados: list[ResultadoBusca]) -> RespostaRAG`
- Usa `ChatNVIDIA` via LangChain (conector NVIDIA NIM)
- Fontes = conjunto único de `resultado.chunk.fonte`

---

### interface/

**`app.py`** — Aplicação Streamlit com `@st.cache_resource`; exibe pergunta, resposta e fontes:
- Usa `SemanticSearcher` e `RAGGenerator` diretamente como módulos Python
- `@st.cache_resource` garante que os componentes sejam instanciados uma única vez por sessão

---

## Como Rodar Localmente

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env
# Preencher NVIDIA_API_KEY no arquivo .env

# 2. Subir Qdrant e a aplicação via Docker Compose
docker-compose up --build
# Qdrant: http://localhost:6333/dashboard
# App:    http://localhost:8501

# 3. Indexar documentos (no host ou em outro terminal)
python scripts/ingest.py --caminho data/raw/
```

---

## Testes

```bash
pytest tests/ -v  # 39 testes, todos passando
```

- Nenhum teste requer Qdrant ou NVIDIA NIM em execução (todos usam mocks)
- Fixtures compartilhadas em `tests/conftest.py`: `settings_mock`, `chunks_exemplo`, `resultados_exemplo`
- `tests/test_interface.py` — testes da aplicação Streamlit (mocks de `SemanticSearcher` e `RAGGenerator`)
