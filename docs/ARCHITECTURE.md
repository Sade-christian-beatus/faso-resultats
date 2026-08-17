# Architecture — Faso Résultats

> Maintenu à jour à chaque évolution du schéma ou de la structure applicative.
> Dernière mise à jour : 2026-08-17 — couvre la Phase 1 (fondations, auth,
> ingestion, API publique, frontend, Docker Compose réel), le pivot multi-tenant
> et le profil candidat unifié. La Phase 3 (mobile, `mobile/`) est documentée
> séparément dans `mobile/docs/`.

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
│   │   ├── services/        Logique métier, testable sans DB
│   │   │   ├── ingestion/    Parsers Excel/PDF/OCR, normalisation, publication
│   │   │   ├── parsers/      Détection de type PDF + parser scan Fonction publique
│   │   │   └── sources/      Abstraction ResultsSource (voir § Sources de données)
│   │   ├── data/reference/   Référentiels statiques (ministères de tutelle...)
│   │   └── core/            Sécurité (JWT/bcrypt), cache, rate limiting
│   ├── alembic/              Migrations
│   ├── tests/                Tests pytest
│   ├── seed.py                Peuple l'admin par défaut + examens d'exemple
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

> Architecture multi-tenant (pivot SaaS B2G, voir `docs/PIVOT_SAAS_B2G.md` et
> `docs/MULTI_TENANCY.md`) : schéma partagé, isolation par colonne
> `administration_id` sur chaque table métier.

### `administrations`
Un tenant (administration cliente : OCECOS, Office du BAC, AGRE...).

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| code | string, unique | identifiant technique (slug) |
| nom_officiel / sigle / ministere_tutelle | string | |
| logo_url / couleur_primaire / domaine_personnalise | string nullable | personnalisation par tenant |
| contact_referent_nom / email / telephone | string | |
| date_signature_convention | date nullable | |
| convention_active | bool, défaut `False` | |
| plan_abonnement | enum (`STARTER`, `STANDARD`, `PREMIUM`), défaut `STARTER` | |
| quota_sms_mensuel / quota_examens_annuel | int, défaut `0` | |
| statut | enum (`ACTIF`, `SUSPENDU`, `PILOTE`, `RESILIE`), défaut `PILOTE` | |
| created_at / updated_at | timestamptz | |

Index : `code` (unique).

### `examens`
Un examen ou concours pour une année donnée (ex : "BAC 2026 - Session normale").

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| administration_id | UUID (FK → administrations, CASCADE), **NOT NULL** | tenant propriétaire |
| type_examen | enum `TypeExamen`, voir taxonomie complète en § Sources de données | `BAC` et `CONCOURS_DIRECT` conservés (non-breaking) en plus des variantes précises (`BAC_GENERAL`...) |
| annee | int | |
| libelle | string | |
| statut | enum (`DRAFT`, `PUBLISHED`, `ARCHIVED`) | défaut `DRAFT` — jamais visible côté public tant que non `PUBLISHED` |
| categorie | enum `CategorieExamen` nullable | `EXAMEN_SCOLAIRE` / `CONCOURS_DIRECT` / `CONCOURS_PROFESSIONNEL` / `CONCOURS_PARAMILITAIRE` |
| serie | string nullable | ex. série du BAC (A, C, D...) ou corps d'un concours |
| ministere_tutelle | string nullable | traçabilité de l'organisme responsable ; voir aussi `app/data/reference/organismes.py` |
| source_donnees | enum `SourceDonnees`, défaut `FILE_IMPORT` | d'où proviennent les résultats — voir § Sources de données |
| partenariat_officiel | bool, défaut `False` | reconnaissance officielle par convention signée |
| phases_publication | jsonb (liste), défaut `[]` | phases attendues pour ce type d'examen — voir § Phases de publication |
| created_at / updated_at | timestamptz | |

Index : `(administration_id, statut)` — filtrage tenant des examens publiés.

### `utilisateurs`
Comptes de connexion à l'espace admin (anciennement `admins`).

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| administration_id | UUID (FK → administrations, CASCADE) nullable | NULL uniquement pour les rôles plateforme (`SUPER_ADMIN`, `SUPPORT`) — voir `docs/MULTI_TENANCY.md` |
| email | string, unique | |
| mot_de_passe_hash | string | bcrypt, jamais en clair |
| nom_complet | string | |
| telephone | string nullable | |
| role | enum `RoleUtilisateur` (`SUPER_ADMIN`, `SUPPORT`, `ADMIN_ADMINISTRATION`, `OPERATEUR_INGESTION`, `OPERATEUR_PUBLICATION`, `LECTEUR`) | |
| actif | bool | |
| derniere_connexion | timestamptz nullable | |

