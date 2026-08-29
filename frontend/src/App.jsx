import { useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Home from "./pages/Home";
import History from "./pages/History";
import Files from "./pages/Files";
import SettingsPage from "./pages/Settings";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { useAuth } from "./services/AuthContext";
import { api } from "./services/api";
import { useTheme } from "./services/ThemeContext";

const PAGE_TITLES = {
  "/": "Chat",
  "/history": "History",
  "/files": "Files",
  "/settings": "Settings",
};

function PrivateLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [settings, setSettings] = useState(null);
  const location = useLocation();
  const { setTheme } = useTheme();

  useEffect(() => {
    api
      .getSettings()
      .then((s) => {
        setSettings(s);
        setTheme(s.theme);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleUpdateSettings(partial) {
    const updated = await api.updateSettings(partial);
    setSettings(updated);
  }

  const title =
    PAGE_TITLES[location.pathname] || (location.pathname.startsWith("/chat/") ? "Chat" : "JohnBot");

  return (
    <div className="app-layout">
      <Sidebar collapsed={!sidebarOpen} onClose={() => setSidebarOpen(false)} />
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <div className="app-main">
        <Header title={title} onMenuClick={() => setSidebarOpen((v) => !v)} />
        <div className="app-content">
          <Routes>
            <Route path="/" element={<Home settings={settings} />} />
            <Route path="/chat/:chatId" element={<Home settings={settings} />} />
            <Route path="/history" element={<History />} />
            <Route path="/files" element={<Files />} />
            <Route path="/settings" element={<SettingsPage settings={settings} onUpdate={handleUpdateSettings} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <div className="full-page-loading">Loading JohnBot...</div>;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return <PrivateLayout />;
}
