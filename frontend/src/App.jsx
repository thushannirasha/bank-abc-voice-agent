import { useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const DEFAULT_MESSAGE = "Hi, my card was declined at the store.";

function App() {
  const [message, setMessage] = useState("");
  const [customerId, setCustomerId] = useState("cust_1001");
  const [pin, setPin] = useState("1234");
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState([]);
  const [route, setRoute] = useState("-");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);

  const canSend = useMemo(() => message.trim().length > 0 && !loading, [message, loading]);

  const sendMessage = async () => {
    if (!canSend) return;
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          session_id: sessionId || null,
          customer_id: customerId || null,
          pin: pin || null,
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(data.messages || []);
      setRoute(data.route || "-");
      setMessage("");

      if (speechEnabled && data?.messages?.length) {
        const last = data.messages[data.messages.length - 1];
        if (last?.role === "assistant" && "speechSynthesis" in window) {
          const utterance = new SpeechSynthesisUtterance(last.content);
          utterance.rate = 1;
          utterance.pitch = 1;
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utterance);
        }
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Speech recognition is not supported in this browser. Try Chrome.",
        },
      ]);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      setMessage(transcript);
    };

    recognition.start();
  };

  return (
    <div className="page">
      <header className="hero">
        <div>
          <h1>Bank ABC Voice Agent</h1>
          <p>
            LangGraph-based routing with identity verification guardrails and LangSmith tracing.
          </p>
        </div>
        <button className="ghost" onClick={() => setMessage(DEFAULT_MESSAGE)}>
          Load sample
        </button>
      </header>

      <section className="panel">
        <div className="fields">
          <label>
            Customer ID
            <input
              value={customerId}
              onChange={(event) => setCustomerId(event.target.value)}
              placeholder="cust_1001"
            />
          </label>
          <label>
            PIN
            <input
              value={pin}
              onChange={(event) => setPin(event.target.value)}
              placeholder="1234"
              type="password"
            />
          </label>
          <label>
            Session ID
            <input
              value={sessionId}
              onChange={(event) => setSessionId(event.target.value)}
              placeholder="Auto-generated"
            />
          </label>
          <label className="toggle">
            <span>Speech reply</span>
            <input
              type="checkbox"
              checked={speechEnabled}
              onChange={(event) => setSpeechEnabled(event.target.checked)}
            />
          </label>
        </div>

        <div className="chat">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="empty">Start a conversation to see the transcript.</div>
            ) : (
              messages.map((item, index) => (
                <div key={`${item.role}-${index}`} className={`message ${item.role}`}>
                  <span className="role">{item.role}</span>
                  <span>{item.content}</span>
                </div>
              ))
            )}
          </div>
          <div className="composer">
            <input
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Describe your issue..."
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  sendMessage();
                }
              }}
            />
            <button className="ghost" onClick={startListening} disabled={listening}>
              {listening ? "Listening..." : "Speak"}
            </button>
            <button onClick={sendMessage} disabled={!canSend}>
              {loading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </section>

      <section className="footer">
        <div>Last route: {route}</div>
      </section>
    </div>
  );
}

export default App;
