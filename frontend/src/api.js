const API_URL = "http://127.0.0.1:8000";

// Envia uma mensagem ao bot e devolve { resposta, session_id }.
// O session_id mantém o contexto da conversa entre mensagens.
export async function enviarMensagem(mensagem, sessionId, clienteId = 1) {
  const resposta = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mensagem: mensagem,
      session_id: sessionId,   // null na primeira mensagem; a API cria um novo
      cliente_id: clienteId,
    }),
  });

  if (!resposta.ok) {
    throw new Error(`Erro na API: ${resposta.status}`);
  }

  return await resposta.json(); // { resposta: "...", session_id: "..." }
}