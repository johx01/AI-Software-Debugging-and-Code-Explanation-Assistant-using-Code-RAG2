import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";

export default function History() {
  const [chats, setChats] = useState([]);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    load();
  }, []);

  function load() {
    api.listChats().then(setChats).catch((err) => setError(err.message));
  }

  async function handleDelete(id, e) {
    e.stopPropagation();
    try {
      await api.deleteChat(id);
      setChats((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2 className="page-title">History</h2>
      {error && <p className="form-error">{error}</p>}
      {chats.length === 0 ? (
        <p className="empty-state">No conversations yet. Start a new chat to see it here.</p>
      ) : (
        <ul className="history-list">
          {chats.map((c) => (
            <li key={c.id} className="history-item" onClick={() => navigate(`/chat/${c.id}`)}>
              <div>
                <div className="history-item-title">{c.title}</div>
                <div className="history-item-date">{new Date(c.updated_at).toLocaleString()}</div>
              </div>
              <button className="btn-link btn-danger" onClick={(e) => handleDelete(c.id, e)}>
                Delete
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
