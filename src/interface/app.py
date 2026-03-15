"""Interface web do Jarvis Personal Trainer — aplicação Streamlit."""
import sys
import os

# Garante que src/ está no path ao rodar com: streamlit run src/interface/app.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import streamlit as st
from src.config.settings import Settings
from src.retrieval.searcher import SemanticSearcher
from src.generation.llm import RAGGenerator


# Inicializa componentes uma única vez por sessão (evita recarregar modelos)
@st.cache_resource
def carregar_componentes():
    """Carrega settings, searcher e generator uma vez por sessão."""
    settings = Settings()
    searcher = SemanticSearcher(settings)
    generator = RAGGenerator(settings)
    return searcher, generator


# Configuração da página
st.set_page_config(page_title="Jarvis - Personal Trainer", layout="centered")

# Título
st.title("JARVIS - Personal Trainer")

# Instrução
st.markdown("Digite as informações do aluno e sua dúvida sobre treinamento, anamnese ou prescrição de exercícios.")

# Caixa de texto
pergunta = st.text_area(
    label="Sua pergunta:",
    placeholder="Ex.: Aluno de 35 anos, histórico de lombalgia. Como montar um programa de força?",
    height=150,
)

# Botão de envio
if st.button("Enviar"):
    if not pergunta.strip():
        st.warning("Por favor, digite sua pergunta antes de enviar.")
    else:
        try:
            searcher, generator = carregar_componentes()
            with st.spinner("Consultando base de conhecimento..."):
                resultados = searcher.buscar(pergunta)
                resposta = generator.gerar(pergunta, resultados)

            st.markdown("### Resposta")
            st.markdown(resposta.texto)

            if resposta.fontes:
                st.markdown("**Fontes consultadas:**")
                for fonte in resposta.fontes:
                    st.markdown(f"- {fonte}")

        except Exception as e:
            st.error(f"Erro ao processar a pergunta: {e}")
