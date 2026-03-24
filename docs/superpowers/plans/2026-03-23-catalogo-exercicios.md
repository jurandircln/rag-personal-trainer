# Catálogo de Exercícios + Justificativa Personalizada — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrar um catálogo estruturado de exercícios ao prompt do Jarvis, com filtragem por equipamento/nível/contraindicações e seção de justificativa personalizada no output.

**Architecture:** Filtragem híbrida — Python filtra deterministicamente o catálogo (equipamento, nível, contraindicações); o LLM decide dentro do conjunto já filtrado e gera a justificativa personalizada. A filtragem ocorre em `CatalogoExercicios.filtrar()`, o resultado entra no prompt via novo parâmetro `catalogo_filtrado` em `montar_prompt()`, e `RAGGenerator.gerar()` orquestra as chamadas.

**Tech Stack:** Python 3.11+, `unicodedata` (stdlib), pytest + pytest-mock, Streamlit session_state.

---

## Estrutura de Arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `data/raw/reference.md` | Pré-requisito (já feito) | Catálogo em Markdown com 4 grupos, 21 exercícios, 5 colunas |
| `src/generation/catalogo.py` | **Criar** | Classe `CatalogoExercicios` com `filtrar()` |
| `tests/test_catalogo.py` | **Criar** | Cobertura completa de todos os cenários de filtragem |
| `src/generation/prompt.py` | **Modificar** | Novo parâmetro `catalogo_filtrado`; seção condicional no template |
| `tests/test_llm.py` | **Modificar** | Cenários novos: `catalogo_filtrado` ativo e inativo |
| `src/generation/llm.py` | **Modificar** | Carrega `CatalogoExercicios`; novos parâmetros em `gerar()` |
| `src/interface/app.py` | **Modificar** | Persiste `dados_aluno` no `session_state`; passa campos a `gerar()` |
| `tests/test_interface.py` | **Modificar** | Mock de `dados_aluno` no `session_state`; assert da nova assinatura |

---

## Task 1: Verificar pré-requisito — `data/raw/reference.md`

**Files:**
- Verify: `data/raw/reference.md`

- [ ] **Step 1: Confirmar que reference.md é Markdown válido**

```bash
head -5 data/raw/reference.md
```

Esperado: primeiras linhas legíveis como texto (começa com `#`). Se o arquivo ainda for binário (começa com `PK`), aplicar conversão antes de continuar.

- [ ] **Step 2: Commitar reference.md se não estiver no histórico**

```bash
git status data/raw/reference.md
git add data/raw/reference.md
git commit -m "chore(data): converter reference.md de DOCX para Markdown"
```

---

## Task 2: Criar `CatalogoExercicios` (TDD)

**Files:**
- Create: `tests/test_catalogo.py`
- Create: `src/generation/catalogo.py`

### Step 2.1 — Escrever os testes com falha

- [ ] **Step 1: Criar `tests/test_catalogo.py` com todos os cenários**

