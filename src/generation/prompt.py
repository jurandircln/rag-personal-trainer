"""
Monta o prompt RAG com metodologia, contexto do aluno, catálogo de exercícios e template de saída.

Combina: instrução de sistema, metodologia RB, contexto do aluno (anamnese),
catálogo de exercícios filtrado (quando disponível), referências científicas
recuperadas do Qdrant, e template de formato de resposta.
"""

import logging

from src.config.types import ResultadoBusca

logger = logging.getLogger(__name__)

# Instrução base do sistema
_INSTRUCAO_BASE = (
    "Você é um assistente especializado em personal training.\n"
    "Use APENAS as referências abaixo para embasar cientificamente o treino.\n"
    "NÃO inclua citações de fontes nem referências bibliográficas na resposta.\n"
    "Gere SEMPRE um protocolo completo periodizado com múltiplas semanas adaptado ao "
    "contexto do aluno: iniciante → tipicamente 4 semanas; "
    "intermediário/avançado → tipicamente 5 semanas.\n"
    "SEMPRE gere pelo menos 4 semanas completas — nunca abrevie ou use reticências (...).\n"
    "O número de DIAS por semana DEVE ser exatamente igual ao campo 'Dias disponíveis por semana' "
    "informado no contexto do aluno. Ex.: se o aluno tem 4 dias → gere exatamente 4 dias em cada semana.\n"
    "Quantidade mínima de exercícios de FORTALECIMENTO por grupo muscular em cada sessão: "
    "músculos pequenos (bíceps, tríceps, ombros, panturrilha) → mínimo 3 exercícios; "
    "músculos grandes (peitoral, costas, quadríceps, posteriores de coxa, glúteo, core) "
    "→ mínimo 4 exercícios.\n"
    "Dentro da seção Fortalecimento, organize os exercícios por grupo muscular usando "
    "sub-headers #### (ex.: #### Peitoral, #### Tríceps).\n"
    "Formato obrigatório de cada exercício: duas linhas — "
    "primeira linha: nome do exercício com bullet (-); "
    "segunda linha (indentada com 2 espaços): N séries × N–N reps OU duração em segundos. "
    "Exemplo: - Supino reto com barra\\n  4 séries × 6–8 reps\n"
    "A seção '## Resumo do Aluno' deve ser um parágrafo contínuo, NÃO bullet points.\n"
    "A escolha e justificativa da divisão muscular seguem obrigatoriamente os critérios "
    "do bloco [DIVISÃO DE TREINO — MÉTODO RB] presente neste prompt.\n"
)

# Critérios do Método RB para divisão de treino — injetado em todo prompt
_DIVISAO_TREINO_RB = (
    "[DIVISÃO DE TREINO — MÉTODO RB]\n"
    "Quando o aluno selecionar 'Deixar o agente decidir', aplique os critérios abaixo "
    "para escolher a divisão mais adequada ao perfil do aluno:\n\n"
    "- Full Body (Corpo todo) → indicado para: iniciantes, 2–3x/semana, reabilitação, "
    "alunos com pouco tempo disponível.\n"
    "- Superior + Inferior → indicado para: intermediários, 3–4x/semana. "
    "Vantagem: melhor controle de volume e maior recuperação por grupamento.\n"
    "- Superior Anterior/Inferior Anterior ou Superior Posterior/Inferior Posterior (Corpo todo) → "
    "indicado para: intermediários e atletas. Respeita cadeias musculares e melhora equilíbrio.\n"
    "- Divisão completa em 4 partes (Superior Anterior, Superior Posterior, Inferior Anterior, "
    "Inferior Posterior) → indicado para: avançados, foco em hipertrofia, ≥4x/semana. "
    "Maior especificidade e volume por grupamento.\n\n"
    "REGRAS OBRIGATÓRIAS — aplicam-se a qualquer divisão:\n"
    "- Todo treino deve conter exercícios de core: anti-extensão, anti-rotação, "
    "anti-flexão lateral e estabilidade dinâmica.\n"
    "- Mínimo de 12 exercícios por sessão (ideal: 12–15; máximo: 18–20).\n"
    "- Estrutura obrigatória da sessão: Liberação Miofascial → Mobilidade → Ativação → Fortalecimento.\n"
    "- Em treinos de membros inferiores: incluir core. "
    "Em treinos de membros superiores: incluir estabilidade escapular.\n\n"
    "JUSTIFICATIVA OBRIGATÓRIA: na seção '## Metodologia do Treino', explique sempre "
    "qual divisão foi escolhida ou seguida e por quê, com base nos dados do aluno "
    "(frequência semanal, nível de condicionamento e objetivo principal).\n"
)

