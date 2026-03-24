# Qdrant Cloud Deploy — Suporte ao Streamlit Cloud

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que o app Jarvis, deployado no Streamlit Cloud, conecte ao Qdrant Cloud (gerenciado) em vez do Qdrant local via Docker.

**Architecture:** Adicionar suporte a dois modos de conexão no `QdrantClient` — modo local (`host:port`) e modo cloud (`url + api_key`) — controlado por variáveis de ambiente. A lógica de criação do cliente é encapsulada em uma função auxiliar em cada módulo que já importa `QdrantClient`, preservando os mocks existentes nos testes.

**Tech Stack:** `qdrant-client` (já instalado, suporta cloud nativamente), Qdrant Cloud free tier (1 cluster, 1GB).

---

## Contexto do Problema

O Streamlit Cloud não executa Docker. Logo:
- `QDRANT_HOST=localhost` não resolve para nenhum serviço.
- `scripts/ingest.py` precisou ser executado localmente — os vetores ficaram apenas no `data/qdrant_storage/` local.
- O app deployado falha ao tentar buscar no Qdrant.

**Solução:** Qdrant Cloud. Os documentos são ingeridos uma vez (localmente, apontando para o cluster cloud). O app em produção conecta ao mesmo cluster via URL + API key.

---

## Mapa de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/config/settings.py` | Modificar | Adicionar `qdrant_url`, `qdrant_api_key`, `usar_qdrant_cloud`; tornar `QDRANT_HOST` condicional |
| `src/ingestion/embedder.py` | Modificar | Substituir `QdrantClient(host, port)` por função auxiliar que detecta modo cloud |
| `src/retrieval/searcher.py` | Modificar | Mesmo padrão do embedder |
| `tests/test_config.py` | Modificar | Adicionar testes para modo cloud |
| `.env.example` | Modificar | Documentar as novas variáveis |

> **Não criar arquivos novos.** A função auxiliar vai direto em `embedder.py` e `searcher.py` para preservar os mocks existentes (`src.ingestion.embedder.QdrantClient` e `src.retrieval.searcher.QdrantClient`).

---

## Chunk 1: Suporte a Qdrant Cloud no Settings e Módulos de Acesso

### Task 1: Atualizar `src/config/settings.py`

**Files:**
- Modify: `src/config/settings.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Escrever os testes que vão falhar**

Adicionar a classe `TestSettingsModoCloud` ao final de `tests/test_config.py`:

```python
class TestSettingsModoCloud:
    """Testes para o modo cloud do Qdrant via QDRANT_URL."""

    def test_modo_cloud_aceita_url_sem_qdrant_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que Settings aceita QDRANT_URL + QDRANT_API_KEY sem exigir QDRANT_HOST."""
        _desabilitar_dotenv(monkeypatch)
        monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
        monkeypatch.setenv("QDRANT_URL", "https://xyz.cloud.qdrant.io")
        monkeypatch.setenv("QDRANT_API_KEY", "chave-qdrant-cloud")
        monkeypatch.delenv("QDRANT_HOST", raising=False)

        settings = Settings()

        assert settings.qdrant_url == "https://xyz.cloud.qdrant.io"
        assert settings.qdrant_api_key == "chave-qdrant-cloud"
        assert settings.usar_qdrant_cloud is True

    def test_modo_cloud_lanca_erro_sem_qdrant_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que ValueError é lançado quando QDRANT_URL está definida mas QDRANT_API_KEY não."""
        _desabilitar_dotenv(monkeypatch)
        monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
        monkeypatch.setenv("QDRANT_URL", "https://xyz.cloud.qdrant.io")
        monkeypatch.delenv("QDRANT_API_KEY", raising=False)
        monkeypatch.delenv("QDRANT_HOST", raising=False)

        with pytest.raises(ValueError, match="QDRANT_API_KEY"):
            Settings()

    def test_modo_local_continua_exigindo_qdrant_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que QDRANT_HOST ainda é obrigatório quando QDRANT_URL está ausente."""
        _desabilitar_dotenv(monkeypatch)
        monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
        monkeypatch.delenv("QDRANT_URL", raising=False)
        monkeypatch.delenv("QDRANT_HOST", raising=False)

        with pytest.raises(ValueError, match="QDRANT_HOST"):
            Settings()

    def test_modo_local_usar_qdrant_cloud_e_falso(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifica que usar_qdrant_cloud é False no modo local."""
        _desabilitar_dotenv(monkeypatch)
        monkeypatch.setenv("NVIDIA_API_KEY", "chave-nvidia-teste")
        monkeypatch.setenv("QDRANT_HOST", "localhost")
        monkeypatch.delenv("QDRANT_URL", raising=False)

        settings = Settings()

        assert settings.usar_qdrant_cloud is False
