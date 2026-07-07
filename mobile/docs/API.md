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
| Aucune infrastructure push (FCM) côté backend : pas de modèle, pas d'endpoint d'enregistrement de token | SDK FCM intégré côté client (jour 6), écrans gated « bientôt disponible » — aucun appel réseau vers un endpoint qui n'existe pas |
| SMS jamais connecté à un vrai opérateur (stub backend uniquement) | Écran « Consulter par SMS » gated « bientôt disponible » (jour 7) |
| Pas de liste de sessions actives / révocation côté candidat (JWT sans état) | Fonctionnalité non construite — noté comme limite connue |

## Consultation rapide (sans compte)

| Écran | Endpoint |
|---|---|
| Sélection administration | `GET /api/v1/public/administrations` |
| Sélection examen | `GET /api/v1/public/exams` (filtré côté client par `administration_id`) |
| Résultat | `GET /api/v1/public/results?examen_id&numero_pv&jury` |

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
