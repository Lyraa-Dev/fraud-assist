import os
import tempfile
import pytest

from src.schema import create_schema, get_connection
from src.generate_data import generate


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.remove(path)


def test_schema_cria_tabelas(temp_db):
    create_schema(temp_db)
    conn = get_connection(temp_db)
    tabelas = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert "transacoes" in tabelas
    assert "contestacoes" in tabelas


def test_geracao_popula_quantidade_correta(temp_db):
    total, _ = generate(temp_db, n_clientes=10, n_transacoes=200,
                        taxa_fraude=0.05, seed=1)
    assert total == 200


def test_taxa_fraude_respeitada(temp_db):
    _, fraudes = generate(temp_db, n_clientes=10, n_transacoes=200,
                         taxa_fraude=0.05, seed=1)
    assert fraudes == 10  # 5% de 200


def test_geracao_reprodutivel(temp_db):
    generate(temp_db, n_transacoes=100, seed=42)
    conn = get_connection(temp_db)
    primeiro = conn.execute(
        "SELECT valor FROM transacoes ORDER BY id LIMIT 1").fetchone()[0]
    conn.close()

    fd, path2 = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    generate(path2, n_transacoes=100, seed=42)
    conn2 = get_connection(path2)
    primeiro2 = conn2.execute(
        "SELECT valor FROM transacoes ORDER BY id LIMIT 1").fetchone()[0]
    conn2.close()
    os.remove(path2)

    assert primeiro == primeiro2  # mesma seed produz mesmo banco


def test_fraudes_tem_assinatura(temp_db):
    generate(temp_db, n_transacoes=500, taxa_fraude=0.1, seed=7)
    conn = get_connection(temp_db)
    # toda fraude deve ter valor alto E horário de madrugada
    fraudes = conn.execute(
        "SELECT valor, hora, pais FROM transacoes WHERE is_fraude=1").fetchall()
    conn.close()
    assert len(fraudes) > 0
    for valor, hora, pais in fraudes:
        assert valor >= 1500          # valor atípico
        assert hora in (0, 1, 2, 3, 4)  # madrugada
        assert pais != "Brasil"        # país estrangeiro


def test_transacoes_normais_sao_brasil(temp_db):
    generate(temp_db, n_transacoes=500, taxa_fraude=0.1, seed=7)
    conn = get_connection(temp_db)
    normais = conn.execute(
        "SELECT pais FROM transacoes WHERE is_fraude=0").fetchall()
    conn.close()
    assert all(r[0] == "Brasil" for r in normais)