# Template de saída unificado — os marcadores ## SEMANA N são parseados pela interface
_TEMPLATE_SAIDA = """Estruture sua resposta EXATAMENTE neste formato. Use os marcadores de seção exatamente como indicado.

ATENÇÃO: O número de dias mostrado abaixo (Dia 1, Dia 2) é apenas exemplo estrutural.
Você DEVE gerar exatamente N dias por semana, onde N = 'Dias disponíveis por semana' do aluno.

## Resumo do Aluno
[Parágrafo único com: nome, idade, modalidade, objetivo, nível, restrições, dias/semana, tempo/sessão. NÃO usar bullet points.]

## Metodologia do Treino
[Raciocínio clínico para este aluno: divisão muscular escolhida, calibragem de volume/intensidade \
por nível, como as restrições físicas foram consideradas na seleção dos exercícios.]

## SEMANA 1 — [nome descritivo, ex: Adaptação e Técnica]

### Dia 1 — [foco do dia]

### Liberação Miofascial

* [nome do exercício]
  [duração, ex: 60s]

### Mobilidade

* [nome do exercício]
  [N séries × N reps]

### Ativação

* [nome do exercício]
  [N séries × N reps]

### Fortalecimento

#### [Músculo Grande, ex: Peitoral]

* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno, ex: Tríceps]

* [nome do exercício]
  [N séries × N–N reps (método)]

### Observações

* Descanso: [tempo entre séries]
* Intensidade: [RPE ou %]

### Dia 2 — [foco do dia]

### Liberação Miofascial

* [nome do exercício]
  [duração]

### Mobilidade

* [nome do exercício]
  [N séries × N reps]

### Ativação

* [nome do exercício]
  [N séries × N reps]

### Fortalecimento

#### [Músculo Grande]

* [nome do exercício]
  [N séries × N–N reps (método)]

#### [Músculo Pequeno]

* [nome do exercício]
  [N séries × N–N reps (método)]

### Observações

* Descanso: [tempo entre séries]
* Intensidade: [RPE ou %]

[continuar com Dia 3, Dia 4... até completar todos os dias do aluno]

## SEMANA 2 — [nome descritivo]

[mesma estrutura da SEMANA 1 — todos os dias completos]

## SEMANA 3 — [nome descritivo]

[mesma estrutura da SEMANA 1 — todos os dias completos]

## SEMANA 4 — [nome descritivo]

[mesma estrutura da SEMANA 1 — todos os dias completos]

"""


def montar_prompt(
    query: str,
    resultados: list[ResultadoBusca],
    metodologia: str = "",
    contexto_aluno: str = "",
    catalogo_filtrado=None,
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
    secoes.append(_INSTRUCAO_BASE)

    # Critérios de divisão de treino do Método RB
    secoes.append(_DIVISAO_TREINO_RB)

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
            "- Use o nome EXATO do exercício conforme escrito na coluna 'Exercício'. "
            "Não renomeie, abrevie nem adapte os nomes.\n"
            "- Exercícios marcados [PRIORIZAR] devem ser a primeira escolha para o nível do aluno.\n"
            "- Exercícios marcados [SUBSTITUTO OBRIGATÓRIO] substituem obrigatoriamente o exercício "
            "original. Nunca sugira o exercício original quando houver substituto marcado.\n"
            "- Cada sessão deve ter 12 a 15 exercícios no total: 2-3 liberações (se necessário) + "
            "3-4 mobilidades (se necessário) + 3-4 ativações + 5-8 fortalecimento "
            "(respeitando o mínimo por grupo muscular definido acima). "
            "Use a coluna 'Tempo por rep. (s)' para dimensionar o tempo total de cada exercício.\n"
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

    # Template de saída unificado
    secoes.append(_TEMPLATE_SAIDA)

    # Pergunta do personal
    secoes.append(f"PERGUNTA: {query}")

    return "\n".join(secoes)
