import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function GithubRepoPicker({ onClose }) {
  const [repos, setRepos] = useState([]);
  const [search, setSearch] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [job, setJob] = useState(null);

  useEffect(() => {
    api
      .listGithubRepos()
      .then(setRepos)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!job || job.status === "ready" || job.status === "error") return;
    const timer = setInterval(() => {
      api
        .getGithubJob(job.id)
        .then(setJob)
        .catch((err) => setError(err.message));
    }, 2000);
    return () => clearInterval(timer);
  }, [job]);

  async function handleIngest(repo) {
    setError(null);
    try {
      const createdJob = await api.ingestGithubRepo(repo.owner, repo.name);
      setJob(createdJob);
    } catch (err) {
      setError(err.message);
    }
  }

  const filtered = repos.filter((r) => r.full_name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Select a repository to index</h3>
        <input
          className="text-input"
          placeholder="Search repositories..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {error && <p className="form-error">{error}</p>}

        {job && (
          <div className="settings-row">
            <p>
              Indexing <strong className="mono">{job.repo_full_name}</strong>:{" "}
              {job.status === "ready" ? (
                "Done"
              ) : job.status === "error" ? (
                `Error — ${job.error_message || "unknown error"}`
              ) : (
                `${job.processed_files}/${job.total_files || "?"} files (${job.status})`
              )}
            </p>
          </div>
        )}

        {loading ? (
          <p>Loading repositories...</p>
        ) : (
          <ul className="repo-list">
            {filtered.map((repo) => (
              <li key={repo.full_name} className="repo-list-item">
                <span className="mono">{repo.full_name}</span>
                <span className={`status-badge ${repo.private ? "status-error" : "status-ready"}`}>
                  {repo.private ? "Private" : "Public"}
                </span>
                <button className="btn-link" onClick={() => handleIngest(repo)} disabled={Boolean(job) && job.status !== "ready" && job.status !== "error"}>
                  Ingest
                </button>
              </li>
            ))}
            {filtered.length === 0 && <li className="empty-state">No repositories found.</li>}
          </ul>
        )}

        <button className="btn-link" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
}
