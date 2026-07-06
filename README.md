# fraud-assist — Assistente Transacional Anti-Fraude

> Chatbot transacional para o domínio bancário que orquestra **ferramentas reais** (consulta de transações, scoring de fraude, contestação) via **tool calling**, com **RAG** sobre regras de negócio, **guardrails** de segurança e **avaliação quantitativa** de roteamento e alucinação.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LLM](https://img.shields.io/badge/LLM-Groq%20(Llama%203.3)-orange)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb)
![Testes](https://img.shields.io/badge/testes-42%20passing-brightgreen)

---

## O problema

Clientes de bancos e fintechs precisam resolver dúvidas sobre transações — *"essa compra foi minha?"*, *"quero contestar essa cobrança"*, *"por que essa transação foi bloqueada?"*. Um chatbot que apenas **conversa** não resolve: ele precisa **executar ações** e **consultar dados reais**, sem inventar valores.

A diferença entre um chatbot de FAQ e um chatbot **transacional** é o *tool calling*: o LLM não inventa o saldo nem decide sozinho se algo é fraude — ele **orquestra ferramentas** que consultam o banco e chamam o modelo de detecção. O LLM é o maestro; as ferramentas fazem o trabalho. É isso que torna as respostas confiáveis.

---

## Resultados

| Métrica | Valor |
|---|---|
| **Acurácia de roteamento de intenções** | **94,6% ± 5,4%** (5 rodadas independentes) |
| Cobertura de testes automatizados | 42 testes (dados, ferramentas, segurança) |
| Detecção de alucinação | 2 abordagens: verificação factual + LLM-as-a-Judge |
| Proteção contra prompt injection | filtro determinístico + isolamento de `cliente_id` |

> A acurácia é reportada como **média ± desvio de múltiplas rodadas**, excluindo falhas de API do cálculo — porque LLMs são não-determinísticos e uma rodada única é um ponto ruidoso.

---

## Arquitetura

```
┌─────────────┐     HTTP      ┌──────────────┐
│  Front-end  │ ────────────► │   FastAPI    │
│ React+Vite  │ ◄──────────── │ (sessões em  │
└─────────────┘   resposta    │   memória)   │
                              └──────┬───────┘
                                     │
                         ┌───────────▼─────────────┐
                         │   GUARDRAILS (entrada)  │  ◄─ bloqueia injection,
                         └───────────┬─────────────┘     valida antes do LLM
                                     │
                         ┌───────────▼─────────────┐
                         │   ORCHESTRATOR (Groq)   │  ◄─ tool calling
                         │  llama-3.3-70b-versatile│
                         └───────────┬─────────────┘
                                     │ decide qual ferramenta
        ┌──────────────┬─────────────┼──────────────┬──────────────┐
        ▼              ▼             ▼              ▼              ▼
  consultar_      score_       explicar_     abrir_         consultar_
  transacoes      fraude       transacao     contestacao    regras (RAG)
        │              │             │              │              │
        └──────────────┴─────────────┴──────────────┘              │
                       ▼                                           ▼
                 SQLite (transações,                      FAISS + embeddings
                  contestações)                          multilíngues (regras)
```

**Princípios de design:**

- **Segurança arquitetural:** o `cliente_id` vem sempre da sessão, nunca do LLM — um usuário não consegue pedir dados de outro cliente, mesmo tentando via prompt injection.
- **Ferramentas testáveis sem LLM:** cada ferramenta é uma função pura, testada isoladamente. O LLM só decide *quando* chamá-las.
- **Avaliação separada da execução:** métricas são geradas offline e versionadas; o dashboard apenas visualiza, sem gastar cota de API.

---

## Funcionalidades

- **Chatbot transacional** com memória de conversa por sessão.
- **5 ferramentas** orquestradas por tool calling: consulta de extrato, scoring de fraude, explicação de transação, abertura de contestação e consulta de regras.
- **RAG** sobre políticas de negócio (bloqueio, contestação, limites) com FAISS e embeddings multilíngues.
- **Detecção de fraude** por sinais de risco (valor atípico, horário incomum, origem internacional), com arquitetura pronta para plugar um modelo de ML.
- **Guardrails**: detecção de prompt injection, validação de entrada e confirmação de ações que modificam estado.
- **Framework de avaliação**: acurácia de roteamento com análise de variância + detecção de alucinação (factual e LLM-as-a-Judge).
- **Dashboard de métricas** em Streamlit.
- **API REST** (FastAPI) + **front-end** React.

---

## Stack

**Back-end:** Python · FastAPI · Groq (Llama 3.3) · LangChain · FAISS · sentence-transformers · SQLite
**Front-end:** React · Vite · react-markdown
**Avaliação/Viz:** Streamlit · pytest

---

## Como executar

**Pré-requisitos:** Python 3.11+, Node.js, e uma chave de API do [Groq](https://console.groq.com) (plano gratuito).

```bash
# 1. Clonar e criar ambiente
git clone https://github.com/Lyraa-Dev/fraud-assist.git
cd fraud-assist
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Configurar a chave (arquivo .env na raiz)
echo GROQ_API_KEY=sua_chave_aqui > .env

# 3. Gerar o banco de dados sintético
python -m src.generate_data

# 4. Rodar a API (terminal 1)
uvicorn src.api:app --reload

# 5. Rodar o front-end (terminal 2)
cd frontend && npm install && npm run dev
# abre em http://localhost:5173
```

**Outros comandos:**

```bash
pytest                              # roda os 42 testes
python -m src.eval.avaliador --salvar   # gera as métricas de avaliação
streamlit run app/dashboard.py          # dashboard de métricas
python -m src.chat                       # chat pelo terminal
```

---

## Estrutura

```
fraud-assist/
├── src/
│   ├── schema.py            # schema do banco SQLite
│   ├── generate_data.py     # gerador de transações sintéticas
│   ├── tools/fraud_tools.py # as 4 ferramentas transacionais
│   ├── tool_schemas.py      # descrição das ferramentas p/ o LLM
│   ├── rag.py               # RAG sobre regras (FAISS)
│   ├── orchestrator.py      # tool calling (Groq)
│   ├── guardrails.py        # segurança (injection, validação)
│   ├── api.py               # API REST (FastAPI)
│   ├── chat.py              # chat via terminal
│   └── eval/                # framework de avaliação
├── frontend/                # front-end React + Vite
├── app/dashboard.py         # dashboard Streamlit de métricas
├── rules/                   # documentos de regras (base do RAG)
├── tests/                   # 42 testes automatizados
└── reports/                 # métricas de avaliação versionadas
```

---

## Decisões técnicas

| Decisão | Justificativa |
|---|---|
| Groq (nuvem) em vez de Ollama (local) | Modelo maior (70B) sem depender de GPU local; deployável |
| `cliente_id` da sessão, não do LLM | Segurança: impede acesso a dados de terceiros por prompt injection |
| Embeddings multilíngues | Conteúdo em português; modelos só-inglês falham (lição de projeto anterior) |
| Avaliação multi-rodada (média ± desvio) | LLMs são não-determinísticos; média ± desvio é honesto, ponto único não |
| Guardrails determinísticos antes do LLM | Bloqueia o óbvio sem gastar cota; defesa em camadas |
| Coerção de parâmetros numéricos | Modelos às vezes mandam número como string; sistema tolerante não quebra |

---

## Limitações conhecidas

- **Sessões em memória:** reiniciar o servidor perde o histórico. Em produção, migraria para Redis.
- **Guardrail por regex:** primeira barreira, não exaustiva. A defesa real contra acesso indevido é arquitetural (`cliente_id` da sessão).
- **Dados sintéticos:** as transações são geradas para demonstração, não são dados reais.
- **Roteamento imperfeito:** ~5% dos casos em fronteiras ambíguas (ex.: "regra geral" vs. "transação específica"). Documentado, não mascarado.

---

## 👤 Autor

**Ricardo Henrique da Silva Lyra** — Cientista de Dados
[LinkedIn](https://www.linkedin.com/in/lyraa-dev/) · [GitHub](https://github.com/Lyraa-Dev)