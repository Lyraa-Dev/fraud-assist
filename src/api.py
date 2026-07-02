import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.orchestrator import conversar

app = FastAPI(
    title="fraud-assist API",
    description="Assistente transacional anti-fraude com tool calling e RAG.",
    version="1.0.0",
)

# CORS: permite que um front-end em outro domínio (ex: Vercel) chame a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# armazenamento de sessões em memória: {session_id: historico}
_sessoes: dict[str, list] = {}


# modelos de request/response (validação automática via Pydantic) 
class ChatRequest(BaseModel):
    mensagem: str
    session_id: str | None = None   # se ausente, cria uma nova sessão
    cliente_id: int = 1             # quem está logado (viria da autenticação)


class ChatResponse(BaseModel):
    resposta: str
    session_id: str


# ---- endpoints ----
@app.get("/")
def raiz():
    """Health check simples — útil para saber se a API está no ar."""
    return {"status": "ok", "servico": "fraud-assist API"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    # Processa uma mensagem do usuário e devolve a resposta do bot.

    # recupera ou cria a sessão
    session_id = req.session_id or str(uuid.uuid4())
    historico = _sessoes.get(session_id, [])

    try:
        resposta, historico = conversar(
            req.mensagem, historico, req.cliente_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {e}")

    # guarda o histórico atualizado de volta na sessão
    _sessoes[session_id] = historico
    return ChatResponse(resposta=resposta, session_id=session_id)


@app.delete("/chat/{session_id}")
def encerrar_sessao(session_id: str):
    if session_id in _sessoes:
        del _sessoes[session_id]
        return {"status": "sessão encerrada"}
    raise HTTPException(status_code=404, detail="Sessão não encontrada.")