// Base URL de l'API. En dev, le frontend (nginx, :8080) et le backend
// (uvicorn, :8000) tournent sur des ports différents -> appel cross-origin,
// autorisé par CORS_ORIGINS côté backend. À rendre configurable avant une
// vraie mise en production (reverse proxy unique, ou variable injectée au
// build).
const HOTES_LOCAUX = ["localhost", "127.0.0.1"];
const API_BASE = HOTES_LOCAUX.includes(window.location.hostname)
  ? `${window.location.protocol}//${window.location.hostname}:8000`
  : "";

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    const message = (body && body.detail) || "Une erreur est survenue. Veuillez réessayer.";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return body;
}
