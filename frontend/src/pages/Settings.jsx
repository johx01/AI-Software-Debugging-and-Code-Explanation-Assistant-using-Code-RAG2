import { useEffect, useState } from "react";
import { useTheme } from "../services/ThemeContext";
import { api } from "../services/api";
import GithubRepoPicker from "../components/GithubRepoPicker";

export default function Settings({ settings, onUpdate }) {
  const { theme, setTheme } = useTheme();
  const [github, setGithub] = useState(null);
  const [githubError, setGithubError] = useState(null);
  const [pickerOpen, setPickerOpen] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("github_error")) setGithubError(params.get("github_error"));
    if (params.get("github") || params.get("github_error")) {
      window.history.replaceState({}, "", window.location.pathname);
    }
    loadGithub();
  }, []);

  function loadGithub() {
    api.getGithubConnection().then(setGithub).catch((err) => setGithubError(err.message));
  }

  async function handleConnect() {
    try {
      const { authorize_url } = await api.getGithubConnectUrl();
      window.location.href = authorize_url;
    } catch (err) {
      setGithubError(err.message);
    }
  }

  async function handleDisconnect() {
    try {
      await api.disconnectGithub();
      setGithub({ connected: false });
    } catch (err) {
      setGithubError(err.message);
    }
  }

  function handleThemeChange(value) {
    setTheme(value);
    onUpdate({ theme: value });
  }

  if (!settings) return null;

  return (
    <div className="page">
      <h2 className="page-title">Settings</h2>

      <section className="settings-section">
        <h3>Appearance</h3>
        <div className="settings-row">
          {["light", "dark", "system"].map((option) => (
            <button
              key={option}
              className={`chip ${theme === option ? "chip-active" : ""}`}
              onClick={() => handleThemeChange(option)}
            >
              {option.charAt(0).toUpperCase() + option.slice(1)}
            </button>
          ))}
        </div>
      </section>

      <section className="settings-section">
        <h3>Chat</h3>
        <label className="settings-toggle">
          <input
            type="checkbox"
            checked={settings.enter_to_send}
            onChange={(e) => onUpdate({ enter_to_send: e.target.checked })}
          />
          Enter to send
        </label>
        <label className="settings-toggle">
          <input
            type="checkbox"
            checked={settings.show_sources}
            onChange={(e) => onUpdate({ show_sources: e.target.checked })}
          />
          Show sources
        </label>
      </section>

      <section className="settings-section">
        <h3>GitHub</h3>
        {githubError && <p className="form-error">{githubError}</p>}
        {github?.connected ? (
          <div className="settings-row">
            <p>
              Connected as <strong>{github.github_login}</strong>
            </p>
            <button className="btn-link" onClick={() => setPickerOpen(true)}>
              Select repository to index
            </button>
            <button className="btn-link btn-danger" onClick={handleDisconnect}>
              Disconnect
            </button>
          </div>
        ) : (
          <button className="btn-link" onClick={handleConnect}>
            Connect GitHub
          </button>
        )}
        {pickerOpen && <GithubRepoPicker onClose={() => setPickerOpen(false)} />}
      </section>

      <section className="settings-section">
        <h3>AI</h3>
        <p>
          Provider: <strong>{settings.provider}</strong>
        </p>
        <p>
          Model: <strong className="mono">{settings.model}</strong>
        </p>
      </section>
    </div>
  );
}
