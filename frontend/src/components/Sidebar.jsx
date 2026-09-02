import { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../services/AuthContext";
import { api } from "../services/api";

export default function Sidebar({ collapsed, onClose, onOpenSettings }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const location = useLocation();
  const chatMatch = location.pathname.match(/^\/chat\/(.+)$/);
  const chatId = chatMatch ? chatMatch[1] : null;
  const [query, setQuery] = useState("");
  const [chats, setChats] = useState([]);
  const [error, setError] = useState(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileRef = useRef(null);

  useEffect(() => {
    loadChats();
  }, [location.pathname]);

  useEffect(() => {
    function handleClickOutside(e) {
      if (profileRef.current && !profileRef.current.contains(e.target)) {
        setProfileMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function loadChats() {
    api.listChats().then(setChats).catch((err) => setError(err.message));
  }

  function handleNewChat() {
    navigate("/");
    onClose?.();
  }

  function handleSelectChat(id) {
    navigate(`/chat/${id}`);
    onClose?.();
  }

  function handleOpenSettings() {
    setProfileMenuOpen(false);
    onOpenSettings?.();
    onClose?.();
  }

  function handleLogout() {
    setProfileMenuOpen(false);
    logout();
  }

  async function handleDelete(id, e) {
    e.stopPropagation();
    try {
      await api.deleteChat(id);
      setChats((prev) => prev.filter((c) => c.id !== id));
      if (String(chatId) === String(id)) navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  const filteredChats = query
    ? chats.filter((c) => c.title?.toLowerCase().includes(query.toLowerCase()))
    : chats;

  return (
    <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      <div className="sidebar-brand">JohnBot</div>

      <button className="btn-new-chat" onClick={handleNewChat}>
        + New Chat
      </button>

      <div className="sidebar-search">
        <input
          type="text"
          className="sidebar-search-input"
          placeholder="Search chats..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <nav className="sidebar-nav">
        <span className="sidebar-section-label">Workspace</span>
        <NavLink to="/" end className="sidebar-link" onClick={onClose}>
          Chat
        </NavLink>
        <NavLink to="/files" className="sidebar-link" onClick={onClose}>
          Files
        </NavLink>

        <span className="sidebar-section-label">Recents</span>
        <div className="sidebar-history">
          {error && <p className="form-error">{error}</p>}
          {filteredChats.length === 0 ? (
            <p className="sidebar-history-empty">
              {query ? `No chats match "${query}".` : "No conversations yet."}
            </p>
          ) : (
            filteredChats.map((c) => (
              <div
                key={c.id}
                className={`sidebar-history-item ${String(chatId) === String(c.id) ? "active" : ""}`}
                onClick={() => handleSelectChat(c.id)}
              >
                <span className="sidebar-history-title">{c.title}</span>
                <button
                  className="sidebar-history-delete"
                  onClick={(e) => handleDelete(c.id, e)}
                  aria-label="Delete chat"
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
      </nav>

      {user && (
        <div className="sidebar-footer" ref={profileRef}>
          {profileMenuOpen && (
            <div className="sidebar-profile-menu">
              <button className="sidebar-profile-menu-item" onClick={handleOpenSettings}>
                Settings
              </button>
              <button className="sidebar-profile-menu-item" onClick={handleLogout}>
                Log out
              </button>
            </div>
          )}
          <button
            type="button"
            className="sidebar-user"
            onClick={() => setProfileMenuOpen((v) => !v)}
          >
            <div className="sidebar-user-avatar">{user.name?.[0]?.toUpperCase() || "?"}</div>
            <div className="sidebar-user-info">
              <div className="sidebar-user-name">{user.name}</div>
              <div className="sidebar-user-email">{user.email}</div>
            </div>
          </button>
        </div>
      )}
    </aside>
  );
}
