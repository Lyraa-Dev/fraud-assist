# 🤖 fraud-assist — Assistente Transacional Anti-Fraude

> Chatbot transacional que orquestra **ferramentas reais** (consulta de histórico, scoring de fraude, abertura de contestação) via *tool calling*, com RAG sobre regras de negócio, guardrails de segurança e avaliação quantitativa de roteamento de intenções.

**Status:** 🚧 em construção — desenvolvido em fases incrementais.

---

## 🎯 O problema

Clientes de bancos e fintechs precisam resolver dúvidas sobre suas transações — "essa compra foi minha?", "quero contestar esse valor", "por que essa transação foi bloqueada?". Um chatbot que apenas *conversa* não resolve: ele precisa **executar ações** e **consultar dados reais**.

A diferença entre um chatbot de FAQ e um chatbot **transacional** é o *tool calling*: o LLM não inventa o saldo nem decide se algo é fraude — ele orquestra ferramentas que consultam o banco e chamam o modelo de detecção de fraude. O LLM é o maestro; as ferramentas fazem o trabalho.

---

## 🧩 Arquitetura

```
Usuário (linguagem natural, PT-BR)
        │
        ▼
   LLM (Ollama) ──── entende a intenção e escolhe a ferramenta
        │
        ├─► consultar_transacoes()   → banco SQLite
        ├─► score_fraude()           → modelo de ML (reuso do detection-fraude)
        ├─► abrir_contestacao()      → grava no banco
        └─► RAG (FAISS)              → regras de negócio
        │
        ▼
   Resposta em linguagem natural + guardrails
```

---

## 🗺️ Roadmap por fases

| Fase | Entrega | Status |
|------|---------|--------|
| 0 | Estrutura e configuração | ✅ |
| 1 | Camada de dados (SQLite + transações sintéticas) | ✅ |
| 2 | Ferramentas transacionais + testes | ✅ |
| 3 | Orquestração via tool calling | ⬜ |
| 4 | RAG sobre regras de negócio | ⬜ |
| 5 | Interface Streamlit | ⬜ |
| 6 | Framework de avaliação (roteamento + alucinação) | ⬜ |
| 7 | Guardrails de segurança + documentação final | ⬜ |

---

## 🛠️ Stack

Python · Ollama · LangChain · FAISS · Scikit-learn · SQLite · Streamlit · Pytest

## 🤝 Contato

**Ricardo Lyra** — [LinkedIn](https://www.linkedin.com/in/lyraa-dev/) · [GitHub](https://github.com/Lyraa-Dev)