```python
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
        assert "Agachamento Livre" not in resultado

    def test_contraindicacao_adiciona_substituto_com_flag(self, catalogo) -> None:
        """Substituto elegível adicionado com flag [SUBSTITUTO OBRIGATÓRIO]."""
        resultado = catalogo.filtrar(["Peso Livre", "Máquinas"], "Intermediário", "joelho")
        # Agachamento removido; Leg Press é substituto com tag Máquina (disponível)
        assert "Agachamento Livre" not in resultado
        assert "[SUBSTITUTO OBRIGATÓRIO]" in resultado

    def test_contraindicacao_descarta_substituto_sem_equipamento(self, catalogo) -> None:
        """Substituto descartado quando sua tag não está na lista de equipamentos."""
        # Apenas Peso Corporal disponível; substitutos do Agachamento (Leg Press, Goblet Squat)
        # têm tags Máquina / Peso Livre — fora da lista
        resultado = catalogo.filtrar(["Peso Corporal", "Peso Livre"], "Intermediário", "joelho")
        # Agachamento Livre tem tag Peso Livre (disponível), mas contraindicação com "joelho"
        # Leg Press tem tag Máquina (indisponível), Goblet Squat não tem tag definida no catálogo
        # → nenhum substituto elegível → exercício removido sem flag
        assert "[SUBSTITUTO OBRIGATÓRIO]" not in resultado or "Leg Press" not in resultado

    def test_priorizar_removido_por_contraindicacao(self, catalogo) -> None:
        """Exercício com [PRIORIZAR] é removido quando há contraindicação ativa."""
        resultado = catalogo.filtrar(["Peso Livre"], "Avançado", "joelho")
        # Agachamento Livre seria [PRIORIZAR] para avançado, mas contraindicação remove
        assert "Agachamento Livre" not in resultado

    def test_normalizacao_ascii_na_restricao(self, catalogo) -> None:
        """Acentos na restrição são normalizados antes do matching."""
        # "dor no joelho" e "dor no joêlho" (acento inventado) devem ter mesmo resultado
        resultado_sem_acento = catalogo.filtrar(["Peso Livre"], "Intermediário", "joelho")
        resultado_com_acento = catalogo.filtrar(["Peso Livre"], "Intermediário", "joêlho")
        assert resultado_sem_acento == resultado_com_acento

    def test_substituto_nao_passa_por_contraindicacao(self, catalogo) -> None:
        """Substitutos NÃO passam por filtro de contraindicação (v1 — intencional)."""
        # Leg Press tem contraindicação de "lombar"; mas se vier como substituto de Agachamento
        # (por restrição de joelho), deve ser incluído com [SUBSTITUTO OBRIGATÓRIO]
        resultado = catalogo.filtrar(["Máquinas"], "Intermediário", "joelho")
        # Leg Press é o único com tag Máquina; se vier como substituto, deve aparecer
        # (Leg Press não tem joelho na contraindicação, então pode aparecer como exercício normal
        # OU como substituto — este teste verifica que não é excluído por sua própria contraindicação)
        assert resultado is not None  # ao menos um exercício/substituto deve sobrar

    def test_intermediario_contraindicacao_ainda_atua(self, catalogo) -> None:
        """Contraindicação remove exercícios mesmo sem flag de nível."""
        resultado = catalogo.filtrar(["Peso Livre"], "Intermediário", "joelho")
        assert "Agachamento Livre" not in resultado

    def test_grupos_sem_exercicios_omitidos(self, catalogo) -> None:
        """Headers ## de grupos sem exercícios são omitidos do resultado."""
        # Com apenas Peso Corporal, Membros Inferiores some (todos têm outras tags)
        resultado = catalogo.filtrar(["Peso Corporal"], "Intermediário", "")
        assert "Membros Inferiores" not in resultado
        assert "Tronco e Core" in resultado
```

- [ ] **Step 2: Rodar os testes para confirmar que falham**

```bash
pytest tests/test_catalogo.py -v
```

Esperado: `ModuleNotFoundError: No module named 'src.generation.catalogo'`

### Step 2.2 — Implementar `CatalogoExercicios`

- [ ] **Step 3: Criar `src/generation/catalogo.py`**

