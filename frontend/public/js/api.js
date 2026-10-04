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
    // The API's own French message when there is one (e.g. "account locked" on admin
    // login). The rate limiter answers 429 without one: then the visitor only has to
    // wait (proclamation day), say so.
    const message =
      (body && body.detail) ||
      (response.status === 429 ? MESSAGE_TROP_DE_REQUETES : "Une erreur est survenue. Veuillez réessayer.");
    // A list means a field validation error (422): never show raw JSON to a person.
    const erreur = new Error(
      typeof message === "string" ? message : "Certaines informations saisies ne sont pas valides. Vérifiez-les."
    );
    erreur.status = response.status;
    throw erreur;
  }
  return body;
}
