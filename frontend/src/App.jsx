import { useState, useRef, useEffect } from "react";
import { enviarMensagem } from "./api";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function App() {
  // ESTADO do componente (useState): quando muda, a tela re-renderiza.
  const [mensagens, setMensagens] = useState([]);   // lista de {autor, texto}
  const [entrada, setEntrada] = useState("");        // o que o usuário digita
  const [sessionId, setSessionId] = useState(null);  // mantém o contexto
  const [carregando, setCarregando] = useState(false);

  const fimDasMensagens = useRef(null);

  // rola para a última mensagem sempre que a lista muda
  useEffect(() => {
    fimDasMensagens.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens]);

  async function handleEnviar() {
    const texto = entrada.trim();
    if (!texto || carregando) return;

    // adiciona a mensagem do usuário à tela imediatamente
    setMensagens((prev) => [...prev, { autor: "user", texto }]);
    setEntrada("");
    setCarregando(true);

    try {
      const data = await enviarMensagem(texto, sessionId);
      setSessionId(data.session_id); // guarda o id para manter o contexto
      setMensagens((prev) => [...prev, { autor: "bot", texto: data.resposta }]);
    } catch (erro) {
      setMensagens((prev) => [
        ...prev,
        { autor: "bot", texto: "Desculpe, houve um erro ao processar. Verifique se a API está rodando." },
      ]);
    } finally {
      setCarregando(false);
    }
  }

  // envia com Enter (Shift+Enter quebra linha)
  function handleTecla(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleEnviar();
    }
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>🛡️ fraud-assist</h1>
        <p>Assistente transacional anti-fraude</p>
      </header>

      <div className="chat-mensagens">
        {mensagens.length === 0 && (
          <div className="chat-vazio">
            Olá! Pergunte sobre suas transações, contestações ou regras.
          </div>
        )}
        {mensagens.map((m, i) => (
          <div key={i} className={`bolha bolha-${m.autor}`}>
            {m.autor === "bot" ? (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="tabela-wrapper">
                      <table {...props} />
                    </div>
                  ),
                }}
              >
                {m.texto}
              </ReactMarkdown>
            ) : (
              m.texto
            )}
          </div>
        ))}
        {carregando && <div className="bolha bolha-bot">Digitando…</div>}
        <div ref={fimDasMensagens} />
      </div>

      <div className="chat-entrada">
        <textarea
          value={entrada}
          onChange={(e) => setEntrada(e.target.value)}
          onKeyDown={handleTecla}
          placeholder="Digite sua mensagem…"
          rows={1}
        />
        <button onClick={handleEnviar} disabled={carregando}>
          Enviar
        </button>
      </div>
    </div>
  );
}

export default App;