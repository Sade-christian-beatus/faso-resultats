// The API is always reached on the page's own origin (/api/...): nginx forwards it to
// the backend, in development (docker-compose.yml, http://localhost:8080) as in
// production (deploy/nginx). This also makes the site work from a phone on the same
// Wi-Fi in development, and keeps CORS out of the way.
const API_BASE = "";

const MESSAGE_TROP_DE_REQUETES =
  "Beaucoup de consultations en ce moment : patientez une minute, puis réessayez.";

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  if (!response.ok) {
    // Rate limit reached (proclamation day): the visitor only has to wait, say so.
    const message =
      response.status === 429
        ? MESSAGE_TROP_DE_REQUETES
        : (body && body.detail) || "Une erreur est survenue. Veuillez réessayer.";
    const erreur = new Error(typeof message === "string" ? message : JSON.stringify(message));
    erreur.status = response.status;
    throw erreur;
  }
  return body;
}
