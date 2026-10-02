// How a decision reads to the candidate, shared by the public page and the candidate
// space. Same rules as the backend (app/services/phases.py, decision_negative) and the
// mobile app (Resultat.tonalite): decisions are free text from official files, so
// negative forms are tested first ("NON ADMIS" contains "ADMIS", "INAPTE" contains
// "APTE"), and a decision matching no rule is neutral, never shown as a success.
const PREFIXES_NEGATIFS = ["NON ", "NON-"];
const MARQUEURS_NEGATIFS = ["AJOURN", "INAPTE", "ELIMIN", "ÉLIMIN", "ABSENT", "REFUS"];
const MARQUEURS_POSITIFS = ["ADMIS", "APTE", "REÇU", "RECU"];

function tonaliteDecision(decision) {
  const valeur = String(decision ?? "").trim().toUpperCase();
  if (
    PREFIXES_NEGATIFS.some((prefixe) => valeur.startsWith(prefixe)) ||
    MARQUEURS_NEGATIFS.some((marqueur) => valeur.includes(marqueur))
  ) {
    return "negative";
  }
  if (MARQUEURS_POSITIFS.some((marqueur) => valeur.includes(marqueur))) return "positive";
  return "neutre";
}

// Status colours (docs/CHARTE_GRAPHIQUE.md § Couleurs d'état): never the decorative
// brand red for a failed candidate.
const STYLE_TONALITE = {
  positive: { badge: "bg-faso-700 text-white", bordure: "border-faso-500", texte: "text-faso-800" },
  negative: { badge: "bg-red-700 text-white", bordure: "border-red-400", texte: "text-red-800" },
  neutre: { badge: "bg-amber-500 text-white", bordure: "border-amber-400", texte: "text-slate-900" },
};

function styleDecision(decision) {
  return STYLE_TONALITE[tonaliteDecision(decision)];
}
