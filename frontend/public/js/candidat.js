const etat = {
  token: localStorage.getItem("faso_candidat_token") || null,
  telephoneEnCoursDeValidation: null,
  examens: [],
};

const sectionAuth = document.getElementById("section-auth");
const sectionDashboard = document.getElementById("section-dashboard");
const btnDeconnexion = document.getElementById("btn-deconnexion");
const messageAuth = document.getElementById("message-auth");

const formConnexion = document.getElementById("form-connexion");
const formInscription = document.getElementById("form-inscription");
const formOtp = document.getElementById("form-otp");

const ongletConnexion = document.getElementById("onglet-connexion");
const ongletInscription = document.getElementById("onglet-inscription");

function enTeteAuth() {
  return { Authorization: `Bearer ${etat.token}` };
}

function afficherMessageAuth(texte, estErreur = true) {
  messageAuth.innerHTML = `<p class="text-sm rounded-lg px-3 py-2.5 border ${
    estErreur ? "bg-red-50 text-red-700 border-red-200" : "bg-emerald-50 text-emerald-700 border-emerald-200"
  }">${texte}</p>`;
}

function viderMessageAuth() {
  messageAuth.innerHTML = "";
}

function afficherConnecte(connecte) {
  sectionAuth.classList.toggle("hidden", connecte);
  sectionDashboard.classList.toggle("hidden", !connecte);
  btnDeconnexion.classList.toggle("hidden", !connecte);
}

function deconnecter() {
  etat.token = null;
  localStorage.removeItem("faso_candidat_token");
  afficherConnecte(false);
  formConnexion.classList.remove("hidden");
  formInscription.classList.add("hidden");
  formOtp.classList.add("hidden");
}

btnDeconnexion.addEventListener("click", deconnecter);

// --- Onglets connexion / inscription ---

function activerOnglet(inscription) {
  formOtp.classList.add("hidden");
  viderMessageAuth();
  formConnexion.classList.toggle("hidden", inscription);
  formInscription.classList.toggle("hidden", !inscription);
  ongletConnexion.classList.toggle("bg-emerald-700", !inscription);
  ongletConnexion.classList.toggle("text-white", !inscription);
  ongletConnexion.classList.toggle("bg-slate-100", inscription);
  ongletConnexion.classList.toggle("text-slate-600", inscription);
  ongletInscription.classList.toggle("bg-emerald-700", inscription);
  ongletInscription.classList.toggle("text-white", inscription);
  ongletInscription.classList.toggle("bg-slate-100", !inscription);
  ongletInscription.classList.toggle("text-slate-600", !inscription);
}

ongletConnexion.addEventListener("click", () => activerOnglet(false));
ongletInscription.addEventListener("click", () => activerOnglet(true));

// --- Connexion (envoi OTP) ---

formConnexion.addEventListener("submit", async (event) => {
  event.preventDefault();
  viderMessageAuth();
  const telephone = document.getElementById("connexion-telephone").value.trim();

  try {
    const reponse = await apiFetch("/api/v1/candidat/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telephone }),
    });
    demarrerEtapeOtp(telephone, reponse.code_otp_debug);
  } catch (erreur) {
    afficherMessageAuth("Une erreur est survenue. Veuillez réessayer.");
  }
});

// --- Inscription (envoi OTP) ---

formInscription.addEventListener("submit", async (event) => {
  event.preventDefault();
  viderMessageAuth();

  if (!document.getElementById("inscription-consentement").checked) {
    afficherMessageAuth("Le consentement est nécessaire pour créer votre espace.");
    return;
  }

  const telephone = document.getElementById("inscription-telephone").value.trim();
  const payload = {
    numero_cnib: document.getElementById("inscription-cnib").value.trim(),
    nom_complet: document.getElementById("inscription-nom").value.trim(),
    date_naissance: document.getElementById("inscription-naissance").value,
    telephone,
    consentement_apdp: true,
    consentement_apdp_version: "v1",
  };

  try {
    const reponse = await apiFetch("/api/v1/candidat/inscription", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    demarrerEtapeOtp(telephone, reponse.code_otp_debug);
  } catch (erreur) {
    afficherMessageAuth(erreur.message || "Une erreur est survenue. Veuillez réessayer.");
  }
});

// --- Validation OTP (commune connexion/inscription) ---

function demarrerEtapeOtp(telephone, codeDebug) {
  etat.telephoneEnCoursDeValidation = telephone;
  formConnexion.classList.add("hidden");
  formInscription.classList.add("hidden");
  formOtp.classList.remove("hidden");
  document.getElementById("otp-telephone-affiche").textContent = telephone;
  document.getElementById("otp-code").value = codeDebug || "";
  viderMessageAuth();
  if (codeDebug) {
    afficherMessageAuth(`Mode développement : code pré-rempli (${codeDebug}).`, false);
  }
}

formOtp.addEventListener("submit", async (event) => {
  event.preventDefault();
  const code = document.getElementById("otp-code").value.trim();

  try {
    const reponse = await apiFetch("/api/v1/candidat/otp/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ telephone: etat.telephoneEnCoursDeValidation, code }),
    });
    etat.token = reponse.access_token;
    localStorage.setItem("faso_candidat_token", etat.token);
    afficherConnecte(true);
    chargerDashboard();
  } catch (erreur) {
    afficherMessageAuth("Code invalide ou expiré. Veuillez réessayer.");
  }
});

