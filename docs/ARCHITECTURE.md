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
- **`coverage.run.concurrency = ["greenlet", "thread"]`** : SQLAlchemy 2.0 async
  fait passer les appels DBAPI synchrones par un greenlet (`greenlet_spawn`).
  Sans ce réglage, `coverage.py` ne trace pas le code exécuté côté greenlet et
  sous-évalue fortement la couverture des routes qui touchent la base.

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

## Admin — examens

- `POST /api/v1/admin/exams` : crée un examen en statut `DRAFT`.
- `GET /api/v1/admin/exams` : liste tous les examens (vue admin, tous statuts).
- `POST /api/v1/admin/exams/{id}/publish` : passe l'examen en `PUBLISHED`,
  le rendant visible côté public (une fois les routes publiques construites).
  Séparé volontairement de la publication d'une ingestion : charger des
  résultats et rendre un examen public sont deux décisions distinctes.

## Pipeline d'ingestion

Toute importation suit strictement : **upload → prévisualisation → correction
manuelle possible → publication explicite**, conformément à CLAUDE.md.

### Parsers (`app/services/ingestion/`)

- `normalizer.py` : logique pure (aucune I/O) qui reconnaît les en-têtes de
  colonnes (alias français tolérants aux accents/casse) et normalise chaque
  ligne brute vers les champs `Resultat`, en **collectant les erreurs plutôt
  qu'en levant une exception** — une ligne en erreur reste visible dans
  l'aperçu pour correction manuelle, au lieu de faire échouer tout l'import.
  Champs obligatoires : `numero_pv`, `jury`, `nom`, `prenom`, `decision`.
- `excel_parser.py` (openpyxl) : entièrement testé avec de vrais fichiers
  `.xlsx` générés dans les tests (aucune dépendance externe nécessaire pour
  écrire *et* lire du Excel).
- `pdf_parser.py` (pdfplumber) : extrait les tableaux d'un PDF natif (texte,
  non scanné). ⚠️ Non calibré sur de vrais PV — aucun spécimen OCECOS/DGEC
  n'était disponible pendant le développement, et générer un PDF de test
  réaliste aurait nécessité une dépendance supplémentaire non justifiée à ce
  stade. À valider dès qu'un vrai PV PDF sera fourni.
- `ocr_parser.py` (pdf2image + OpenCV + pytesseract, `lang='fra'`) : pipeline
  image → texte, puis découpage en colonnes par heuristique (séparateur =
  2+ espaces). La fonction de découpage (`lignes_depuis_texte`) est pure et
  testée ; le pipeline image lui-même nécessite les binaires `tesseract` et
  `poppler` (présents dans le Dockerfile, absents de l'environnement de dev
  sandbox) et n'a donc pas pu être testé en conditions réelles. ⚠️ Heuristique
  de premier jet, à calibrer sur de vrais PV scannés.
- `dispatch.py` : sélectionne le bon parser selon `TypeFichier`.
- `publication.py` : transforme l'aperçu validé (`Ingestion.apercu_donnees`)
  en lignes `Resultat` prêtes à insérer.

### Flux admin (`app/routes/admin/ingestions.py`)

1. `POST /api/v1/admin/ingestions` (multipart : `file`, `examen_id`,
   `type_fichier`) : sauvegarde le fichier sous
   `{UPLOADS_DIR}/{examen_id}/{ingestion_id}.{ext}`, parse immédiatement
   (synchrone — pas de file d'attente à ce stade), crée l'`Ingestion` en
   statut `PREVISUALISATION` avec `apercu_donnees` (lignes + erreurs par
   ligne). Rejette les extensions incompatibles avec le `type_fichier`
   déclaré et les fichiers dépassant `MAX_UPLOAD_SIZE_MB` (défaut 20 Mo).
2. `GET /api/v1/admin/ingestions/{id}` : aperçu complet pour relecture.
3. `PATCH /api/v1/admin/ingestions/{id}` : remplace `apercu_donnees` par la
   version corrigée par l'admin (uniquement si statut `PREVISUALISATION`).
4. `POST /api/v1/admin/ingestions/{id}/publish` : **bloqué si une seule ligne
   porte encore une erreur** (validation humaine obligatoire) — crée les
   `Resultat` (avec `donnees_brutes` = ligne brute d'origine, pour l'audit),
   passe l'ingestion en `PUBLIEE`.
5. `POST /api/v1/admin/ingestions/{id}/reject` : écarte l'ingestion sans
   créer de résultats.

Note : publier une ingestion ne rend pas les résultats visibles côté public
si l'examen parent est encore en `DRAFT` — les deux publications (ingestion
et examen) sont des étapes distinctes, contrôlées séparément.

## Routes publiques (`app/routes/public/results.py`)

- `GET /api/v1/public/exams` : examens en statut `PUBLISHED` uniquement.
- `GET /api/v1/public/results?examen_id=&numero_pv=&jury=` : recherche par
  numéro de PV (le `jury` est optionnel, utile pour désambiguïser — c'est
  exactement l'index composite `(examen_id, numero_pv, jury)`). 404 si aucun
  résultat, ou si l'examen n'est pas `PUBLISHED` (même si l'ingestion l'a
  déjà été).
- **Champs sensibles non exposés** : `date_naissance` et `lieu_naissance` sont
  volontairement absents de `ResultatPublicOut`, par principe de minimisation
  des données (APDP) — le candidat n'a pas besoin de se les voir confirmer
  pour retrouver son résultat. ⚠️ Décision prise sans validation produit
  explicite ; à confirmer.
- **Anti-scraping non traité à ce stade** : la recherche ne demande que
  `numero_pv` (+ `jury`), sans second facteur (ex. date de naissance). Le
  rate limiting (30 req/min/IP par défaut) limite le débit mais n'empêche pas
  un scraping lent et distribué. À réévaluer si le produit expose un jour les
  résultats à plus grande échelle.

### Cache (`app/core/cache.py`)

- Redis (`REDIS_URL`) avec repli automatique en mémoire process si Redis est
  injoignable (`RedisError`/`OSError` interceptées), conformément à CLAUDE.md.
- TTL configurable (`CACHE_TTL_SECONDS`, défaut 300s) sur `/exams` et chaque
  requête `/results` (clé incluant `examen_id`+`numero_pv`+`jury`).
- **Client Redis "loop-aware"** : recréé automatiquement si l'event loop
  asyncio courant change (`_get_redis_client()`). En production il n'y a
  qu'une seule loop (celle d'uvicorn), donc le client est créé une fois pour
  toute la durée du process. Cette précaution évite un piège classique
  Redis-async + pytest (chaque test peut tourner sur une nouvelle event loop,
  ce qui casse un client créé une fois au niveau module).
- Mesuré en local (Postgres + Redis réels, hors conditions de prod) :
  ~7ms en cache froid, ~2ms en cache chaud sur `/results` — largement sous
  la cible de 200ms de CLAUDE.md, mais à re-mesurer une fois hébergé sur
  l'infrastructure burkinabè cible.

## Ce qui reste à faire (Phase 1)

Voir le suivi de tâches en session. Prochaine étape : frontend minimal
(consultation + admin.html).
