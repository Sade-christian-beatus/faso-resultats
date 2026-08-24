# Roadmap — Faso Résultats

> Document de planification. Aucune phase suivante ne doit être démarrée sans
> demande explicite (règle rappelée dans `CLAUDE.md`), même si les choix
> techniques ci-dessous sont déjà tranchés.

## ✅ Livré

- Fondations FastAPI + PostgreSQL + Redis + Docker
- Pipeline d'ingestion PDF avec OCR (Tesseract fra) et parser scan Fonction publique
- Multi-tenancy strict (schéma partagé + `administration_id`), voir `docs/MULTI_TENANCY.md`
- Isolation vérifiée par tests dédiés (tenant-à-tenant et candidat-à-candidat)
- Profil candidat unifié (schéma `plateforme` séparé), voir `docs/PROFIL_CANDIDAT_UNIFIE.md`
- Inscription OTP SMS (stub), dashboard candidat, session 30 jours
- Matching automatique par CNIB (rétroactif à l'inscription et proactif à la publication)
- Chiffrement au repos (Fernet) du CNIB/téléphone/date de naissance, hash déterministe
  pour la recherche — clé de chiffrement désormais obligatoire au démarrage (pas de
  valeur par défaut fonctionnelle), voir `README.md` § Configuration obligatoire
- AuditLog complet (qui a fait quoi, quand, sur quel tenant) sur les actions
  d'authentification et d'ingestion admin
- Endpoints super-admin API pour gérer les `Administration` et provisionner le premier
  utilisateur d'un nouveau tenant (`POST /api/v1/admin/administrations/*`)
- Verrouillage OTP réellement temporisé (clé de verrouillage dédiée, indépendante de la
  génération d'un nouveau code — voir `AuthCandidatService`)
- Détection d'abus (seuil de candidatures rejetées → suspension automatique du profil,
  `candidat_abus_taux_rejet_suspension`)
- Alerte de prise de contrôle de compte (SMS immédiat au numéro utilisé pour créer un
  compte)
- Purge des candidatures orphelines à la résiliation d'une administration (marquage
  immédiat + suppression après 6 mois) et des comptes candidat inactifs
  (`purge_candidats.py`, à planifier via cron — pas de file de tâches en Phase 1)
- UI candidat pour le mécanisme 3 de vérification (fallback OTP quand ni le CNIB ni la
  date de naissance ne figurent dans le résultat publié)
- Fondation API B2B (Phase 4, § dédiée ci-dessous) : modèles `Partenaire`/`ApiKey`,
  gestion super-admin, routes `/api/v1/b2b/exams` et `/api/v1/b2b/results` avec quota
  par clé — pas encore de facturation ni de contrat partenaire réel

## 🚧 En cours / à faire avant un lancement pilote réel

- Restructuration des routes vers l'arborescence cible (`docs/PIVOT_SAAS_B2G.md` § 2.5)
- Intégration réelle des passerelles SMS (Orange Business en priorité, voir détail
  technique ci-dessous) — l'envoi reste un stub journalisé
- Durées de rétention (`candidat_purge_inactivite_jours`, 2 ans par défaut) non
  validées par la CIL — voir `docs/APDP_PROFIL_CANDIDAT.md` § 5

## 📅 Phase 2 — Intégration SMS et notifications proactives

**Objectif :** notifier un candidat par SMS dès que son résultat est publié.

**Fournisseur retenu : Orange Business (API Bulk SMS).** ⚠️ À vérifier avant de
s'engager : couverture Moov/Telecel via l'interconnexion inter-opérateurs, et si
l'API SMS et l'API USSD (Phase 4) sont un seul contrat ou deux chez ce fournisseur.

**File de tâches retenue : RQ** (Redis Queue) — Redis est déjà dans la stack (cache),
RQ s'appuie dessus sans nouvelle brique d'infrastructure.

Ce qui existe déjà côté code, prêt à être branché à un vrai fournisseur :
- `NotificationEngine.envoyer_sms()` (stub actuel, à remplacer)
- `NotificationEngine.formater_message_resultat()` (format du message, déjà utilisé)
- La table `notifications_preinscription` (historique, hors profil candidat unifié)

Étapes techniques restantes : client Orange Business derrière l'interface
`envoyer_sms(numero, message) -> bool` déjà en place, worker RQ dédié (nouveau service
`docker-compose.yml`), retry sur échec, garde-fou de quota mensuel, report différé
d'une notification tombant dans la plage silencieuse 22h-6h (aujourd'hui abandonnée,
pas mise en file).

## 🟡 Phase 3 — Application mobile Android puis iOS, espace établissement (démarrée, partielle)

**Mise à jour du 2026-08-17 (audit) :** ce chantier a en fait déjà démarré (12
commits `feat(mobile)` mergés sur `main`) sans que cette page ne soit tenue à jour.
État réel :

- ✅ App Flutter (`mobile/`) : authentification candidat (OTP), dashboard, ajout/
  retrait de candidature, consultation rapide sans compte, cache hors-ligne des
  résultats déjà consultés. Réutilise l'API candidat (`/api/v1/candidat/*`) et
  publique (`/api/v1/public/*`) existante.
- 🔒 Notifications push et consultation par SMS : écrans présents mais
  volontairement désactivés (`gated`), dépendants de la Phase 2 (SMS) non
  démarrée.
