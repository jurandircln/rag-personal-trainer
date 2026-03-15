"""Interface web do Jarvis Personal Trainer — aplicação Streamlit com anamnese híbrida."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st

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
    equipamentos = ", ".join(dados.get("equipamentos", [])) or "não informado"
    return (
        f"Nome: {dados['nome']}\n"
        f"Idade: {dados['idade']} anos\n"
        f"Modalidade/esporte: {dados['modalidade']}\n"
        f"Objetivo principal: {dados['objetivo']}\n"
        f"Dias disponíveis por semana: {dados['dias_semana']}\n"
        f"Equipamentos disponíveis: {equipamentos}\n"
        f"Lesões ou restrições: {dados['lesoes'] or 'nenhuma'}\n"
        f"Nível de condicionamento: {dados['nivel']}\n"
    )


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

# ---------------------------------------------------------------------------
# ESTADO 1: Anamnese
# ---------------------------------------------------------------------------

if st.session_state["estado"] == "anamnese":
    st.markdown("Preencha os dados do aluno para começar.")

    with st.form("form_anamnese"):
        nome = st.text_input("Nome do aluno")
        col1, col2 = st.columns(2)
        with col1:
            idade = st.number_input("Idade", min_value=10, max_value=100, value=30)
            dias_semana = st.number_input(
                "Dias disponíveis por semana", min_value=1, max_value=7, value=3
            )
            nivel = st.selectbox(
                "Nível de condicionamento",
                ["iniciante", "intermediário", "avançado"],
            )
        with col2:
            modalidade = st.text_input("Modalidade / esporte praticado")
            objetivo = st.selectbox(
                "Objetivo principal",
                [
                    "hipertrofia",
                    "resistência",
                    "emagrecimento",
                    "desempenho esportivo",
                    "reabilitação",
                ],
            )

        equipamentos = st.multiselect(
            "Equipamentos disponíveis",
            ["peso livre", "máquinas", "peso corporal", "elásticos", "sem equipamento"],
            default=["peso corporal"],
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
                "nome": nome.strip(),
                "idade": idade,
                "modalidade": modalidade.strip(),
                "objetivo": objetivo,
                "dias_semana": dias_semana,
                "equipamentos": equipamentos,
                "lesoes": lesoes.strip(),
                "nivel": nivel,
            }
            st.session_state["contexto_aluno"] = formatar_contexto_aluno(dados)
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
        label="Sua pergunta:",
        placeholder="Ex.: Monte um programa de força para 3 dias por semana.",
        height=100,
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Enviar"):
            if not pergunta.strip():
                st.warning("Por favor, digite sua pergunta antes de enviar.")
            else:
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
            st.markdown(mensagem["content"])
            st.divider()

    # Só processa se a última mensagem for do usuário (precisa de resposta)
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
                resultados = searcher.buscar(historico[0]["content"])
                resposta = generator.gerar(
                    query=query_completa,
                    resultados=resultados,
                    contexto_aluno=st.session_state["contexto_aluno"],
                )

            # Adiciona resposta ao histórico
            historico.append({"role": "assistant", "content": resposta.texto})
            st.session_state["historico_conversa"] = historico

            st.markdown(resposta.texto)

            if resposta.fontes:
                st.markdown("**Fontes consultadas:**")
                for fonte in resposta.fontes:
                    st.markdown(f"- {fonte}")

            st.divider()

            # Detecta se o LLM fez pergunta de follow-up (máx. 3 rodadas)
            rodadas = st.session_state["rodadas_followup"]
            fez_pergunta = "?" in resposta.texto[-300:]

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
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Nova consulta (mesmo aluno)"):
                        st.session_state["estado"] = "pergunta"
                        st.session_state["historico_conversa"] = []
                        st.session_state["rodadas_followup"] = 0
                        st.rerun()
                with col2:
                    if st.button("Nova consulta (novo aluno)"):
                        st.session_state["estado"] = "anamnese"
                        st.session_state["contexto_aluno"] = ""
                        st.session_state["historico_conversa"] = []
                        st.session_state["rodadas_followup"] = 0
                        st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar a pergunta: {e}")
