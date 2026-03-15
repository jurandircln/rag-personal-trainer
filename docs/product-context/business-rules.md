# Regras de Negócio — Jarvis Personal Trainer

## RN-001: Fonte Obrigatória nas Respostas

Toda sugestão de exercício, protocolo ou decisão de treino no plano gerado DEVE citar a fonte (documento + localização aproximada, ex: "Protocolo de Hipertrofia — Capítulo 3, p. 12"). Respostas sem embasamento nos materiais indexados não devem ser apresentadas como recomendações — o agente deve informar explicitamente que não encontrou referência suficiente nos materiais disponíveis.

## RN-002: Perguntas Complementares

Se o contexto fornecido pelo personal for insuficiente para gerar um plano adequado (ex: sem objetivo definido, sem informação sobre restrições físicas), o agente DEVE fazer perguntas complementares antes de gerar o plano. Máximo de 3 rodadas de perguntas por sessão — acima disso, o agente gera o melhor plano possível com as informações disponíveis e sinaliza as lacunas de contexto.

## RN-003: Escopo de Conhecimento

O agente responde apenas com base nos materiais indexados pelo personal. Se a pergunta estiver fora do escopo dos documentos disponíveis, o agente informa claramente: "Não encontrei referência suficiente nos seus materiais para esta recomendação." O agente não deve completar lacunas com conhecimento geral do LLM sem sinalizar explicitamente que está fazendo isso.

## RN-004: Idioma

Toda interação com o usuário final é em português (pt-BR). O personal trainer envia mensagens em português; o agente responde em português. Termos técnicos do domínio fitness podem ser mantidos em inglês quando não há equivalente consolidado em PT-BR (ex: "deadlift", "HIIT", "burnout set").

## RN-005: Exportação PDF

O plano de treino gerado deve poder ser exportado como PDF diretamente da interface. O PDF deve conter: contexto do aluno (se fornecido pelo personal), exercícios organizados por sessão, séries/repetições/cadência/descanso, e as fontes citadas para cada decisão. O PDF não deve incluir dados identificadores do aluno (nome, CPF, dados de saúde) sem que o personal tenha inserido explicitamente essas informações na sessão.

## RN-006: Privacidade de Dados

Anamneses e dados de saúde dos alunos são tratados como dados sensíveis. O Jarvis não armazena conversas fora da sessão ativa — ao encerrar a sessão, o histórico da conversa não é persistido. Dados de saúde do aluno só devem ser indexados na base vetorial mediante decisão explícita do personal trainer, que é o responsável pela guarda dessas informações.
