"""Módulo de observabilidade do Jarvis — coleta de métricas de desempenho do LLM."""
from src.observability.metrics import registrar_feedback, registrar_resposta

__all__ = ["registrar_resposta", "registrar_feedback"]
