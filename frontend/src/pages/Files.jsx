import { useEffect, useState } from "react";
import FileUpload from "../components/FileUpload";
import { api } from "../services/api";

const STATUS_LABELS = {
  uploading: "Uploading",
  processing: "Processing",
  ready: "Ready",
  error: "Error",
};

export default function Files() {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    load();
  }, []);

  function load() {
    api.listFiles().then(setFiles).catch((err) => setError(err.message));
  }

  async function handleDelete(id) {
    try {
      await api.deleteFile(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="page">
      <h2 className="page-title">Files</h2>
      <FileUpload onUploaded={load} />
      {error && <p className="form-error">{error}</p>}

      {files.length === 0 ? (
        <p className="empty-state">No files uploaded yet.</p>
      ) : (
        <table className="files-table">
          <thead>
            <tr>
              <th>Filename</th>
              <th>Source</th>
              <th>Language</th>
              <th>Status</th>
              <th>Chunks</th>
              <th>Uploaded</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {files.map((f) => (
              <tr key={f.id}>
                <td className="mono">{f.file_name}</td>
                <td>{f.source === "github" ? "GitHub" : "Upload"}</td>
                <td>{f.language || "—"}</td>
                <td>
                  <span className={`status-badge status-${f.status}`}>{STATUS_LABELS[f.status] || f.status}</span>
                </td>
                <td>{f.chunk_count}</td>
                <td>{new Date(f.created_at).toLocaleString()}</td>
                <td>
                  <button className="btn-link btn-danger" onClick={() => handleDelete(f.id)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