- 🔒 Build release Android : infrastructure de signature en place, pas de
  keystore de production généré. iOS jamais testé (pas d'environnement Xcode
  disponible en session).
- 📅 Espace établissement : pas commencé — nouvelle table normalisée +
  vérification automatique contre une liste officielle d'établissements (liste
  des établissements privés déjà reçue, liste des établissements publics
  encore à obtenir).
- 📅 Portails cobrandés par administration (sous-domaines dédiés) — alternative
  ou complément au portail unique actuel (`docs/PIVOT_SAAS_B2G.md` § 2.6, option
  A) : pas commencé.

## 🟡 Phase 4 — USSD, API B2B (fondation API B2B démarrée)

**2026-08-17 :** l'USSD reste bloqué par le même prérequis que la Phase 2 (contrat
Orange Business, non signé). La fondation technique de l'**API B2B**, elle,
n'en dépendait pas — démarrée sur demande explicite pendant l'attente du contrat :

- ✅ Modèles `Partenaire`/`ApiKey` : clé en clair générée une seule fois (jamais
  stockée, seul son hash HMAC — pepper dédié `api_key_pepper`, distinct de celui du
  candidat), préfixe non sensible pour l'identification.
- ✅ Endpoints super-admin `POST/GET/PATCH /api/v1/admin/partenaires`,
  `POST /api/v1/admin/partenaires/{id}/api-keys`, `.../revoke` — gestion
  transversale (pas liée à une administration cliente), cohérent avec le modèle
  actuel des `Administration`.
- ✅ Routes `GET /api/v1/b2b/exams`, `GET /api/v1/b2b/results` : mêmes champs que
  l'API publique (pas d'accès élargi aux données sensibles pour l'instant — décision
  du 2026-08-17), authentifiées par `X-API-Key`, quota quotidien par clé (compteur
  cache, non atomique — comme le verrouillage OTP candidat) au lieu d'un rate-limit
  par IP.
- 🔒 Pas de facturation automatisée : `tier`/`quota_quotidien` configurables
  manuellement par le SUPER_ADMIN à l'émission de la clé, grille tarifaire toujours
  non tranchée.
- 📅 USSD (Orange Business) : candidat compose un code, entre son numéro de PV,
  reçoit sa décision à l'écran — pertinent pour les téléphones basiques et zones à
  connectivité limitée. Toujours bloqué par le contrat opérateur.

## Hors périmètre (décisions actées le 2026-07-03)

- **CEP (Certificat d'Études Primaires)** : couvert par la plateforme officielle
  SIGEC-CEP, ne fait pas partie du périmètre Faso Résultats.
- **Guide d'orientation** : supprimé du périmètre.
- **Expansion sous-régionale UEMOA** : supprimée. Faso Résultats reste un produit
  mono-pays (Burkina Faso) de façon permanente.

## Chantiers transverses (indépendants des phases)

1. **Validation juridique de `docs/APDP.md` et `docs/APDP_PROFIL_CANDIDAT.md`** —
   plusieurs points (base légale, responsable de traitement, durée de conservation)
   explicitement marqués comme non tranchés.
2. **Tests de charge à grande échelle** — première mesure réelle effectuée le
   2026-07-07 (client `httpx` async local contre un serveur `uvicorn` mono-processus,
   sur `GET /api/v1/public/results` en cache chaud) :

   | Concurrence client | Débit | p50 | p95 | p99 |
   |---|---|---|---|---|
   | 10 | 576 req/s | 10 ms | 48 ms | 119 ms |
   | 25 | 404 req/s | 40 ms | 181 ms | 287 ms |
   | 50 | 255-315 req/s | 105-135 ms | 450-575 ms | 800-940 ms |

   L'objectif <200 ms est tenu à concurrence modérée (10-25 clients) mais dépassé au
   p95/p99 à 50. Point important : le processus `uvicorn` restait à ~23-30% CPU même
   au pic — ce n'est **pas** le serveur qui sature, c'est le générateur de charge
   (client asyncio mono-processus sur la même machine, seul cœur disponible pour lui).
   Le débit qui *baisse* quand la concurrence *augmente* (576→255 req/s) est la
   signature classique d'un client saturé, pas d'un serveur saturé. **Donc toujours
   pas de mesure fiable de la vraie limite serveur** — il faut un outil de charge
   dédié (k6, locust, plusieurs machines clientes) contre un déploiement réel avant un
   vrai jour de proclamation. Ce qui est acquis : le chemin cache chaud fonctionne
   sans erreur sous charge, et le serveur a manifestement de la marge CPU non utilisée
   à explorer (ex. `uvicorn --workers N`).
3. **Mise en production réelle** : hébergement burkinabè (souveraineté des données),
   HTTPS, rotation des mots de passe par défaut créés par `seed.py`.
4. **Calibrage OCR** : aucun spécimen de PV scanné/photo n'est disponible actuellement
   pour calibrer le parser OCR — à refaire dès qu'un nouveau spécimen sera fourni.
5. **Intégration SMS réelle (Orange Business)** : nécessite un contrat et des
   identifiants API que ce projet n'a pas encore — `NotificationEngine.envoyer_sms`
   reste un stub journalisé en attendant.

Chaque phase reste conditionnée à une demande explicite avant de démarrer le code,
conformément à `CLAUDE.md`, même si les choix techniques ci-dessus sont déjà actés.
