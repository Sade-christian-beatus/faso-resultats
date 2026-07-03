const selectExamen = document.getElementById("select-examen");
const form = document.getElementById("form-recherche");
const zoneMessage = document.getElementById("zone-message");
const zoneResultats = document.getElementById("zone-resultats");

const LIBELLES_EXAMEN = {
  CEP: "CEP",
  BEPC: "BEPC",
  BAC: "BAC",
  CONCOURS_DIRECT: "Concours direct",
};

function afficherMessage(texte, type = "erreur") {
  const couleurs =
    type === "erreur"
      ? "bg-red-50 text-red-700 border-red-200"
      : "bg-slate-50 text-slate-600 border-slate-200";
  zoneMessage.innerHTML = `<p class="border rounded px-3 py-2 text-sm ${couleurs}">${texte}</p>`;
}

function viderMessage() {
  zoneMessage.innerHTML = "";
}

async function chargerExamens() {
  try {
    const examens = await apiFetch("/api/v1/public/exams");
    if (examens.length === 0) {
      selectExamen.innerHTML = `<option value="">Aucun résultat publié pour le moment</option>`;
      return;
    }
    selectExamen.innerHTML = examens
      .map(
        (examen) =>
          `<option value="${examen.id}">${LIBELLES_EXAMEN[examen.type_examen] || examen.type_examen} ${examen.annee} — ${examen.libelle}</option>`
      )
      .join("");
  } catch (erreur) {
    selectExamen.innerHTML = `<option value="">Erreur de chargement</option>`;
    afficherMessage(
      "Impossible de charger la liste des examens. Vérifiez votre connexion et réessayez."
    );
  }
}

function afficherResultats(resultats) {
  zoneResultats.innerHTML = resultats
    .map(
      (r) => `
      <div class="border border-emerald-200 bg-emerald-50 rounded-lg p-4">
        <p class="text-lg font-semibold">${r.nom} ${r.prenom}</p>
        <p class="text-sm text-slate-600">PV n° ${r.numero_pv} — ${r.jury}</p>
        <p class="mt-2">
          <span class="inline-block px-3 py-1 rounded-full text-sm font-semibold ${
            r.decision === "ADMIS"
              ? "bg-emerald-600 text-white"
              : "bg-amber-500 text-white"
          }">${r.decision}</span>
          ${r.moyenne !== null ? `<span class="ml-2 text-sm text-slate-600">Moyenne : ${r.moyenne}</span>` : ""}
        </p>
        ${r.etablissement ? `<p class="text-sm text-slate-500 mt-1">${r.etablissement}</p>` : ""}
      </div>`
    )
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
    const resultats = await apiFetch(`/api/v1/public/results?${params.toString()}`);
    viderMessage();
    afficherResultats(resultats);
  } catch (erreur) {
    afficherMessage(
      erreur.message.includes("Aucun résultat")
        ? "Aucun résultat trouvé pour ce numéro de PV. Vérifiez les informations saisies."
        : "Une erreur est survenue. Veuillez réessayer dans quelques instants."
    );
  }
});

chargerExamens();
