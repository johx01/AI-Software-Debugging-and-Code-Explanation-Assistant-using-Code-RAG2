import { useTheme } from "../services/ThemeContext";

export default function Settings({ settings, onUpdate }) {
  const { theme, setTheme } = useTheme();

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
