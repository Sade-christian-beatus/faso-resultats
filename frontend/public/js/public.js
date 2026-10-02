// Home page (index.html): exam search, categories, latest publications, result lookup.
const form = document.getElementById("form-recherche");
const inputRecherche = document.getElementById("input-recherche-examen");
const listeSuggestions = document.getElementById("liste-suggestions");
const etapePv = document.getElementById("etape-pv");
const inputNumeroPv = document.getElementById("input-numero-pv");
const zoneMessage = document.getElementById("zone-message");
const zoneResultats = document.getElementById("zone-resultats");
const zoneCategories = document.getElementById("zone-categories");
const zonePublications = document.getElementById("zone-publications");
const panneauAide = document.getElementById("panneau-aide");

// Official social pages, shown in the top bar and the footer. An empty URL hides the icon.
const RESEAUX_SOCIAUX = {
  facebook: "",
  x: "",
  youtube: "",
  whatsapp: "",
};

const NB_PUBLICATIONS_RESUMEES = 5;

const LIBELLES_EXAMEN = {
  CEP: "CEP",
  BEPC: "BEPC",
  BEP: "BEP",
  CAP: "CAP",
  BAC: "BAC",
  BAC_GENERAL: "BAC général",
  BAC_TECHNOLOGIQUE: "BAC technologique",
  BAC_PROFESSIONNEL: "BAC professionnel",
  CQP: "CQP",
  BQP: "BQP",
  BPT: "BPT",
  CONCOURS_DIRECT: "Concours direct",
  CD_CATEGORIE_A: "Concours direct cat. A",
  CD_CATEGORIE_B: "Concours direct cat. B",
  CD_CATEGORIE_C: "Concours direct cat. C",
  CD_CATEGORIE_D: "Concours direct cat. D",
  CONCOURS_PROFESSIONNEL: "Concours professionnel",
  ARMEE: "Armée",
  POLICE: "Police",
  DOUANES: "Douanes",
  GENDARMERIE: "Gendarmerie",
  EAUX_FORETS: "Eaux et forêts",
  SECURITE_PENITENTIAIRE: "Sécurité pénitentiaire",
  AUTRE: "Autre",
};

const ICONES = {
  examens: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 10 12 5 2 10l10 5 10-5z" /><path d="M6 12v5c3 2 9 2 12 0v-5M22 10v6" /></svg>',
  concours: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M8 13h8M8 17h5" /></svg>',
  fonctionPublique: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18M5 21V10M19 21V10M9 21V10M15 21V10M2 10l10-7 10 7z" /></svg>',
  paramilitaires: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="m12 7 1.2 2.6 2.8.3-2.1 1.9.6 2.8L12 13.2l-2.5 1.4.6-2.8L8 9.9l2.8-.3z" /></svg>',
  autres: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8 12h.01M12 12h.01M16 12h.01" /></svg>',
  fleche: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>',
  chevron: '<svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg>',
};

// Home page shortcuts, grouped by TypeExamen (backend/app/models/examen.py).
// "Universités" from the blueprint is left out: out of scope (decision of 2026-07-03).
const CATEGORIES = [
  {
    code: "EXAMENS",
    titre: "Examens",
    description: "BAC, BEPC, CAP, CEP, BEP…",
    icone: ICONES.examens,
    teinte: "teinte-examens",
    types: ["CEP", "BEPC", "BEP", "CAP", "BAC", "BAC_GENERAL", "BAC_TECHNOLOGIQUE", "BAC_PROFESSIONNEL", "CQP", "BQP", "BPT"],
  },
  {
    code: "CONCOURS",
    titre: "Concours",
    description: "Concours directs de la fonction publique",
    icone: ICONES.concours,
    teinte: "teinte-concours",
    types: ["CONCOURS_DIRECT", "CD_CATEGORIE_A", "CD_CATEGORIE_B", "CD_CATEGORIE_C", "CD_CATEGORIE_D"],
  },
  {
    code: "FONCTION_PUBLIQUE",
    titre: "Fonction publique",
    description: "Concours professionnels",
    icone: ICONES.fonctionPublique,
    teinte: "teinte-fonction-publique",
    types: ["CONCOURS_PROFESSIONNEL"],
  },
  {
    code: "PARAMILITAIRES",
    titre: "Paramilitaires",
    description: "Armée, gendarmerie, police, douanes…",
    icone: ICONES.paramilitaires,
    teinte: "teinte-paramilitaires",
    types: ["ARMEE", "POLICE", "DOUANES", "GENDARMERIE", "EAUX_FORETS", "SECURITE_PENITENTIAIRE"],
  },
];
const CATEGORIE_AUTRES = { code: "AUTRES", titre: "Autres", icone: ICONES.autres, teinte: "teinte-autres" };

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
      : { fond: "bg-white text-slate-600 border-slate-200", icone: ICONE_CHARGEMENT };
  zoneMessage.innerHTML = `
    <p class="flex items-center gap-2 border rounded-lg px-3 py-2.5 text-sm ${styles.fond}">
      ${styles.icone}<span>${texte}</span>
    </p>`;
}