### `ingestions`
Un événement d'import de fichier source. Point d'ancrage de la traçabilité :
chaque résultat créé référence l'ingestion qui l'a produit.

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| administration_id | UUID (FK → administrations, CASCADE), **NOT NULL** | tenant propriétaire |
| examen_id | UUID (FK → examens, CASCADE) | |
| admin_id | UUID (FK → utilisateurs, RESTRICT) | qui a uploadé |
| nom_fichier / chemin_fichier | string | |
| type_fichier | enum (`PDF`, `EXCEL`, `PDF_OCR`) | |
| statut | enum (`EN_ATTENTE`, `PREVISUALISATION`, `VALIDEE`, `PUBLIEE`, `REJETEE`) | reflète le flux upload → prévisualisation → correction → publication |
| nombre_lignes_detectees / nombre_erreurs | int | |
| apercu_donnees | jsonb | lignes extraites en attente de correction/publication |
| erreurs_fichier | jsonb (liste de string) | messages au niveau du fichier entier (colonnes non reconnues, fichier vide...), pas d'une ligne précise |
| publiee_at | timestamptz nullable | |

Index : `(administration_id, created_at)`.

### `resultats`
Un résultat individuel, rattaché à un examen et à l'ingestion qui l'a produit.

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| administration_id | UUID (FK → administrations, CASCADE), **NOT NULL** | tenant propriétaire |
| examen_id | UUID (FK → examens, CASCADE), **NOT NULL** | un résultat sans examen valide est refusé |
| ingestion_id | UUID (FK → ingestions, RESTRICT), **NOT NULL** | traçabilité vers le fichier source |
| numero_pv / jury | string | |
| nom / prenom / date_naissance / lieu_naissance | | données sensibles — jamais loguées |
| etablissement | string nullable | |
| numero_cnib | string(20) nullable | numéro de carte d'identité, renseigné pour les concours directs (identification forte) ; vide pour CEP/BEPC/BAC. **Absent de l'API publique** (même sensibilité que date/lieu de naissance) |
| numero_recepisse / code_concours / code_centre / rang_numerique / rang_affiche | nullable | spécifiques aux communiqués scannés de la Fonction publique (voir § Parser scan Fonction publique) ; vides pour les autres types d'examens. `numero_recepisse` duplique `numero_pv` plutôt que de le remplacer, pour ne pas casser la recherche publique existante |
| decision | string | ex. `ADMIS`, `AJOURNE`, ou `ADMISSIBLE` pour une liste d'admissibilité de concours |
| moyenne | numeric(4,2) nullable | |
| phase | enum `PhasePublication`, défaut `RESULTAT_UNIQUE` | voir § Phases de publication |
| date_publication_phase | timestamptz nullable | |
| phase_suivante_attendue | enum `PhasePublication` nullable | |
| donnees_brutes | JSONB | ligne brute extraite du fichier source, conservée pour audit |

Index : `(examen_id, numero_pv, jury, phase)` — requête principale de consultation
(non filtrée par tenant, voir § Routes publiques), un candidat pouvant désormais
avoir plusieurs `Resultat` pour un même examen (un par phase). Il s'agit d'un index
de performance, pas d'une contrainte d'unicité — rien n'empêche au niveau base deux
lignes strictement identiques ; la déduplication reste une responsabilité
applicative si besoin. Index séparé sur `administration_id` pour les vues admin.

### `notifications_preinscription`
Préinscription à la notification SMS (fonctionnalité Phase 2, table créée dès
Phase 1 pour ne pas devoir réécrire le schéma plus tard).

| Colonne | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| administration_id | UUID (FK → administrations, CASCADE), **NOT NULL** | tenant propriétaire |
| examen_id | UUID (FK → examens, CASCADE) | |
| telephone | string | donnée sensible |
| numero_pv | string | |
| consentement | bool | jamais pré-coché côté formulaire |
| statut | enum (`EN_ATTENTE`, `ENVOYE`, `ECHEC`) | |
| envoye_at | timestamptz nullable | |

Index : `(examen_id, statut)` — envoi en masse.

