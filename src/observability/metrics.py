"""
Registra métricas de desempenho do Jarvis no Supabase (Postgres).

Todas as funções são best-effort: falhas de rede ou configuração ausente
são logadas como WARNING e descartadas — o app continua normalmente.
"""
import logging
import os
import threading
from typing import Optional

from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Singleton do cliente — inicializado na primeira chamada bem-sucedida
_cliente: Optional[Client] = None
_lock = threading.Lock()


def _obter_cliente() -> Optional[Client]:
    """Retorna o cliente Supabase ou None se as variáveis não estiverem configuradas.

    Usa double-checked locking para segurança em ambiente multi-thread.
    Não cacheia None nem erros: tenta reconectar a cada chamada quando
    o cliente ainda não foi inicializado com sucesso.

    Returns:
        Instância do cliente Supabase ou None.
    """
    global _cliente
    if _cliente is not None:
        return _cliente
    with _lock:
        if _cliente is not None:  # double-checked locking
            return _cliente

        url = os.environ.get("SUPABASE_URL", "").strip()
        key = os.environ.get("SUPABASE_KEY", "").strip()

        if not url or not key:
            logger.warning(
                "SUPABASE_URL ou SUPABASE_KEY não configurados — métricas desativadas."
            )
            return None

        try:
            _cliente = create_client(url, key)
            logger.debug("Cliente Supabase inicializado com sucesso.")
        except Exception as exc:
            logger.warning("Falha ao criar cliente Supabase: %s", exc)

    return _cliente


def registrar_resposta(tempo_segundos: float) -> None:
    """Insere uma linha em jarvis_respostas. Falha silenciosa com log warning.

    Args:
        tempo_segundos: tempo total de geração da resposta pelo LLM, em segundos.
    """
    cliente = _obter_cliente()
    if cliente is None:
        return
    try:
        cliente.table("jarvis_respostas").insert(
            {"tempo_resposta_segundos": tempo_segundos}
        ).execute()
        logger.debug("Resposta registrada: %.2fs.", tempo_segundos)
    except Exception as exc:
        logger.warning("Falha ao registrar resposta no Supabase: %s", exc)


def registrar_feedback(satisfeito: bool) -> None:
    """Insere uma linha em jarvis_feedbacks. Falha silenciosa com log warning.

    Args:
        satisfeito: True se o usuário marcou 'Satisfeito', False caso contrário.
    """
    cliente = _obter_cliente()
    if cliente is None:
        return
    try:
        cliente.table("jarvis_feedbacks").insert(
            {"satisfeito": satisfeito}
        ).execute()
        logger.debug("Feedback registrado: satisfeito=%s.", satisfeito)
    except Exception as exc:
        logger.warning("Falha ao registrar feedback no Supabase: %s", exc)