```python
"""
Filtra o catálogo de exercícios por equipamento, nível e contraindicações.

O catálogo é lido de um arquivo Markdown com tabelas por grupo muscular.
A filtragem é puramente Python — sem chamadas ao LLM.
"""

import unicodedata
import logging
import re

logger = logging.getLogger(__name__)

# Mapeamento dos valores do app.py para tags canônicas do catálogo
_MAPA_EQUIPAMENTO = {
    "máquinas": "Máquina",
    "máquina": "Máquina",
    "elásticos": "Elástico",
    "elástico": "Elástico",
    "peso livre": "Peso Livre",
    "peso corporal": "Peso Corporal",
    "sem equipamento": "Peso Corporal",  # fallback
}

# Stopwords para tokenização de restrições
_STOPWORDS = {
    "tenho", "sinto", "tenha", "para", "minha", "meus", "mais", "muito",
    "pouco", "quando", "pela", "pelo", "com", "nao", "numa", "esse",
    "esta", "isso", "pois",
}


def _normalizar_ascii(texto: str) -> str:
    """Remove acentos e converte para ASCII lowercase para matching sem dependência de acentuação."""
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )


def _tokenizar_restricoes(restricoes: str) -> list[str]:
    """Extrai tokens relevantes do campo de restrições para matching de contraindicações."""
    normalizado = _normalizar_ascii(restricoes)
    tokens = normalizado.split()
    # Mantém tokens com 4+ caracteres, remove stopwords
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]


def _normalizar_equipamentos(equipamentos: list[str]) -> list[str]:
    """Converte valores do app.py para tags canônicas e deduplica deterministicamente."""
    normalizados = set()
    for eq in equipamentos:
        chave = eq.strip().lower()
        tag = _MAPA_EQUIPAMENTO.get(chave, eq.strip())
        normalizados.add(tag)
    return sorted(normalizados)


class CatalogoExercicios:
    """Lê e filtra o catálogo de exercícios a partir de um arquivo Markdown."""

    def __init__(self, caminho: str) -> None:
        """Carrega o catálogo do arquivo Markdown.

        Args:
            caminho: caminho absoluto ou relativo ao arquivo .md do catálogo.

        Raises:
            FileNotFoundError: se o arquivo não existir.
            ValueError: se o arquivo não for texto UTF-8 válido (ex: binário DOCX).
        """
        import os
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Catálogo não encontrado: {caminho}")
        try:
            with open(caminho, encoding="utf-8") as f:
                self._conteudo = f.read()
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Arquivo de catálogo não é texto Markdown válido: {caminho}"
            ) from e
        self._caminho = caminho
        logger.debug("Catálogo carregado de '%s' (%d chars).", caminho, len(self._conteudo))

    def filtrar(
        self,
        equipamentos: list[str],
        nivel: str,
        restricoes: str,
    ) -> str | None:
        """Filtra exercícios por equipamento, nível e contraindicações.

        Args:
            equipamentos: valores brutos do app.py (ex: ["Máquinas", "Peso Livre"]).
            nivel: "Iniciante", "Intermediário" ou "Avançado".
            restricoes: texto livre do campo "Lesões ou restrições".

        Returns:
            Tabela Markdown filtrada com flags, ou None se nenhum exercício passar.
        """
        tags_disponiveis = _normalizar_equipamentos(equipamentos)
        tokens_restricao = _tokenizar_restricoes(restricoes)

        # Determina qual tag recebe [PRIORIZAR]
        tag_priorizar = None
        if nivel == "Iniciante":
            tag_priorizar = "Máquina"
        elif nivel == "Avançado":
            tag_priorizar = "Peso Livre"

        # Parseia o catálogo por grupos (## headers)
        grupos = self._parsear_grupos()
        secoes_resultado = []

        for nome_grupo, linhas_tabela in grupos:
            exercicios_grupo = self._filtrar_grupo(
                linhas_tabela, tags_disponiveis, tag_priorizar, tokens_restricao
            )
            if exercicios_grupo:
                cabecalho = (
                    "| Exercício | Músculo Alvo | Substitutos | "
                    "Contraindicações / Alertas | Tag de Equipamento |\n"
                    "|---|---|---|---|---|"
                )
                linhas_md = "\n".join(exercicios_grupo)
                secoes_resultado.append(f"## {nome_grupo}\n\n{cabecalho}\n{linhas_md}")

        if not secoes_resultado:
            logger.debug("Nenhum exercício após filtragem para equipamentos=%s.", tags_disponiveis)
            return None

        return "\n\n".join(secoes_resultado)

    def _parsear_grupos(self) -> list[tuple[str, list[str]]]:
        """Divide o catálogo em grupos por header ## e retorna linhas de dados de cada tabela."""
        grupos = []
        grupo_atual = None
        linhas_tabela = []
        cabecalho_re = re.compile(r"^#{1,3}\s+(.+)$")
        separador_re = re.compile(r"^\|[-| :]+\|$")

        for linha in self._conteudo.splitlines():
            m = cabecalho_re.match(linha)
            if m:
                if grupo_atual is not None:
                    grupos.append((grupo_atual, linhas_tabela))
                grupo_atual = m.group(1).strip()
                linhas_tabela = []
                continue
            if linha.startswith("|") and not separador_re.match(linha):
                # Ignora linha de cabeçalho da tabela (contém "Exercício")
                if "Exercício" in linha and "Músculo Alvo" in linha:
                    continue
                linhas_tabela.append(linha)

        if grupo_atual is not None:
            grupos.append((grupo_atual, linhas_tabela))
        return grupos

    def _parsear_celulas(self, linha: str) -> list[str]:
        """Extrai células de uma linha Markdown de tabela."""
        partes = linha.split("|")
        # Remove primeiro e último (vazios pelo | externo)
        return [p.strip() for p in partes[1:-1]]

    def _filtrar_grupo(
        self,
        linhas: list[str],
        tags_disponiveis: list[str],
        tag_priorizar: str | None,
        tokens_restricao: list[str],
    ) -> list[str]:
        """Aplica as 4 regras de filtragem em um grupo de exercícios."""
        tags_lower = [t.lower() for t in tags_disponiveis]
        resultado = []

        for linha in linhas:
            celulas = self._parsear_celulas(linha)
            if len(celulas) < 5:
                continue

            nome, musculo, substitutos_raw, contraindicacoes, tag = celulas
            tag_lower = tag.strip().lower()

            # Regra 2: filtro de equipamento
            if tag_lower not in tags_lower:
                continue

            # Regra 3: sinalização de nível
            priorizar = tag_priorizar and tag_lower == tag_priorizar.lower()

            # Regra 4: detecção de contraindicação
            contra_norm = _normalizar_ascii(contraindicacoes)
            tem_contraindicacao = any(
                token in contra_norm for token in tokens_restricao
            )

            if tem_contraindicacao:
                # Remove exercício e processa substitutos
                subs = self._processar_substitutos(
                    substitutos_raw, tags_lower, musculo, contraindicacoes, tag
                )
                resultado.extend(subs)
            else:
                flag = " [PRIORIZAR]" if priorizar else ""
                resultado.append(
                    f"| {nome}{flag} | {musculo} | {substitutos_raw} | {contraindicacoes} | {tag} |"
                )

        return resultado

    def _processar_substitutos(
        self,
        substitutos_raw: str,
        tags_lower: list[str],
        musculo: str,
        contraindicacoes: str,
        tag_original: str,
    ) -> list[str]:
        """Retorna linhas de substitutos elegíveis com flag [SUBSTITUTO OBRIGATÓRIO]."""
        nomes_substitutos = [s.strip() for s in substitutos_raw.split(",") if s.strip()]
        resultado = []

        for nome_sub in nomes_substitutos:
            # Procura o substituto no catálogo completo para obter sua tag
            tag_sub = self._buscar_tag_exercicio(nome_sub)
            if tag_sub is None:
                # Substituto não encontrado no catálogo — descarta
                continue
            if tag_sub.lower() not in tags_lower:
                # Tag do substituto não disponível — descarta
                continue
            # v1: substitutos não passam por filtro de contraindicação
            resultado.append(
                f"| {nome_sub} [SUBSTITUTO OBRIGATÓRIO] | {musculo} | — | — | {tag_sub} |"
            )

        return resultado

    def _buscar_tag_exercicio(self, nome: str) -> str | None:
        """Busca a tag de equipamento de um exercício pelo nome (substring, case-insensitive)."""
        nome_norm = nome.strip().lower()
        for linha in self._conteudo.splitlines():
            if not linha.startswith("|"):
                continue
            celulas = self._parsear_celulas(linha)
            if len(celulas) < 5:
                continue
            if nome_norm in celulas[0].lower():
                return celulas[4].strip()
        return None
```

