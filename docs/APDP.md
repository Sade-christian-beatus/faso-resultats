# Documentation de traitement — Conformité APDP

> Document de travail technique, à faire valider par un professionnel du
> droit et/ou directement par l'Autorité de Protection des Données à
> caractère Personnel du Burkina Faso (APDP, https://www.cil.bf) avant toute
> mise en production réelle. Il décrit ce que fait le système aujourd'hui
> (Phase 1) ; il ne constitue pas à lui seul une déclaration de traitement
> officielle. Les points marqués ⚠️ nécessitent une confirmation juridique.

Maintenu à jour à chaque évolution touchant des données à caractère
personnel, conformément à `CLAUDE.md`.

---

## 1. Responsable de traitement

⚠️ À compléter avec l'entité officielle porteuse du projet (ex. OCECOS,
DGEC, ou la structure publique/privée retenue dans la convention). Tant que
cette information n'est pas formalisée, ce document reste un brouillon
technique.

---

## 2. Données traitées

### 2.1 Résultats de candidats (`resultats`)

| Donnée | Sensibilité | Utilisée pour |
|---|---|---|
| `numero_pv`, `jury` | Non sensible | Clé de recherche publique |
| `nom`, `prenom` | Identifiante | Affichage du résultat |
| `decision`, `moyenne`, `etablissement` | Résultat scolaire | Affichage du résultat |
| `date_naissance`, `lieu_naissance` | Identifiante, sensible | Stockées (traçabilité), **non exposées côté API publique** (voir `CLAUDE.md`, décision du 2026-07-03) |
| `donnees_brutes` (jsonb) | Copie de la ligne source | Audit — permet de remonter à ce qui a été réellement importé, en cas de contestation |

### 2.2 Comptes administrateurs (`admins`)

| Donnée | Sensibilité | Utilisée pour |
|---|---|---|
| `email` | Identifiante | Connexion |
| `mot_de_passe_hash` | Sensible (jamais en clair, bcrypt) | Authentification |
| `nom_complet` | Identifiante | Affichage interne |

### 2.3 Préinscriptions SMS (`notifications_preinscription`)

Table créée en Phase 1 pour ne pas devoir modifier le schéma en Phase 2,
**mais aucune route ne la lit ou ne l'écrit actuellement** — elle n'est pas
en usage tant que la Phase 2 (intégration SMS) n'a pas démarré.

| Donnée | Sensibilité | Utilisée pour (Phase 2) |
|---|---|---|
| `telephone` | Identifiante, sensible | Envoi du SMS de résultat |
| `numero_pv` | Non sensible | Rattacher la notification au bon résultat |
| `consentement` | — | Preuve de consentement explicite (case non pré-cochée, cf. `CLAUDE.md`) |

### 2.4 Fichiers sources uploadés

Les fichiers PDF/Excel importés (`backend/uploads/`, jamais commités —
voir `.gitignore`) peuvent contenir les mêmes données que `donnees_brutes`,
en plus de toute donnée superflue présente dans le fichier d'origine
(colonnes non mappées, mise en page). Conservés en l'état pour audit et
retraitement en cas d'erreur de parsing.

---

## 3. Finalités du traitement