```

- [ ] **Step 2: Rodar os novos testes para confirmar que falham**

```bash
python3 -m pytest tests/test_config.py::TestSettingsModoCloud -v
```

Esperado: 4 × `FAILED` — `AttributeError: 'Settings' object has no attribute 'qdrant_url'` ou `TypeError`.

- [ ] **Step 3: Implementar as mudanças em `src/config/settings.py`**

Substituir o bloco de configuração do Qdrant (linhas 37–41) por:

```python
        # --- Configurações do Qdrant ---
        # Modo cloud: QDRANT_URL + QDRANT_API_KEY
        # Modo local: QDRANT_HOST + QDRANT_PORT
        self.qdrant_url: str = os.environ.get("QDRANT_URL", "").strip()
        self.qdrant_api_key: str = os.environ.get("QDRANT_API_KEY", "").strip()

        if self.qdrant_url:
            # Modo cloud — valida que a chave de API foi fornecida
            if not self.qdrant_api_key:
                raise ValueError(
                    "Variável de ambiente obrigatória 'QDRANT_API_KEY' não encontrada "
                    "quando 'QDRANT_URL' está definida (modo cloud)."
                )
            self.qdrant_host: str = ""
        else:
            # Modo local — QDRANT_HOST é obrigatório
            self.qdrant_host = self._obter_obrigatorio("QDRANT_HOST")

        self.qdrant_port: int = int(os.environ.get("QDRANT_PORT", "6333"))
        self.qdrant_collection: str = os.environ.get(
            "QDRANT_COLLECTION", "jarvis_knowledge"
        )
```

Adicionar a property abaixo de `_obter_obrigatorio`:

```python
    @property
    def usar_qdrant_cloud(self) -> bool:
        """Retorna True se o modo cloud do Qdrant estiver configurado via QDRANT_URL."""
        return bool(self.qdrant_url)
```

Também atualizar o docstring do `__init__` — a linha `Raises` para incluir o modo cloud:

```python
        Raises:
            ValueError: se NVIDIA_API_KEY não estiver definida; se QDRANT_URL estiver
                definida mas QDRANT_API_KEY estiver ausente; ou se nenhuma das duas
                (QDRANT_URL, QDRANT_HOST) estiver definida.
```

- [ ] **Step 4: Rodar os novos testes e todos os testes de config**

```bash
python3 -m pytest tests/test_config.py -v
```

Esperado: todos passando (incluindo os 4 novos + os 4 existentes = 8 total).

- [ ] **Step 5: Commit**

```bash
git add src/config/settings.py tests/test_config.py
git commit -m "feat(config): suportar modo cloud do Qdrant via QDRANT_URL e QDRANT_API_KEY"
```

---

### Task 2: Atualizar `src/ingestion/embedder.py`

**Files:**
- Modify: `src/ingestion/embedder.py`

> Os testes existentes em `tests/test_embedder.py` **não precisam ser alterados** — eles já mockam `src.ingestion.embedder.QdrantClient`, que continua sendo importado neste módulo.

- [ ] **Step 1: Rodar os testes existentes do embedder para confirmar linha base**

```bash
python3 -m pytest tests/test_embedder.py -v
```

Esperado: todos passando (4 testes).

- [ ] **Step 2: Adicionar a função auxiliar e atualizar o `__init__` em `embedder.py`**

Adicionar após os imports (antes da definição de `VectorIndexer`):

```python
def _criar_cliente_qdrant(settings: Settings) -> QdrantClient:
    """Cria o cliente Qdrant no modo local (host:port) ou cloud (url + api_key)."""
    if settings.usar_qdrant_cloud:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
```

No `__init__` de `VectorIndexer`, substituir:

```python
        # Conecta ao Qdrant com as configurações fornecidas
        self.cliente = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
```

Por:

```python
        # Conecta ao Qdrant no modo local ou cloud conforme a configuração
        self.cliente = _criar_cliente_qdrant(settings)
```

Atualizar o `logger.debug` para não referenciar host/port diretamente:

```python
        logger.debug(
            "VectorIndexer inicializado com modelo '%s' (dim=%d, cloud=%s).",
            settings.embedding_model,
            self._dim,
            settings.usar_qdrant_cloud,
        )
```

- [ ] **Step 3: Rodar os testes do embedder**

```bash
python3 -m pytest tests/test_embedder.py -v
```

Esperado: todos passando (sem alterações nos testes).

- [ ] **Step 4: Commit**

```bash
git add src/ingestion/embedder.py
git commit -m "feat(ingestion): usar função auxiliar para criar cliente Qdrant local ou cloud"
```

---

### Task 3: Atualizar `src/retrieval/searcher.py`

**Files:**
- Modify: `src/retrieval/searcher.py`

> Mesma estratégia do embedder. Testes existentes em `tests/test_searcher.py` não precisam ser alterados.

- [ ] **Step 1: Rodar os testes existentes do searcher**

```bash
python3 -m pytest tests/test_searcher.py -v
```

Esperado: todos passando (9 testes).

- [ ] **Step 2: Adicionar a função auxiliar e atualizar o `__init__` em `searcher.py`**

Adicionar após os imports (antes da definição de `SemanticSearcher`):

```python
def _criar_cliente_qdrant(settings: Settings) -> QdrantClient:
    """Cria o cliente Qdrant no modo local (host:port) ou cloud (url + api_key)."""
    if settings.usar_qdrant_cloud:
        return QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
```

No `__init__` de `SemanticSearcher`, substituir:

```python
        # Conecta ao servidor Qdrant local
        self.cliente = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
