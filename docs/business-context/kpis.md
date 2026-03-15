# KPIs — Jarvis Personal Trainer

Métricas alinhadas ao problema central: reduzir o tempo de criação de planos personalizados sem abrir mão da qualidade e da rastreabilidade.

## Métricas de Impacto

| KPI | Meta (MVP) | Como medir |
|---|---|---|
| Tempo médio para gerar um plano de treino | < 5 min (vs. ~90 min manual) | Feedback direto do usuário; timestamp de início e exportação de sessão |
| Taxa de planos exportados como PDF | > 60% das sessões | Contagem de cliques em "Baixar PDF" por sessão iniciada |
| Taxa de rejeição do plano gerado | < 20% | Sessões em que o personal descartou e começou do zero sem usar o rascunho |
| NPS do personal trainer | ≥ 50 | Pesquisa periódica com usuários ativos |

## Métricas de Qualidade do Agente

| KPI | Meta | Como medir |
|---|---|---|
| Taxa de respostas com fonte citada | 100% | Regra de negócio obrigatória (RN-001); verificação automática no pipeline |
| Taxa de perguntas complementares por sessão | 0–2 por sessão | Log de interações; acima de 3 indica contexto inicial insuficiente ou falha no agente |
| Taxa de respostas "sem referência suficiente" | Monitorar (sem meta fixa no MVP) | Sinaliza lacunas na biblioteca do personal; útil para orientar o que indexar |

## Notas

- As metas de MVP são baseadas nas personas documentadas (`personas.md`) e no problema descrito na visão (`vision.md`).
- Tempo de geração de plano inclui apenas o tempo dentro da ferramenta — não o tempo de revisão e ajuste pelo personal, que é esperado e desejado.
- Taxa de rejeição acima de 20% indica que o agente está gerando planos fora do padrão do profissional ou com qualidade insuficiente para servir de rascunho.
