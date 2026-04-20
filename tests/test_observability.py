"""Testes unitários do módulo de observabilidade."""
from unittest.mock import MagicMock, patch

import pytest


class TestRegistrarResposta:
    """Testes para a função registrar_resposta."""

    def test_insere_linha_quando_cliente_disponivel(self, monkeypatch):
        """Quando SUPABASE_URL e SUPABASE_KEY estão definidas, insere em jarvis_respostas."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None  # garante estado limpo

            from src.observability.metrics import registrar_resposta
            registrar_resposta(1.23)

        mock_cliente.table.assert_called_once_with("jarvis_respostas")
        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"tempo_resposta_segundos": 1.23}
        )

    def test_nao_levanta_excecao_quando_variaveis_ausentes(self, monkeypatch):
        """Quando SUPABASE_URL não está definida, a função retorna silenciosamente."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None
            from src.observability.metrics import registrar_resposta
            registrar_resposta(0.5)  # não deve lançar exceção

    def test_nao_levanta_excecao_quando_insert_falha(self, monkeypatch):
        """Falha no insert é capturada silenciosamente."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.side_effect = (
            RuntimeError("timeout")
        )

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_resposta
            registrar_resposta(0.8)  # não deve lançar exceção


class TestRegistrarFeedback:
    """Testes para a função registrar_feedback."""

    def test_insere_satisfeito_true(self, monkeypatch):
        """Feedback positivo insere satisfeito=True em jarvis_feedbacks."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=True)

        mock_cliente.table.assert_called_once_with("jarvis_feedbacks")
        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"satisfeito": True}
        )

    def test_insere_satisfeito_false(self, monkeypatch):
        """Feedback negativo insere satisfeito=False em jarvis_feedbacks."""
        monkeypatch.setenv("SUPABASE_URL", "https://exemplo.supabase.co")
        monkeypatch.setenv("SUPABASE_KEY", "chave-de-teste")

        mock_cliente = MagicMock()
        mock_cliente.table.return_value.insert.return_value.execute.return_value = None

        with patch("src.observability.metrics.create_client", return_value=mock_cliente), \
             patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None

            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=False)

        mock_cliente.table.return_value.insert.assert_called_once_with(
            {"satisfeito": False}
        )

    def test_nao_levanta_excecao_quando_variaveis_ausentes(self, monkeypatch):
        """Sem variáveis de ambiente, retorna silenciosamente."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        with patch("src.observability.metrics._cliente", None):
            import src.observability.metrics as mod
            mod._cliente = None
            from src.observability.metrics import registrar_feedback
            registrar_feedback(satisfeito=True)  # não deve lançar exceção
