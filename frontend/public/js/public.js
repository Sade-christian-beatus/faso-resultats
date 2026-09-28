const selectExamen = document.getElementById("select-examen");
const form = document.getElementById("form-recherche");
const zoneMessage = document.getElementById("zone-message");
const zoneResultats = document.getElementById("zone-resultats");
const zoneExamensDisponibles = document.getElementById("zone-examens-disponibles");

const LIBELLES_EXAMEN = {
  CEP: "CEP",
  BEPC: "BEPC",
  BAC: "BAC",
  CONCOURS_DIRECT: "Concours direct",
};

const CARACTERES_HTML = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

// Les données affichées ici (nom, établissement, décision...) viennent de fichiers
// importés par un admin (Excel/PDF/OCR), pas d'un formulaire validé — un caractère
// HTML dans une ligne source ne doit jamais s'exécuter chez un visiteur public non
// authentifié.
function escapeHtml(valeur) {
  return String(valeur ?? "").replace(/[&<>"']/g, (caractere) => CARACTERES_HTML[caractere]);
}

const ICONE_ERREUR = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" /></svg>`;
const ICONE_CHARGEMENT = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" class="w-4 h-4 shrink-0 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-9-9" /></svg>`;

function afficherMessage(texte, type = "erreur") {
  const styles =
    type === "erreur"
      ? { fond: "bg-red-50 text-red-700 border-red-200", icone: ICONE_ERREUR }
      : { fond: "bg-slate-50 text-slate-600 border-slate-200", icone: ICONE_CHARGEMENT };
  zoneMessage.innerHTML = `
    <p class="flex items-center gap-2 border rounded-lg px-3 py-2.5 text-sm ${styles.fond}">
      ${styles.icone}<span>${texte}</span>
    </p>`;
}

function viderMessage() {
  zoneMessage.innerHTML = "";
}

function renderExamensDisponibles(examens) {
  if (examens.length === 0) {
    zoneExamensDisponibles.innerHTML =
      '<p class="text-sm text-slate-400">Aucun résultat publié pour le moment.</p>';
    return;
  }

  // Band scrolling right to left (css/brand.css). The list is repeated so each half of
  // the track is wide enough to loop without a gap even with very few exams, then
  // doubled; the second copy is hidden from screen readers and keyboard navigation.
  const carte = (examen, copie) => `
    <button
      type="button"
      data-examen-id="${escapeHtml(examen.id)}"
      class="btn-choisir-examen carte-examen"
      ${copie ? 'aria-hidden="true" tabindex="-1"' : ""}
    >
      <span class="carte-examen__type">${escapeHtml(LIBELLES_EXAMEN[examen.type_examen] || examen.type_examen)}</span>
      <span class="carte-examen__libelle">${escapeHtml(examen.annee)} — ${escapeHtml(examen.libelle)}</span>
    </button>`;
  const repetitions = Math.max(1, Math.ceil(6 / examens.length));
  const moitie = Array.from({ length: repetitions }, () => examens).flat();
  const cartes = [
    ...moitie.map((examen, index) => carte(examen, index >= examens.length)),
    ...moitie.map((examen) => carte(examen, true)),
  ].join("");

  zoneExamensDisponibles.innerHTML = `
    <div class="bande-examens" role="region" aria-label="Examens et concours disponibles, défilement automatique (survolez pour mettre en pause)">
      <div class="bande-examens__piste" style="--duree-defilement: ${moitie.length * 5}s">${cartes}</div>
    </div>
    <p class="text-xs text-slate-400 mt-2">Touchez un examen pour le sélectionner.</p>`;

  // No hover on phones: pause while a finger is on the band, resume shortly after.
  const bande = zoneExamensDisponibles.querySelector(".bande-examens");
  let repriseDefilement;
  bande.addEventListener("pointerdown", () => {
    clearTimeout(repriseDefilement);
    bande.classList.add("en-pause");
  });
  bande.addEventListener("pointerup", () => {
    repriseDefilement = setTimeout(() => bande.classList.remove("en-pause"), 3000);
  });

  zoneExamensDisponibles.querySelectorAll(".btn-choisir-examen").forEach((bouton) => {
    bouton.addEventListener("click", () => {
      selectExamen.value = bouton.dataset.examenId;
      document.getElementById("input-numero-pv").focus();
      form.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

async function chargerExamens() {
  try {
    const examens = await apiFetch("/api/v1/public/exams");
    if (examens.length === 0) {
      selectExamen.innerHTML = `<option value="">Aucun résultat publié pour le moment</option>`;
      renderExamensDisponibles(examens);
      return;
    }
    selectExamen.innerHTML = examens
      .map(
        (examen) =>
          `<option value="${escapeHtml(examen.id)}">${escapeHtml(LIBELLES_EXAMEN[examen.type_examen] || examen.type_examen)} ${examen.annee} — ${escapeHtml(examen.libelle)}</option>`
      )
      .join("");
    renderExamensDisponibles(examens);
  } catch (erreur) {
    selectExamen.innerHTML = `<option value="">Erreur de chargement</option>`;
    zoneExamensDisponibles.innerHTML =
      '<p class="text-sm text-red-600">Impossible de charger la liste des examens.</p>';
    afficherMessage(
      "Impossible de charger la liste des examens. Vérifiez votre connexion et réessayez."
    );
  }
}

const STYLE_DECISION = {
  ADMIS: { badge: "bg-faso-600 text-white", bordure: "border-faso-500" },
  APTE: { badge: "bg-faso-600 text-white", bordure: "border-faso-500" },
  ADMISSIBLE: { badge: "bg-sky-600 text-white", bordure: "border-sky-500" },
};
const STYLE_DECISION_DEFAUT = { badge: "bg-amber-500 text-white", bordure: "border-amber-400" };

// Publication par phase (docs/CONTEXTE_METIER.md § 2.4) — la situation de chaque phase
// est calculée côté serveur (GET /results/progress) : « ne figure pas sur la liste »
// n'est annoncé qu'une fois la phase clôturée par l'administration.
const LIBELLES_PHASE = {
  RESULTAT_UNIQUE: "Résultat",
  EPREUVES_SPORTIVES: "Épreuves sportives",
  ADMISSIBILITE: "Admissibilité",
  ADMISSION_DEFINITIVE: "Admission définitive",
  SECOND_TOUR: "Second tour",
};

const DATE_FR = new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "long", year: "numeric" });

function renderEtape(etape) {
  const libelle = escapeHtml(LIBELLES_PHASE[etape.phase] || etape.phase);
  const r = etape.resultat;
  let pastille;
  let detail;
  switch (etape.situation) {
    case "RESULTAT": {
      const style = STYLE_DECISION[r.decision] || STYLE_DECISION_DEFAUT;
      pastille = "bg-faso-600";
      const date = r.date_publication_phase ? ` · publié le ${DATE_FR.format(new Date(r.date_publication_phase))}` : "";
      const suite = r.phase_suivante_attendue
        ? `<p class="text-xs text-slate-500 mt-1">Prochaine étape : ${escapeHtml(LIBELLES_PHASE[r.phase_suivante_attendue])}</p>`
        : "";
      detail = `<span class="inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${style.badge}">${escapeHtml(r.decision)}</span>
        ${r.rang_affiche ? `<span class="text-xs text-slate-500 ml-1">Rang : ${escapeHtml(r.rang_affiche)}</span>` : ""}
        <span class="text-xs text-slate-400">${date}</span>${suite}`;
      break;
    }
    case "EN_ATTENTE":
      pastille = "bg-amber-400";
      detail = `<p class="text-sm text-slate-600">Publication en cours : votre nom ne figure pas sur les listes publiées à ce jour. D'autres listes peuvent encore paraître.</p>`;
      break;
    case "NE_FIGURE_PAS":
      pastille = "bg-slate-400";
      detail = `<p class="text-sm text-slate-700">Toutes les listes de cette phase sont publiées : vous n'y figurez pas.</p>
        <p class="text-xs text-slate-500 mt-0.5">En cas de doute, rapprochez-vous de l'organisateur du concours.</p>`;
      break;
    case "NON_CONCERNE":
      pastille = "bg-slate-200";
      detail = `<p class="text-sm text-slate-400">Non concerné</p>`;
      break;
    default:
      pastille = "bg-slate-200";
      detail = `<p class="text-sm text-slate-400">Pas encore publiée</p>`;
  }
  return `
    <li class="relative pl-6 pb-4 last:pb-0">
      <span class="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full ring-2 ring-white ${pastille}"></span>
      <p class="text-sm font-semibold text-slate-800">${libelle}</p>
      <div class="mt-0.5">${detail}</div>
    </li>`;
}

function renderResultatUnique(r) {
  const style = STYLE_DECISION[r.decision] || STYLE_DECISION_DEFAUT;
  return `
      <div class="carte-resultat border-l-4 ${style.bordure} bg-white border border-slate-100 rounded-lg p-4 shadow-sm">
        <p class="text-lg font-semibold text-slate-900">${escapeHtml(r.nom)} ${escapeHtml(r.prenom)}</p>
        <p class="text-sm text-slate-500">PV n° ${escapeHtml(r.numero_pv)} — ${escapeHtml(r.jury)}</p>
        <p class="mt-2.5">
          <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${style.badge}">${escapeHtml(r.decision)}</span>
          ${r.moyenne !== null ? `<span class="ml-2 text-sm text-slate-600">Moyenne : ${escapeHtml(r.moyenne)}</span>` : ""}
        </p>
        ${r.etablissement ? `<p class="text-sm text-slate-500 mt-1.5">${escapeHtml(r.etablissement)}</p>` : ""}
      </div>`;
}

function afficherParcours(listeParcours) {
  zoneResultats.innerHTML = listeParcours
    .map((parcours) => {
      if (parcours.etapes.length === 1) return renderResultatUnique(parcours.etapes[0].resultat);
      const identite = parcours.etapes.find((e) => e.resultat).resultat;
      return `
      <div class="carte-resultat bg-white border border-slate-100 rounded-lg p-4 shadow-sm">
        <p class="text-lg font-semibold text-slate-900">${escapeHtml(identite.nom)} ${escapeHtml(identite.prenom)}</p>
        <p class="text-sm text-slate-500 mb-3">PV n° ${escapeHtml(parcours.numero_pv)} — ${escapeHtml(parcours.jury)}</p>
        <ol class="border-l border-slate-200 ml-1.5">${parcours.etapes.map(renderEtape).join("")}</ol>
      </div>`;
    })
    .join("");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  viderMessage();
  zoneResultats.innerHTML = "";

  const examenId = selectExamen.value;
  const numeroPv = document.getElementById("input-numero-pv").value.trim();
  const jury = document.getElementById("input-jury").value.trim();

  if (!examenId) {
    afficherMessage("Veuillez sélectionner un examen.");
    return;
  }

  const params = new URLSearchParams({ examen_id: examenId, numero_pv: numeroPv });
  if (jury) params.set("jury", jury);

  afficherMessage("Recherche en cours…", "info");
  try {
    const parcours = await apiFetch(`/api/v1/public/results/progress?${params.toString()}`);
    viderMessage();
    afficherParcours(parcours);
  } catch (erreur) {
    afficherMessage(
      erreur.message.includes("Aucun résultat")
        ? "Aucun résultat trouvé pour ce numéro de PV. Vérifiez les informations saisies."
        : "Une erreur est survenue. Veuillez réessayer dans quelques instants."
    );
  }
});

chargerExamens();
