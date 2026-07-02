from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

MODELO_EMBEDDINGS = "paraphrase-multilingual-MiniLM-L12-v2"

RULES_DIR = "rules"
_INDICE = None


def _carregar_documentos(rules_dir: str = RULES_DIR) -> str:
    # Lê e concatena todos os .md da pasta de regras.
    textos = []
    for caminho in sorted(Path(rules_dir).glob("*.md")):
        textos.append(caminho.read_text(encoding="utf-8"))
    return "\n\n".join(textos)


def _chunk_por_secao(texto: str) -> list[str]:
    # Quebra o texto em chunks usando os cabeçalhos '##' como divisor.

    partes = []
    atual = []
    for linha in texto.splitlines():
        if linha.startswith("## "):
            if atual:
                partes.append("\n".join(atual).strip())
            atual = [linha]
        else:
            atual.append(linha)
    if atual:
        partes.append("\n".join(atual).strip())
    # remove chunks vazios ou muito curtos
    return [p for p in partes if len(p) > 40]


def _construir_indice(rules_dir: str = RULES_DIR):
    # Constrói o modelo, o índice FAISS e a lista de chunks
    global _INDICE
    if _INDICE is not None:
        return _INDICE

    texto = _carregar_documentos(rules_dir)
    chunks = _chunk_por_secao(texto)

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)
    embeddings = modelo.encode(chunks, convert_to_numpy=True,
                               normalize_embeddings=True)

    # IndexFlatIP = produto interno; com vetores normalizados equivale a
    # similaridade do cosseno.
    dim = embeddings.shape[1]
    indice = faiss.IndexFlatIP(dim)
    indice.add(embeddings.astype(np.float32))

    _INDICE = (modelo, indice, chunks)
    return _INDICE


def buscar_regras(pergunta: str, k: int = 2, rules_dir: str = RULES_DIR) -> str:
    # Busca os k chunks mais relevantes para a pergunta e os retorna como texto.
    modelo, indice, chunks = _construir_indice(rules_dir)
    vetor = modelo.encode([pergunta], convert_to_numpy=True,
                          normalize_embeddings=True).astype(np.float32)
    scores, ids = indice.search(vetor, k)

    trechos = []
    for idx in ids[0]:
        if 0 <= idx < len(chunks):
            trechos.append(chunks[idx])
    return "\n\n---\n\n".join(trechos)


if __name__ == "__main__":
    # teste manual: faz uma pergunta e mostra os trechos recuperados
    resultado = buscar_regras("qual o prazo para contestar uma compra?")
    print("TRECHOS RECUPERADOS:\n")
    print(resultado)