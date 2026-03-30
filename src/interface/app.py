"""Interface web do Jarvis Personal Trainer — aplicação Streamlit com anamnese híbrida."""
import sys
import os
import logging
import re

from qdrant_client.http.exceptions import UnexpectedResponse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st

logger = logging.getLogger(__name__)

from src.config.settings import Settings
from src.retrieval.searcher import SemanticSearcher
from src.generation.llm import RAGGenerator


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def formatar_contexto_aluno(dados: dict) -> str:
    """Formata os dados da anamnese como texto estruturado para o prompt.

    Args:
        dados: dicionário com os campos da anamnese.

    Returns:
        String formatada com as informações do aluno.
    """
    equipamentos = ", ".join(dados.get("Equipamentos disponíveis", [])) or "não informado"

    # Filtra a opção "Deixar o agente decidir" para não enviá-la ao LLM
    divisao_raw = dados.get("Divisão de treino", [])
    divisao_opcoes = [d for d in divisao_raw if d != "Deixar o agente decidir"]

    linhas = [
        f"Nome: {dados['Nome']}",
        f"Idade: {dados['Idade']} anos",
        f"Modalidade/esporte: {dados['Modalidade / Esporte praticado']}",
        f"Objetivo principal: {dados['Objetivo']}",
        f"Dias disponíveis por semana: {dados['Dias disponíveis por semana']}",
        f"Tempo por sessão: {dados['Tempo por sessão']}",
        f"Equipamentos disponíveis: {equipamentos}",
        f"Lesões ou restrições: {dados['Lesões ou restrições'] or 'nenhuma'}",
        f"Nível de condicionamento: {dados['Nível de condicionamento']}",
    ]

    if divisao_opcoes:
        linhas.append(f"Divisão de treino preferida: {', '.join(divisao_opcoes)}")

    return "\n".join(linhas)


def _parsear_semanas(texto: str) -> dict:
    """Divide o texto gerado pelo LLM em cabeçalho, semanas e fontes.

    Args:
        texto: resposta completa do LLM.

    Returns:
        Dict com chaves 'cabecalho' (str), 'semanas' (list[tuple[str, str]]) e 'fontes' (str).
        'semanas' é vazia se nenhum marcador ## SEMANA N for encontrado (fallback).
    """
    # Divide no início de cada marcador ## SEMANA N, preservando o marcador em cada parte
    partes = re.split(r"(?=^## SEMANA \d+)", texto, flags=re.MULTILINE)

    cabecalho = partes[0].strip() if partes else ""
    semanas = []
    fontes = ""

    for parte in partes[1:]:
        # Verifica se esta parte contém a seção de fontes
        match_fontes = re.search(r"^## Fontes Consultadas", parte, re.MULTILINE)
        if match_fontes:
            corpo_semana = parte[: match_fontes.start()]
            fontes = parte[match_fontes.start() :].strip()
        else:
            corpo_semana = parte

        # Extrai nome (primeira linha) e conteúdo (restante)
        linhas = corpo_semana.strip().split("\n", 1)
        nome = re.sub(r"^#+\s*", "", linhas[0]).strip()
        conteudo = linhas[1].strip() if len(linhas) > 1 else ""
        semanas.append((nome, conteudo))

    return {"cabecalho": cabecalho, "semanas": semanas, "fontes": fontes}


# ---------------------------------------------------------------------------
# Cache de componentes
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner="🤖 Carregando Jarvis...")
def carregar_componentes():
    """Carrega settings, searcher e generator uma vez por sessão."""
    settings = Settings()
    searcher = SemanticSearcher(settings)
    generator = RAGGenerator(settings)
    return searcher, generator


# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Jarvis - Personal Trainer", layout="centered")
st.title("JARVIS - Personal Trainer")

# ---------------------------------------------------------------------------
# Inicialização do session_state
# ---------------------------------------------------------------------------

if "estado" not in st.session_state:
    st.session_state["estado"] = "anamnese"  # estados: anamnese | pergunta | resposta

if "contexto_aluno" not in st.session_state:
    st.session_state["contexto_aluno"] = ""

if "historico_conversa" not in st.session_state:
    st.session_state["historico_conversa"] = []  # lista de {role, content}

if "rodadas_followup" not in st.session_state:
    st.session_state["rodadas_followup"] = 0

if "ultimas_fontes" not in st.session_state:
    st.session_state["ultimas_fontes"] = []