function viderMessage() {
  zoneMessage.innerHTML = "";
}

// --- State ---

const etat = {
  examens: [],
  administrations: new Map(),
  examenChoisi: null,
  categorie: "",
  toutAfficher: false,
  suggestions: [],
  suggestionActive: -1,
};

function categorieDe(examen) {
  return CATEGORIES.find((c) => c.types.includes(examen.type_examen)) || CATEGORIE_AUTRES;
}

function libelleType(examen) {
  return LIBELLES_EXAMEN[examen.type_examen] || examen.type_examen;
}

function titreExamen(examen) {
  return `${libelleType(examen)} ${examen.annee}`;
}

// Lower-case, accent-free text so "fonction publique" matches "Fonction Publique" and
// "eaux forets" matches "Eaux et forêts".
function normaliser(texte) {
  return String(texte ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}

function texteIndexe(examen) {
  const administration = etat.administrations.get(examen.administration_id);
  const categorie = categorieDe(examen);
  return normaliser(
    [
      libelleType(examen),
      examen.annee,
      examen.libelle,
      categorie.titre,
      categorie.description,
      administration?.sigle,
      administration?.nom_officiel,
    ].join(" ")
  );
}

function rechercherExamens(requete) {
  const mots = normaliser(requete).split(/\s+/).filter(Boolean);
  if (mots.length === 0) return etat.examens;
  return etat.examens.filter((examen) => {
    const texte = texteIndexe(examen);
    return mots.every((mot) => texte.includes(mot));
  });
}

// --- Exam search (combobox) ---

function fermerSuggestions() {
  listeSuggestions.classList.add("hidden");
  inputRecherche.setAttribute("aria-expanded", "false");
  inputRecherche.removeAttribute("aria-activedescendant");
  etat.suggestionActive = -1;
}

function afficherSuggestions() {
  etat.suggestions = rechercherExamens(inputRecherche.value).slice(0, 8);
  etat.suggestionActive = -1;
  if (etat.examens.length === 0) {
    listeSuggestions.innerHTML =
      '<li class="px-4 py-3 text-sm text-slate-500">Aucun résultat publié pour le moment.</li>';
  } else if (etat.suggestions.length === 0) {
    listeSuggestions.innerHTML =
      '<li class="px-4 py-3 text-sm text-slate-500">Aucun examen ne correspond. Essayez « BAC », « BEPC » ou « Police ».</li>';
  } else {
    listeSuggestions.innerHTML = etat.suggestions
      .map((examen, index) => {
        const categorie = categorieDe(examen);
        return `
        <li id="suggestion-${index}" role="option" aria-selected="false" data-examen-id="${escapeHtml(examen.id)}"
            class="suggestion flex items-center gap-3 px-4 py-2.5 cursor-pointer hover:bg-faso-50">
          <span class="pastille-icone pastille-icone--petite ${categorie.teinte}">${categorie.icone}</span>
          <span class="min-w-0">
            <span class="block text-sm font-semibold text-nuit">${escapeHtml(titreExamen(examen))}</span>
            <span class="block text-xs text-slate-500 truncate">${escapeHtml(examen.libelle)}</span>
          </span>
        </li>`;
      })
      .join("");
  }
  listeSuggestions.classList.remove("hidden");
  inputRecherche.setAttribute("aria-expanded", "true");
}

function surlignerSuggestion(index) {
  const options = listeSuggestions.querySelectorAll(".suggestion");
  if (options.length === 0) return;
  etat.suggestionActive = (index + options.length) % options.length;
  options.forEach((option, i) => {
    const actif = i === etat.suggestionActive;
    option.setAttribute("aria-selected", String(actif));
    option.classList.toggle("bg-faso-50", actif);
  });
  const active = options[etat.suggestionActive];
  inputRecherche.setAttribute("aria-activedescendant", active.id);
  active.scrollIntoView({ block: "nearest" });
}

function choisirExamen(examenId) {
  const examen = etat.examens.find((e) => e.id === examenId);
  if (!examen) return;
  etat.examenChoisi = examen;
  inputRecherche.value = titreExamen(examen);
  document.getElementById("libelle-examen-choisi").textContent =
    `${titreExamen(examen)} — ${examen.libelle}`;
  fermerSuggestions();
  viderMessage();
  zoneResultats.innerHTML = "";
  etapePv.classList.remove("hidden");
  inputNumeroPv.focus();
}

function oublierExamen() {
  etat.examenChoisi = null;
  etapePv.classList.add("hidden");
  zoneResultats.innerHTML = "";
}

inputRecherche.addEventListener("input", () => {
  if (etat.examenChoisi && inputRecherche.value !== titreExamen(etat.examenChoisi)) oublierExamen();
  afficherSuggestions();
});
inputRecherche.addEventListener("focus", () => {
  if (!etat.examenChoisi) afficherSuggestions();
});
inputRecherche.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" || event.key === "ArrowUp") {
    event.preventDefault();
    if (listeSuggestions.classList.contains("hidden")) afficherSuggestions();
    surlignerSuggestion(etat.suggestionActive + (event.key === "ArrowDown" ? 1 : -1));
  } else if (event.key === "Enter" && etat.suggestionActive >= 0) {
    event.preventDefault();
    choisirExamen(etat.suggestions[etat.suggestionActive].id);
  } else if (event.key === "Escape") {
    fermerSuggestions();
  }
});
// mousedown (not click) so the choice happens before the input loses focus.
listeSuggestions.addEventListener("mousedown", (event) => {
  const option = event.target.closest(".suggestion");
  if (!option) return;
  event.preventDefault();
  choisirExamen(option.dataset.examenId);
});
document.addEventListener("click", (event) => {
  if (!event.target.closest("#recherche")) fermerSuggestions();
});
document.getElementById("btn-changer-examen").addEventListener("click", () => {
  oublierExamen();
  inputRecherche.value = "";
  inputRecherche.focus();
});
document.getElementById("btn-exemples").addEventListener("click", () => {
  // Suggest the most recent published exam type as an example query.
  inputRecherche.value = etat.examens[0] ? libelleType(etat.examens[0]) : "BAC";
  oublierExamen();
  inputRecherche.focus();
  afficherSuggestions();
});