## Sources de données (`app/services/sources/`)

Contexte complet : `docs/CONTEXTE_METIER.md` § 4.2. Abstraction `ResultsSource`
(`base.py`) unifiant la récupération des résultats depuis n'importe quel canal de
publication gouvernemental existant, avec une seule méthode `fetch_results(examen_id,
**kwargs) -> list[LigneExtraite]` :

- **`FileImportSource`** (implémentée) — délègue à
  `app.services.ingestion.dispatch.parser_fichier`, déjà utilisé directement par
  `POST /api/v1/admin/ingestions`. Seule source réellement utilisée en Phase 1 : c'est
  le cœur stratégique du projet, puisqu'à l'exception du CEP (couvert par SIGEC-CEP,
  hors périmètre de Faso Résultats — voir `docs/PIVOT_SAAS_B2G.md`), **aucun**
  examen ni concours du Burkina Faso ne dispose aujourd'hui d'une
  consultation individuelle par numéro de PV — tout reste au format PDF/communiqué
  téléchargeable. La qualité et la vitesse de ce pipeline sont l'avantage compétitif
  principal.
- **`SigecApiSource`, `GouvPdfMonitorSource`, `FacebookMonitorSource`,
  `PressMonitoringSource`** (`stubs.py`) — classes documentées mais **non
  implémentées** : chacune lève `NotImplementedError` avec une explication de ce qui
  bloque (partenariat à conclure, validation juridique du scraping, évaluation Graph
  API Facebook, absence de canal numérique pour Armée/Gendarmerie). Formalisent
  l'extensibilité future sans contraindre l'architecture ni être activées sans
  décision explicite.

### Cartographie des plateformes gouvernementales existantes (juillet 2026)

Référence pour comprendre le positionnement du produit — détail complet dans
`docs/CONTEXTE_METIER.md` § 1-2 :

| Examen / concours | Plateforme actuelle | Consultation individuelle ? |
|---|---|---|
| CEP | SIGEC-CEP (`resultats.examens.gov.bf`) | ✅ Oui — seul segment couvert |
| BEPC / BAC | `education.gov.bf` (annonces) + affichage physique | ❌ Non |
| Concours directs Fonction publique | PDF sur `fonction-publique.gov.bf` | ❌ Non |
| Douanes / GSP / Eaux et Forêts | PDF sur `fonction-publique.gov.bf` | ❌ Non |
| Police Nationale | `securite.gov.bf` + Facebook (msecubf) | ❌ Non |
| Armée / Gendarmerie | RTB, Sidwaya, affichage physique en camps | ❌ Non (aucun canal en ligne) |

`econcours.gov.bf` et `econcours-pro.gov.bf` gèrent uniquement les **inscriptions**
aux concours, jamais la publication des résultats — à ne pas confondre avec une
plateforme concurrente de consultation.

## Phases de publication (concours paramilitaires)

Contexte complet : `docs/CONTEXTE_METIER.md` § 2.4. Contrairement aux examens
scolaires (résultat unique : admis/ajourné), les concours paramilitaires se déroulent
en **3 phases successives**, chacune publiée séparément :

1. `EPREUVES_SPORTIVES` — aptes à composer aux épreuves écrites
2. `ADMISSIBILITE` — retenus pour la visite médicale d'incorporation
3. `ADMISSION_DEFINITIVE` — liste finale, sous réserve d'enquête de moralité

Un même candidat peut donc avoir **plusieurs lignes `Resultat`** pour un même examen
(une par phase), avec des décisions différentes à chaque étape — il peut apparaître
« apte » en phase 1 et ne plus figurer en phase 2 (échec à l'écrit). `Resultat.phase`
distingue ces lignes ; `phase_suivante_attendue` indique à l'utilisateur la prochaine
étape s'il y en a une. `Examen.phases_publication` liste les phases prévues pour ce
type d'examen (`RESULTAT_UNIQUE` par défaut pour tout le reste, y compris `SECOND_TOUR`
pour un BEPC/BAC en seconde session).

⚠️ Le frontend n'affiche pas encore d'indicateur de phase ni de sélecteur d'examen à
deux niveaux (catégorie puis type précis) — améliorations UX documentées comme
« bonus, non prioritaires » dans `docs/CONTEXTE_METIER.md` § 7, à traiter avec le
reste du travail esthétique.

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
- Token JWT (`python-jose`, HS256) : `sub` = id utilisateur, expiration
  configurable (`JWT_EXPIRE_MINUTES`, défaut 60 min).
