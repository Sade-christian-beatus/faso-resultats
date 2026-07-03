# Architecture — Faso Résultats

> Maintenu à jour à chaque évolution du schéma ou de la structure applicative.
> Dernière mise à jour : Phase 1 complète et validée de bout en bout
> (fondations, auth, ingestion, API publique, frontend, Docker Compose réel).

## Structure du dépôt

```
faso-resultats/
├── backend/
│   ├── app/
│   │   ├── main.py          Point d'entrée FastAPI, montage des routers
│   │   ├── config.py        Settings (pydantic-settings, lues depuis .env)
│   │   ├── database.py      Engine + session SQLAlchemy async, dépendance get_db
│   │   ├── models/          Modèles SQLAlchemy 2.0 (Mapped / mapped_column)
│   │   ├── schemas/         Schémas Pydantic (requêtes/réponses)
│   │   ├── routes/          Routers FastAPI (public/, admin/, health)
│   │   ├── services/        Logique métier, testable sans DB (parsers d'ingestion)
│   │   └── core/            Sécurité (JWT/bcrypt), cache, rate limiting
│   ├── alembic/              Migrations
│   ├── tests/                Tests pytest
│   ├── seed.py                Peuple l'admin par défaut
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/public/          HTML/CSS/JS vanilla + Tailwind CDN, servi par nginx
│   ├── index.html             Consultation publique
│   ├── admin.html              Interface admin (login, examens, import)
│   └── js/                    api.js (fetch wrapper), public.js, admin.js
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
| numero_cnib | string(20) nullable | numéro de carte d'identité, renseigné pour les concours directs (identification forte) ; vide pour CEP/BEPC/BAC. **Absent de l'API publique** (même sensibilité que date/lieu de naissance) |
| decision | string | ex. `ADMIS`, `AJOURNE`, ou `ADMISSIBLE` pour une liste d'admissibilité de concours |
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

### Calibrage sur un vrai document de concours (2026-07-03)

Un vrai PV de concours direct (Assistants des Douanes, admissibilité aux
épreuves sportives) a permis de tester le parser Excel sur une structure
réelle, très différente d'un examen scolaire (CEP/BEPC/BAC) : colonnes
`N°`, `NOM ET PRENOM(s)`, `RECEPISSE-CODE-CENTRE`, `N°CNIB`, `DATE NAIS.`
(dates à année sur 2 chiffres, ex. `15/02/01`), `CENTRE`. Avant calibrage,
le parser rejetait entièrement ce type de document (`numero_pv`, `nom`,
`prenom`, `decision` tous signalés manquants). Trois évolutions livrées en
conséquence :

1. **`decision_par_defaut`** : nouveau paramètre optionnel de l'upload
   (`app/services/ingestion/normalizer.normaliser_ligne`, thread jusqu'à
   `POST /api/v1/admin/ingestions`). Pour les documents sans colonne
   décision par ligne (une liste d'admissibilité vaut pour tout le
   document), l'admin choisit une décision à l'upload, appliquée à toute
   ligne sans décision propre — la décision par ligne, quand elle existe,
   prime toujours.
2. **Colonne nom+prénom combinée** : nouvel alias `nom_prenom` reconnu
   (« NOM ET PRENOM(s) » et variantes). **Pas de découpage automatique**
   (risque d'erreur sur les noms composés burkinabè) — le nom complet est
   importé tel quel dans `nom`, `prenom` reste vide et donc signalé en
   erreur, pour que l'admin le sépare manuellement dans l'écran de
   correction existant (aucune UI supplémentaire nécessaire).
3. **`numero_cnib`** : nouveau champ optionnel sur `Resultat` (alias
   reconnus : « N°CNIB », « CNIB »). Absent de l'API publique, même
   sensibilité que `date_naissance`/`lieu_naissance`.

Au passage, `_FORMATS_DATE` accepte désormais aussi les années sur 2
chiffres (`%d/%m/%y`), format courant sur ce type de document.

Aliases supplémentaires reconnus pour `numero_pv` (« récépissé-code-centre »,
« récépissé ») et `date_naissance` (« date nais. »).

Le PDF natif et l'OCR restent non calibrés (voir plus haut) — cette
calibration n'a porté que sur le parser Excel, le document fourni étant au
format image/PDF mais reconstruit en `.xlsx` pour le test (même structure
de colonnes).

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
  des données (APDP). Décision actée — voir « Historique des décisions
  techniques importantes » dans `CLAUDE.md`.
- **Pas de second facteur anti-scraping en Phase 1** : la recherche ne demande
  que `numero_pv` (+ `jury`), protégée par le rate limiting (30 req/min/IP) et
  l'absence de tout endpoint de liste/wildcard. Risque accepté pour la Phase 1,
  à réévaluer avant un déploiement à grande échelle — voir `CLAUDE.md`.

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

## Frontend (`frontend/public/`)

HTML/CSS/JS vanilla + Tailwind via CDN (`<script src="https://cdn.tailwindcss.com">`),
conformément à la stack verrouillée. Aucun bundler, aucune dépendance npm.

- **`index.html` + `js/public.js`** : consultation publique. Charge la liste
  des examens publiés (`/api/v1/public/exams`), recherche un résultat par
  numéro de PV (+ jury optionnel), affiche la décision/moyenne/établissement.
- **`admin.html` + `js/admin.js`** : connexion (JWT stocké en
  `sessionStorage`, jamais en `localStorage`, pour limiter la durée de vie
  du token à l'onglet), création/publication d'examens, upload de fichier,
  aperçu éditable ligne par ligne (inputs liés à `apercu_donnees`),
  enregistrement des corrections (`PATCH`), publication/rejet.
- **`js/api.js`** : wrapper `fetch` commun, détecte l'environnement de dev
  (`localhost`/`127.0.0.1`) pour pointer vers `http://<hôte>:8000` ; en
  production, `API_BASE` reste vide (même origine attendue derrière un
  reverse proxy — à confirmer selon l'hébergement final).

### Bugs trouvés et corrigés en testant dans un vrai navigateur (Playwright)

Les tests `curl` et `httpx` ne déclenchent jamais de préflight CORS ni
n'exécutent de JavaScript — ces deux bugs n'étaient donc visibles qu'en
conditions réelles de navigateur :

1. **CORS bloquait `PATCH`** : `CORSMiddleware` n'autorisait que
   `GET/POST/PUT/DELETE`, donc *toute* correction d'ingestion échouait
   silencieusement dans un navigateur (le préflight `OPTIONS` échouait).
   Corrigé dans `app/main.py` + test de non-régression (`tests/test_cors.py`).
2. **`moyenne` vide envoyait `""` au lieu de `null`** dans
   `lireCorrectionsDepuisTable()` (`admin.js`), ce qui faisait planter
   l'insertion PostgreSQL (`NUMERIC(4,2)` refuse une chaîne vide) au moment
   de la publication. Corrigé.
3. **`.hidden` de Tailwind dépend entièrement du CDN** : si le CDN est lent
   ou indisponible (réaliste en 3G), la classe `hidden` ne fait plus rien et
   le formulaire de connexion et le tableau de bord admin s'affichent
   simultanément. Un filet de sécurité CSS inline (`<style>.hidden{display:none}</style>`)
   a été ajouté pour que cet état reste correct indépendamment du CDN — la
   mise en forme visuelle, elle, reste dégradée sans Tailwind.

### Rendu visuel

La logique/structure a été vérifiée via Playwright dans le sandbox de
développement (réseau sans accès à `cdn.tailwindcss.com`, donc sans CSS).
Le rendu visuel réel (couleurs, espacements Tailwind) a été confirmé
ensuite sur poste réel avec accès internet, sur `index.html` et
`admin.html` (mise en forme correcte, pas de superposition connexion/
tableau de bord).

## Validation Docker Compose

`docker compose up --build` a été validé de bout en bout, en deux temps :

- **Dans le sandbox de développement de cette session** : `docker compose
  config` réussit (fichier valide — interpolation des variables
  d'environnement, volumes, healthchecks, dépendances `service_healthy`
  correctes), mais `docker compose up --build` était bloqué par la politique
  réseau du sandbox (téléchargement de toute image Docker Hub refusé côté
  proxy, confirmé sur plusieurs images différentes — incident de
  l'environnement, pas du projet).
- **Sur poste réel (Windows, Docker Desktop)** : validé intégralement le
  2026-07-03 — `docker compose up --build -d` (4 conteneurs `Healthy`/
  `Started`), `alembic upgrade head` (migrations appliquées), `python
  seed.py` (admin par défaut créé), `GET /health` → `{"status":"ok"}`,
  `GET /api/v1/public/exams` → `[]` (comportement attendu, aucun examen
  publié). Deux vrais bugs d'intégration trouvés et corrigés au passage :
  1. Le service `redis` publiait le port 6379 vers l'hôte alors que le
     backend l'atteint via le réseau Docker interne — ça faisait échouer
     tout le stack sur toute machine ayant déjà un process sur ce port
     (`docker-compose.yml`, port retiré).
  2. Un dossier local non suivi par git avait dérivé du dépôt réel
     (fichiers assemblés à la main au fil des échanges plutôt que clonés),
     ce qui a provoqué une erreur `psycopg2 is not async` en migration —
     résolu par un clone git propre. Aucun bug de code réel ici, mais un
     rappel que l'empaquetage Docker doit toujours être testé depuis un
     clone propre du dépôt, jamais depuis une copie assemblée à la main.

Le pipeline complet (base + cache + backend + frontend, construits et
démarrés via Docker, migrations et seed appliqués, API qui répond) est donc
confirmé fonctionnel de bout en bout.

## Ce qui reste à faire (Phase 1)

La Phase 1 (fondations : API + base + ingestion + web public + admin minimal)
est complète et validée de bout en bout (code + Docker Compose + rendu
visuel). Pistes restantes avant une vraie mise en production :
- Calibrer les parsers PDF natif et OCR sur de vrais spécimens OCECOS/DGEC.
- Faire valider `docs/APDP.md` par l'APDP / un professionnel du droit —
  plusieurs points (base légale, durée de conservation, responsable de
  traitement) y sont explicitement marqués comme non tranchés.