```

Por:

```python
        # Conecta ao Qdrant no modo local ou cloud conforme a configuração
        self.cliente = _criar_cliente_qdrant(settings)
```

Atualizar o `logger.debug` do `__init__`:

```python
        logger.debug(
            "SemanticSearcher inicializado com modelo '%s' (cloud=%s).",
            settings.embedding_model,
            settings.usar_qdrant_cloud,
        )
```

- [ ] **Step 3: Rodar todos os testes**

```bash
python3 -m pytest tests/ -v
```

Esperado: 51+ testes passando, zero falhas.

- [ ] **Step 4: Commit**

```bash
git add src/retrieval/searcher.py
git commit -m "feat(retrieval): usar função auxiliar para criar cliente Qdrant local ou cloud"
```

---

### Task 4: Atualizar `.env.example`

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Adicionar as novas variáveis ao `.env.example`**

Substituir o bloco `# Qdrant` por:

```
# Qdrant — Modo Local (Docker)
# Use este modo para desenvolvimento local com docker-compose
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=jarvis_knowledge

# Qdrant — Modo Cloud (Qdrant Cloud)
# Defina QDRANT_URL para ativar o modo cloud (QDRANT_HOST será ignorado)
# Obtenha sua URL e API Key em: https://cloud.qdrant.io
# QDRANT_URL=https://xxxxxxxxxxxx.us-east4-0.gcp.cloud.qdrant.io
# QDRANT_API_KEY=your_qdrant_cloud_api_key_here
```

- [ ] **Step 2: Commit**

```bash
git add .env.example
git commit -m "docs(config): documentar variáveis de modo cloud do Qdrant no .env.example"
```

---

## Chunk 2: Ingestão no Qdrant Cloud e Configuração do Streamlit Cloud

> **Atenção:** Os passos abaixo são **ações manuais do usuário** (não automatizáveis pelo agente). O agente pode executar `scripts/ingest.py` se o usuário fornecer as credenciais.

### Task 5: Criar Cluster no Qdrant Cloud (ação manual)

- [ ] **Step 1: Criar conta e cluster**
  1. Acessar [cloud.qdrant.io](https://cloud.qdrant.io)
  2. Criar uma conta (free tier disponível)
  3. Criar um novo cluster — região mais próxima (ex: GCP us-east4 ou AWS us-east-1)
  4. Anotar a **Cluster URL** (ex: `https://xxxx.cloud.qdrant.io`) e gerar uma **API Key**

- [ ] **Step 2: Copiar credenciais para o `.env` local**

Adicionar ao `.env` (nunca commitar):

```
QDRANT_URL=https://xxxx.cloud.qdrant.io
QDRANT_API_KEY=<sua_api_key>
```

Comentar ou remover `QDRANT_HOST=localhost` (pois `QDRANT_URL` tem precedência).

---

### Task 6: Ingesta dos Documentos no Qdrant Cloud

- [ ] **Step 1: Verificar que os PDFs existem localmente**

```bash
ls data/raw/*.pdf | wc -l
```

Esperado: `15` arquivos.

- [ ] **Step 2: Executar o script de ingestão apontando para o Qdrant Cloud**

Com o `.env` atualizado com `QDRANT_URL` e `QDRANT_API_KEY`:

```bash
python3 scripts/ingest.py --caminho data/raw/
```

Acompanhar o output — espera-se logs de `N chunks indexados na coleção 'jarvis_knowledge'`.

> **Estimativa:** ~1.5GB de PDFs, pode levar 30–90 min dependendo da máquina. Execute em background se necessário.

- [ ] **Step 3: Verificar a ingestão no dashboard do Qdrant Cloud**

Acessar `https://cloud.qdrant.io` → selecionar o cluster → Collections → `jarvis_knowledge`.
Verificar que a coleção existe e contém pontos (vetores).

---

### Task 7: Configurar Secrets no Streamlit Cloud

- [ ] **Step 1: Acessar as configurações do app no Streamlit Cloud**

No dashboard do Streamlit Cloud:
1. Selecionar o app Jarvis
2. Ir em `Settings` → `Secrets`

- [ ] **Step 2: Adicionar os secrets**

```toml
NVIDIA_API_KEY = "sua_nvidia_api_key"
QDRANT_URL = "https://xxxx.cloud.qdrant.io"
QDRANT_API_KEY = "sua_qdrant_api_key"
```

> **Não adicionar `QDRANT_HOST`** — com `QDRANT_URL` definida, o modo cloud é ativado automaticamente.

- [ ] **Step 3: Forçar redeploy do app**

Após salvar os secrets, o Streamlit Cloud faz redeploy automaticamente. Verificar os logs.

---

## Verificação Final

- [ ] `python3 -m pytest tests/ -v` → todos passando
- [ ] Dashboard Qdrant Cloud → coleção `jarvis_knowledge` com vetores indexados
- [ ] App no Streamlit Cloud → preencher anamnese, enviar pergunta → receber resposta com fontes citadas
- [ ] Logs do Streamlit Cloud → sem erros de `ConnectionRefusedError` ou `QDRANT_HOST`