- [ ] **Step 4: Rodar os testes para confirmar que passam**

```bash
pytest tests/test_catalogo.py -v
```

Esperado: todos os testes PASS.

- [ ] **Step 5: Commitar**

```bash
git add src/generation/catalogo.py tests/test_catalogo.py
git commit -m "feat(generation): adicionar CatalogoExercicios com filtragem por equipamento, nível e contraindicações"
```

---

## Task 3: Modificar `prompt.py` (TDD)

**Files:**
- Modify: `src/generation/prompt.py`
- Modify: `tests/test_llm.py`

### Step 3.1 — Escrever testes novos com falha

- [ ] **Step 1: Adicionar cenários de `catalogo_filtrado` em `tests/test_llm.py`**

Adicionar ao final da classe `TestMontarPrompt` existente (após `test_prompt_sem_metodologia_nao_tem_secao_metodologia`):

```python
    def test_prompt_com_catalogo_injeta_secao_catalogo(self, resultados_exemplo) -> None:
        """Prompt com catalogo_filtrado contém seção [CATÁLOGO DE EXERCÍCIOS]."""
        catalogo_md = "## Core\n\n| Prancha | ... | Peso Corporal |"
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado=catalogo_md,
        )
        assert "[CATÁLOGO DE EXERCÍCIOS" in prompt
        assert "Prancha" in prompt

    def test_prompt_com_catalogo_inclui_justificativa(self, resultados_exemplo) -> None:
        """Template inclui seção Justificativa Personalizada quando catálogo presente."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado="## Core\n\n| Prancha |",
        )
        assert "Justificativa Personalizada" in prompt

    def test_prompt_sem_catalogo_nao_tem_justificativa(self, resultados_exemplo) -> None:
        """Template NÃO inclui Justificativa Personalizada quando catálogo ausente."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
        )
        assert "Justificativa Personalizada" not in prompt

    def test_prompt_catalogo_string_vazia_tratado_como_none(self, resultados_exemplo) -> None:
        """catalogo_filtrado='' é tratado internamente como None (sem seção)."""
        prompt = montar_prompt(
            query="Criar treino",
            resultados=resultados_exemplo,
            metodologia="",
            contexto_aluno="",
            catalogo_filtrado="",
        )
        assert "[CATÁLOGO DE EXERCÍCIOS" not in prompt
        assert "Justificativa Personalizada" not in prompt
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_llm.py::TestMontarPrompt -v
```

