const BASE_URL = "/api";

function getToken() {
  return localStorage.getItem("johnbot_token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = "JohnBot couldn't process the request. Please try again.";
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // ignore parse errors, keep default message
    }
    const error = new Error(detail);
    error.status = res.status;
    throw error;
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Auth
  register: (name, email, password) =>
    request("/auth/register", { method: "POST", body: JSON.stringify({ name, email, password }) }),
  login: (email, password) =>
    request("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  me: () => request("/auth/me"),

  // Files
  uploadFiles: (fileList) => {
    const formData = new FormData();
    Array.from(fileList).forEach((f) => formData.append("files", f, f.webkitRelativePath || f.name));
    return request("/upload", { method: "POST", body: formData });
  },
  listFiles: () => request("/files"),
  deleteFile: (id) => request(`/files/${id}`, { method: "DELETE" }),

  // Chat
  sendMessage: (conversationId, message) =>
    request("/chat", { method: "POST", body: JSON.stringify({ conversation_id: conversationId, message }) }),
  listChats: () => request("/chats"),
  getChat: (id) => request(`/chats/${id}`),
  deleteChat: (id) => request(`/chats/${id}`, { method: "DELETE" }),

  // Settings
  getSettings: () => request("/settings"),
  updateSettings: (payload) => request("/settings", { method: "PUT", body: JSON.stringify(payload) }),

  // GitHub
  getGithubConnection: () => request("/github/connection"),
  getGithubConnectUrl: () => request("/github/connect"),
  disconnectGithub: () => request("/github/connection", { method: "DELETE" }),
  listGithubRepos: () => request("/github/repos"),
  ingestGithubRepo: (owner, repo) => request(`/github/repos/${owner}/${repo}/ingest`, { method: "POST" }),
  ingestGithubUrl: (url, conversationId) =>
    request("/github/ingest-url", { method: "POST", body: JSON.stringify({ url, conversation_id: conversationId }) }),
  getGithubJob: (jobId) => request(`/github/jobs/${jobId}`),
};

export function setToken(token) {
  if (token) localStorage.setItem("johnbot_token", token);
  else localStorage.removeItem("johnbot_token");
}

export function hasToken() {
  return Boolean(getToken());
}
