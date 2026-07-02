import json
import ollama

from src.tool_schemas import TOOL_SCHEMAS
from src.tools.fraud_tools import (
    consultar_transacoes,
    score_fraude,
    explicar_transacao,
    abrir_contestacao,
)
from src.rag import buscar_regras

MODELO = "llama3.1"

SYSTEM_PROMPT = (
    "Você é um assistente de atendimento de um banco, especializado em "
    "transações e prevenção a fraudes. Responda sempre em português do "
    "Brasil, de forma clara e cordial. Use as ferramentas disponíveis para "
    "consultar dados reais do cliente — nunca invente valores, datas ou "
    "transações. Se não houver dados, diga que não encontrou. "
    "IMPORTANTE: ao listar transações, SEMPRE mostre o ID real de cada uma "
    "(campo 'id' retornado pela ferramenta), pois o cliente usa esse ID "
    "para se referir a uma transação específica. Nunca renumere as "
    "transações com uma sequência própria (1, 2, 3...); use sempre o ID "
    "verdadeiro. Quando o cliente quiser contestar uma transação, confirme "
    "o ID e o motivo antes de prosseguir."
)


def _mapa_ferramentas(cliente_id: int, db_path: str):
    # Liga o NOME que o LLM usa à FUNÇÃO Python real.

    return {
        "consultar_transacoes": lambda limite=10: consultar_transacoes(
            cliente_id, limite, db_path),
        "score_fraude": lambda transacao_id: score_fraude(
            transacao_id, db_path),
        "explicar_transacao": lambda transacao_id: explicar_transacao(
            transacao_id, db_path),
        "abrir_contestacao": lambda transacao_id, motivo: abrir_contestacao(
            transacao_id, cliente_id, motivo, db_path),
        "consultar_regras": lambda pergunta: {
            "regras_encontradas": buscar_regras(pergunta)
        },
    }


def conversar(mensagem: str, historico: list, cliente_id: int,
              db_path: str = "data/fraud_assist.db") -> tuple[str, list]:
    ferramentas = _mapa_ferramentas(cliente_id, db_path)
    # monta o histórico: system prompt (só na 1ª vez) + conversa + nova msg
    mensagens = list(historico)
    if not mensagens:
        mensagens.append({"role": "system", "content": SYSTEM_PROMPT})
    mensagens.append({"role": "user", "content": mensagem})

    # PASSO 1 e 2: envia ao LLM com as ferramentas disponíveis
    resposta = ollama.chat(
        model=MODELO,
        messages=mensagens,
        tools=TOOL_SCHEMAS,
    )
    msg = resposta["message"]
    mensagens.append(msg)

    # PASSO 3: se o LLM pediu ferramentas, executa cada uma
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        for chamada in tool_calls:
            nome = chamada["function"]["name"]
            args = chamada["function"]["arguments"]
            if nome in ferramentas:
                try:
                    resultado = ferramentas[nome](**args)
                except TypeError as e:
                    resultado = {"erro": f"Parâmetros inválidos: {e}"}
            else:
                resultado = {"erro": f"Ferramenta desconhecida: {nome}"}
            # devolve o resultado da ferramenta ao histórico
            mensagens.append({
                "role": "tool",
                "content": json.dumps(resultado, ensure_ascii=False),
            })

        # PASSO 4: o LLM gera a resposta final com base nos resultados
        resposta_final = ollama.chat(model=MODELO, messages=mensagens)
        texto = resposta_final["message"]["content"]
        mensagens.append(resposta_final["message"])
        return texto, mensagens

    # sem tool call: resposta direta em texto
    return msg["content"], mensagens


if __name__ == "__main__":
    # teste manual rápido (requer Ollama rodando e o banco gerado)
    hist = []
    resp, hist = conversar("Quais foram minhas últimas 3 transações?",
                           hist, cliente_id=1)
    print("BOT:", resp)