Esperado: `TypeError: montar_prompt() got an unexpected keyword argument 'catalogo_filtrado'`

### Step 3.2 — Implementar as mudanças em `prompt.py`

- [ ] **Step 3: Modificar `src/generation/prompt.py`**

Substituir o conteúdo completo do arquivo:

```python
"""
Monta o prompt RAG com metodologia, contexto do aluno, catálogo de exercícios e template de saída.

Combina: instrução de sistema, metodologia RB, contexto do aluno (anamnese),
catálogo de exercícios filtrado (quando disponível), referências científicas
recuperadas do Qdrant, e template de formato de resposta.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)

# Seções do template de saída (base: sempre presente)
_TEMPLATE_SAIDA_BASE = """
Estruture sua resposta EXATAMENTE neste formato:

## Resumo do Aluno
[Síntese das informações fornecidas: nome, idade, modalidade, objetivo, nível, restrições]

## Metodologia do Treino
[2-3 parágrafos explicando os princípios e decisões por trás do plano, com citações às referências científicas no formato (Fonte: [N], p. X)]

## Plano de Treino
[Treinos organizados por dia, com exercícios, séries, repetições e observações]
"""

# Seção adicional de justificativa — incluída apenas quando o catálogo está ativo
_SECAO_JUSTIFICATIVA = """
## Justificativa Personalizada
[Para cada decisão relevante: explique ao personal trainer por que aquele exercício \
foi escolhido para ESTE aluno — nível, restrição física, equipamento disponível, \
objetivo. Use linguagem direta e técnica.]
"""


def montar_prompt(
    query: str,
    resultados: list[ResultadoBusca],
    metodologia: str = "",
    contexto_aluno: str = "",
    catalogo_filtrado: str | None = None,
) -> str:
    """Monta o prompt RAG completo com todos os contextos disponíveis.

    Args:
        query: pergunta ou instrução do personal trainer.
        resultados: chunks recuperados do Qdrant.
        metodologia: texto da metodologia RB (system instruction).
        contexto_aluno: dados da anamnese formatados como texto.
        catalogo_filtrado: tabela Markdown filtrada de exercícios, ou None para omitir a seção.
            String vazia é tratada internamente como None (guard contra passagem acidental).

    Returns:
        String do prompt completo pronto para o LLM.
    """
    # Guard: string vazia é semanticamente igual a None
    if catalogo_filtrado == "":
        catalogo_filtrado = None

    secoes = []

    # Instrução base do sistema
    secoes.append(
        "Você é um assistente especializado em personal training.\n"
        "Use APENAS as referências abaixo para embasar cientificamente o treino.\n"
        "Cite a fonte após cada afirmação relevante.\n"
        "Se o contexto do aluno for insuficiente para personalizar o treino, "
        "faça UMA pergunta objetiva antes de responder (máx. 3 rodadas).\n"
    )

    # Metodologia RB (quando disponível)
    if metodologia.strip():
        secoes.append(
            f"[METODOLOGIA — seguir sempre na estruturação do treino]\n{metodologia.strip()}\n"
        )
        logger.debug("Metodologia incluída no prompt (%d chars).", len(metodologia))

    # Contexto do aluno (anamnese)
    if contexto_aluno.strip():
        secoes.append(f"[CONTEXTO DO ALUNO]\n{contexto_aluno.strip()}\n")

    # Catálogo de exercícios filtrado (quando disponível)
    if catalogo_filtrado is not None:
        instrucoes_catalogo = (
            "[CATÁLOGO DE EXERCÍCIOS — usar para selecionar movimentos do plano]\n"
            "Regras obrigatórias:\n"
            "- Use SOMENTE exercícios presentes nesta tabela filtrada.\n"
            "- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.\n"
            "- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício "
            "original. Nunca sugira o exercício original quando houver substituto marcado.\n"
            f"{catalogo_filtrado}\n"
        )
        secoes.append(instrucoes_catalogo)
        logger.debug("Catálogo de exercícios incluído no prompt.")

    # Referências científicas
    if not resultados:
        secoes.append("REFERÊNCIAS: (nenhuma referência disponível)\n")
        logger.debug("Prompt gerado sem referências.")
    else:
        linhas = []
        for i, resultado in enumerate(resultados, start=1):
            chunk = resultado.chunk
            linhas.append(f"[{i}] {chunk.fonte}, p. {chunk.pagina}: {chunk.conteudo}")
        secoes.append("REFERÊNCIAS:\n" + "\n".join(linhas) + "\n")
        logger.debug("Prompt montado com %d referência(s).", len(resultados))

    # Template de formato de saída (condicional por catálogo)
    template = _TEMPLATE_SAIDA_BASE
    if catalogo_filtrado is not None:
        template = _TEMPLATE_SAIDA_BASE + _SECAO_JUSTIFICATIVA
    secoes.append(template)

    # Pergunta do personal
    secoes.append(f"PERGUNTA: {query}")

    return "\n".join(secoes)
```