- `app/core/deps.get_current_utilisateur` : dépendance FastAPI (`HTTPBearer`)
  injectée dans toute route `/api/v1/admin/*` pour exiger un token valide et
  un compte actif.
- `app/core/deps.get_current_administration` : dépendance qui résout le
  tenant (`Administration`) de l'utilisateur connecté — voir
  `docs/MULTI_TENANCY.md` pour le détail de l'isolation multi-tenant.
- `GET /api/v1/admin/me` : exemple de route protégée, renvoie le profil de
  l'utilisateur authentifié (jamais le hash du mot de passe), avec son
  `role` et son `administration_id`.
- `backend/seed.py` : crée un super-admin plateforme
  (`superadmin@faso-resultats.bf`) et un utilisateur `ADMIN_ADMINISTRATION`
  par tenant pilote (OCECOS, Office du BAC, AGRE), tous en
  `ChangeMe123!` (à changer avant mise en production), idempotent.

## Admin — examens

- `POST /api/v1/admin/exams` : crée un examen en statut `DRAFT`, rattaché à
  l'administration de l'utilisateur connecté.
- `GET /api/v1/admin/exams` : liste les examens de l'administration courante
  (vue admin, tous statuts).
- `POST /api/v1/admin/exams/{id}/publish` : passe l'examen en `PUBLISHED`,
  le rendant visible côté public. Séparé volontairement de la publication
  d'une ingestion : charger des résultats et rendre un examen public sont
  deux décisions distinctes. 404 si l'examen appartient à une autre
  administration.

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

### Calibrage du parser PDF natif sur un vrai document (2026-07-04)

Test de `pdf_parser.py` contre la liste officielle des établissements
privés reçue le 2026-07-03 (62 pages, 2029 lignes, tableau natif
`N°/REGION/NOM DE L'ETABLISSEMENT/PROVINCES/COMMUNES/SECTEUR`). Ce
document n'est pas un PV de résultats — ses colonnes ne correspondent à
aucun alias métier — mais c'est un vrai PDF gouvernemental multi-pages, ce
qui permet de tester la robustesse de l'extraction elle-même :

- **Aucun crash, aucune ligne perdue** sur les 62 pages : `pdfplumber`
  détecte correctement un tableau par page et notre logique de mapping
  d'en-tête (calculé une seule fois sur la première page, réutilisé
  ensuite) gère bien la continuité du tableau sans dupliquer l'en-tête.
- **Document au mauvais format correctement rejeté** : les 2029 lignes
  sont toutes signalées en erreur (`numero_pv`/`nom`/`prenom`/`decision`
  manquants), donc la publication resterait bloquée — comportement
  attendu si un admin importe le mauvais fichier par erreur.
