export default function SourceList({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="source-list">
      <div className="source-list-label">Sources</div>
      <ul>
        {sources.map((s, i) => (
          <li key={i} className="mono">
            {s.file_name}
            {s.start_line ? ` — lines ${s.start_line}–${s.end_line}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