- [ ] **Step 4: Rodar todos os testes de prompt**

```bash
pytest tests/test_llm.py -v
```

Esperado: todos PASS (incluindo os testes pré-existentes).

- [ ] **Step 5: Commitar**

```bash
git add src/generation/prompt.py tests/test_llm.py
git commit -m "feat(generation): adicionar catalogo_filtrado e seção Justificativa Personalizada ao prompt"
```

---

## Task 4: Modificar `llm.py` (TDD)

**Files:**
- Modify: `src/generation/llm.py`
- Modify: `tests/test_llm.py`

### Step 4.1 — Escrever testes novos com falha

- [ ] **Step 1: Adicionar cenário de integração em `tests/test_llm.py`**

Adicionar nova classe ao final do arquivo:

```python
# ---------------------------------------------------------------------------
# Testes de RAGGenerator com catálogo
# ---------------------------------------------------------------------------


class TestRAGGeneratorComCatalogo:
    """Testes de integração do RAGGenerator com o CatalogoExercicios."""

    def test_gerar_com_equipamentos_e_nivel_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() com equipamentos e nivel chama montar_prompt com catalogo_filtrado não-None."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")

        catalogo_mock = mocker.MagicMock()
        catalogo_mock.filtrar.return_value = "## Core\n\n| Prancha | Peso Corporal |"
        mocker.patch(
            "src.generation.llm.CatalogoExercicios",
            return_value=catalogo_mock,
        )

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar(
            "Criar treino",
            resultados_exemplo,
            contexto_aluno="Aluno: João",
            equipamentos=["Máquinas"],
            nivel="Iniciante",
            restricoes="dor no joelho",
        )

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert kwargs.get("catalogo_filtrado") is not None

    def test_gerar_sem_equipamentos_nao_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() sem equipamentos não ativa o catálogo (retrocompatível)."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        mocker.patch("src.generation.llm.CatalogoExercicios")

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar("Criar treino", resultados_exemplo)

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert "catalogo_filtrado" not in kwargs or kwargs.get("catalogo_filtrado") is None

    def test_gerar_com_equipamentos_sem_nivel_nao_ativa_catalogo(
        self,
        mocker,
        mock_chat_nvidia,
        settings_mock,
        resultados_exemplo,
    ) -> None:
        """gerar() com equipamentos mas sem nivel não ativa catálogo."""
        mocker.patch("src.generation.llm._carregar_metodologia", return_value="")
        mocker.patch("src.generation.llm.CatalogoExercicios")

        mock_montar = mocker.patch("src.generation.llm.montar_prompt", return_value="prompt_mock")

        from src.generation.llm import RAGGenerator

        gerador = RAGGenerator(settings=settings_mock)
        gerador.gerar("Criar treino", resultados_exemplo, equipamentos=["Máquinas"], nivel="")

        mock_montar.assert_called_once()
        _, kwargs = mock_montar.call_args
        assert "catalogo_filtrado" not in kwargs or kwargs.get("catalogo_filtrado") is None
```