- **Corruption de texte source, 1 ligne sur 2029** : la ligne 34 de la
  page 2 contient un nom d'établissement dont les caractères sont
  entremêlés au niveau du flux PDF lui-même (`LCYOCLELEE GPER IPVREI...`
  au lieu d'un nom lisible) — confirmé en testant aussi bien l'extraction
  par défaut que la stratégie `vertical_strategy="text"`, et en lisant le
  texte brut de la page : la corruption est déjà présente dans le contenu
  du PDF, pas introduite par notre parsing. Cause probable : une correction
  manuelle faite dans le document source (texte superposé à l'ancien).
  Une détection automatique de ce cas précis a été testée par curiosité
  (heuristique sur le nombre de mots courts) mais produit des faux
  positifs et rate le vrai cas — pas assez fiable pour un seul cas sur
  2029 lignes, donc pas retenue (inutile d'ajouter de la complexité pour
  un problème que la relecture manuelle obligatoire avant publication
  couvre déjà). Conclusion : la validation humaine systématique reste la
  bonne protection contre ce type de corruption, pas un correctif
  automatique.

**L'OCR reste non calibré** : aucun spécimen de PV scanné n'est disponible
dans cette session (les images partagées le 2026-07-03 n'ont pas été
conservées après compactage de la conversation). À calibrer dès qu'un vrai
PV scanné/photo sera à nouveau fourni.

### Calibrage OCR sur une reconstitution fidèle (2026-07-04)

Les photos du PV « Assistants des Douanes » repartagées dans la conversation
n'ont, comme les fois précédentes, pas été conservées sur disque après
compactage — impossible de les relire directement avec `pytesseract`.
Reconstitution à l'identique (même en-têtes, mêmes colonnes, mêmes lignes,
police monospace) rendue en image puis dégradée (légère rotation, flou,
bruit, compression JPEG) pour simuler une vraie photo, et passée dans le
véritable pipeline OCR (`tesseract` installé pour l'occasion). Trois défauts
réels trouvés et corrigés dans `ocr_parser.py` :

1. **Mode de segmentation Tesseract par défaut (PSM 3) mélange les colonnes**
   sur un tableau large : le texte ressort regroupé par bloc détecté (tous
   les N°, puis tous les noms, puis tous les récépissés...) au lieu de ligne
   par ligne. **Corrigé** en forçant `--psm 6` (bloc de texte uniforme), qui
   restitue l'ordre naturel des lignes.
2. **L'en-tête n'est pas forcément la première ligne de texte** : les
   documents officiels ont presque toujours un titre au-dessus (ex.
   « ASSISTANTS DES DOUANES/HOMMES », « ADMISSIBLES »), ce que confirme aussi
   bien ce PV que la liste des établissements. `lignes_depuis_texte`
   supposait `lignes_texte[0]` = en-tête. **Corrigé** avec
   `_trouver_ligne_entete` : cherche la première ligne reconnaissant au
   moins 2 colonnes métier, reste au comportement précédent quand l'en-tête
   est bien en ligne 1 (aucune régression sur les tests existants).
3. **⚠️ Non corrigé — nécessite une décision de conception avant de coder
   davantage.** L'heuristique de découpage en colonnes (`\s{2,}` : au moins
   2 espaces = séparateur) ne fonctionne pas de façon fiable sur du texte
   réellement sorti de Tesseract : le rendu en chaîne ne préserve pas les
   espacements visuels de façon cohérente (une même largeur d'écart entre
   deux colonnes peut ressortir en 1 espace à un endroit et en plusieurs à
   un autre). Sur la reconstitution testée, même après les deux corrections
   ci-dessus, aucune ligne ne se mappe correctement aux champs métier via
   cette heuristique. `pytesseract.image_to_data(...)` (positions en pixels
   de chaque mot, via `Output.DICT`) donne des coordonnées fiables et
   permettrait un vrai découpage en colonnes par position — mais c'est un
   changement d'architecture pour `lignes_depuis_texte` (qui prend
   aujourd'hui une chaîne de texte, pas des positions de mots), pas une
   simple correction. **Décision à prendre avant de poursuivre** : soit
   investir dans ce découpage par position (plus fiable, plus de code),
   soit accepter que l'OCR se limite à extraire le texte brut sans tenter de
   mapper les colonnes automatiquement (l'admin ressaisit manuellement —
   moins d'automatisation mais rien de plus fragile que ce qui existe déjà).

### Faciliter la publication pour les administrations (2026-07-04)

Trois évolutions livrées pour que les administrations (OCECOS, DGEC,
Fonction publique) publient plus vite et avec moins d'allers-retours avec
nous à chaque nouveau format de document :

1. **Modèle Excel téléchargeable** (`GET /api/v1/admin/ingestions/template`,
   `app/services/ingestion/template.py`) : classeur `.xlsx` généré à la
   volée avec les en-têtes exactes reconnues par le parser (Numéro PV,
   Jury, Nom, Prénom, Date de naissance, Décision, Moyenne, Établissement,
   N°CNIB) plus une ligne d'exemple. Bouton « Télécharger le modèle Excel »
   dans la section Import de l'admin. Garantit un parsing fiable dès le
   premier essai pour une administration qui n'a pas encore de fichier dans
   un format compatible, sans attendre une calibration de notre part.
2. **Colonnes non reconnues signalées explicitement.** Jusqu'ici,
   `erreurs_fichier` (calculé par les parsers pour "Fichier vide", "Aucun
   tableau détecté"...) n'était jamais exposé par l'API — un admin dont le
   fichier avait par exemple une colonne "Décision" mal nommée voyait juste
   "decision manquant" sur chaque ligne, sans indice sur la cause. Ajout de
   `colonnes_non_reconnues()` / `message_colonnes_non_reconnues()`
   (`normalizer.py`), utilisées par les 3 parsers, et d'une colonne
   `erreurs_fichier` sur `Ingestion` (migration `a3f8c1d92b47`) exposée dans
   `IngestionOut`. Affiché dans l'aperçu admin (bandeau ambre) : "Colonnes
   non reconnues, ignorées : X, Y." — l'admin peut renommer sa colonne et
   réessayer seul, sans nous solliciter.
3. **Option "PDF scanné (OCR)" désactivée dans le formulaire d'import**,
   avec info-bulle expliquant que le découpage en colonnes n'est pas encore
   fiable (voir calibrage OCR ci-dessus). Évite qu'un admin publie des
   données mal alignées en pensant le chemin fiable ; l'API backend
   continue d'accepter `PDF_OCR` techniquement, seule l'UI décourage son
   usage pour l'instant.

### Parser des communiqués scannés de la Fonction publique (2026-07-04)

Contexte détaillé dans `docs/CONTEXTE_METIER_maj.md` et
`docs/PARSER_PDF_FONCTION_PUBLIQUE.md` : les communiqués publiés sur
`fonction-publique.gov.bf` (concours directs) sont systématiquement des
**scans sans couche texte** (HP Scan, PaperStream), avec un format à 4
colonnes très stable (`RANG° | NOM ET PRÉNOM(s) | RÉCÉPISSÉ-CODE-CENTRE +
N°CNIB | DATE NAISS.`), très différent du tableau générique attendu par
`ocr_parser.py`. `docs/parser_poc.py` (fourni séparément, validé à 100% sur
2 PDF officiels 2025 : 7/7 et 120/120 résultats) a servi de base :

- **`app/services/parsers/pdf_type_detector.py`** — `detecter_type_pdf()`
  utilise `pdffonts` (poppler-utils, déjà dans le Dockerfile) : une sortie
  de 2 lignes ou moins (aucune police détectée) signale un scan.
- **`app/services/parsers/scan_pdf_parser.py`** — `parser_pdf_scan()`,
  adapté du POC pour s'intégrer au pipeline existant : réutilise
  `pdf2image` + `pytesseract` (`--psm 6`, cohérent avec le calibrage OCR
  ci-dessus) au lieu des appels `subprocess` bruts du POC, et produit des
  `LigneExtraite`/`ResultatExtraction` (types communs à tous les parsers)
  plutôt que les dataclasses `MetadonneesPdf`/`Resultat` du POC, pour
  passer par le même flux upload → aperçu → correction → publication.
  Détecte automatiquement la décision (`ADMISSIBLE`/`ADMIS`) depuis le
  titre du communiqué (repli sur `decision_par_defaut` si indétectable),
  et signale un écart dans `erreurs_fichier` si le nombre de lignes
  extraites ne correspond pas au total déclaré en pied de page (contrôle
  qualité principal recommandé par la spec).
- **Détection automatique dans `dispatch.py`** : `TypeFichier.PDF` route
  désormais vers `detecter_type_pdf()` puis vers `parser_pdf` (natif) ou
  `parser_pdf_scan` (scan) selon le résultat — l'admin choisit juste
  « PDF », sans avoir besoin de savoir à l'avance si le fichier est un
  scan (renommé dans `admin.html` : « PDF (texte ou scanné, détecté
  automatiquement) »).
- **Modèle `Resultat`** (migration `c7e2a4f91d05`) : nouveaux champs
  nullables `numero_recepisse`, `code_concours`, `code_centre`,
  `rang_numerique`, `rang_affiche` (voir tableau `resultats` ci-dessus).

**Écarts assumés par rapport à la spec fournie**, documentés ici pour
traçabilité :
- **Pas de renommage de `numero_pv` en `numero_recepisse`** (proposé en
  §8 point 8 de la spec) : changement invasif (API publique, frontend,
  tous les tests) non demandé explicitement cette session. `numero_pv`
  reste le champ utilisé par la recherche publique ; `numero_recepisse`
  stocke la même valeur sous le nom officiel du document, en plus.
- **Pas de `donnees_brutes_ligne` dédié** : la ligne OCR brute est stockée
  dans le `donnees_brutes` JSONB déjà existant (`{"ligne_ocr": "..."}`),
  cohérent avec la traçabilité déjà en place pour tous les autres parsers,
  plutôt qu'une colonne spécifique à ce seul parser.
- **Pas de `native_pdf_parser.py` ni d'abstraction `FileImportSource`**
  (proposés en §8 points 5-6 de la spec) : dupliqueraient respectivement
  `app/services/ingestion/pdf_parser.py` et `dispatch.py`, qui remplissent
  déjà ce rôle.
- **La refonte plus large de `CONTEXTE_METIER_maj.md`** (nouvel enum
  `TypeExamen` complet, `PhasePublication`, abstraction `ResultsSource`,
  modèles `Corps`/`Centre`/`Concours`, seed, README) n'a **pas** été
  entreprise cette session — hors périmètre de cette demande précise, à
  traiter séparément si demandé explicitement.

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

- **Portail unique cross-tenant, volontairement non filtré par
  administration** : un candidat consulte son résultat par numéro de PV sans
  connaître ni choisir une administration. Décision actée dans
  `docs/PIVOT_SAAS_B2G.md` § 2.6 (option A) — voir `docs/MULTI_TENANCY.md`
  § 3 pour la justification complète.
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
- **`candidat.html` + `js/candidat.js`** : espace candidat plateforme (voir
  § Profil candidat unifié ci-dessous). Inscription (CNIB + nom + date de
  naissance + téléphone + consentement), connexion et inscription passent
  toutes les deux par une étape de code OTP commune. Le token candidat est
  stocké en `localStorage` (pas `sessionStorage`) pour permettre la session
  persistante de 30 jours du § 4.2 de `docs/PROFIL_CANDIDAT_UNIFIE.md`.
  Dashboard : ajout d'une candidature (sélection d'un examen public +
  numéro de récépissé) et liste des candidatures avec statut de
  vérification. Ne couvre pas la confirmation par OTP du mécanisme 3
  (fallback, § 5) — le candidat voit sa candidature en attente mais
  l'endpoint `POST .../confirmer-otp` n'est pas encore relié à une UI.

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
tableau de bord). Le même filet de sécurité `.hidden` a été ajouté à
`candidat.html` et vérifié dans les mêmes conditions dégradées.

## Profil candidat unifié

Voir `docs/PROFIL_CANDIDAT_UNIFIE.md` pour la spécification complète et
`docs/APDP_PROFIL_CANDIDAT.md` pour la conformité APDP dédiée. Résumé
architectural :

- **Modèles** (`app/models/profil_candidat.py`, `app/models/candidature.py`,
  `app/models/journal_consultation_profil.py`) : vivent dans le schéma
  Postgres `plateforme`, distinct des schémas tenants (`administration_id`
  sur `Candidature` est une simple référence, sans FK cross-schéma). CNIB,
  téléphone et date de naissance sont chiffrés au repos
  (`app/models/encrypted_str.py`, Fernet/AES) ; `numero_cnib_hash` et
  `telephone_hash` (HMAC-SHA256, `app.core.security.hash_deterministe`)
  permettent la recherche/unicité sans jamais indexer la valeur en clair.
- **Auth candidat** (`app/services/candidat/auth_service.py`,
  `app/routes/candidat/auth.py`) : OTP SMS (stub d'envoi, code renvoyé en
  clair dans la réponse HTTP uniquement hors production — voir
  `settings.environment`), JWT dédié avec audience `candidat` (distincte de
  `admin` — `app/core/security.py`), session 30 jours
  (`CANDIDAT_JWT_EXPIRE_MINUTES`).
- **Vérification de propriété d'un récépissé**
  (`app/services/candidat/verification_service.py`) : CNIB automatique →
  date de naissance → fallback OTP, dans cet ordre (§5 de la spec).
- **Matching et notifications**
  (`app/services/candidat/matching_service.py`,
  `app/services/candidat/notification_engine.py`) : rapprochement
  rétroactif à l'inscription (résultats déjà publiés), rapprochement à la
  publication d'un examen (`app/routes/admin/exams.py::publish_exam`
  appelle `MatchingService.traiter_publication_examen`). L'envoi SMS reste
  un stub journalisé (voir `docs/ROADMAP.md`, Phase 2).
- **Isolation** : aucune route admin ne permet de lister les profils
  candidats ; un candidat ne peut jamais voir les candidatures d'un autre
  candidat — voir `tests/test_isolation_profil_candidat.py`.
- **Non implémenté à ce jour** (voir `docs/APDP_PROFIL_CANDIDAT.md` § 6) :
  détection d'abus avancée (seuil de 30 % de rejets), alerte de prise de
  contrôle de compte, purge automatique des comptes inactifs, traitement
  des candidatures orphelines à la résiliation d'une administration.

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
