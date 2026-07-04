const etat = {
  token: sessionStorage.getItem("faso_admin_token") || null,
  examens: [],
  ingestionCourante: null,
};

const sectionConnexion = document.getElementById("section-connexion");
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

function renderExamens() {
  const corps = document.getElementById("corps-table-examens");
  corps.innerHTML = etat.examens
    .map(
      (e) => `
      <tr class="border-b border-slate-100 last:border-0 transition">
        <td class="py-2.5">${LIBELLES_EXAMEN[e.type_examen] || e.type_examen} ${e.annee} — ${e.libelle}</td>
        <td>
          <span class="px-2 py-0.5 rounded-full text-xs font-semibold ${
            e.statut === "PUBLISHED" ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600"
          }">${e.statut}</span>
        </td>
        <td class="text-right">
          ${
            e.statut === "DRAFT"
              ? `<button data-id="${e.id}" class="btn-publier-examen text-xs font-medium text-emerald-700 hover:text-emerald-900 hover:underline transition">Publier</button>`
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
}

function renderSelectExamenImport() {
  const select = document.getElementById("select-examen-import");
  select.innerHTML = etat.examens
    .map(
      (e) =>
        `<option value="${e.id}">${LIBELLES_EXAMEN[e.type_examen] || e.type_examen} ${e.annee} — ${e.libelle}</option>`
    )
    .join("");
}

document.getElementById("form-examen").addEventListener("submit", async (event) => {
  event.preventDefault();
  await apiFetch("/api/v1/admin/exams", {
    method: "POST",
    headers: { ...enTeteAuth(), "Content-Type": "application/json" },
    body: JSON.stringify({
      type_examen: document.getElementById("input-type-examen").value,
      annee: Number(document.getElementById("input-annee").value),
      libelle: document.getElementById("input-libelle").value,
    }),
  });
  event.target.reset();
  await chargerExamens();
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

  try {
    const ingestion = await apiFetch("/api/v1/admin/ingestions", {
      method: "POST",
      headers: enTeteAuth(),
      body: formData,
    });
    etat.ingestionCourante = ingestion;
    renderApercu();
    event.target.reset();
  } catch (erreur) {
    messageEl.textContent = erreur.message;
  }
});

// --- Aperçu / correction / publication ---

function renderApercu() {
  const ingestion = etat.ingestionCourante;
  document.getElementById("section-apercu").classList.remove("hidden");
  document.getElementById("apercu-statut").textContent =
    `${ingestion.statut} — ${ingestion.nombre_lignes_detectees} ligne(s), ${ingestion.nombre_erreurs} erreur(s)`;

  const erreursFichierEl = document.getElementById("apercu-erreurs-fichier");
  if (ingestion.erreurs_fichier && ingestion.erreurs_fichier.length) {
    erreursFichierEl.textContent = ingestion.erreurs_fichier.join(" ");
    erreursFichierEl.classList.remove("hidden");
  } else {
    erreursFichierEl.classList.add("hidden");
  }

  const corps = document.getElementById("corps-table-apercu");
  const classeChamp =
    "border border-slate-300 rounded px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 transition";
  corps.innerHTML = ingestion.lignes
    .map(
      (ligne, index) => `
      <tr class="border-b border-slate-100 last:border-0 transition ${ligne.erreurs.length ? "bg-red-50/70" : ""}">
        <td class="py-1.5 pr-2 pl-3 text-slate-500">${ligne.ligne}</td>
        <td class="pr-2"><input data-index="${index}" data-champ="numero_pv" value="${ligne.donnees.numero_pv || ""}" class="${classeChamp} w-24" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="jury" value="${ligne.donnees.jury || ""}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="nom" value="${ligne.donnees.nom || ""}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="prenom" value="${ligne.donnees.prenom || ""}" class="${classeChamp} w-28" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="decision" value="${ligne.donnees.decision || ""}" class="${classeChamp} w-24" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="moyenne" value="${ligne.donnees.moyenne ?? ""}" class="${classeChamp} w-16" /></td>
        <td class="pr-2"><input data-index="${index}" data-champ="numero_cnib" value="${ligne.donnees.numero_cnib || ""}" class="${classeChamp} w-24" /></td>
        <td class="text-red-600 text-xs pr-2">${ligne.erreurs.join(", ")}</td>
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

    etat.ingestionCourante = await apiFetch(
      `/api/v1/admin/ingestions/${etat.ingestionCourante.id}/publish`,
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
  messageEl.className = "text-sm mt-3 text-emerald-700";

  if (examen && examen.statut === "DRAFT") {
    messageEl.innerHTML = `
      Résultats enregistrés. Ils resteront invisibles du public tant que l'examen n'est
      pas publié.
      <button id="btn-publier-examen-maintenant" class="ml-1 underline hover:text-emerald-900">
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
