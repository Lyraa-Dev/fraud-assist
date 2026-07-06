import re

# 1. Detecção de prompt injection

PADROES_INJECTION = [
    r"ignore?\s+(as\s+|suas\s+|todas\s+as\s+)?(instru[çc][õo]es|regras|prompts?)",
    r"esque[çc]a\s+(as\s+|suas\s+|tudo)",
    r"voc[êe]\s+agora\s+[ée]",
    r"aja\s+como",
    r"finja\s+(que\s+)?(ser|voc[êe])",
    r"sem\s+(restri[çc][õo]es|filtros?|limites?)",
    r"modo\s+(desenvolvedor|developer|admin|debug)",
    r"system\s+prompt",
    r"cliente\s*[_\s]?id\s*[:=]?\s*\d+",
    r"cliente\s+(de\s+)?(id\s+)?\d+",
    r"(dados|transa[çc][õo]es|compras|extrato|informa[çc][õo]es|gastos)\s+"
    r"d[oe]\s+(outro\s+cliente|cliente\s+\d+|cliente\s+de\s+id)",
    r"d[oe]\s+cliente\s+(de\s+)?(id\s+)?\d+",
    r"revele?\s+(suas\s+)?(instru[çc][õo]es|prompt)",
]

_regex_injection = [re.compile(p, re.IGNORECASE) for p in PADROES_INJECTION]


def detectar_injection(mensagem: str) -> dict:
    """Verifica se a mensagem tem sinais de prompt injection.

    Returns:
        dict com 'suspeita' (bool) e 'padrao' (o padrão que casou, se houver).
    """
    for regex in _regex_injection:
        if regex.search(mensagem):
            return {"suspeita": True, "padrao": regex.pattern}
    return {"suspeita": False, "padrao": None}

# 2. Validação de entrada

TAMANHO_MAXIMO = 2000   # caracteres — evita mensagens absurdas


def validar_entrada(mensagem: str) -> dict:
    if mensagem is None or not mensagem.strip():
        return {"valida": False, "motivo": "Mensagem vazia."}
    if len(mensagem) > TAMANHO_MAXIMO:
        return {"valida": False,
                "motivo": f"Mensagem muito longa (máx. {TAMANHO_MAXIMO})."}
    return {"valida": True, "motivo": None}

# 3. Confirmação de ações que modificam estado

ACOES_QUE_MODIFICAM = {"abrir_contestacao"}


def exige_confirmacao(nome_ferramenta: str) -> bool:
    """Diz se uma ferramenta modifica estado e precisa de confirmação."""
    return nome_ferramenta in ACOES_QUE_MODIFICAM

def checar_mensagem(mensagem: str) -> dict:
    v = validar_entrada(mensagem)
    if not v["valida"]:
        return {"ok": False, "motivo": v["motivo"]}

    inj = detectar_injection(mensagem)
    if inj["suspeita"]:
        return {"ok": False,
                "motivo": "Sua mensagem parece conter uma instrução não "
                          "permitida. Por segurança, não posso processá-la. "
                          "Reformule sua dúvida sobre transações ou regras."}

    return {"ok": True, "motivo": None}