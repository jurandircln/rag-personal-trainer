# Visão do Produto — Jarvis Personal Trainer

## Problema

Personal trainers lidam diariamente com grandes volumes de materiais técnicos:
- PDFs de metodologias de treinamento
- Anamneses de clientes
- Artigos científicos sobre fisiologia e nutrição
- Protocolos de avaliação física

A pesquisa manual nesses materiais é lenta e propensa a erros, especialmente quando o personal precisa responder rapidamente às necessidades de um cliente.

## Solução

Jarvis é um assistente inteligente especializado no domínio do personal trainer. Usando RAG (Retrieval-Augmented Generation), o sistema:

1. Indexa os materiais do personal trainer em uma base vetorial
2. Quando perguntado, recupera os trechos mais relevantes
3. Usa um LLM para gerar respostas contextualizadas e precisas
4. Permite montar planos de treino personalizados com base nos materiais do próprio profissional

## Diferencial

- **Especializado no domínio:** treinado com os materiais do próprio personal, não um assistente genérico
- **Respostas fundamentadas:** toda resposta é baseada em documentos reais, não em "alucinação" do LLM
- **Interface simples:** Streamlit web, sem necessidade de conhecimento técnico pelo usuário final

## Visão de Longo Prazo

> TODO: Definir com o time a visão de 1-3 anos para o produto.

## Métricas de Sucesso

> TODO: Definir KPIs após entrevistas com usuários. Ver docs/business-context/kpis.md

## Público-Alvo

> TODO: Ver docs/business-context/personas.md para detalhes das personas.
