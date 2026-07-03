# Architecture — Faso Résultats

> Maintenu à jour à chaque évolution du schéma ou de la structure applicative.
> Dernière mise à jour : Phase 1 — squelette backend.

## Structure du dépôt

```
faso-resultats/
├── backend/
│   ├── app/
│   │   ├── main.py          Point d'entrée FastAPI, montage des routers
│   │   ├── config.py        Settings (pydantic-settings, lues depuis .env)
│   │   ├── database.py      Engine + session SQLAlchemy async, dépendance get_db
│   │   ├── models/          Modèles SQLAlchemy 2.0 (Mapped / mapped_column)
│   │   ├── schemas/         Schémas Pydantic (requêtes/réponses) — à venir
│   │   ├── routes/          Routers FastAPI (public/, admin/, health)
│   │   ├── services/        Logique métier, testable sans DB — à venir
│   │   └── core/            Sécurité, cache — à venir
│   ├── alembic/              Migrations
│   ├── tests/                Tests pytest
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/public/          HTML/CSS/JS vanilla, servi par nginx
├── docs/                     Documentation technique
└── docker-compose.yml
```

## Modèle de données

### `examens`
Un examen ou concours pour une année donnée (ex : "BAC 2026 - Session normale").

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| type_examen | enum (`CEP`, `BEPC`, `BAC`, `CONCOURS_DIRECT`) | |
| annee | int | |
| libelle | string | |
| statut | enum (`DRAFT`, `PUBLISHED`, `ARCHIVED`) | défaut `DRAFT` — jamais visible côté public tant que non `PUBLISHED` |
| created_at / updated_at | timestamptz | |

Index : `(statut, annee)` — filtrage des examens publiés récents.

### `admins`
Comptes d'administration (upload, validation, publication).

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| email | string, unique | |
| mot_de_passe_hash | string | bcrypt, jamais en clair |
| nom_complet | string | |
| actif | bool | |
| derniere_connexion | timestamptz nullable | |

### `ingestions`
Un événement d'import de fichier source. Point d'ancrage de la traçabilité :
chaque résultat créé référence l'ingestion qui l'a produit.

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| examen_id | UUID (FK → examens, CASCADE) | |
| admin_id | UUID (FK → admins, RESTRICT) | qui a uploadé |
| nom_fichier / chemin_fichier | string | |
| type_fichier | enum (`PDF`, `EXCEL`, `PDF_OCR`) | |
| statut | enum (`EN_ATTENTE`, `PREVISUALISATION`, `VALIDEE`, `PUBLIEE`, `REJETEE`) | reflète le flux upload → prévisualisation → correction → publication |
| nombre_lignes_detectees / nombre_erreurs | int | |
| publiee_at | timestamptz nullable | |

### `resultats`
Un résultat individuel, rattaché à un examen et à l'ingestion qui l'a produit.

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| examen_id | UUID (FK → examens, CASCADE), **NOT NULL** | un résultat sans examen valide est refusé |
| ingestion_id | UUID (FK → ingestions, RESTRICT), **NOT NULL** | traçabilité vers le fichier source |
| numero_pv / jury | string | |
| nom / prenom / date_naissance / lieu_naissance | | données sensibles — jamais loguées |
| etablissement | string nullable | |
| decision | string | ex. `ADMIS`, `AJOURNE` |
| moyenne | numeric(4,2) nullable | |
| donnees_brutes | JSONB | ligne brute extraite du fichier source, conservée pour audit |

Index : `(examen_id, numero_pv, jury)` — requête principale de consultation.

### `notifications_preinscription`
Préinscription à la notification SMS (fonctionnalité Phase 2, table créée dès
Phase 1 pour ne pas devoir réécrire le schéma plus tard).

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| examen_id | UUID (FK → examens, CASCADE) | |
| telephone | string | donnée sensible |
| numero_pv | string | |
| consentement | bool | jamais pré-coché côté formulaire |
| statut | enum (`EN_ATTENTE`, `ENVOYE`, `ECHEC`) | |
| envoye_at | timestamptz nullable | |

Index : `(examen_id, statut)` — envoi en masse.

## Décisions techniques

- **UUID portable (`app/models/guid.py`)** : les PK/FK utilisent un `TypeDecorator`
  custom (`GUID`) plutôt que `postgresql.UUID` directement, pour que les modèles
  restent testables sur SQLite en mémoire sans dépendance à un Postgres réel.
  En production (dialecte `postgresql`), il se comporte comme un UUID natif.
- **`donnees_brutes` en JSON avec variante JSONB** : `JSON().with_variant(JSONB, "postgresql")`
  donne un stockage JSONB natif sur PostgreSQL (production) tout en restant
  compatible SQLite pour les tests unitaires rapides.
- **Migrations Alembic en mode async** : `alembic/env.py` utilise
  `async_engine_from_config` pour rester cohérent avec le reste de l'application
  (SQLAlchemy 2.0 async partout).
- **Tests sur SQLite en mémoire** : rapides, aucune dépendance à Postgres pour la
  CI. Les contraintes NOT NULL sont bien vérifiées par SQLite ; les contraintes
  FK ne le sont pas par défaut (non activées), donc les tests ciblent les
  colonnes NOT NULL plutôt que la seule présence de la FK.
- **`bcrypt` épinglé à 4.0.1** : `passlib` 1.7.4 lit `bcrypt.__about__.__version__`,
  supprimé dans `bcrypt` 4.1+. Épingler évite un warning au démarrage ; le hash
  bcrypt lui-même n'est pas affecté par cette version.

## Auth admin (JWT)

- `POST /api/v1/admin/login` : `{email, password}` → `{access_token, token_type}`.
  Rate-limité (`RATE_LIMIT_LOGIN`, défaut 5/minute par IP) via slowapi, pour
  limiter le brute force. Réponse 401 générique ("Email ou mot de passe
  incorrect") que l'email existe ou non, pour ne pas permettre l'énumération
  de comptes.
- Token JWT (`python-jose`, HS256) : `sub` = id admin, expiration configurable
  (`JWT_EXPIRE_MINUTES`, défaut 60 min).
- `app/core/deps.get_current_admin` : dépendance FastAPI (`HTTPBearer`) à
  injecter dans toute future route `/api/v1/admin/*` pour exiger un token
  valide et un compte actif.
- `GET /api/v1/admin/me` : exemple de route protégée, renvoie le profil de
  l'admin authentifié (jamais le hash du mot de passe).
- `backend/seed.py` : crée l'admin par défaut (`admin@faso-resultats.bf` /
  `ChangeMe123!`, à changer avant mise en production), idempotent.

## Ce qui reste à faire (Phase 1)

Voir le suivi de tâches en session. Prochaines étapes : pipeline d'ingestion
(parsers PDF/Excel/OCR + upload → prévisualisation → correction →
publication), routes publiques avec cache Redis et rate limiting, frontend
minimal.