1. Permettre à un candidat de consulter son propre résultat via son numéro
   de PV (et jury, en cas d'ambiguïté).
2. Assurer la traçabilité de chaque résultat publié jusqu'à son fichier
   source et l'administrateur ayant réalisé l'import (`ingestion_id`,
   `admin_id`), en cas de contestation ou d'erreur.
3. (Phase 2, non actif) Notifier un candidat par SMS de la disponibilité de
   son résultat, sur préinscription et consentement explicite.

Aucune autre finalité (statistiques, profilage, revente de données,
prospection) n'est mise en œuvre.

---

## 4. Base légale

⚠️ À confirmer avec l'APDP / un juriste. Piste de travail : mission de
service public (organismes d'examens officiels) pour la publication des
résultats, et consentement explicite pour les notifications SMS (Phase 2).

---

## 5. Minimisation des données

- L'API publique (`/api/v1/public/results`) ne renvoie jamais
  `date_naissance` ni `lieu_naissance` — seules les données strictement
  nécessaires pour confirmer un résultat déjà recherché par numéro de PV
  sont exposées (voir `CLAUDE.md`, historique des décisions).
- Aucun endpoint public ne permet de lister ou d'énumérer des candidats :
  il faut déjà connaître un numéro de PV précis. Pas de recherche par nom.
- Les logs applicatifs ne doivent contenir aucune donnée personnelle
  sensible (nom, date de naissance, téléphone) — voir §7.

---

## 6. Durée de conservation

⚠️ Durée légale à confirmer avec l'APDP / le responsable de traitement.
**Non implémenté à ce jour** : aucun mécanisme de purge automatique
n'existe encore dans le code (Phase 1). C'est un manque identifié, à
combler avant une mise en production réelle — voir §9.

---

## 7. Sécurité des données

Mesures déjà en place (Phase 1) :

- Mots de passe admin hashés avec bcrypt, jamais stockés/loggés en clair.
- Authentification admin par JWT (expiration configurable), routes
  d'écriture toutes protégées par `get_current_admin`.
- Rate limiting sur le login (5/min/IP par défaut) et les routes publiques
  (30/min/IP par défaut).
- CORS restreint aux origines déclarées (`CORS_ORIGINS`).
- Variables sensibles (secrets JWT, mots de passe DB) uniquement via `.env`,
  jamais commitées (`.gitignore`).
- `donnees_brutes` stocké en JSONB, accessible uniquement via les routes
  admin protégées — jamais exposé publiquement.

À vérifier/compléter avant mise en production :

- ⚠️ **Absence de purge/rotation des mots de passe par défaut** : le compte
  admin créé par `seed.py` (`admin@faso-resultats.bf` / `ChangeMe123!`) doit
  être changé avant toute exposition publique du service.
- ⚠️ **Logs applicatifs** : non audités formellement à ce stade pour
  vérifier qu'aucune donnée personnelle sensible n'y transite (FastAPI/
  uvicorn logguent les requêtes, potentiellement avec des paramètres de
  recherche contenant des numéros de PV — à examiner, un numéro de PV
  seul n'est pas considéré sensible ici mais mérite vérification).
- ⚠️ HTTPS non configuré à ce stade (Phase 1 tourne en HTTP local/Docker) —
  obligatoire avant toute exposition publique.
- ⚠️ Hébergement sur serveurs burkinabè (souveraineté des données, cf.
  `CLAUDE.md`) — à valider selon l'infrastructure de déploiement retenue.

---

## 8. Destinataires et sous-traitants

- **Administrateurs habilités** (comptes `admins`) : accès à l'ensemble des
  données candidats via les routes admin, pour l'import et la correction.
- **Hébergeur** : ⚠️ à préciser une fois l'infrastructure de production
  choisie (doit être burkinabè, cf. `CLAUDE.md`).
- **Opérateurs télécom** (Orange, Moov, Telecel) : ⚠️ concernera le numéro
  de téléphone dès la Phase 2 (envoi SMS) — non applicable en Phase 1.
- Aucune donnée n'est partagée avec un tiers en dehors de ce périmètre.

---

## 9. Droits des personnes concernées

⚠️ Non implémenté techniquement à ce jour (Phase 1) : aucun endpoint ne
permet à un candidat de demander l'accès, la rectification ou l'effacement
de ses données. À prévoir avant mise en production :

- Un canal de contact (ex. adresse email ou formulaire) pour les demandes
  d'exercice de droits, tant qu'aucun endpoint self-service n'existe.
- Une procédure de correction : les corrections de résultats erronés
  passent déjà par le flux admin (upload → correction → republication),
  mais une correction *après* publication n'a pas encore de flux dédié
  (aujourd'hui, seule une ingestion encore en `PREVISUALISATION` est
  corrigible — voir `docs/ARCHITECTURE.md`).

---

## 10. Consentement SMS (Phase 2, non actif)

Le modèle `NotificationPreinscription.consentement` (bool, défaut `False`)
est prêt à porter la preuve d'un consentement explicite, non pré-coché,
conformément à `CLAUDE.md`. Aucune collecte n'a lieu tant que la Phase 2 n'a
pas démarré.

---

## 11. Prochaines étapes avant une vraie mise en production

1. Faire valider ce document par l'APDP ou un professionnel du droit
   (base légale, durée de conservation, responsable de traitement).
2. Implémenter un mécanisme de purge des données après la durée légale de
   conservation (une fois celle-ci confirmée).
3. Auditer les logs applicatifs pour confirmer l'absence de données
   personnelles sensibles.
4. Mettre en place HTTPS et un hébergement burkinabè avant toute ouverture
   au public.
5. Changer le mot de passe admin par défaut créé par `seed.py`.