if "dados_aluno" not in st.session_state:
    st.session_state["dados_aluno"] = {}

# ---------------------------------------------------------------------------
# ESTADO 1: Anamnese
# ---------------------------------------------------------------------------

if st.session_state["estado"] == "anamnese":
    st.markdown("Preencha os dados do aluno para iniciarmos a consulta:")

    with st.form("form_anamnese"):
        nome = st.text_input("Nome do aluno")
        col1, col2 = st.columns(2)
        with col1:
            idade = st.number_input("Idade", min_value=10, max_value=100, value=30)
            dias_semana = st.number_input(
                "Dias disponíveis por semana", min_value=1, max_value=7, value=3
            )
        with col2:
            modalidade = st.text_input("Modalidade / Esporte praticado")
            objetivo = st.selectbox(
                "Objetivo principal",
                [
                    "Hipertrofia",
                    "Resistência",
                    "Emagrecimento",
                    "Desempenho Esportivo",
                    "Reabilitação",
                ],
            )

        col3, col4 = st.columns(2)
        with col3:
            tempo_sessao = st.selectbox(
                "Tempo disponível por sessão",
                ["30 min", "45 min", "60 min", "90 min+"],
            )
        with col4:
            nivel = st.selectbox(
                "Nível de condicionamento",
                ["Iniciante", "Intermediário", "Avançado"],
            )

        divisao_treino = st.multiselect(
            "Divisão de treino",
            [
                "Deixar o agente decidir",
                "Full Body (Corpo todo)",
                "Superior",
                "Inferior",
                "Superior Anterior / Inferior Anterior (Corpo todo)",
                "Superior Posterior / Inferior Posterior (Corpo todo)",
                "Superior Anterior",
                "Superior Posterior",
                "Inferior Anterior",
                "Inferior Posterior",
            ],
            default=["Deixar o agente decidir"],
        )

        equipamentos = st.multiselect(
            "Equipamentos disponíveis",
            ["Peso Livre", "Máquinas", "Peso Corporal", "Elásticos", "Sem Equipamento"],
            default=["Peso Corporal"],
        )
        lesoes = st.text_area(
            "Lesões ou restrições (deixe em branco se nenhuma)", height=80
        )

        enviado = st.form_submit_button("Iniciar consulta →")

    if enviado:
        if not nome.strip() or not modalidade.strip():
            st.warning("Por favor, preencha pelo menos o nome e a modalidade do aluno.")
        else:
            dados = {
                "Nome": nome.strip(),
                "Idade": idade,
                "Modalidade / Esporte praticado": modalidade.strip(),
                "Objetivo": objetivo,
                "Dias disponíveis por semana": dias_semana,
                "Tempo por sessão": tempo_sessao,
                "Equipamentos disponíveis": equipamentos,
                "Lesões ou restrições": lesoes.strip(),
                "Nível de condicionamento": nivel,
                "Divisão de treino": divisao_treino,
            }
            st.session_state["contexto_aluno"] = formatar_contexto_aluno(dados)
            st.session_state["dados_aluno"] = dados
            st.session_state["estado"] = "pergunta"
            st.rerun()

# ---------------------------------------------------------------------------
# ESTADO 2: Pergunta
# ---------------------------------------------------------------------------

