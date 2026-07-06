"""
dashboard.py
------------
Dashboard de métricas de avaliação do fraud-assist (Streamlit).

Lê o arquivo reports/avaliacao.json (gerado por
`python -m src.eval.avaliador --salvar`) e visualiza os resultados.
NÃO faz chamadas ao LLM — só lê e mostra. Assim é instantâneo, não gasta
cota e funciona mesmo para quem clona o repo sem chave de API.

Rodar:  streamlit run app/dashboard.py
"""

import json
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="fraud-assist — Avaliação", layout="wide")

st.title("🛡️ fraud-assist — Dashboard de Avaliação")
st.caption(
    "Métricas de roteamento de intenções do assistente. Avaliação gerada "
    "offline e versionada — este painel apenas visualiza os resultados."
)

CAMINHO = Path("reports/avaliacao.json")

if not CAMINHO.exists():
    st.warning(
        "Nenhuma avaliação encontrada. Gere com:\n\n"
        "`python -m src.eval.avaliador --salvar`"
    )
    st.stop()

with open(CAMINHO, encoding="utf-8") as f:
    dados = json.load(f)

# ---- cabeçalho com metadados ----
col_a, col_b, col_c = st.columns(3)
media = dados.get("acuracia_media", dados.get("acuracia", 0))
desvio = dados.get("desvio_padrao", 0)
n_rodadas = dados.get("n_rodadas", 1)
col_a.metric("Acurácia média de roteamento",
             f"{media:.0%}", f"± {desvio:.0%} (desvio)")
col_b.metric("Rodadas de avaliação", n_rodadas)
col_c.metric("Faixa (min–max)",
             f"{dados.get('acuracia_min', media):.0%}–"
             f"{dados.get('acuracia_max', media):.0%}")
st.caption(f"Modelo: `{dados.get('modelo', '—')}`  ·  "
           f"Avaliado em: {dados.get('data_avaliacao', '—')}  ·  "
           f"Média de {n_rodadas} rodadas independentes")

st.divider()

# ---- acurácia por rodada (mostra a variância visualmente) ----
if dados.get("rodadas"):
    st.subheader("Acurácia por rodada (variância entre execuções)")
    st.caption(
        "LLMs são não-determinísticos: cada execução dá um número um pouco "
        "diferente. Por isso reportamos a média de várias rodadas, não um "
        "ponto único."
    )
    st.bar_chart(
        {"acurácia": {f"rodada {r['rodada']}": r["acuracia"]
                      for r in dados["rodadas"]}},
        height=250,
    )
    st.divider()

# ---- acurácia por ferramenta (gráfico de barras) ----
st.subheader("Acurácia por ferramenta (última rodada)")
por_ferr = dados["por_ferramenta"]
labels = list(por_ferr.keys())
acuracias = [por_ferr[k]["acuracia"] for k in labels]

st.bar_chart(
    {"acurácia": {labels[i]: acuracias[i] for i in range(len(labels))}},
    height=300,
)

# tabela detalhada por ferramenta
st.dataframe(
    [
        {
            "Ferramenta": k,
            "Acurácia": f"{v['acuracia']:.0%}",
            "Acertos": v["acertos"],
            "Total": v["total"],
        }
        for k, v in por_ferr.items()
    ],
    use_container_width=True,
    hide_index=True,
)

st.divider()

# ---- detalhamento caso a caso ----
st.subheader("Detalhamento dos casos (última rodada)")
mostrar_so_erros = st.checkbox("Mostrar apenas os erros", value=False)

linhas = []
for d in dados["detalhes"]:
    if mostrar_so_erros and d["acertou"]:
        continue
    linhas.append({
        "Pergunta": d["pergunta"],
        "Esperado": d["esperado"] or "—",
        "Obtido": d["obtido"] or "—",
        "Resultado": "✅" if d["acertou"] else "❌",
    })

st.dataframe(linhas, use_container_width=True, hide_index=True)

st.divider()
st.caption(
    "A verificação de alucinação (factual + LLM-as-a-Judge) está em "
    "src/eval/checar_alucinacao.py. Rode `python -m src.eval.checar_alucinacao` "
    "para a demonstração."
)