// Header search box: hands the query over to the hero search.
document.getElementById("form-recherche-entete").addEventListener("submit", (event) => {
  event.preventDefault();
  oublierExamen();
  inputRecherche.value = document.getElementById("input-recherche-entete").value;
  window.scrollTo({ top: 0, behavior: "smooth" });
  inputRecherche.focus();
  afficherSuggestions();
});

// --- Categories and latest publications ---

function renderCategories() {
  zoneCategories.innerHTML = CATEGORIES.map((categorie) => {
    const nombre = etat.examens.filter((e) => categorie.types.includes(e.type_examen)).length;
    return `
      <button type="button" class="categorie" data-categorie="${categorie.code}" aria-pressed="${etat.categorie === categorie.code}">
        <span class="pastille-icone ${categorie.teinte}">${categorie.icone}</span>
        <span class="min-w-0 flex-1">
          <span class="block font-semibold text-nuit">${categorie.titre}</span>
          <span class="hidden sm:block text-xs text-slate-500 leading-snug">${categorie.description}</span>
          <span class="block text-xs text-faso-700 font-medium mt-1">${nombre} publié${nombre > 1 ? "s" : ""}</span>
        </span>
        <span class="text-faso-700 self-end">${ICONES.fleche}</span>
      </button>`;
  }).join("");
}

