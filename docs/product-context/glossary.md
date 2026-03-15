# Glossário — Jarvis Personal Trainer

## Termos do Domínio

| Termo | Definição |
|---|---|
| Anamnese | Ficha de avaliação inicial do aluno com histórico de saúde, objetivos, restrições físicas e histórico de treinamento. Pode ser indexada no Jarvis mediante decisão explícita do personal trainer. |
| Plano de Treino | Documento gerado pelo Jarvis contendo exercícios, séries, repetições, cadência e tempo de descanso, organizado por sessão e semana. Sempre inclui as fontes que embasaram cada decisão. |
| Material de Referência | Qualquer documento indexado no Jarvis — PDFs de metodologias, artigos científicos, protocolos de treinamento, anamneses. Base de conhecimento do personal trainer. |
| Pergunta Complementar | Pergunta que o agente faz ao personal quando o contexto fornecido é insuficiente para gerar um plano adequado (ex: objetivo não definido, ausência de informação sobre restrições). Máximo de 3 rodadas por sessão. |
| Fonte Citada | Referência ao trecho específico do material de referência que embasou uma decisão no plano (ex: "Protocolo de Hipertrofia — Capítulo 3, p. 12"). Obrigatória em toda recomendação. |
| Exportação PDF | Funcionalidade que converte o plano de treino gerado em um arquivo PDF formatado, pronto para ser compartilhado com o aluno. |
| Sessão | Uma conversa completa entre o personal e o Jarvis, desde a descrição do aluno até a exportação do plano. Dados não são persistidos entre sessões. |
| Personal Trainer | Profissional de educação física especializado em treinamento individual. Usuário primário do Jarvis. |

## Termos Técnicos

| Termo | Definição |
|---|---|
| RAG | Retrieval-Augmented Generation — técnica que combina busca em base de conhecimento com geração de texto por LLM. Fundamento técnico do Jarvis. |
| Chunk | Fragmento de texto extraído de um documento para indexação vetorial. Unidade mínima de recuperação pelo agente. |
| Embedding | Representação vetorial de um texto que captura seu significado semântico. Permite busca por similaridade. |
| Vector Store | Banco de dados especializado em busca por similaridade vetorial (usamos Qdrant). |
| LLM | Large Language Model — modelo de linguagem de grande escala. Usado para geração de texto (Llama 3.x via NVIDIA NIM). |
| NVIDIA NIM | Plataforma de inferência de modelos de IA da NVIDIA com API OpenAI-compatible. |
| Qdrant | Vector database open-source usado como backend de busca semântica. |
| LangChain | Framework Python para orquestração de pipelines com LLMs. |
| Streamlit | Framework Python para criação rápida de interfaces web. |
