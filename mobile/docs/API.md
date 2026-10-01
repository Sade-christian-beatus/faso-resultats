# API consommée — mapping écrans ↔ endpoints

Backend : `../../backend` (FastAPI). Toutes les routes ci-dessous existent et
sont testées côté backend (`backend/tests/`) au moment de la rédaction
(2026-07-07). Ce document est tenu à jour à chaque endpoint ajouté ou modifié
côté mobile.

## Audit initial (avant le début du développement mobile)

Le prompt de départ supposait plusieurs choses que le backend ne fait pas.
Écarts identifiés et décisions prises :

| Écart constaté | Décision |
|---|---|
| Pas d'endpoint public listant les administrations (nom, logo) | Ajouté : `GET /api/v1/public/administrations` |
| La consultation publique n'utilise **pas** la date de naissance (choix de minimisation des données, CLAUDE.md backend, 2026-07-03) — le prompt supposait un flux à 2 facteurs récépissé + date de naissance | L'app suit l'API réelle : récépissé (+ jury optionnel) uniquement, comme le web |
| `ResultatPublicOut` n'exposait pas `rang_numerique`/`rang_affiche`/`phase`/`phase_suivante_attendue` (existent sur le modèle depuis la Phase 1, jamais exposés publiquement) — le prompt attend un affichage « Rang / Phase / Prochaine étape » | Ajoutés à `ResultatPublicOut` (jour 2) |
| Pas d'endpoint pour envoyer un résultat par SMS à un numéro arbitraire (hors compte candidat) | Bouton « Recevoir par SMS » présent dans l'UI (carte résultat) mais gated « bientôt disponible » (jour 2) — dépend de l'intégration SMS réelle, non démarrée |
| Aucune infrastructure push (FCM) côté backend : pas de modèle, pas d'endpoint d'enregistrement de token, et aucun projet Firebase configuré dans ce dépôt (pas de `google-services.json`/`GoogleService-Info.plist`) | Écran « Notifications » gated « bientôt disponible » (jour 6). Décision plus prudente que prévu initialement : le SDK FCM (`firebase_core`/`firebase_messaging`, déjà en dépendance depuis le jour 1) n'est **pas** initialisé — sans projet Firebase réel, `Firebase.initializeApp()` planterait l'app au démarrage plutôt que d'échouer proprement. La préférence « Notifications push » reste modifiable et persistée (`PATCH /me`) : seule la livraison manque |
| SMS jamais connecté à un vrai opérateur (stub backend uniquement, Phase 2 volontairement non démarrée — CLAUDE.md § Roadmap) : ni numéro court réel ni syntaxe SMS définie | Écran « Consulter par SMS » gated « pas encore disponible » (jour 7, accessible depuis l'accueil). Aucun numéro ni syntaxe affichés : un faux numéro induirait un candidat en erreur (SMS envoyé dans le vide), jugé plus grave qu'un écran incomplet |
| Pas de liste de sessions actives / révocation côté candidat (JWT sans état) | Fonctionnalité non construite — écran « Sécurité » l'indique explicitement (jour 4) plutôt que de l'omettre silencieusement |
| Le prompt attend « édition téléphone » sur l'écran profil — `ProfilCandidatUpdate` (backend) n'accepte que `email`/`notifications_*`, l'identité (téléphone, CNIB, nom, date de naissance) est volontairement immuable (docs/CIL_PROFIL_CANDIDAT.md § 8) | L'app suit l'API réelle : téléphone affiché en lecture seule (badge vérifié), seuls email et préférences de notification sont éditables (jour 4) |

## Consultation rapide (sans compte)

| Écran | Endpoint |
|---|---|
| Sélection administration | `GET /api/v1/public/administrations` (cache client 1h, `dio_cache_interceptor`, jour 9) |
| Sélection examen | `GET /api/v1/public/exams` (filtré côté client par `administration_id`, cache client 1h) |
| Résultat | `GET /api/v1/public/results/progress?examen_id&numero_pv&jury` depuis le 2026-10-01 (avant : `/results`) — parcours phase par phase, une seule étape pour un examen à liste unique (cache client 24h — « résultats déjà consultés », jour 9) |

## Authentification candidat

| Écran | Endpoint |
|---|---|
| Inscription (envoi OTP) | `POST /api/v1/candidat/inscription` |
| Connexion (envoi OTP) | `POST /api/v1/candidat/login` |
| Validation OTP | `POST /api/v1/candidat/otp/verify` |

## Profil et dashboard

| Écran | Endpoint |
|---|---|
| Profil courant | `GET /api/v1/candidat/me` |
| Modifier préférences | `PATCH /api/v1/candidat/me` |
| Supprimer le compte | `DELETE /api/v1/candidat/me` |
| Exporter mes données | `GET /api/v1/candidat/me/export` |
| Journal d'accès (écran Sécurité) | `GET /api/v1/candidat/me/export` (champ `journal`, pas d'endpoint dédié) |
| Liste des candidatures | `GET /api/v1/candidat/candidatures` |
| Mes droits (contact DPO) | `GET /api/v1/public/droits-candidat` |

## Candidatures

| Écran | Endpoint |
|---|---|
| Ajouter une candidature | `POST /api/v1/candidat/candidatures` |
| Confirmer par OTP (mécanisme 3) | `POST /api/v1/candidat/candidatures/{id}/confirmer-otp` |
| Retirer une candidature | `DELETE /api/v1/candidat/candidatures/{id}` |

## Notifications push, SMS

Aucun endpoint — voir tableau d'écarts ci-dessus.
