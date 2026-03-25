"""
Carrega variáveis de ambiente do .env e expõe as configurações do sistema.

Utiliza python-dotenv para leitura do arquivo .env e valida
a presença das variáveis obrigatórias na inicialização.
"""

import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Settings:
    """Centraliza todas as configurações do sistema Jarvis carregadas do ambiente."""

    def __init__(self) -> None:
        """Carrega o arquivo .env e inicializa os atributos de configuração.

        Raises:
            ValueError: se NVIDIA_API_KEY não estiver definida; se QDRANT_URL estiver
                definida mas QDRANT_API_KEY estiver ausente; ou se nenhuma das duas
                (QDRANT_URL, QDRANT_HOST) estiver definida.
        """
        # Carrega variáveis do arquivo .env para o ambiente do processo
        load_dotenv()

        # --- Configurações da API NVIDIA NIM ---
        self.nvidia_api_key: str = self._obter_obrigatorio("NVIDIA_API_KEY")
        self.nvidia_base_url: str = os.environ.get(
            "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
        )
        self.llm_model: str = os.environ.get(
            "LLM_MODEL", "meta/llama-3.1-70b-instruct"
        )
        # Máximo de tokens na resposta do LLM (padrão: 4096 — limite do Llama 3.1 70B no NIM)
        self.llm_max_tokens: int = int(os.environ.get("LLM_MAX_TOKENS", "4096"))

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

        # --- Configurações de embeddings ---
        self.embedding_model: str = os.environ.get(
            "EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        )

        # --- Configurações de log ---
        self.log_level: str = os.environ.get("LOG_LEVEL", "INFO")

        logger.debug("Configurações carregadas com sucesso.")

    def _obter_obrigatorio(self, nome_variavel: str) -> str:
        """Lê uma variável de ambiente obrigatória ou lança ValueError.

        Args:
            nome_variavel: nome da variável de ambiente esperada.

        Returns:
            O valor da variável de ambiente.

        Raises:
            ValueError: se a variável não estiver definida ou estiver vazia.
        """
        valor = os.environ.get(nome_variavel, "").strip()
        if not valor:
            raise ValueError(
                f"Variável de ambiente obrigatória '{nome_variavel}' não encontrada. "
                f"Verifique o arquivo .env ou as variáveis de ambiente do sistema."
            )
        return valor

    @property
    def usar_qdrant_cloud(self) -> bool:
        """Retorna True se o modo cloud do Qdrant estiver configurado via QDRANT_URL."""
        return bool(self.qdrant_url)
