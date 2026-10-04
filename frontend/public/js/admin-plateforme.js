// Platform dashboard (SUPER_ADMIN): administrations (tenants) and their agents' accounts.
// Uses the globals of admin.js (etat, apiFetch, enTeteAuth, escapeHtml).

const LIBELLES_STATUT_ADMINISTRATION = {
  PILOTE: "Pilote",
  ACTIF: "Actif",
  SUSPENDU: "Suspendu",
  RESILIE: "Résilié",
};

// What changing to each status does, shown before the admin confirms.
const CONSEQUENCES_STATUT = {
  PILOTE: "Ses résultats publiés restent visibles du public.",
  ACTIF: "Ses résultats publiés restent visibles du public.",
  SUSPENDU: "Ses résultats deviennent immédiatement invisibles du public, jusqu'à réactivation.",
  RESILIE:
    "Ses résultats deviennent invisibles du public et les espaces candidats liés seront purgés dans 6 mois. À réserver à la fin de la convention.",
};

function messagePlateforme(id, texte, erreur = false) {
  const el = document.getElementById(id);
  el.className = `text-sm mt-3 ${erreur ? "text-red-700" : "text-faso-800"}`;
  el.textContent = texte;
}

async function chargerPlateforme() {
  try {
    etat.administrations = await apiFetch("/api/v1/admin/administrations", { headers: enTeteAuth() });
  } catch (erreur) {
    messagePlateforme("message-plateforme", erreur.message, true);
    return;
  }
  renderAdministrations();
  document.getElementById("util-administration").innerHTML = etat.administrations
    .map((a) => `<option value="${escapeHtml(a.id)}">${escapeHtml(a.sigle)} — ${escapeHtml(a.nom_officiel)}</option>`)
    .join("");
}

function renderAdministrations() {
  const corps = document.getElementById("corps-table-administrations");
  if (etat.administrations.length === 0) {
    corps.innerHTML =
      '<tr><td colspan="3" class="py-4 text-slate-500">Aucune administration pour le moment : ajoutez la première ci-dessous.</td></tr>';
    return;
  }
  corps.innerHTML = etat.administrations
    .map(
      (a) => `
      <tr class="border-b border-slate-100 last:border-0 align-top">
        <td class="py-2.5 pr-3">
          <strong class="text-nuit">${escapeHtml(a.sigle)}</strong>
          <span class="block text-xs text-slate-500">${escapeHtml(a.nom_officiel)}</span>
        </td>
        <td class="py-2.5 pr-3 text-xs text-slate-600">
          ${escapeHtml(a.contact_referent_nom)}<br />${escapeHtml(a.contact_referent_telephone)}
        </td>
        <td class="py-2.5">
          <label class="sr-only" for="statut-${escapeHtml(a.id)}">Statut de ${escapeHtml(a.sigle)}</label>
          <select id="statut-${escapeHtml(a.id)}" data-id="${escapeHtml(a.id)}" class="select-statut border border-slate-300 rounded-lg px-2 py-1.5 bg-white text-sm">
            ${Object.entries(LIBELLES_STATUT_ADMINISTRATION)
              .map(([valeur, libelle]) => `<option value="${valeur}" ${a.statut === valeur ? "selected" : ""}>${libelle}</option>`)
              .join("")}
          </select>
        </td>
      </tr>`
    )
    .join("");

  corps.querySelectorAll(".select-statut").forEach((select) => {
    select.addEventListener("change", async () => {
      const administration = etat.administrations.find((a) => a.id === select.dataset.id);
      const nouveau = select.value;
      const confirme = window.confirm(
        `Passer ${administration.sigle} en « ${LIBELLES_STATUT_ADMINISTRATION[nouveau]} » ?\n\n${CONSEQUENCES_STATUT[nouveau]}`
      );
      if (!confirme) {
        select.value = administration.statut;
        return;
      }
      try {
        await apiFetch(`/api/v1/admin/administrations/${administration.id}`, {
          method: "PATCH",
          headers: { ...enTeteAuth(), "Content-Type": "application/json" },
          body: JSON.stringify({ statut: nouveau }),
        });
        messagePlateforme("message-plateforme", `${administration.sigle} : statut « ${LIBELLES_STATUT_ADMINISTRATION[nouveau]} ».`);
        await chargerPlateforme();
      } catch (erreur) {
        select.value = administration.statut;
        messagePlateforme("message-plateforme", erreur.message, true);
      }
    });
  });
}

document.getElementById("form-administration").addEventListener("submit", async (event) => {
  event.preventDefault();
  const valeur = (id) => document.getElementById(id).value.trim();
  try {
    const creee = await apiFetch("/api/v1/admin/administrations", {
      method: "POST",
      headers: { ...enTeteAuth(), "Content-Type": "application/json" },
      body: JSON.stringify({
        code: valeur("adm-code"),
        sigle: valeur("adm-sigle"),
        nom_officiel: valeur("adm-nom"),
        ministere_tutelle: valeur("adm-ministere"),
        contact_referent_nom: valeur("adm-referent-nom"),
        contact_referent_email: valeur("adm-referent-email"),
        contact_referent_telephone: valeur("adm-referent-telephone"),
        statut: valeur("adm-statut"),
      }),
    });
    event.target.reset();
    messagePlateforme("message-form-administration", `${creee.sigle} ajoutée. Créez maintenant le compte de son premier agent.`);
    await chargerPlateforme();
    document.getElementById("util-administration").value = creee.id;
  } catch (erreur) {
    messagePlateforme("message-form-administration", erreur.message, true);
  }
});

document.getElementById("form-utilisateur").addEventListener("submit", async (event) => {
  event.preventDefault();
  const administrationId = document.getElementById("util-administration").value;
  const administration = etat.administrations.find((a) => a.id === administrationId);
  try {
    const utilisateur = await apiFetch(`/api/v1/admin/administrations/${administrationId}/utilisateurs`, {
      method: "POST",
      headers: { ...enTeteAuth(), "Content-Type": "application/json" },
      body: JSON.stringify({
        nom_complet: document.getElementById("util-nom").value.trim(),
        email: document.getElementById("util-email").value.trim(),
        role: document.getElementById("util-role").value,
        password: document.getElementById("util-mot-de-passe").value,
      }),
    });
    event.target.reset();
    if (administration) document.getElementById("util-administration").value = administration.id;
    messagePlateforme(
      "message-form-utilisateur",
      `Compte créé pour ${utilisateur.email}${administration ? ` (${administration.sigle})` : ""}.`
    );
  } catch (erreur) {
    messagePlateforme("message-form-utilisateur", erreur.message, true);
  }
});
