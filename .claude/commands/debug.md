# /debug

Workflow sistemático de debugging em 6 fases para o projeto Jarvis.

## Uso

```
/debug <descrição do problema>
```

## Fases

### Fase 1: Entender o problema

Antes de qualquer hipótese, faça as 5 perguntas diagnósticas:

1. **O que deveria acontecer?** — comportamento esperado
2. **O que está acontecendo de fato?** — comportamento observado (mensagem de erro, output incorreto)
3. **Quando começou?** — última versão funcionando, mudança recente
4. **É reproduzível?** — sempre, às vezes, sob condições específicas
5. **Qual o contexto?** — módulo afetado, dados de entrada, ambiente (local/docker)

Aguarde as respostas antes de prosseguir.

### Fase 2: Levantar hipóteses

Com base nas respostas, liste **3 hipóteses** ordenadas da mais para a menos provável:

```
H1 (mais provável): <hipótese>
H2: <hipótese>
H3 (menos provável): <hipótese>
```

### Fase 3: Investigar H1

Investigue a hipótese mais provável primeiro. Pontos de falha comuns por módulo no Jarvis:

| Módulo | Pontos de falha comuns |
|---|---|
| `ingestion/` | PDF corrompido, encoding inesperado, chunk size inadequado |
| `retrieval/` | Qdrant offline, collection inexistente, embedding dimension mismatch |
| `generation/` | NVIDIA_NIM_API_KEY inválida, rate limit, timeout, prompt malformado |
| `interface/` | Estado do Streamlit corrompido, variável de sessão ausente |
| `config/` | `.env` não carregado, variável de ambiente faltando |

Execute verificações específicas e mostre o output ao dev.

Se H1 for descartada, investigue H2, depois H3.

### Fase 4: Declarar causa raiz

Quando encontrada, declare explicitamente:

```
CAUSA RAIZ IDENTIFICADA
────────────────────────
Localização : <arquivo>:<linha>
Problema    : <descrição técnica precisa>
Evidência   : <output ou trecho de código que confirma>
```

### Fase 5: Propor solução mínima

Proponha a correção mais simples que resolve o problema sem introduzir complexidade desnecessária.

**Mostre a solução proposta e aguarde aprovação antes de alterar qualquer código.**

```
SOLUÇÃO PROPOSTA
─────────────────
Arquivo : <arquivo>
Mudança : <descrição da alteração>

[mostrar diff ou pseudocódigo]

Aprovar? (sim/não/ajustar)
```

### Fase 6: Prevenir regressão

Após aplicar a correção, sugira um teste automatizado que teria detectado o bug antes:

```
TESTE SUGERIDO
───────────────
Arquivo : tests/<módulo>/test_<nome>.py
O que testa: <descrição>
Por quê: este teste teria falhado antes da correção e passará agora
```

Se o dev aceitar, implemente o teste usando o workflow TDD do projeto.

---

> **Nota:** Se você tiver o plugin Superpowers instalado, o skill `systematic-debugging`
> oferece orquestração de subagentes para investigações mais complexas.