elif st.session_state["estado"] == "pergunta":
    st.markdown("**Aluno configurado.** Agora faça sua pergunta ou pedido de treino.")

    with st.expander("Ver dados do aluno"):
        st.text(st.session_state["contexto_aluno"])

    pergunta = st.text_area(
        label="Adicione mais informações (opcional)",
        placeholder=(
            'Ex.: "Prefiro exercícios compostos no início. Evitar agachamento por limitação de tornozelo."\n'
            '"Aluno ex-atleta de natação — priorizar mobilidade de ombro e volume de costas."\n'
            '"Monte o treino com progressão de carga semana a semana."'
        ),
        height=150,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Enviar"):
            st.session_state["historico_conversa"] = [
                {"role": "user", "content": pergunta.strip()}
            ]
            st.session_state["rodadas_followup"] = 0
            st.session_state["estado"] = "resposta"
            st.rerun()
    with col2:
        if st.button("← Alterar dados do aluno"):
            st.session_state["estado"] = "anamnese"
            st.session_state["contexto_aluno"] = ""
            st.session_state["historico_conversa"] = []
            st.rerun()

# ---------------------------------------------------------------------------
# ESTADO 3: Resposta / Follow-up
# ---------------------------------------------------------------------------

elif st.session_state["estado"] == "resposta":
    # Exibe histórico da conversa
    for mensagem in st.session_state["historico_conversa"]:
        if mensagem["role"] == "user":
            st.markdown(f"**Você:** {mensagem['content']}")
        else:
            parsed = _parsear_semanas(mensagem["content"])
            if parsed["cabecalho"]:
                st.markdown(parsed["cabecalho"])
            if parsed["semanas"]:
                abas = st.tabs([nome for nome, _ in parsed["semanas"]])
                for aba, (_, conteudo) in zip(abas, parsed["semanas"]):
                    with aba:
                        st.markdown(conteudo)
            else:
                # Fallback: exibe texto completo sem abas
                st.markdown(mensagem["content"])
            st.divider()

    # Recupera fontes da última resposta (antes de processar nova mensagem)
    ultimas_fontes = st.session_state.get("ultimas_fontes", [])

    historico = st.session_state["historico_conversa"]
    ultima_mensagem = historico[-1] if historico else None

    if ultima_mensagem and ultima_mensagem["role"] == "user":
        try:
            searcher, generator = carregar_componentes()

            # Constrói a query incluindo o histórico de follow-up
            query_completa = "\n".join(
                f"{'Personal' if m['role'] == 'user' else 'Jarvis'}: {m['content']}"
                for m in historico
            )

            with st.spinner("🤖 Aguarde enquanto estou estudando o seu caso..."):
                resultados = searcher.buscar(historico[0]["content"], top_k=10, max_por_fonte=3)
                dados_aluno = st.session_state.get("dados_aluno", {})
                resposta = generator.gerar(
                    query=query_completa,
                    resultados=resultados,
                    contexto_aluno=st.session_state["contexto_aluno"],
                    equipamentos=dados_aluno.get("Equipamentos disponíveis", []) or None,
                    nivel=dados_aluno.get("Nível de condicionamento", ""),
                    restricoes=dados_aluno.get("Lesões ou restrições", ""),
                )

            # Adiciona resposta ao histórico e armazena fontes no session_state
            historico.append({"role": "assistant", "content": resposta.texto})
            st.session_state["historico_conversa"] = historico
            st.session_state["ultimas_fontes"] = resposta.fontes
            st.rerun()

        except UnexpectedResponse as e:
            if e.status_code == 404 and "doesn't exist" in str(e.content):
                st.error(
                    "A base de conhecimento ainda não foi indexada no Qdrant Cloud. "
                    "Execute: `python scripts/ingest.py --caminho data/raw/` "
                    "com QDRANT_URL e QDRANT_API_KEY apontando para o Qdrant Cloud."
                )
            else:
                st.error(
                    f"Erro na conexão com o Qdrant (status {e.status_code}). "
                    "Verifique QDRANT_URL e QDRANT_API_KEY nos secrets do Streamlit Cloud."
                )
            logger.error("Erro do Qdrant: %s", e)
        except Exception as e:
            logger.error("Erro ao processar a pergunta: %s", e, exc_info=True)
            st.error("Ocorreu um erro ao processar a pergunta. Tente novamente.")

    else:
        rodadas = st.session_state["rodadas_followup"]

        # Detecta se a última mensagem do assistente contém uma pergunta de follow-up
        ultima_resposta = next(
            (m["content"] for m in reversed(historico) if m["role"] == "assistant"),
            ""
        )
        fez_pergunta = "?" in ultima_resposta[-300:]

        if fez_pergunta and rodadas < 3:
            followup = st.text_area(
                "Responda para que eu possa personalizar melhor o treino:",
                key=f"followup_{rodadas}",
                height=80,
            )
            if st.button("Responder", key=f"btn_followup_{rodadas}"):
                if followup.strip():
                    historico.append({"role": "user", "content": followup.strip()})
                    st.session_state["historico_conversa"] = historico
                    st.session_state["rodadas_followup"] = rodadas + 1
                    st.rerun()

        # Botão para iniciar nova consulta
        if st.button("Nova consulta"):
            st.session_state["estado"] = "anamnese"
            st.session_state["contexto_aluno"] = ""
            st.session_state["historico_conversa"] = []
            st.session_state["rodadas_followup"] = 0
            st.rerun()