// --- Dashboard ---

const STYLE_STATUT = {
  VERIFIE_AUTO: { texte: "Vérifiée", classe: "bg-emerald-100 text-emerald-800" },
  VERIFIE_MANUEL: { texte: "Vérifiée", classe: "bg-emerald-100 text-emerald-800" },
  EN_ATTENTE: { texte: "En attente de publication", classe: "bg-amber-100 text-amber-800" },
  REJETE: { texte: "Non vérifiée", classe: "bg-red-100 text-red-800" },
};

function rendreCandidatures(candidatures) {
  const zone = document.getElementById("zone-candidatures");
  if (candidatures.length === 0) {
    zone.innerHTML = '<p class="text-sm text-slate-400 px-1">Aucune candidature pour le moment.</p>';
    return;
  }

  zone.innerHTML = candidatures
    .map((c) => {
      const style = STYLE_STATUT[c.statut_verification] || STYLE_STATUT.EN_ATTENTE;
      return `
      <div class="carte-candidature bg-white border border-slate-100 rounded-lg p-4 shadow-sm">
        <div class="flex items-center justify-between gap-2">
          <p class="text-sm text-slate-500">Récépissé n° ${c.numero_recepisse}</p>
          <span class="text-xs font-semibold px-2.5 py-1 rounded-full ${style.classe}">${style.texte}</span>
        </div>
        ${
          c.dernier_resultat_statut
            ? `<p class="mt-2 text-lg font-semibold text-slate-900">${c.dernier_resultat_statut}</p>`
            : `<p class="mt-2 text-sm text-slate-400">Résultat pas encore publié</p>`
        }
        <button type="button" data-id="${c.id}" class="btn-retirer-candidature mt-2 text-xs text-slate-400 hover:text-red-600 underline underline-offset-2">
          Retirer
        </button>
      </div>`;
    })
    .join("");

  zone.querySelectorAll(".btn-retirer-candidature").forEach((bouton) => {
    bouton.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/v1/candidat/candidatures/${bouton.dataset.id}`, {
          method: "DELETE",
          headers: enTeteAuth(),
        });
        chargerCandidatures();
      } catch (erreur) {
        // silencieux : l'utilisateur peut réessayer
      }
    });
  });
}

async function chargerCandidatures() {
  try {
    const candidatures = await apiFetch("/api/v1/candidat/candidatures", { headers: enTeteAuth() });
    rendreCandidatures(candidatures);
  } catch (erreur) {
    document.getElementById("zone-candidatures").innerHTML =
      '<p class="text-sm text-red-600 px-1">Impossible de charger vos candidatures.</p>';
  }
}

async function chargerExamensPourAjout() {
  const select = document.getElementById("ajout-examen");
  try {
    etat.examens = await apiFetch("/api/v1/public/exams");
    select.innerHTML = etat.examens
      .map((e) => `<option value="${e.id}|${e.administration_id}">${e.annee} — ${e.libelle}</option>`)
      .join("");
  } catch (erreur) {
    select.innerHTML = '<option value="">Erreur de chargement</option>';
  }
}

document.getElementById("form-ajout-candidature").addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("message-ajout");
  messageEl.innerHTML = "";

  const [examenId, administrationId] = document.getElementById("ajout-examen").value.split("|");
  const numeroRecepisse = document.getElementById("ajout-recepisse").value.trim();
  if (!examenId) {
    messageEl.innerHTML = '<p class="text-sm text-red-600">Veuillez sélectionner un examen.</p>';
    return;
  }

  try {
    await apiFetch("/api/v1/candidat/candidatures", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...enTeteAuth() },
      body: JSON.stringify({
        administration_id: administrationId,
        examen_id: examenId,
        numero_recepisse: numeroRecepisse,
      }),
    });
    document.getElementById("ajout-recepisse").value = "";
    chargerCandidatures();
  } catch (erreur) {
    messageEl.innerHTML = `<p class="text-sm text-red-600">${erreur.message}</p>`;
  }
});

async function chargerDashboard() {
  await Promise.all([chargerCandidatures(), chargerExamensPourAjout()]);
}

// --- Démarrage ---

if (etat.token) {
  afficherConnecte(true);
  chargerDashboard();
} else {
  afficherConnecte(false);
}
