const etat = {
  token: sessionStorage.getItem("faso_admin_token") || null,
  examens: [],
  ingestionCourante: null,
};

const sectionConnexion = document.getElementById("section-connexion");

const CARACTERES_HTML = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

function escapeHtml(valeur) {
  return String(valeur ?? "").replace(/[&<>"']/g, (caractere) => CARACTERES_HTML[caractere]);
}

// Publication par phase (docs/CONTEXTE_METIER.md § 2.4).
const PHASES_CONCOURS = ["EPREUVES_SPORTIVES", "ADMISSIBILITE", "ADMISSION_DEFINITIVE"];
const LIBELLES_PHASE = {
  RESULTAT_UNIQUE: "Résultat",
  EPREUVES_SPORTIVES: "Épreuves sportives",
  ADMISSIBILITE: "Admissibilité",
  ADMISSION_DEFINITIVE: "Admission définitive",
  SECOND_TOUR: "Second tour",
};

// First phase not closed yet: the only one accepting lists (phases are published in order).
function phaseOuverte(examen) {
  return (examen.phases_publication || []).find((p) => !(examen.phases_cloturees || []).includes(p)) || null;
}
const sectionAdmin = document.getElementById("section-admin");
const btnDeconnexion = document.getElementById("btn-deconnexion");

function enTeteAuth() {
  return { Authorization: `Bearer ${etat.token}` };
}

function afficherConnecte(connecte) {
  sectionConnexion.classList.toggle("hidden", connecte);
  sectionAdmin.classList.toggle("hidden", !connecte);
  btnDeconnexion.classList.toggle("hidden", !connecte);
}

function deconnecter() {
  etat.token = null;
  sessionStorage.removeItem("faso_admin_token");
  afficherConnecte(false);
}

// --- Connexion ---

document.getElementById("form-connexion").addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("message-connexion");
  messageEl.textContent = "";

  const email = document.getElementById("input-email").value.trim();
  const password = document.getElementById("input-password").value;

  try {
    const reponse = await apiFetch("/api/v1/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    etat.token = reponse.access_token;
    sessionStorage.setItem("faso_admin_token", etat.token);
    afficherConnecte(true);
    await chargerExamens();
  } catch (erreur) {
    messageEl.textContent = "Email ou mot de passe incorrect.";
  }
});

btnDeconnexion.addEventListener("click", deconnecter);

// --- Examens ---

const LIBELLES_EXAMEN = {
  CEP: "CEP",
  BEPC: "BEPC",
  BAC: "BAC",
  CONCOURS_DIRECT: "Concours direct",
};

async function chargerExamens() {
  etat.examens = await apiFetch("/api/v1/admin/exams", { headers: enTeteAuth() });
  renderExamens();
  renderSelectExamenImport();
}

function renderPhases(examen) {
  const phases = examen.phases_publication || [];
  if (phases.length < 2) return "";
  const ouverte = phaseOuverte(examen);
  const pastilles = phases
    .map((phase) => {
      const cloturee = (examen.phases_cloturees || []).includes(phase);
      const style = cloturee
        ? "bg-faso-100 text-faso-800"
        : phase === ouverte
          ? "bg-amber-100 text-amber-800"
          : "bg-slate-100 text-slate-500";
      const etat = cloturee ? "clôturée" : phase === ouverte ? "en cours" : "à venir";
      return `<span class="px-2 py-0.5 rounded-full text-xs ${style}">${LIBELLES_PHASE[phase]} · ${etat}</span>`;
    })
    .join(" ");
  const bouton = ouverte
    ? `<button data-id="${examen.id}" data-phase="${ouverte}" class="btn-cloturer-phase text-xs font-medium text-amber-800 hover:underline ml-1">Clôturer « ${LIBELLES_PHASE[ouverte]} »</button>`
    : "";
  return `<div class="mt-1.5 flex flex-wrap items-center gap-1">${pastilles}${bouton}</div>`;
}

function renderExamens() {
  const corps = document.getElementById("corps-table-examens");
  corps.innerHTML = etat.examens
    .map(
      (e) => `
      <tr class="border-b border-slate-100 last:border-0 transition">
        <td class="py-2.5">${escapeHtml(LIBELLES_EXAMEN[e.type_examen] || e.type_examen)} ${escapeHtml(e.annee)} — ${escapeHtml(e.libelle)}${renderPhases(e)}</td>
        <td>
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold ${
            e.statut === "PUBLISHED" ? "bg-faso-100 text-faso-700" : "bg-slate-100 text-slate-600"
          }">${e.statut}</span>
        </td>
        <td class="text-right">
          ${
            e.statut === "DRAFT"
              ? `<button data-id="${e.id}" class="btn-publier-examen text-xs font-medium text-faso-700 hover:text-faso-900 hover:underline transition">Publier</button>`
              : ""
          }
        </td>
      </tr>`
    )
    .join("");

  corps.querySelectorAll(".btn-publier-examen").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await apiFetch(`/api/v1/admin/exams/${btn.dataset.id}/publish`, {
        method: "POST",
        headers: enTeteAuth(),
      });
      await chargerExamens();
    });
  });

  corps.querySelectorAll(".btn-cloturer-phase").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const libelle = LIBELLES_PHASE[btn.dataset.phase];
      const confirme = window.confirm(
        `Clôturer la phase « ${libelle} » ?\n\n` +
          "Confirmez que TOUTES les listes de cette phase sont publiées. C'est irréversible : " +
          "plus aucune liste ne pourra y être ajoutée, et les candidats de la phase précédente " +
          "absents de ces listes verront qu'ils n'y figurent pas."
      );
      if (!confirme) return;
      const messageEl = document.getElementById("message-examens");
      messageEl.textContent = "";
      try {
        await apiFetch(`/api/v1/admin/exams/${btn.dataset.id}/phases/${btn.dataset.phase}/close`, {
          method: "POST",
          headers: enTeteAuth(),
        });
        await chargerExamens();
      } catch (erreur) {
        messageEl.textContent = erreur.message;
      }
    });
  });
}