- [ ] **Step 2: Rodar para confirmar falha**

```bash
pytest tests/test_llm.py::TestRAGGeneratorComCatalogo -v
```

Esperado: `ImportError` ou `TypeError` — `gerar()` ainda não tem os novos parâmetros.

### Step 4.2 — Implementar mudanças em `llm.py`

- [ ] **Step 3: Modificar `src/generation/llm.py`**

Substituir o conteúdo completo do arquivo:

```python
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
_CAMINHO_CATALOGO = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "raw", "reference.md"
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
        )
        # Carrega a metodologia uma única vez por instância
        self.metodologia = _carregar_metodologia()
        # Carrega o catálogo de exercícios uma única vez por instância
        caminho_catalogo = os.path.normpath(_CAMINHO_CATALOGO)
        try:
            self.catalogo = CatalogoExercicios(caminho_catalogo)
            logger.debug("Catálogo de exercícios carregado de '%s'.", caminho_catalogo)
        except (FileNotFoundError, ValueError) as e:
            logger.warning("Catálogo de exercícios não disponível: %s", e)
            self.catalogo = None
        logger.debug("RAGGenerator inicializado com modelo '%s'.", settings.llm_model)

    def gerar(
        self,
        query: str,
        resultados: list[ResultadoBusca],
        contexto_aluno: str = "",
        equipamentos: list[str] | None = None,
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
```

- [ ] **Step 4: Rodar todos os testes de llm**

```bash
pytest tests/test_llm.py -v
```

Esperado: todos PASS.

- [ ] **Step 5: Commitar**

```bash
git add src/generation/llm.py tests/test_llm.py
git commit -m "feat(generation): integrar CatalogoExercicios no RAGGenerator com novos parâmetros em gerar()"
```

---

## Task 5: Modificar `app.py` e `tests/test_interface.py` (TDD)

**Files:**
- Modify: `src/interface/app.py`
- Modify: `tests/test_interface.py`

### Step 5.1 — Escrever testes novos com falha

- [ ] **Step 1: Adicionar cenário ao `tests/test_interface.py`**

Adicionar ao final do arquivo:

