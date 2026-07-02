import os
import tempfile
import pytest

from src.schema import get_connection
from src.generate_data import generate
from src.tools.fraud_tools import (
    consultar_transacoes,
    score_fraude,
    explicar_transacao,
    abrir_contestacao,
)


@pytest.fixture
def db():
    # Banco temporário populado, com uma fraude e uma normal conhecidas.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    generate(path, n_clientes=10, n_transacoes=200, taxa_fraude=0.1, seed=1)
    yield path
    os.remove(path)


def _id_de_uma_fraude(db_path):
    conn = get_connection(db_path)
    tid = conn.execute(
        "SELECT id FROM transacoes WHERE is_fraude=1 LIMIT 1").fetchone()[0]
    conn.close()
    return tid


def _id_de_uma_normal(db_path):
    conn = get_connection(db_path)
    tid = conn.execute(
        "SELECT id FROM transacoes WHERE is_fraude=0 LIMIT 1").fetchone()[0]
    conn.close()
    return tid


# consultar_transacoes
def test_consultar_retorna_transacoes(db):
    conn = get_connection(db)
    cliente = conn.execute(
        "SELECT cliente_id FROM transacoes LIMIT 1").fetchone()[0]
    conn.close()
    res = consultar_transacoes(cliente, limite=5, db_path=db)
    assert isinstance(res, list)
    assert len(res) <= 5
    assert all(r["cliente_id"] == cliente for r in res)


def test_consultar_cliente_inexistente_retorna_vazio(db):
    assert consultar_transacoes(99999, db_path=db) == []


def test_consultar_ordena_mais_recente_primeiro(db):
    conn = get_connection(db)
    cliente = conn.execute(
        """SELECT cliente_id FROM transacoes
           GROUP BY cliente_id HAVING COUNT(*) >= 2 LIMIT 1""").fetchone()[0]
    conn.close()
    res = consultar_transacoes(cliente, limite=10, db_path=db)
    datas = [r["data_hora"] for r in res]
    assert datas == sorted(datas, reverse=True)


# score_fraude 
def test_score_fraude_alto_para_fraude(db):
    tid = _id_de_uma_fraude(db)
    res = score_fraude(tid, db_path=db)
    assert res["nivel"] == "alto"
    assert res["score"] >= 0.6
    assert len(res["sinais"]) >= 2


def test_score_baixo_para_normal(db):
    tid = _id_de_uma_normal(db)
    res = score_fraude(tid, db_path=db)
    assert res["nivel"] == "baixo"


def test_score_transacao_inexistente_retorna_erro(db):
    res = score_fraude(99999, db_path=db)
    assert "erro" in res


# explicar_transacao 
def test_explicar_fraude_lista_sinais(db):
    tid = _id_de_uma_fraude(db)
    res = explicar_transacao(tid, db_path=db)
    assert res["nivel_risco"] == "alto"
    assert "risco" in res["explicacao"].lower()


def test_explicar_transacao_inexistente_retorna_erro(db):
    assert "erro" in explicar_transacao(99999, db_path=db)


# abrir_contestacao 
def test_abrir_contestacao_sucesso(db):
    tid = _id_de_uma_fraude(db)
    dono = _buscar_dono(db, tid)
    res = abrir_contestacao(tid, dono, "Não reconheço esta compra", db_path=db)
    assert res["status"] == "aberta"
    assert "contestacao_id" in res


def test_contestacao_de_transacao_alheia_falha(db):
    tid = _id_de_uma_fraude(db)
    dono = _buscar_dono(db, tid)
    outro = dono + 1  # cliente diferente do dono
    res = abrir_contestacao(tid, outro, "teste", db_path=db)
    assert "erro" in res


def test_contestacao_transacao_inexistente_falha(db):
    assert "erro" in abrir_contestacao(99999, 1, "teste", db_path=db)


def _buscar_dono(db_path, transacao_id):
    conn = get_connection(db_path)
    dono = conn.execute(
        "SELECT cliente_id FROM transacoes WHERE id=?",
        (transacao_id,)).fetchone()[0]
    conn.close()
    return dono
