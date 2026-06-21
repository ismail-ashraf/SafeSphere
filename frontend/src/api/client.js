const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof payload === "string" ? payload : payload.detail || payload.message || "Request failed";
    throw new Error(message);
  }

  return payload;
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseResponse(response);
}

export async function analyzeText(text) {
  const response = await fetch(`${API_BASE_URL}/predict/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  return parseResponse(response);
}

export async function analyzeImage(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict/image`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export async function analyzeCombined({ text, file }) {
  const formData = new FormData();
  if (text) formData.append("text", text);
  if (file) formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict/combined`, {
    method: "POST",
    body: formData,
  });
  return parseResponse(response);
}

export { API_BASE_URL };
