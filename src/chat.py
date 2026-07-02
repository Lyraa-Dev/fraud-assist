import sys
from src.orchestrator import conversar


def _parse_cliente_id(argv) -> int:
    """Lê --cliente N dos argumentos (padrão: cliente 1)."""
    if "--cliente" in argv:
        i = argv.index("--cliente")
        try:
            return int(argv[i + 1])
        except (IndexError, ValueError):
            print("Aviso: --cliente inválido, usando cliente 1.")
    return 1


def main():
    cliente_id = _parse_cliente_id(sys.argv)
    historico = []  # a "memória" da sessão vive aqui, fora do loop

    print("=" * 60)
    print(f"  fraud-assist — assistente anti-fraude")
    print(f"  Cliente logado: #{cliente_id}")
    print("  Digite sua mensagem (ou 'sair' para encerrar).")
    print("=" * 60)

    while True:
        try:
            mensagem = input("\nVocê: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAté logo!")
            break

        if not mensagem:
            continue
        if mensagem.lower() in ("sair", "exit", "quit"):
            print("Até logo!")
            break

        print("\n(processando...)")
        try:
            resposta, historico = conversar(mensagem, historico, cliente_id)
        except Exception as e:
            print(f"[erro ao processar: {e}]")
            continue

        print(f"\nBOT: {resposta}")


if __name__ == "__main__":
    main()