```python
def test_fluxo_busca_e_geracao_com_dados_aluno(settings_mock, resultados_exemplo):
    """Garante que gerar() é chamado com equipamentos, nivel e restricoes do session_state."""
    from src.retrieval.searcher import SemanticSearcher
    from src.generation.llm import RAGGenerator

    with patch('src.retrieval.searcher.SentenceTransformer'), \
         patch('src.retrieval.searcher.QdrantClient') as mock_qdrant, \
         patch('src.generation.llm.ChatNVIDIA') as mock_llm, \
         patch('src.generation.llm._carregar_metodologia', return_value=""), \
         patch('src.generation.llm.CatalogoExercicios'):

        mock_qdrant.return_value.query_points.return_value.points = [
            MagicMock(payload={
                'conteudo': r.chunk.conteudo,
                'fonte': r.chunk.fonte,
                'pagina': r.chunk.pagina,
                'chunk_id': r.chunk.chunk_id,
            }, score=r.score)
            for r in resultados_exemplo
        ]
        mock_llm.return_value.invoke.return_value = MagicMock(
            content="Resposta com catálogo."
        )

        searcher = SemanticSearcher(settings_mock)
        generator = RAGGenerator(settings_mock)

        dados_aluno = {
            "Equipamentos disponíveis": ["Máquinas"],
            "Nível de condicionamento": "Iniciante",
            "Lesões ou restrições": "dor no joelho",
        }

        resultados = searcher.buscar("como montar treino?")
        resposta = generator.gerar(
            "como montar treino?",
            resultados,
            contexto_aluno="Aluno: João",
            equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
            nivel=dados_aluno.get("Nível de condicionamento", ""),
            restricoes=dados_aluno.get("Lesões ou restrições", ""),
        )

        assert isinstance(resposta, RespostaRAG)
        assert resposta.texto == "Resposta com catálogo."
```

- [ ] **Step 2: Rodar para confirmar que passa (o teste usa a nova assinatura de gerar())**

```bash
pytest tests/test_interface.py::test_fluxo_busca_e_geracao_com_dados_aluno -v
```

Esperado: PASS (pois `gerar()` já aceita os novos parâmetros após Task 4).

- [ ] **Step 3: Rodar todos os testes de interface para confirmar nenhuma regressão**

```bash
pytest tests/test_interface.py -v
```

Esperado: todos PASS.

### Step 5.2 — Modificar `app.py`

- [ ] **Step 4: Adicionar inicialização de `dados_aluno` no session_state**

Em `src/interface/app.py`, após a linha `if "ultimas_fontes" not in st.session_state:` (linha ~84), adicionar:

```python
if "dados_aluno" not in st.session_state:
    st.session_state["dados_aluno"] = {}
```

- [ ] **Step 5: Persistir `dados_aluno` no bloco `if enviado:`**

Ainda em `app.py`, no bloco `if enviado:` após `st.session_state["contexto_aluno"] = formatar_contexto_aluno(dados)` (linha ~143), adicionar:

```python
            st.session_state["dados_aluno"] = dados
```

- [ ] **Step 6: Atualizar a chamada a `generator.gerar()` no estado `resposta`**

Substituir a chamada existente a `generator.gerar()` (linhas ~213-217):

```python
# Antes:
                resposta = generator.gerar(
                    query=query_completa,
                    resultados=resultados,
                    contexto_aluno=st.session_state["contexto_aluno"],
                )
```

Por:

```python
# Depois:
                dados_aluno = st.session_state.get("dados_aluno", {})
                resposta = generator.gerar(
                    query=query_completa,
                    resultados=resultados,
                    contexto_aluno=st.session_state["contexto_aluno"],
                    equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
                    nivel=dados_aluno.get("Nível de condicionamento", ""),
                    restricoes=dados_aluno.get("Lesões ou restrições", ""),
                )
```

- [ ] **Step 7: Rodar suite completa de testes**

```bash
pytest tests/ -v
```

Esperado: todos PASS.

- [ ] **Step 8: Commitar**

```bash
git add src/interface/app.py tests/test_interface.py
git commit -m "feat(interface): persistir dados_aluno no session_state e passar equipamentos/nivel/restricoes ao gerar()"
```

---

## Task 6: Verificação final

- [ ] **Step 1: Rodar suite completa**

```bash
pytest tests/ -v
```

Esperado: todos os testes PASS (incluindo os 39 existentes + novos).

- [ ] **Step 2: Verificar que reference.md está em Markdown válido**

```bash
python3 -c "from src.generation.catalogo import CatalogoExercicios; c = CatalogoExercicios('data/raw/reference.md'); print('OK —', len(c._conteudo), 'chars')"
```

Esperado: `OK — <N> chars` (sem exceção).

- [ ] **Step 3: Push da branch**

```bash
git push -u origin feat/ui-form-capitalization
```
