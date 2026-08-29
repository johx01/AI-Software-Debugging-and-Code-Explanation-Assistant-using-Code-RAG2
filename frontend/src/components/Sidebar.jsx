import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../services/AuthContext";

export default function Sidebar({ collapsed, onClose }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  function handleNewChat() {
    navigate("/");
    onClose?.();
  }

  return (
    <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      <div className="sidebar-brand">JohnBot</div>

      <button className="btn-new-chat" onClick={handleNewChat}>
        + New Chat
      </button>

      <nav className="sidebar-nav">
        <span className="sidebar-section-label">Workspace</span>
        <NavLink to="/" end className="sidebar-link" onClick={onClose}>
          Chat
        </NavLink>
        <NavLink to="/history" className="sidebar-link" onClick={onClose}>
          History
        </NavLink>
        <NavLink to="/files" className="sidebar-link" onClick={onClose}>
          Files
        </NavLink>

        <span className="sidebar-section-label">Account</span>
        <NavLink to="/settings" className="sidebar-link" onClick={onClose}>
          Settings
        </NavLink>
      </nav>

      {user && (
        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-user-name">{user.name}</div>
            <div className="sidebar-user-email">{user.email}</div>
          </div>
          <button className="btn-link" onClick={logout}>
            Log out
          </button>
        </div>
      )}
    </aside>
  );
}
