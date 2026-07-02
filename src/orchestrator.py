import os
import json
from groq import Groq
from dotenv import load_dotenv
 
from src.tool_schemas import TOOL_SCHEMAS
from src.tools.fraud_tools import (
    consultar_transacoes,
    score_fraude,
    explicar_transacao,
    abrir_contestacao,
)
from src.rag import buscar_regras
 
load_dotenv()
_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
 
MODELO = "llama-3.3-70b-versatile"
 
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
    """Processa uma mensagem do usuário e devolve (resposta, historico_novo)."""
    ferramentas = _mapa_ferramentas(cliente_id, db_path)
 
    mensagens = list(historico)
    if not mensagens:
        mensagens.append({"role": "system", "content": SYSTEM_PROMPT})
    mensagens.append({"role": "user", "content": mensagem})
 
    # PASSO 1 e 2: envia ao LLM com as ferramentas disponíveis
    resposta = _client.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )
    msg = resposta.choices[0].message
    # converte o objeto de mensagem do Groq em dict para guardar no histórico
    mensagens.append(_msg_para_dict(msg))
 
    # PASSO 3: se o LLM pediu ferramentas, executa cada uma
    if msg.tool_calls:
        for chamada in msg.tool_calls:
            nome = chamada.function.name
            try:
                args = json.loads(chamada.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            if nome in ferramentas:
                try:
                    resultado = ferramentas[nome](**args)
                except TypeError as e:
                    resultado = {"erro": f"Parâmetros inválidos: {e}"}
            else:
                resultado = {"erro": f"Ferramenta desconhecida: {nome}"}
            # devolve o resultado da ferramenta ao histórico, ligado pelo id
            mensagens.append({
                "role": "tool",
                "tool_call_id": chamada.id,
                "content": json.dumps(resultado, ensure_ascii=False),
            })
 
        # PASSO 4: o LLM gera a resposta final com base nos resultados
        resposta_final = _client.chat.completions.create(
            model=MODELO, messages=mensagens)
        texto = resposta_final.choices[0].message.content
        mensagens.append({"role": "assistant", "content": texto})
        return texto, mensagens
 
    # sem tool call: resposta direta em texto
    return msg.content, mensagens
 
 
def _msg_para_dict(msg) -> dict:
    """Converte a mensagem do assistente (objeto Groq) em dict serializável,
    preservando os tool_calls para o histórico ficar coerente."""
    d = {"role": "assistant", "content": msg.content or ""}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in msg.tool_calls
        ]
    return d
 
 
if __name__ == "__main__":
    hist = []
    resp, hist = conversar("Quais foram minhas últimas 3 transações?",
                           hist, cliente_id=1)
    print("BOT:", resp)