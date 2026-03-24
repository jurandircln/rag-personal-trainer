"""Testes unitários para src/generation/catalogo.py."""
import pytest

from src.generation.catalogo import CatalogoExercicios


# ---------------------------------------------------------------------------
# Fixture: catálogo mínimo em memória (tmp_path)
# ---------------------------------------------------------------------------

CATALOGO_MINIMO = """\
## Membros Inferiores

| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |
|---|---|---|---|---|
| Agachamento Livre | Quadríceps, Glúteo | Leg Press, Goblet Squat | Hérnia de disco, dor aguda no joelho. | Peso Livre |
| Leg Press 45º | Quadríceps, Glúteo | Agachamento Hack, Passada | Dor lombar crônica. | Máquina |
| Cadeira Extensora | Quadríceps | Extensão com Caneleira | Condromalácia patelar aguda. | Máquina |

## Tronco e Core

| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |
|---|---|---|---|---|
| Prancha Abdominal | Transverso do abdome | Deadbug, Prancha Lateral | Dor lombar aguda. | Peso Corporal |
| Abdominal Supra | Reto Abdominal | Abdominal na Máquina | Protusões discais cervicais. | Peso Corporal |
"""


@pytest.fixture
def catalogo(tmp_path):
    """Instancia CatalogoExercicios com catálogo mínimo em arquivo temporário."""
    arquivo = tmp_path / "reference.md"
    arquivo.write_text(CATALOGO_MINIMO, encoding="utf-8")
    return CatalogoExercicios(str(arquivo))


# ---------------------------------------------------------------------------
# Testes de inicialização
# ---------------------------------------------------------------------------


class TestInicializacao:
    """Testes de inicialização e erros de arquivo."""

    def test_arquivo_nao_encontrado(self, tmp_path) -> None:
        """FileNotFoundError se o arquivo não existir."""
        with pytest.raises(FileNotFoundError):
            CatalogoExercicios(str(tmp_path / "inexistente.md"))

    def test_arquivo_binario_lanca_value_error(self, tmp_path) -> None:
        """ValueError se o arquivo não for texto UTF-8 válido."""
        arquivo = tmp_path / "binario.md"
        arquivo.write_bytes(b"\x50\x4b\x03\x04\xff\xfe")  # cabeçalho ZIP
        with pytest.raises(ValueError, match="não é texto Markdown válido"):
            CatalogoExercicios(str(arquivo))


# ---------------------------------------------------------------------------
# Testes de filtro de equipamento
# ---------------------------------------------------------------------------


class TestFiltroEquipamento:
    """Testes para filtragem por tag de equipamento."""

    def test_tag_ausente_remove_exercicio(self, catalogo) -> None:
        """Exercício removido quando tag não está na lista."""
        resultado = catalogo.filtrar(["Peso Corporal"], "Intermediário", "")
        assert "Agachamento Livre" not in resultado
        assert "Leg Press" not in resultado

    def test_tag_presente_mantem_exercicio(self, catalogo) -> None:
        """Exercício mantido quando tag está na lista."""
        resultado = catalogo.filtrar(["Peso Livre"], "Intermediário", "")
        assert "Agachamento Livre" in resultado

    def test_normalizacao_maquinas_plural(self, catalogo) -> None:
        """Valor 'Máquinas' (plural) normalizado para 'Máquina' antes de filtrar."""
        resultado = catalogo.filtrar(["Máquinas"], "Intermediário", "")
        assert "Leg Press 45º" in resultado
        assert "Cadeira Extensora" in resultado

    def test_normalizacao_elasticos_plural(self, tmp_path) -> None:
        """Valor 'Elásticos' (plural) normalizado para 'Elástico'."""
        conteudo = (
            "## Grupo\n\n"
            "| Exercício | Músculo Alvo | Substitutos | Contraindicações / Alertas | Tag de Equipamento |\n"
            "|---|---|---|---|---|\n"
            "| Exercício Elástico | Bíceps | Rosca Direta | Nenhuma. | Elástico |\n"
        )
        arquivo = tmp_path / "ref.md"
        arquivo.write_text(conteudo, encoding="utf-8")
        c = CatalogoExercicios(str(arquivo))
        resultado = c.filtrar(["Elásticos"], "Intermediário", "")
        assert "Exercício Elástico" in resultado

    def test_sem_equipamento_mapeia_para_peso_corporal(self, catalogo) -> None:
        """'Sem Equipamento' é tratado como fallback de 'Peso Corporal'."""
        resultado = catalogo.filtrar(["Sem Equipamento"], "Intermediário", "")
        assert "Prancha Abdominal" in resultado

    def test_deduplicacao_sem_equipamento_e_peso_corporal(self, catalogo) -> None:
        """['Sem Equipamento', 'Peso Corporal'] não duplica exercícios de Peso Corporal."""
        resultado = catalogo.filtrar(
            ["Sem Equipamento", "Peso Corporal"], "Intermediário", ""
        )
        # Prancha deve aparecer exatamente uma vez
        assert resultado.count("Prancha Abdominal") == 1

    def test_retorna_none_quando_nenhum_exercicio_passa(self, catalogo) -> None:
        """Retorna None quando nenhum exercício passa pelo filtro de equipamento."""
        resultado = catalogo.filtrar(["Elástico"], "Intermediário", "")
        assert resultado is None


