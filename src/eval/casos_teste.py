CASOS_TESTE = [
    # --- consultar_transacoes ---
    ("Quais foram minhas últimas transações?", "consultar_transacoes"),
    ("Me mostra meu extrato", "consultar_transacoes"),
    ("Quanto eu gastei recentemente?", "consultar_transacoes"),
    ("Quero ver minhas compras", "consultar_transacoes"),
    ("Lista as transações da minha conta", "consultar_transacoes"),

    # --- score_fraude ---
    ("A transação 2916 é suspeita?", "score_fraude"),
    ("Qual o risco de fraude da compra 2190?", "score_fraude"),
    ("A transação de ID 3683 é arriscada?", "score_fraude"),

    # --- explicar_transacao ---
    ("Por que a transação 2916 foi bloqueada?", "explicar_transacao"),
    ("Me explica por que a compra 2190 parece estranha", "explicar_transacao"),
    ("O que houve com a transação 2916?", "explicar_transacao"),

    # --- abrir_contestacao ---
    ("Quero contestar a transação 2190, não reconheço essa compra",
     "abrir_contestacao"),
    ("Não fiz a compra 2916, quero abrir uma reclamação",
     "abrir_contestacao"),
    ("Contestar a cobrança indevida da transação 2401", "abrir_contestacao"),

    # --- consultar_regras ---
    ("Qual o prazo para contestar uma compra?", "consultar_regras"),
    ("Como funciona o bloqueio de transações?", "consultar_regras"),
    ("Por que uma compra é considerada fraude?", "consultar_regras"),
    ("Qual o limite para compras internacionais?", "consultar_regras"),

    # --- sem ferramenta (saudações / conversa) ---
    ("Olá, tudo bem?", None),
    ("Obrigado pela ajuda!", None),
]