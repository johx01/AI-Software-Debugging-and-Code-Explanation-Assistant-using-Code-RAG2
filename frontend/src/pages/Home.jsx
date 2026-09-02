import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import ChatWindow from "../components/ChatWindow";
import { api } from "../services/api";
import { useAuth } from "../services/AuthContext";

export default function Home({ settings }) {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
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

  const GITHUB_URL_RE = /github\.com\/[\w.-]+\/[\w.-]+/i;

  function updateStatusMessage(statusId, content) {
    setMessages((prev) => prev.map((m) => (m.id === statusId ? { ...m, content } : m)));
  }

  function pollGithubJob(job, statusId) {
    return new Promise((resolve, reject) => {
      const check = async () => {
        try {
          const updated = await api.getGithubJob(job.id);
          if (updated.status === "ready") {
            updateStatusMessage(
              statusId,
              `Imported **${updated.repo_full_name}** — ${updated.processed_files} file(s) indexed.`
            );
            resolve(updated);
          } else if (updated.status === "error") {
            reject(new Error(updated.error_message || "Repo import failed"));
          } else {
            updateStatusMessage(
              statusId,
              `Importing **${updated.repo_full_name}**… ${updated.processed_files}/${updated.total_files || "?"} files (${updated.status})`
            );
            setTimeout(check, 2000);
          }
        } catch (err) {
          reject(err);
        }
      };
      check();
    });
  }

  async function importRepoFromMessage(text) {
    const match = text.match(GITHUB_URL_RE);
    if (!match) return;

    const statusId = `status-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: `Importing **${match[0]}**…`, sources: [], id: statusId },
    ]);

    const job = await api.ingestGithubUrl(match[0], conversationId);
    await pollGithubJob(job, statusId);
  }

  async function handleSend(text) {
    setError(null);
    setMessages((prev) => [...prev, { role: "user", content: text, sources: [] }]);
    setLoading(true);
    try {
      await importRepoFromMessage(text);
      const res = await api.sendMessage(conversationId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply, sources: res.sources }]);
      if (!conversationId) {
        setConversationId(res.conversation_id);
        navigate(`/chat/${res.conversation_id}`, { replace: true });
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Couldn't process that: ${err.message}`, sources: [] },
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
        userName={user?.name}
      />
    </div>
  );
}
