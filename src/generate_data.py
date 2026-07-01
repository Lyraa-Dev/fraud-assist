import random
from datetime import datetime, timedelta

from src.schema import get_connection, create_schema


ESTABELECIMENTOS = {
    "supermercado": ["Pão de Açúcar", "Carrefour", "Assaí", "Atacadão"],
    "restaurante": ["iFood", "McDonald's", "Outback", "Habib's"],
    "streaming": ["Netflix", "Spotify", "Disney+", "Amazon Prime"],
    "vestuario": ["Renner", "Riachuelo", "C&A", "Zara"],
    "eletronicos": ["Amazon", "Magazine Luiza", "Kabum", "Fast Shop"],
    "transporte": ["Uber", "99", "Posto Shell", "Posto Ipiranga"],
    "farmacia": ["Drogasil", "Pague Menos", "Raia", "Pacheco"],
}
CIDADES_BR = ["Recife", "São Paulo", "Rio de Janeiro", "Belo Horizonte",
              "Salvador", "Fortaleza", "Curitiba", "Porto Alegre"]
# países usados para simular fraude (compra internacional inesperada)
PAISES_FRAUDE = ["Rússia", "China", "Nigéria", "Ucrânia", "Romênia"]


def _transacao_normal(cliente_id, base_date, rng):
    """Uma transação legítima: valor moderado, horário comercial, Brasil."""
    categoria = rng.choice(list(ESTABELECIMENTOS.keys()))
    estab = rng.choice(ESTABELECIMENTOS[categoria])
    dias_atras = rng.randint(0, 90)
    hora = rng.choices(
        population=list(range(24)),
        # concentra em horário de vigília (8h-22h)
        weights=[1, 1, 1, 1, 1, 1, 2, 3, 5, 6, 7, 8,
                 8, 7, 6, 6, 6, 7, 8, 7, 5, 4, 2, 1],
        k=1,
    )[0]
    dt = base_date - timedelta(days=dias_atras, hours=rng.randint(0, 23))
    dt = dt.replace(hour=hora)
    valor = round(rng.uniform(10, 500), 2)
    return {
        "cliente_id": cliente_id,
        "data_hora": dt.isoformat(timespec="seconds"),
        "valor": valor,
        "estabelecimento": estab,
        "categoria": categoria,
        "cidade": rng.choice(CIDADES_BR),
        "pais": "Brasil",
        "hora": hora,
        "is_fraude": 0,
        "status": "aprovada",
    }


def _transacao_fraude(cliente_id, base_date, rng):
    """Uma transação fraudulenta: assinatura típica de fraude.

    Combina 2+ sinais de risco: valor alto, madrugada, país estrangeiro,
    categoria de alto valor. É isso que o modelo aprende e o chatbot explica.
    """
    dias_atras = rng.randint(0, 30)
    hora = rng.choice([0, 1, 2, 3, 4])          # madrugada
    dt = (base_date - timedelta(days=dias_atras)).replace(hour=hora)
    valor = round(rng.uniform(1500, 8000), 2)   # valor atípico alto
    return {
        "cliente_id": cliente_id,
        "data_hora": dt.isoformat(timespec="seconds"),
        "valor": valor,
        "estabelecimento": rng.choice(["Loja Online XYZ", "Global Shop",
                                       "Digital Store", "Web Market"]),
        "categoria": "eletronicos",
        "cidade": "Desconhecida",
        "pais": rng.choice(PAISES_FRAUDE),
        "hora": hora,
        "is_fraude": 1,
        "status": rng.choice(["aprovada", "bloqueada"]),
    }


def generate(db_path="data/fraud_assist.db", n_clientes=50,
             n_transacoes=2000, taxa_fraude=0.03, seed=42):
    """Cria o schema e popula o banco com transações sintéticas."""
    rng = random.Random(seed)
    create_schema(db_path)
    conn = get_connection(db_path)
    # limpa antes de repopular (idempotente para reexecução)
    conn.execute("DELETE FROM transacoes")
    conn.execute("DELETE FROM contestacoes")

    base_date = datetime(2026, 6, 30, 12, 0, 0)
    n_fraudes = int(n_transacoes * taxa_fraude)
    registros = []
    for i in range(n_transacoes):
        cliente_id = rng.randint(1, n_clientes)
        if i < n_fraudes:
            registros.append(_transacao_fraude(cliente_id, base_date, rng))
        else:
            registros.append(_transacao_normal(cliente_id, base_date, rng))
    rng.shuffle(registros)

    conn.executemany(
        """INSERT INTO transacoes
           (cliente_id, data_hora, valor, estabelecimento, categoria,
            cidade, pais, hora, is_fraude, status)
           VALUES (:cliente_id, :data_hora, :valor, :estabelecimento,
                   :categoria, :cidade, :pais, :hora, :is_fraude, :status)""",
        registros,
    )
    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM transacoes").fetchone()[0]
    fraudes = conn.execute(
        "SELECT COUNT(*) FROM transacoes WHERE is_fraude=1").fetchone()[0]
    conn.close()
    print(f"Banco populado: {total} transações ({fraudes} fraudes, "
          f"{100*fraudes/total:.1f}%) em {n_clientes} clientes.")
    return total, fraudes


if __name__ == "__main__":
    generate()
