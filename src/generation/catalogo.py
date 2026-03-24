"""
Filtra o catálogo de exercícios por equipamento, nível e contraindicações.

O catálogo é lido de um arquivo Markdown com tabelas por grupo muscular.
A filtragem é puramente Python — sem chamadas ao LLM.
"""

import unicodedata
import logging
import os
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


def _tokenizar_restricoes(restricoes: str) -> list:
    """Extrai tokens relevantes do campo de restrições para matching de contraindicações."""
    normalizado = _normalizar_ascii(restricoes)
    tokens = normalizado.split()
    # Mantém tokens com 4+ caracteres, remove stopwords
    return [t for t in tokens if len(t) >= 4 and t not in _STOPWORDS]


def _normalizar_equipamentos(equipamentos: list) -> list:
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
        equipamentos: list,
        nivel: str,
        restricoes: str,
    ) -> "str | None":
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
                    "Contraindicações / Alertas | Tag de Equipamento | Tempo por rep. (s) |\n"
                    "|---|---|---|---|---|---|"
                )
                linhas_md = "\n".join(exercicios_grupo)
                secoes_resultado.append(f"## {nome_grupo}\n\n{cabecalho}\n{linhas_md}")

        if not secoes_resultado:
            logger.debug("Nenhum exercício após filtragem para equipamentos=%s.", tags_disponiveis)
            return None

        return "\n\n".join(secoes_resultado)

    def _parsear_grupos(self) -> list:
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

    def _parsear_celulas(self, linha: str) -> list:
        """Extrai células de uma linha Markdown de tabela."""
        partes = linha.split("|")
        # Remove primeiro e último (vazios pelo | externo)
        return [p.strip() for p in partes[1:-1]]

    def _filtrar_grupo(
        self,
        linhas: list,
        tags_disponiveis: list,
        tag_priorizar,
        tokens_restricao: list,
    ) -> list:
        """Aplica as 4 regras de filtragem em um grupo de exercícios."""
        tags_lower = [t.lower() for t in tags_disponiveis]
        resultado = []

        for linha in linhas:
            celulas = self._parsear_celulas(linha)
            if len(celulas) < 5:
                continue

            nome, musculo, substitutos_raw, contraindicacoes, tag = celulas[:5]
            tempo_rep = celulas[5] if len(celulas) > 5 else "—"
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
                    f"| {nome}{flag} | {musculo} | {substitutos_raw} | {contraindicacoes} | {tag} | {tempo_rep} |"
                )

        return resultado

    def _processar_substitutos(
        self,
        substitutos_raw: str,
        tags_lower: list,
        musculo: str,
        contraindicacoes: str,
        tag_original: str,
    ) -> list:
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
                f"| {nome_sub} [SUBSTITUTO OBRIGATÓRIO] | {musculo} | — | — | {tag_sub} | — |"
            )

        return resultado

    def _buscar_tag_exercicio(self, nome: str):
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