function renderPublications() {
  const categorie = CATEGORIES.find((c) => c.code === etat.categorie);
  const examens = categorie
    ? etat.examens.filter((e) => categorie.types.includes(e.type_examen))
    : etat.examens;
  const visibles = etat.toutAfficher ? examens : examens.slice(0, NB_PUBLICATIONS_RESUMEES);

  document.getElementById("titre-publications").textContent = categorie
    ? `Publications — ${categorie.titre}`
    : "Dernières publications";
  const boutonToutVoir = document.getElementById("btn-tout-voir");
  boutonToutVoir.classList.toggle("hidden", !categorie && examens.length <= NB_PUBLICATIONS_RESUMEES);
  boutonToutVoir.firstChild.textContent = categorie
    ? "Toutes les catégories "
    : etat.toutAfficher
      ? "Voir moins "
      : "Voir tous les résultats ";

  if (visibles.length === 0) {
    zonePublications.innerHTML = `<li class="px-5 py-6 text-sm text-slate-500">${
      categorie ? "Aucun résultat publié dans cette catégorie pour le moment." : "Aucun résultat publié pour le moment."
    }</li>`;
    return;
  }
  zonePublications.innerHTML = visibles
    .map((examen) => {
      const cat = categorieDe(examen);
      const administration = etat.administrations.get(examen.administration_id);
      return `
      <li>
        <button type="button" data-examen-id="${escapeHtml(examen.id)}" class="btn-publication w-full text-left flex items-center gap-4 px-5 py-3.5 hover:bg-faso-50 transition">
          <span class="pastille-icone pastille-icone--petite ${cat.teinte}">${cat.icone}</span>
          <span class="min-w-0 flex-1">
            <span class="block font-semibold text-nuit">${escapeHtml(titreExamen(examen))}</span>
            <span class="block text-xs text-slate-500 truncate">${escapeHtml(examen.libelle)}${
              administration ? ` · ${escapeHtml(administration.sigle)}` : ""
            }</span>
          </span>
          <span class="hidden sm:inline-block text-xs font-medium text-faso-800 bg-faso-50 border border-faso-200 rounded-full px-2.5 py-0.5">Publié</span>
          <span class="text-slate-400">${ICONES.chevron}</span>
        </button>
      </li>`;
    })
    .join("");
}

function filtrerCategorie(code) {
  etat.categorie = etat.categorie === code ? "" : code;
  etat.toutAfficher = Boolean(etat.categorie);
  renderCategories();
  renderPublications();
  document.querySelectorAll("#nav-principale .lien-nav").forEach((lien) => {
    const actif = lien.dataset.categorie === etat.categorie;
    lien.classList.toggle("text-faso-700", actif);
    lien.classList.toggle("border-b-2", actif);
    lien.classList.toggle("border-faso-600", actif);
  });
}

zoneCategories.addEventListener("click", (event) => {
  const carte = event.target.closest(".categorie");
  if (!carte) return;
  filtrerCategorie(carte.dataset.categorie);
  document.getElementById("publications").scrollIntoView({ behavior: "smooth", block: "start" });
});

zonePublications.addEventListener("click", (event) => {
  const bouton = event.target.closest(".btn-publication");
  if (!bouton) return;
  window.scrollTo({ top: 0, behavior: "smooth" });
  choisirExamen(bouton.dataset.examenId);
});

document.getElementById("btn-tout-voir").addEventListener("click", () => {
  if (etat.categorie) {
    filtrerCategorie(etat.categorie); // toggles back to all categories
    etat.toutAfficher = true;
  } else {
    etat.toutAfficher = !etat.toutAfficher;
  }
  renderPublications();
});

// --- Navigation, help, social links ---

const boutonMenu = document.getElementById("btn-menu");
const menuMobile = document.getElementById("menu-mobile");
boutonMenu.addEventListener("click", () => {
  const ouvert = menuMobile.classList.toggle("hidden") === false;
  boutonMenu.setAttribute("aria-expanded", String(ouvert));
});