function renderSelectPhaseImport() {
  const select = document.getElementById("select-phase-import");
  const examen = etat.examens.find((e) => e.id === document.getElementById("select-examen-import").value);
  const phases = (examen && examen.phases_publication) || [];
  select.classList.toggle("hidden", phases.length < 2);
  const ouverte = examen ? phaseOuverte(examen) : null;
  select.innerHTML = phases
    .map(
      (phase) =>
        `<option value="${phase}" ${phase === ouverte ? "selected" : ""}>Phase : ${LIBELLES_PHASE[phase]}</option>`
    )
    .join("");
}

document.getElementById("select-examen-import").addEventListener("change", renderSelectPhaseImport);

function renderSelectExamenImport() {
  const select = document.getElementById("select-examen-import");
  // Keep the admin's choice across re-renders (after each publication/closure): silently
  // falling back to the first exam would import the next list into the wrong exam.
  const selectionPrecedente = select.value;
  select.innerHTML = etat.examens
    .map(
      (e) =>
        `<option value="${e.id}">${escapeHtml(LIBELLES_EXAMEN[e.type_examen] || e.type_examen)} ${escapeHtml(e.annee)} — ${escapeHtml(e.libelle)}</option>`
    )
    .join("");
  if (etat.examens.some((e) => e.id === selectionPrecedente)) select.value = selectionPrecedente;
  renderSelectPhaseImport();
}

document.getElementById("form-examen").addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("message-examens");
  messageEl.textContent = "";
  const multiPhases = document.getElementById("input-multi-phases").checked;
  try {
    await apiFetch("/api/v1/admin/exams", {
      method: "POST",
      headers: { ...enTeteAuth(), "Content-Type": "application/json" },
      body: JSON.stringify({
        type_examen: document.getElementById("input-type-examen").value,
        annee: Number(document.getElementById("input-annee").value),
        libelle: document.getElementById("input-libelle").value,
        phases_publication: multiPhases ? PHASES_CONCOURS : [],
      }),
    });
    event.target.reset();
    await chargerExamens();
  } catch (erreur) {
    messageEl.textContent = erreur.message;
  }
});

