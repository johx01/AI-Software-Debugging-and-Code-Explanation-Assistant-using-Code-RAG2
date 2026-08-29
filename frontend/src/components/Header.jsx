export default function Header({ title, onMenuClick }) {
  return (
    <header className="app-header">
      <button className="menu-toggle" onClick={onMenuClick} aria-label="Toggle menu">
        ☰
      </button>
      <h1 className="header-title">{title}</h1>
    </header>
  );
}
