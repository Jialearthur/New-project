const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

export function login(username, password) {
  return request("/api/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getMe(token) {
  return request("/api/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function getSettings(token) {
  return request("/api/settings", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updateSettings(token, kbName) {
  return request("/api/settings", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ kbName }),
  });
}

export function listDocuments(token) {
  return request("/api/documents", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function uploadDocument(token, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/api/documents/upload", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
}

export function reindexDocument(token, documentId) {
  return request(`/api/documents/${documentId}/reindex`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function deleteDocument(token, documentId) {
  return request(`/api/documents/${documentId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function askQuestion(token, question) {
  return request("/api/ask", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ question }),
  });
}

export function listLogs(token) {
  return request("/api/logs", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