document.querySelectorAll(".lien-nav").forEach((lien) => {
  lien.addEventListener("click", (event) => {
    menuMobile.classList.add("hidden");
    boutonMenu.setAttribute("aria-expanded", "false");
    if (!lien.dataset.categorie) {
      event.preventDefault();
      if (etat.categorie) filtrerCategorie(etat.categorie);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (etat.categorie !== lien.dataset.categorie) filtrerCategorie(lien.dataset.categorie);
  });
});

document.querySelectorAll(".lien-aide").forEach((bouton) => {
  bouton.addEventListener("click", () => {
    menuMobile.classList.add("hidden");
    panneauAide.classList.remove("hidden");
    panneauAide.scrollIntoView({ behavior: "smooth", block: "center" });
  });
});

const ICONES_RESEAUX = {
  facebook: { nom: "Facebook", svg: '<path fill="currentColor" d="M14 8h3V4h-3c-2.8 0-4 1.8-4 4.5V10H7v4h3v8h4v-8h3l1-4h-4V8.5c0-.3.2-.5.5-.5z" />' },
  x: { nom: "X", svg: '<path fill="currentColor" d="M17.8 3h3.1l-6.8 7.8L22 21h-6.3l-4.9-6.4L5.2 21H2.1l7.3-8.3L1.7 3h6.4l4.4 5.9zm-1.1 16.2h1.7L7.4 4.7H5.6z" />' },
  youtube: { nom: "YouTube", svg: '<path fill="currentColor" d="M22 8.2a3 3 0 0 0-2.1-2.1C18 5.6 12 5.6 12 5.6s-6 0-7.9.5A3 3 0 0 0 2 8.2 31 31 0 0 0 1.6 12 31 31 0 0 0 2 15.8a3 3 0 0 0 2.1 2.1c1.9.5 7.9.5 7.9.5s6 0 7.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .4-3.8 31 31 0 0 0-.4-3.8zM10 15V9l5.2 3z" />' },
  whatsapp: { nom: "WhatsApp", svg: '<path fill="currentColor" d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm5.2 14.1c-.2.6-1.3 1.2-1.8 1.2-.5.1-1 .2-3.3-.7-2.8-1.1-4.5-3.9-4.7-4.1-.1-.2-1.1-1.5-1.1-2.9s.7-2 1-2.3c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 2c.1.2.1.3 0 .5l-.4.6c-.1.2-.3.3-.1.6.2.3.8 1.3 1.7 2.1 1.2 1 2.1 1.4 2.4 1.5.3.1.5.1.6-.1l.9-1c.2-.3.4-.2.6-.1l1.9.9c.3.1.5.2.5.3.1.2.1.8-.1 1.3z" />' },
};

function renderReseaux() {
  const liens = Object.entries(RESEAUX_SOCIAUX)
    .filter(([, url]) => url)
    .map(([cle, url]) => {
      const reseau = ICONES_RESEAUX[cle];
      return `<a href="${escapeHtml(url)}" class="reseau" target="_blank" rel="noopener" aria-label="${reseau.nom} (nouvelle fenêtre)"><svg viewBox="0 0 24 24" aria-hidden="true">${reseau.svg}</svg></a>`;
    })
    .join("");
  if (!liens) return;
  ["zone-reseaux-haut", "zone-reseaux-bas"].forEach((id) => {
    const zone = document.getElementById(id);
    zone.innerHTML = liens;
    zone.classList.remove("hidden");
    zone.classList.add("flex");
  });
}

// --- Loading ---

async function chargerDonnees() {
  // Administrations only enrich the display (sigle, search, count): a failure there must
  // not prevent looking up a result.
  const [examens, administrations] = await Promise.allSettled([
    apiFetch("/api/v1/public/exams"),
    apiFetch("/api/v1/public/administrations"),
  ]);
  if (administrations.status === "fulfilled") {
    etat.administrations = new Map(administrations.value.map((a) => [a.id, a]));
    document.getElementById("stat-administrations").textContent = administrations.value.length;
  }
  if (examens.status === "rejected") {
    zonePublications.innerHTML =
      '<li class="px-5 py-6 text-sm text-red-600">Impossible de charger la liste des examens.</li>';
    renderCategories();
    afficherMessage(
      examens.reason.status === 429
        ? escapeHtml(examens.reason.message)
        : "Impossible de charger la liste des examens. Vérifiez votre connexion et réessayez."
    );
    return;
  }
  etat.examens = examens.value;
  document.getElementById("stat-examens").textContent = etat.examens.length;
  renderCategories();
  renderPublications();
}


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
      const style = styleDecision(r.decision);
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
  const style = styleDecision(r.decision);
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

  if (!etat.examenChoisi) {
    const correspondances = rechercherExamens(inputRecherche.value);
    if (inputRecherche.value.trim() && correspondances.length === 1) {
      choisirExamen(correspondances[0].id);
    } else {
      inputRecherche.focus();
      afficherSuggestions();
    }
    return;
  }

  const numeroPv = inputNumeroPv.value.trim();
  const jury = document.getElementById("input-jury").value.trim();
  if (!numeroPv) {
    afficherMessage("Veuillez saisir votre numéro de PV.");
    inputNumeroPv.focus();
    return;
  }

  const params = new URLSearchParams({ examen_id: etat.examenChoisi.id, numero_pv: numeroPv });
  if (jury) params.set("jury", jury);

  afficherMessage("Recherche en cours…", "info");
  try {
    const parcours = await apiFetch(`/api/v1/public/results/progress?${params.toString()}`);
    viderMessage();
    afficherParcours(parcours);
  } catch (erreur) {
    afficherMessage(
      erreur.status === 429
        ? escapeHtml(erreur.message)
        : erreur.message.includes("Aucun résultat")
          ? "Aucun résultat trouvé pour ce numéro de PV. Vérifiez les informations saisies."
          : "Une erreur est survenue. Veuillez réessayer dans quelques instants."
    );
  }
});

document.getElementById("annee-courante").textContent = new Date().getFullYear();
renderReseaux();
renderCategories();
chargerDonnees();
