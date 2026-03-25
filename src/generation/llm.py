"""
Realiza chamadas ao Llama 3.x via NVIDIA NIM API usando LangChain.

Carrega a metodologia RB e o catálogo de exercícios no startup e os injeta
conforme os dados do aluno fornecidos em cada chamada.
"""

import logging
import os

from langchain_core.messages import HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from src.config.settings import Settings
from src.config.types import RespostaRAG, ResultadoBusca
from src.generation.catalogo import CatalogoExercicios
from src.generation.prompt import montar_prompt

logger = logging.getLogger(__name__)

# Caminho do arquivo de metodologia relativo ao diretório deste módulo
_CAMINHO_METODOLOGIA = os.path.join(
    os.path.dirname(__file__), "metodologia.txt"
)

# Caminho do catálogo de exercícios relativo à raiz do projeto
_CAMINHO_CATALOGO = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "reference.md")
)


def _carregar_metodologia() -> str:
    """Carrega o texto da metodologia RB do arquivo, retorna string vazia se não existir."""
    if not os.path.exists(_CAMINHO_METODOLOGIA):
        logger.warning(
            "Arquivo de metodologia não encontrado em '%s'. "
            "Execute: python3 scripts/extract_metodologia.py",
            _CAMINHO_METODOLOGIA,
        )
        return ""
    with open(_CAMINHO_METODOLOGIA, encoding="utf-8") as f:
        conteudo = f.read()
    logger.debug("Metodologia carregada (%d chars).", len(conteudo))
    return conteudo


class RAGGenerator:
    """Gerador de respostas RAG utilizando Llama 3.x via NVIDIA NIM API."""

    def __init__(self, settings: Settings) -> None:
        """Inicializa o gerador RAG, carrega a metodologia e o catálogo de exercícios.

        Args:
            settings: instância de Settings com credenciais e parâmetros do modelo.
        """
        self.settings = settings
        self.llm = ChatNVIDIA(
            model=settings.llm_model,
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
            max_tokens=settings.llm_max_tokens,
        )
        # Carrega a metodologia uma única vez por instância
        self.metodologia = _carregar_metodologia()
        # Carrega o catálogo de exercícios uma única vez por instância
        try:
            self.catalogo = CatalogoExercicios(_CAMINHO_CATALOGO)
            logger.debug("Catálogo de exercícios carregado de '%s'.", _CAMINHO_CATALOGO)
        except (FileNotFoundError, ValueError) as e:
            logger.warning("Catálogo de exercícios não disponível: %s", e)
            self.catalogo = None
        logger.debug("RAGGenerator inicializado com modelo '%s'.", settings.llm_model)

    def gerar(
        self,
        query: str,
        resultados: list[ResultadoBusca],
        contexto_aluno: str = "",
        equipamentos=None,
        nivel: str = "",
        restricoes: str = "",
    ) -> RespostaRAG:
        """Gera uma resposta RAG com base na query, resultados e contexto do aluno.

        Quando equipamentos e nivel são fornecidos, filtra o catálogo de exercícios
        e injeta o resultado filtrado no prompt para guiar a seleção de movimentos.

        Args:
            query: pergunta ou instrução do personal trainer.
            resultados: chunks recuperados pela busca semântica.
            contexto_aluno: dados da anamnese formatados como texto.
            equipamentos: lista de equipamentos disponíveis (valores brutos do app.py).
                None ou lista vazia desativa o catálogo.
            nivel: nível de condicionamento do aluno ("Iniciante", "Intermediário", "Avançado").
                String vazia desativa o catálogo.
            restricoes: texto livre de lesões ou restrições físicas do aluno.

        Returns:
            RespostaRAG com texto gerado e fontes únicas utilizadas.
        """
        # Determina catalogo_filtrado: ativa somente com equipamentos e nivel fornecidos
        catalogo_filtrado = None
        if equipamentos and nivel and self.catalogo is not None:
            catalogo_filtrado = self.catalogo.filtrar(equipamentos, nivel, restricoes)
            logger.debug(
                "Catálogo filtrado: %s.",
                "ativo" if catalogo_filtrado else "sem exercícios compatíveis",
            )

        prompt = montar_prompt(
            query=query,
            resultados=resultados,
            metodologia=self.metodologia,
            contexto_aluno=contexto_aluno,
            catalogo_filtrado=catalogo_filtrado,
        )
        logger.debug("Enviando prompt ao LLM com %d referência(s).", len(resultados))

        # Invoca o modelo e captura erros de API
        try:
            resposta = self.llm.invoke([HumanMessage(content=prompt)])
            texto = resposta.content
        except Exception as e:
            logger.error("Falha ao invocar o LLM: %s", e)
            raise RuntimeError(f"Erro ao gerar resposta do LLM: {e}") from e

        fontes = list({r.chunk.fonte for r in resultados})

        logger.info("Resposta gerada com %d fonte(s).", len(fontes))
        return RespostaRAG(texto=texto, fontes=fontes)
