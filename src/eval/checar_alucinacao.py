import re
import json
from src.orchestrator import _client, MODELO


# ---------------------------------------------------------------------------
# Abordagem 1 — verificação factual (determinística)
# ---------------------------------------------------------------------------
def _extrair_ids(texto: str) -> set[int]:
    """Extrai IDs de transação mencionados no texto.

    Procura padrões como 'ID 2916', 'transação 2916', 'compra 2916'.
    """
    padrao = re.compile(r"(?:id|transa[çc][ãa]o|compra)\s*[:#]?\s*(\d{3,})",
                        re.IGNORECASE)
    return {int(m) for m in padrao.findall(texto)}


def _extrair_valores(texto: str) -> set[float]:
    """Extrai valores monetários do texto (formato R$ 1.234,56)."""
    padrao = re.compile(r"R\$\s*([\d.]+,\d{2})")
    valores = set()
    for bruto in padrao.findall(texto):
        # normaliza '5.641,24' -> 5641.24
        limpo = bruto.replace(".", "").replace(",", ".")
        try:
            valores.add(round(float(limpo), 2))
        except ValueError:
            pass
    return valores


def verificar_factual(resposta: str, dados_reais: list[dict]) -> dict:
    """Confere se os IDs e valores citados na resposta existem nos dados reais.

    Args:
        resposta: o texto gerado pelo bot
        dados_reais: a lista de transações que a ferramenta retornou

    Returns:
        dict com ids/valores inventados (não presentes nos dados) e um
        booleano 'tem_alucinacao'.
    """
    ids_reais = {d["id"] for d in dados_reais}
    valores_reais = {round(float(d["valor"]), 2) for d in dados_reais}

    ids_citados = _extrair_ids(resposta)
    valores_citados = _extrair_valores(resposta)

    ids_inventados = ids_citados - ids_reais
    valores_inventados = valores_citados - valores_reais

    return {
        "ids_inventados": sorted(ids_inventados),
        "valores_inventados": sorted(valores_inventados),
        "tem_alucinacao": bool(ids_inventados or valores_inventados),
    }


# ---------------------------------------------------------------------------
# Abordagem 2 — LLM-as-a-Judge
# ---------------------------------------------------------------------------
JUIZ_PROMPT = (
    "Você é um avaliador rigoroso de fidelidade factual. Receberá os DADOS "
    "REAIS (JSON) e uma RESPOSTA gerada por um assistente. Sua tarefa é "
    "decidir se a resposta é FIEL aos dados, sem inventar ou distorcer "
    "informação (valores, datas, status, estabelecimentos). "
    "Responda APENAS com um JSON no formato: "
    '{"fiel": true/false, "nota": 0-10, "justificativa": "..."}. '
    "Nota 10 = perfeitamente fiel; 0 = totalmente inventada. Não escreva "
    "nada além do JSON."
)


def juiz_llm(resposta: str, dados_reais: list[dict],
             modelo_juiz: str = "llama-3.1-8b-instant") -> dict:
    """Usa um LLM como juiz para avaliar a fidelidade da resposta.

    Usa por padrão um modelo menor (8b) como juiz — mais barato em cota e
    suficiente para julgar fidelidade. É a técnica de 'LLM-as-a-Judge'.
    """
    conteudo = (
        f"DADOS REAIS:\n{json.dumps(dados_reais, ensure_ascii=False)}\n\n"
        f"RESPOSTA DO ASSISTENTE:\n{resposta}"
    )
    try:
        r = _client.chat.completions.create(
            model=modelo_juiz,
            messages=[
                {"role": "system", "content": JUIZ_PROMPT},
                {"role": "user", "content": conteudo},
            ],
            temperature=0,  # juiz deve ser determinístico
        )
        texto = r.choices[0].message.content.strip()
        # remove cercas de código se o modelo as incluir
        texto = re.sub(r"^```(?:json)?|```$", "", texto).strip()
        return json.loads(texto)
    except json.JSONDecodeError:
        return {"fiel": None, "nota": None,
                "justificativa": "juiz não retornou JSON válido"}
    except Exception as e:
        return {"fiel": None, "nota": None, "justificativa": f"erro: {e}"}


if __name__ == "__main__":
    # demonstração das duas abordagens com um exemplo controlado
    dados = [
        {"id": 2069, "valor": 276.32, "status": "aprovada"},
        {"id": 2916, "valor": 5641.24, "status": "bloqueada"},
    ]
    # resposta correta
    boa = "Sua transação ID 2069 de R$ 276,32 foi aprovada."
    # resposta com alucinação (ID e valor que não existem)
    ruim = "Sua transação ID 9999 de R$ 8.000,00 foi aprovada."

    print("=== Verificação factual ===")
    print("Resposta boa: ", verificar_factual(boa, dados))
    print("Resposta ruim:", verificar_factual(ruim, dados))

    print("\n=== LLM-as-a-Judge (faz 1 chamada ao Groq) ===")
    print("Resposta boa: ", juiz_llm(boa, dados))
    print("Resposta ruim:", juiz_llm(ruim, dados))