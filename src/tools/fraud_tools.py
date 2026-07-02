from datetime import datetime
from src.schema import get_connection

DB_PATH = "data/fraud_assist.db"

# Ferramenta 1 — consultar transações
def consultar_transacoes(cliente_id: int, limite: int = 10,
                         db_path: str = DB_PATH) -> list[dict]:
    ## Retorna as últimas transações de um cliente, mais recentes primeiro.

    conn = get_connection(db_path)
    linhas = conn.execute(
        """SELECT id, cliente_id, data_hora, valor, estabelecimento, categoria,
                  cidade, pais, status, is_fraude
           FROM transacoes
           WHERE cliente_id = ?
           ORDER BY data_hora DESC
           LIMIT ?""",
        (cliente_id, limite),
    ).fetchall()
    conn.close()
    return [dict(linha) for linha in linhas]


def _buscar_transacao(transacao_id: int, db_path: str = DB_PATH):
    # Helper interno: busca uma transação pelo id (ou None).
    conn = get_connection(db_path)
    linha = conn.execute(
        "SELECT * FROM transacoes WHERE id = ?", (transacao_id,)
    ).fetchone()
    conn.close()
    return dict(linha) if linha else None

# Ferramenta 2 — score de fraude (baseado em regras, por ora)

def score_fraude(transacao_id: int, db_path: str = DB_PATH) -> dict:
    #Calcula o risco de fraude de uma transação (0.0 a 1.0).

    t = _buscar_transacao(transacao_id, db_path)
    if t is None:
        return {"erro": f"Transação {transacao_id} não encontrada."}

    sinais = []
    score = 0.0

    if t["valor"] >= 1500:
        sinais.append(f"valor atípico (R$ {t['valor']:.2f})")
        score += 0.4
    if t["hora"] in (0, 1, 2, 3, 4):
        sinais.append(f"horário incomum ({t['hora']:02d}h, madrugada)")
        score += 0.3
    if t["pais"] != "Brasil":
        sinais.append(f"compra internacional ({t['pais']})")
        score += 0.3

    score = min(score, 1.0)
    nivel = "alto" if score >= 0.6 else "medio" if score >= 0.3 else "baixo"
    return {
        "transacao_id": transacao_id,
        "score": round(score, 2),
        "nivel": nivel,
        "sinais": sinais,
    }

# Ferramenta 3 — explicar transação (para o usuário)

def explicar_transacao(transacao_id: int, db_path: str = DB_PATH) -> dict:
    ## Explica por que uma transação é ou não considerada suspeita.

    t = _buscar_transacao(transacao_id, db_path)
    if t is None:
        return {"erro": f"Transação {transacao_id} não encontrada."}

    avaliacao = score_fraude(transacao_id, db_path)
    if avaliacao["nivel"] == "baixo":
        resumo = "Transação com perfil normal, sem sinais relevantes de risco."
    else:
        resumo = ("Transação com sinais de risco: "
                  + ", ".join(avaliacao["sinais"]) + ".")
    return {
        "transacao_id": transacao_id,
        "estabelecimento": t["estabelecimento"],
        "valor": t["valor"],
        "data_hora": t["data_hora"],
        "status": t["status"],
        "nivel_risco": avaliacao["nivel"],
        "explicacao": resumo,
    }


# Ferramenta 4 — abrir contestação 

def abrir_contestacao(transacao_id: int, cliente_id: int, motivo: str,
                     db_path: str = DB_PATH) -> dict:
    # Registra um pedido de contestação para uma transação.

   
    t = _buscar_transacao(transacao_id, db_path)
    if t is None:
        return {"erro": f"Transação {transacao_id} não encontrada."}
    if t["cliente_id"] != cliente_id:
        # validação de posse: cliente não pode contestar transação alheia
        return {"erro": "Esta transação não pertence a este cliente."}

    conn = get_connection(db_path)
    cursor = conn.execute(
        """INSERT INTO contestacoes
           (transacao_id, cliente_id, motivo, data_abertura, status)
           VALUES (?, ?, ?, ?, 'aberta')""",
        (transacao_id, cliente_id, motivo,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    contestacao_id = cursor.lastrowid
    conn.close()
    return {
        "contestacao_id": contestacao_id,
        "transacao_id": transacao_id,
        "status": "aberta",
        "mensagem": "Contestação registrada com sucesso.",
    }
