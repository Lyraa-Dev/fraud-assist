import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id      INTEGER NOT NULL,
    data_hora       TEXT    NOT NULL,   -- ISO 8601
    valor           REAL    NOT NULL,
    estabelecimento TEXT    NOT NULL,
    categoria       TEXT    NOT NULL,
    cidade          TEXT    NOT NULL,
    pais            TEXT    NOT NULL,
    hora            INTEGER NOT NULL,   -- 0-23, facilita features de horário
    is_fraude       INTEGER NOT NULL DEFAULT 0,  -- rótulo real (ground truth)
    status          TEXT    NOT NULL DEFAULT 'aprovada'  -- aprovada|bloqueada
);

CREATE TABLE IF NOT EXISTS contestacoes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transacao_id   INTEGER NOT NULL,
    cliente_id     INTEGER NOT NULL,
    motivo         TEXT    NOT NULL,
    data_abertura  TEXT    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'aberta',  -- aberta|em_analise|resolvida
    FOREIGN KEY (transacao_id) REFERENCES transacoes(id)
);

CREATE INDEX IF NOT EXISTS idx_transacoes_cliente ON transacoes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_contestacoes_cliente ON contestacoes(cliente_id);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    """Abre conexão com o banco, criando o diretório se necessário."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # retorna linhas como dict-like
    return conn


def create_schema(db_path: str) -> None:
    """Cria as tabelas e índices (idempotente)."""
    conn = get_connection(db_path)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_schema("data/fraud_assist.db")
    print("Schema criado em data/fraud_assist.db")
