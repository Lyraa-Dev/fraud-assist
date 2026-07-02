TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_transacoes",
            "description": (
                "Retorna o histórico de transações (extrato) do cliente. "
                "Use quando o usuário quer VER suas compras, gastos, "
                "transações recentes ou o extrato."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {
                        "type": "integer",
                        "description": "Quantas transações retornar (padrão 10).",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_fraude",
            "description": (
                "Calcula o risco de fraude de uma transação específica, "
                "retornando um score de 0 a 1 e os sinais de risco. Use "
                "quando o usuário pergunta se uma transação é suspeita ou "
                "arriscada."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transacao_id": {
                        "type": "integer",
                        "description": "ID da transação a avaliar.",
                    }
                },
                "required": ["transacao_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explicar_transacao",
            "description": (
                "Explica em detalhes por que uma transação é ou não "
                "considerada suspeita. Use quando o usuário pergunta 'por "
                "que' uma transação foi marcada, bloqueada ou parece estranha."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transacao_id": {
                        "type": "integer",
                        "description": "ID da transação a explicar.",
                    }
                },
                "required": ["transacao_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_contestacao",
            "description": (
                "Abre um pedido de contestação para uma transação que o "
                "cliente não reconhece. Use quando o usuário quer contestar, "
                "reclamar de uma cobrança indevida ou dizer que não fez uma "
                "compra."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transacao_id": {
                        "type": "integer",
                        "description": "ID da transação a contestar.",
                    },
                    "motivo": {
                        "type": "string",
                        "description": "Motivo informado pelo cliente.",
                    },
                },
                "required": ["transacao_id", "motivo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_regras",
            "description": (
                "Consulta as regras e políticas do banco sobre prevenção a "
                "fraudes, bloqueios, contestações, prazos, limites e compras "
                "internacionais. Use quando o usuário pergunta COMO algo "
                "funciona, POR QUE existe uma regra, QUAL o prazo/limite, ou "
                "qualquer dúvida sobre política — e não sobre uma transação "
                "específica dele."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {
                        "type": "string",
                        "description": "A dúvida do cliente sobre regras ou políticas.",
                    }
                },
                "required": ["pergunta"],
            },
        },
    },
]