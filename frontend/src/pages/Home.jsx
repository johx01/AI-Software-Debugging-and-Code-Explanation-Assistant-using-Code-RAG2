import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ChatWindow from "../components/ChatWindow";
import { api } from "../services/api";

export default function Home({ settings }) {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [conversationId, setConversationId] = useState(chatId ? Number(chatId) : null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (chatId) {
      setConversationId(Number(chatId));
      loadConversation(Number(chatId));
    } else {
      setConversationId(null);
      setMessages([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId]);

  async function loadConversation(id) {
    try {
      const data = await api.getChat(id);
      setMessages(
        data.messages.map((m) => ({
          role: m.role,
          content: m.content,
          sources: m.sources ? JSON.parse(m.sources) : [],
        }))
      );
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSend(text) {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text, sources: [] }]);
    setLoading(true);
    try {
      const res = await api.sendMessage(conversationId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, sources: res.sources }]);
      if (!conversationId) {
        setConversationId(res.conversation_id);
        navigate(`/chat/${res.conversation_id}`, { replace: true });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `JohnBot couldn't process that: ${err.message}`, sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page-chat">
      {error && <p className="form-error">{error}</p>}
      <ChatWindow
        messages={messages}
        onSend={handleSend}
        loading={loading}
        showSources={settings?.show_sources ?? true}
        enterToSend={settings?.enter_to_send ?? true}
      />
    </div>
  );
}