// --- Import ---

document.getElementById("lien-modele-excel").addEventListener("click", async (event) => {
  event.preventDefault();
  const reponse = await fetch(`${API_BASE}/api/v1/admin/ingestions/template`, {
    headers: enTeteAuth(),
  });
  if (!reponse.ok) return;
  const blob = await reponse.blob();
  const lien = document.createElement("a");
  lien.href = URL.createObjectURL(blob);
  lien.download = "modele-import-resultats.xlsx";
  lien.click();
  URL.revokeObjectURL(lien.href);
});

document.getElementById("form-import").addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("message-import");
  messageEl.textContent = "";

  const decisionParDefaut = document.getElementById("input-decision-defaut").value.trim();

  const formData = new FormData();
  formData.set("examen_id", document.getElementById("select-examen-import").value);
  formData.set("type_fichier", document.getElementById("select-type-fichier").value);
  formData.set("file", document.getElementById("input-fichier").files[0]);
  if (decisionParDefaut) {
    formData.set("decision_par_defaut", decisionParDefaut);
  }
  const selectPhase = document.getElementById("select-phase-import");
  if (!selectPhase.classList.contains("hidden") && selectPhase.value) {
    formData.set("phase", selectPhase.value);
  }

  try {
    const ingestion = await apiFetch("/api/v1/admin/ingestions", {
      method: "POST",
      headers: enTeteAuth(),
      body: formData,
    });
    etat.ingestionCourante = ingestion;
    renderApercu();
    // reset() also puts the exam dropdown back on its first option: without restoring
    // it, the next list would silently be imported into another exam.
    const selectExamen = document.getElementById("select-examen-import");
    const examenChoisi = selectExamen.value;
    event.target.reset();
    selectExamen.value = examenChoisi;
    renderSelectPhaseImport();
  } catch (erreur) {
    messageEl.textContent = erreur.message;
  }
});

// --- Aperçu / correction / publication ---

function renderApercu() {
  const ingestion = etat.ingestionCourante;
  document.getElementById("section-apercu").classList.remove("hidden");
  const phase = ingestion.phase !== "RESULTAT_UNIQUE" ? ` — phase ${LIBELLES_PHASE[ingestion.phase]}` : "";
  document.getElementById("apercu-statut").textContent =
    `${ingestion.statut}${phase} — ${ingestion.nombre_lignes_detectees} ligne(s), ${ingestion.nombre_erreurs} erreur(s)`;

  const blocErreursFichier = document.getElementById("bloc-erreurs-fichier");
  const aDesEcarts = Boolean(ingestion.erreurs_fichier && ingestion.erreurs_fichier.length);
  document.getElementById("apercu-erreurs-fichier").textContent = aDesEcarts
    ? ingestion.erreurs_fichier.join(" ")
    : "";
  blocErreursFichier.classList.toggle("hidden", !aDesEcarts);
  document.getElementById("case-confirmer-ecarts").checked = false;

  const corps = document.getElementById("corps-table-apercu");
  const classeChamp =
    "border border-slate-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-faso-500 focus:border-faso-500 transition";
  corps.innerHTML = ingestion.lignes
    .map(
      (ligne, index) => `
      <tr class="border-b border-slate-100 last:border-0 transition ${ligne.erreurs.length ? "bg-red-50/70" : ""}">
        <td class="py-1.5 pr-2 pl-3 text-slate-500">${ligne.ligne}</td>
        <td class="pr-2"><input data-index="${index}" data-champ="numero_pv" value="${escapeHtml(ligne.donnees.numero_pv)}" class="${classeChamp} w-24" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="jury" value="${escapeHtml(ligne.donnees.jury)}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="nom" value="${escapeHtml(ligne.donnees.nom)}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="prenom" value="${escapeHtml(ligne.donnees.prenom)}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="decision" value="${escapeHtml(ligne.donnees.decision)}" class="${classeChamp} w-24" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="moyenne" value="${escapeHtml(ligne.donnees.moyenne)}" class="${classeChamp} w-16" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="numero_cnib" value="${escapeHtml(ligne.donnees.numero_cnib)}" class="${classeChamp} w-24" /></td>
        <td class="text-red-600 text-xs pr-2">${escapeHtml(ligne.erreurs.join(", "))}</td>
      </tr>`
    )
    .join("");
}

