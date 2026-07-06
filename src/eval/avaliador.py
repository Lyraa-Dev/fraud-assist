import json
import time

from src.orchestrator import _client, MODELO, SYSTEM_PROMPT
from src.tool_schemas import TOOL_SCHEMAS
from src.eval.casos_teste import CASOS_TESTE


def ferramenta_escolhida(pergunta: str, modelo: str = None) -> str | None:
    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pergunta},
    ]
    resposta = _client.chat.completions.create(
        model=modelo or MODELO,
        messages=mensagens,
        tools=TOOL_SCHEMAS,
        tool_choice="auto",
    )
    tool_calls = resposta.choices[0].message.tool_calls
    if tool_calls:
        return tool_calls[0].function.name  # a primeira ferramenta escolhida
    return None


def avaliar_roteamento(casos=None, modelo: str = None) -> dict:
    casos = casos or CASOS_TESTE
    detalhes = []
    acertos = 0
    avaliados = 0   # conta só os casos que rodaram sem erro de API

    for pergunta, esperado in casos:
        erro_api = False
        try:
            obtido = ferramenta_escolhida(pergunta, modelo=modelo)
        except Exception as e:
            obtido = f"ERRO_API: {e}"
            erro_api = True
        # pausa curta entre chamadas para não estourar o rate limit (429)
        time.sleep(1.0)

        if erro_api:
            # caso não avaliável: não conta como acerto nem como erro de modelo
            detalhes.append({
                "pergunta": pergunta,
                "esperado": esperado,
                "obtido": obtido,
                "acertou": None,   # None = não avaliado
            })
            continue

        acertou = (obtido == esperado)
        avaliados += 1
        if acertou:
            acertos += 1
        detalhes.append({
            "pergunta": pergunta,
            "esperado": esperado,
            "obtido": obtido,
            "acertou": acertou,
        })

    # acurácia separada por ferramenta (só casos avaliados)
    por_ferramenta = {}
    for d in detalhes:
        if d["acertou"] is None:   # pula casos com erro de API
            continue
        chave = d["esperado"] or "nenhuma"
        por_ferramenta.setdefault(chave, {"total": 0, "acertos": 0})
        por_ferramenta[chave]["total"] += 1
        if d["acertou"]:
            por_ferramenta[chave]["acertos"] += 1
    for chave, v in por_ferramenta.items():
        v["acuracia"] = v["acertos"] / v["total"] if v["total"] else 0.0

    n_erros_api = sum(1 for d in detalhes if d["acertou"] is None)
    return {
        # acurácia calculada SÓ sobre os casos efetivamente avaliados
        "acuracia": acertos / avaliados if avaliados else 0.0,
        "total": len(casos),
        "avaliados": avaliados,
        "acertos": acertos,
        "erros_api": n_erros_api,
        "detalhes": detalhes,
        "por_ferramenta": por_ferramenta,
    }


def avaliar_variancia(n_rodadas: int = 5, modelo: str = None) -> dict:
    import statistics

    acuracias = []
    rodadas = []
    for i in range(n_rodadas):
        r = avaliar_roteamento(modelo=modelo)
        acuracias.append(r["acuracia"])
        rodadas.append({"rodada": i + 1, "acuracia": r["acuracia"],
                        "acertos": r["acertos"], "total": r["total"]})

    media = statistics.mean(acuracias)
    desvio = statistics.stdev(acuracias) if len(acuracias) > 1 else 0.0
    return {
        "n_rodadas": n_rodadas,
        "acuracia_media": media,
        "desvio_padrao": desvio,
        "acuracia_min": min(acuracias),
        "acuracia_max": max(acuracias),
        "rodadas": rodadas,
        # guarda a última rodada completa para o detalhamento no dashboard
        "ultima_rodada": avaliar_roteamento(modelo=modelo),
    }


def salvar_avaliacao(caminho: str = "reports/avaliacao.json",
                     n_rodadas: int = 5, modelo: str = None) -> dict:
    import os
    from datetime import datetime

    variancia = avaliar_variancia(n_rodadas=n_rodadas, modelo=modelo)
    ultima = variancia.pop("ultima_rodada")

    resultado = {
        # métricas de variância (o destaque honesto)
        "acuracia_media": variancia["acuracia_media"],
        "desvio_padrao": variancia["desvio_padrao"],
        "acuracia_min": variancia["acuracia_min"],
        "acuracia_max": variancia["acuracia_max"],
        "n_rodadas": variancia["n_rodadas"],
        "rodadas": variancia["rodadas"],
        # detalhamento da última rodada (para inspeção caso a caso)
        "acuracia": ultima["acuracia"],
        "total": ultima["total"],
        "avaliados": ultima.get("avaliados", ultima["total"]),
        "acertos": ultima["acertos"],
        "erros_api": ultima.get("erros_api", 0),
        "detalhes": ultima["detalhes"],
        "por_ferramenta": ultima["por_ferramenta"],
        # metadados
        "modelo": modelo or MODELO,
        "data_avaliacao": datetime.now().isoformat(timespec="seconds"),
    }

    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"Avaliação salva em {caminho}")
    print(f"Acurácia: {resultado['acuracia_media']:.1%} "
          f"± {resultado['desvio_padrao']:.1%} "
          f"({n_rodadas} rodadas)")
    if resultado.get("erros_api"):
        print(f"Atenção: {resultado['erros_api']} caso(s) com erro de API na "
              f"última rodada foram EXCLUÍDOS do cálculo (não contam como erro "
              f"de roteamento).")
    return resultado


if __name__ == "__main__":
    import sys
    if "--salvar" in sys.argv:
        # modelo menor por padrão na avaliação em massa (economia de cota)
        modelo = "llama-3.1-8b-instant"
        if "--modelo" in sys.argv:
            modelo = sys.argv[sys.argv.index("--modelo") + 1]
        n = 5
        if "--rodadas" in sys.argv:
            n = int(sys.argv[sys.argv.index("--rodadas") + 1])
        salvar_avaliacao(n_rodadas=n, modelo=modelo)
        raise SystemExit(0)
    print("Avaliando roteamento (isso faz chamadas ao Groq)...\n")
    resultado = avaliar_roteamento()
    print(f"ACURÁCIA GERAL: {resultado['acuracia']:.0%} "
          f"({resultado['acertos']}/{resultado['total']})\n")
    print("Por ferramenta:")
    for ferr, v in resultado["por_ferramenta"].items():
        print(f"  {ferr:22s} {v['acuracia']:.0%} ({v['acertos']}/{v['total']})")
    print("\nErros:")
    for d in resultado["detalhes"]:
        if not d["acertou"]:
            print(f"  '{d['pergunta']}'")
            print(f"     esperado: {d['esperado']} | obtido: {d['obtido']}")