# ---------------------------------------------------------------------------
# Testes de sinalização de nível
# ---------------------------------------------------------------------------


class TestSinalizacaoNivel:
    """Testes para flags de prioridade por nível do aluno."""

    def test_iniciante_prioriza_maquina(self, catalogo) -> None:
        """Exercícios com tag Máquina recebem [PRIORIZAR] para iniciantes."""
        resultado = catalogo.filtrar(["Máquinas"], "Iniciante", "")
        assert "[PRIORIZAR]" in resultado
        assert "Leg Press 45º" in resultado

    def test_avancado_prioriza_peso_livre(self, catalogo) -> None:
        """Exercícios com tag Peso Livre recebem [PRIORIZAR] para avançados."""
        resultado = catalogo.filtrar(["Peso Livre"], "Avançado", "")
        assert "[PRIORIZAR]" in resultado
        assert "Agachamento Livre" in resultado

    def test_intermediario_sem_flag_priorizar(self, catalogo) -> None:
        """Nível Intermediário não adiciona flag [PRIORIZAR]."""
        resultado = catalogo.filtrar(["Peso Livre", "Máquinas"], "Intermediário", "")
        assert "[PRIORIZAR]" not in resultado


# ---------------------------------------------------------------------------
# Testes de contraindicações
# ---------------------------------------------------------------------------


class TestContraindicacoes:
    """Testes para detecção e substituição por contraindicações."""

    def test_contraindicacao_remove_exercicio(self, catalogo) -> None:
        """Exercício removido quando há correspondência com contraindicação."""
        resultado = catalogo.filtrar(["Peso Livre"], "Intermediário", "joelho")
        # filtrar() retorna None quando nenhum exercício resta — Agachamento foi removido
        assert resultado is None or "Agachamento Livre" not in resultado

    def test_contraindicacao_adiciona_substituto_com_flag(self, catalogo) -> None:
        """Substituto elegível adicionado com flag [SUBSTITUTO OBRIGATÓRIO]."""
        resultado = catalogo.filtrar(["Peso Livre", "Máquinas"], "Intermediário", "joelho")
        # Agachamento removido; Leg Press é substituto com tag Máquina (disponível)
        assert "Agachamento Livre" not in resultado
        assert "[SUBSTITUTO OBRIGATÓRIO]" in resultado

    def test_contraindicacao_descarta_substituto_sem_equipamento(self, catalogo) -> None:
        """Substituto descartado quando sua tag não está na lista de equipamentos."""
        # Apenas Peso Corporal disponível; substitutos do Agachamento têm tags fora da lista
        resultado = catalogo.filtrar(["Peso Corporal"], "Intermediário", "joelho")
        # Nenhum substituto elegível (Leg Press=Máquina, Goblet Squat não no catálogo)
        # então o exercício é removido sem flag
        assert "[SUBSTITUTO OBRIGATÓRIO]" not in (resultado or "")

    def test_priorizar_removido_por_contraindicacao(self, catalogo) -> None:
        """Exercício com [PRIORIZAR] é removido quando há contraindicação ativa."""
        resultado = catalogo.filtrar(["Peso Livre"], "Avançado", "joelho")
        # Agachamento Livre seria [PRIORIZAR] para avançado, mas contraindicação remove;
        # filtrar() retorna None quando nenhum exercício resta
        assert resultado is None or "Agachamento Livre" not in resultado

    def test_normalizacao_ascii_na_restricao(self, catalogo) -> None:
        """Acentos na restrição são normalizados antes do matching."""
        resultado_sem_acento = catalogo.filtrar(["Peso Livre"], "Intermediário", "joelho")
        resultado_com_acento = catalogo.filtrar(["Peso Livre"], "Intermediário", "joêlho")
        assert resultado_sem_acento == resultado_com_acento

    def test_substituto_nao_passa_por_contraindicacao(self, catalogo) -> None:
        """Substitutos NÃO passam por filtro de contraindicação (v1 — intencional)."""
        resultado = catalogo.filtrar(["Máquinas"], "Intermediário", "joelho")
        # Leg Press (tag Máquina) não tem "joelho" na contraindicação, então
        # pode aparecer como exercício normal OU como substituto
        assert resultado is not None  # ao menos um exercício/substituto deve sobrar

    def test_intermediario_contraindicacao_ainda_atua(self, catalogo) -> None:
        """Contraindicação remove exercícios mesmo sem flag de nível."""
        resultado = catalogo.filtrar(["Peso Livre"], "Intermediário", "joelho")
        # filtrar() retorna None quando nenhum exercício resta — Agachamento foi removido
        assert resultado is None or "Agachamento Livre" not in resultado

    def test_grupos_sem_exercicios_omitidos(self, catalogo) -> None:
        """Headers ## de grupos sem exercícios são omitidos do resultado."""
        resultado = catalogo.filtrar(["Peso Corporal"], "Intermediário", "")
        assert "Membros Inferiores" not in resultado
        assert "Tronco e Core" in resultado