function lireCorrectionsDepuisTable() {
  const lignes = etat.ingestionCourante.lignes.map((ligne) => ({ ...ligne, donnees: { ...ligne.donnees } }));
  document.querySelectorAll("#corps-table-apercu input").forEach((input) => {
    const index = Number(input.dataset.index);
    const champ = input.dataset.champ;
    if (champ === "moyenne") {
      lignes[index].donnees[champ] = input.value !== "" ? Number(input.value) : null;
    } else {
      lignes[index].donnees[champ] = input.value;
    }
  });

  const champsObligatoires = ["numero_pv", "jury", "nom", "prenom", "decision"];
  lignes.forEach((ligne) => {
    ligne.erreurs = champsObligatoires.filter((champ) => !ligne.donnees[champ]).map((champ) => `${champ} manquant`);
  });

  return lignes;
}

document.getElementById("btn-publier").addEventListener("click", async () => {
  const messageEl = document.getElementById("message-apercu");
  const lignes = lireCorrectionsDepuisTable();
  try {
    etat.ingestionCourante = await apiFetch(`/api/v1/admin/ingestions/${etat.ingestionCourante.id}`, {
      method: "PATCH",
      headers: { ...enTeteAuth(), "Content-Type": "application/json" },
      body: JSON.stringify({ lignes }),
    });
    renderApercu();

    const confirmerEcarts = document.getElementById("case-confirmer-ecarts").checked;
    etat.ingestionCourante = await apiFetch(
      `/api/v1/admin/ingestions/${etat.ingestionCourante.id}/publish?confirmer_ecarts=${confirmerEcarts}`,
      { method: "POST", headers: enTeteAuth() }
    );
    document.getElementById("apercu-statut").textContent = etat.ingestionCourante.statut;
    await afficherMessagePublicationTerminee(messageEl);
  } catch (erreur) {
    messageEl.className = "text-sm mt-3 text-red-600";
    messageEl.textContent = erreur.message;
  }
});

async function afficherMessagePublicationTerminee(messageEl) {
  await chargerExamens();
  const examen = etat.examens.find((e) => e.id === etat.ingestionCourante.examen_id);
  messageEl.className = "text-sm mt-3 text-faso-700";

  if (examen && examen.statut === "DRAFT") {
    messageEl.innerHTML = `
      Résultats enregistrés. Ils resteront invisibles du public tant que l'examen n'est
      pas publié.
      <button id="btn-publier-examen-maintenant" class="ml-1 underline hover:text-faso-900">
        Publier l'examen maintenant
      </button>`;
    document.getElementById("btn-publier-examen-maintenant").addEventListener("click", async () => {
      await apiFetch(`/api/v1/admin/exams/${examen.id}/publish`, {
        method: "POST",
        headers: enTeteAuth(),
      });
      await chargerExamens();
      messageEl.textContent = "Résultats et examen publiés : consultables publiquement.";
    });
  } else {
    messageEl.textContent = "Résultats publiés et consultables publiquement.";
  }
}

document.getElementById("btn-rejeter").addEventListener("click", async () => {
  await apiFetch(`/api/v1/admin/ingestions/${etat.ingestionCourante.id}/reject`, {
    method: "POST",
    headers: enTeteAuth(),
  });
  document.getElementById("section-apercu").classList.add("hidden");
});

// --- Démarrage ---

if (etat.token) {
  afficherConnecte(true);
  chargerExamens().catch(deconnecter);
} else {
  afficherConnecte(false);
}
