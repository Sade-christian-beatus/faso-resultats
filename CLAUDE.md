# CLAUDE.md

> Ce fichier est lu automatiquement par Claude Code au démarrage de chaque session.
> Il maintient la cohérence du projet **Faso Résultats** dans le temps.
> Le placer à la racine du dépôt.

---

## Identité du projet

**Nom :** Faso Résultats
**Domaine :** Plateforme de consultation de résultats d'examens et concours nationaux du Burkina Faso
**Cible utilisateurs finaux :** candidats aux examens (CEP, BEPC, BAC) et concours directs de la Fonction publique, leurs parents, et les établissements scolaires
**Cible commerciale :** structures gouvernementales burkinabè (OCECOS, DGEC, Ministère de la Fonction publique, Ministère de la Transition digitale)
**Modèle envisagé :** convention public-privé, service financé par SMS surtaxés et/ou marché public

---

## Principes directeurs (à ne jamais oublier)

### 1. Contexte burkinabè avant tout
- Utilisateurs souvent sur **connexions 3G faibles ou instables**
- Beaucoup n'ont pas de smartphone → le canal SMS est aussi important que le web
- Français langue principale de l'interface, avec messages clairs et rassurants
- Les données personnelles des candidats sont **sensibles** : conformité APDP (Autorité de Protection des Données Personnelles du Burkina Faso) obligatoire
- Hébergement final sur **serveurs burkinabè** (souveraineté des données) → éviter les dépendances lourdes à AWS, GCP, Azure

### 2. Simplicité > sophistication
- Un code lisible qu'on comprend en 3 mois vaut mieux qu'un code astucieux
- Pas de sur-ingénierie : pas de microservices, pas d'event sourcing, pas de CQRS
- Monolithe modulaire FastAPI, découpé proprement par domaine
- Frontend web léger (objectif < 500 Ko chargés)

### 3. Robustesse en période de pic
- Le jour de la proclamation du BAC : potentiellement **des centaines de milliers de requêtes en quelques heures**
- Cache agressif obligatoire (Redis, fallback mémoire)
- Rate limiting sur toutes les routes publiques
- Prévoir la possibilité de servir les résultats en fichiers statiques via CDN si nécessaire
- Aucune requête publique ne doit dépasser 200 ms en cache chaud

### 4. Fiabilité des données = crédibilité
- Une erreur d'import = un candidat qui pense être ajourné alors qu'il est admis = perte totale de confiance
- **Validation humaine obligatoire avant toute publication**
- Tout import doit passer par : upload → prévisualisation → correction manuelle possible → publication explicite
- Traçabilité complète : chaque résultat doit pouvoir être remonté à son fichier source

### 5. Prêt pour la suite
- Le SMS (Orange, Moov, Telecel), l'app mobile Android/iOS, l'USSD, et l'API B2B viendront en phases ultérieures
- Le code doit **accueillir** ces extensions sans réécriture — prévoir les interfaces dès maintenant

---

## Stack technique (verrouillée)

| Couche | Choix | Notes |
|--------|-------|-------|
| Backend | FastAPI (Python 3.11+) | Async partout où pertinent |
| ORM | SQLAlchemy 2.0 | Style moderne (Mapped, mapped_column) |
| Migrations | Alembic | Autogénération autorisée mais toujours relire |
| Base de données | PostgreSQL 15+ | Via Supabase (self-hosted en dev, migration facile) |
| Cache | Redis | Fallback cache mémoire si indisponible |
| Rate limiting | slowapi | |
| Auth admin | JWT (python-jose + passlib/bcrypt) | Pas d'OAuth pour l'instant |
| Validation | Pydantic v2 | |
| Config | pydantic-settings + .env | |
| Parsing PDF natif | pdfplumber | |
| OCR | pytesseract + pdf2image + OpenCV | Langue française (`lang='fra'`) |
| Parsing Excel | openpyxl | |
| Tests | pytest + httpx | |
| Formatage | black (line length 100) + ruff | |
| Frontend web | HTML/CSS/JS vanilla + Tailwind CDN | Objectif < 500 Ko |
| Conteneurisation | Docker + docker-compose | Impératif pour portabilité |
| Versionnement | Git + GitHub (repo privé) | |

**Ne pas introduire de nouvelle dépendance majeure sans justification écrite dans le PR/commit.**

---

## Architecture logique

```
Utilisateur (web/mobile/SMS)
        ↓
    [ Cache Redis ]
        ↓
   [ API FastAPI ]
        ↓
   [ PostgreSQL ]
        ↑
[ Pipeline d'ingestion admin ]
        ↑
  Fichiers PDF / Excel officiels
```

**Séparation nette :**
- **Routes publiques** (`/api/v1/public/*`) : lecture seule, cachées, rate-limitées, ne renvoient que des examens publiés
- **Routes admin** (`/api/v1/admin/*`) : protégées par JWT, opérations d'écriture
- **Services** : logique métier isolée, testable sans base de données
- **Modèles** : SQLAlchemy, jamais utilisés directement dans les routes (passer par les schémas Pydantic)

---

## Modèle de données de référence

Tables principales : `examens`, `resultats`, `ingestions`, `admins`, `notifications_preinscription`.

**Voir `docs/ARCHITECTURE.md` pour le schéma détaillé** — le maintenir à jour à chaque modification.

**Index critiques** à ne pas oublier :
- `resultats (examen_id, numero_pv, jury)` — composite, requête principale de consultation
- `examens (statut, annee)` — pour filtrer les examens publiés récents
- `notifications_preinscription (examen_id, statut)` — pour l'envoi en masse

**Contraintes :**
- Un résultat sans `examen_id` valide est refusé
- Un examen en statut `DRAFT` n'est jamais visible côté public
- Les données brutes de la source sont conservées dans `donnees_brutes` (jsonb) pour audit

---

## Règles de développement

### Structure des routes
- Toujours documenter avec `summary` et `description` FastAPI
- Toujours typer les réponses avec `response_model`
- Toujours renvoyer des erreurs métier avec `HTTPException` et un `detail` en français côté public

### Nommage
- Fichiers Python : `snake_case`
- Classes : `PascalCase`
- Variables et fonctions : `snake_case`
- Constantes : `SCREAMING_SNAKE_CASE`
- Endpoints d'API : `/kebab-case` en anglais (ex: `/results`, `/pre-registrations`)
- Noms de tables : `snake_case` au pluriel, en français quand métier (`resultats`, `examens`)

### Français vs anglais
- **Interface utilisateur, messages d'erreur publics, noms de tables métier** : français
- **Code, commentaires techniques, docstrings, commits, docs techniques, noms de variables** : anglais
- **Endpoints API** : anglais (professionnel, permet d'exposer à des partenaires internationaux ensuite)

### Commits Git
- Format Conventional Commits : `feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`
- Messages en anglais
- Un commit = une intention claire

### Tests
- Objectif de couverture : **> 60% sur le backend**
- Tests obligatoires sur : parsers (PDF, Excel, OCR), authentification, endpoints publics de consultation, logique de publication
- Fixtures pytest pour données de test réutilisables

### Sécurité (non négociable)
- Aucun mot de passe en clair, jamais
- bcrypt pour les hashs
- Validation Pydantic stricte de tous les inputs
- Rate limiting sur toutes les routes publiques ET sur login admin (protection brute force)
- Aucun log de données personnelles sensibles (nom, date de naissance, téléphone)
- CORS restreint aux domaines connus en production
- Variables sensibles uniquement via `.env`, jamais dans le code

### Conformité APDP
- Collecter le minimum de données nécessaires
- Prévoir mécanisme de purge des données après période légale de conservation
- Documentation de traitement à jour dans `docs/APDP.md`
- Consentement explicite pour les notifications SMS (case à cocher, pas pré-cochée)

---

## Roadmap projet (rappel des phases)

| Phase | Contenu | Statut |
|-------|---------|--------|
| **Phase 1** | Fondations : API + base + ingestion + web public + admin minimal | ✅ Terminée (validée bout en bout, Docker Compose inclus) |
| **Phase 2** | Intégration SMS (Orange, Moov, Telecel), notifications proactives | 🔒 À venir |
| **Phase 3** | App mobile Android (Flutter ou React Native), espace établissement | 🔒 À venir |
| **Phase 4** | USSD, app iOS, API B2B, guide d'orientation | 🔒 À venir |
| **Phase 5** | Expansion sous-régionale UEMOA | 🔒 À venir |

**Phase 1 terminée.** Ne pas démarrer la Phase 2 (SMS) ou une phase suivante sauf demande explicite — l'architecture laisse déjà la porte ouverte (table `notifications_preinscription` créée dès la Phase 1).

---

## Interactions attendues avec Claude Code

### Ce que Claude Code doit faire
- Poser les questions bloquantes en début de session
- Proposer des choix techniques justifiés quand la latitude est laissée
- S'arrêter après chaque étape majeure pour faire un point
- Écrire des tests en même temps que le code, pas après
- Mettre à jour `docs/ARCHITECTURE.md` quand la structure évolue
- Utiliser des messages de commit Conventional Commits clairs

### Ce que Claude Code ne doit PAS faire
- Introduire une nouvelle dépendance majeure sans justification
- Créer des microservices, des couches d'abstraction inutiles, ou du code "juste au cas où"
- Utiliser une bibliothèque exotique quand la standard suffit
- Générer 2000 lignes de code sans point d'arrêt
- Modifier la stack imposée sans discussion préalable
- Ignorer les principes directeurs listés en haut de ce fichier
- Passer directement à une phase ultérieure (SMS, mobile) sans que je le demande

### Format des points d'arrêt
Après chaque étape majeure, produire un résumé structuré :
```
### Étape terminée : [nom]
- ✅ Ce qui a été fait
- 🧪 Comment tester
- 📝 Décisions techniques prises (avec justification)
- ⚠️ Points d'attention pour la suite
- 👉 Prochaine étape proposée
```

---

## Contexte du développeur

- **Développeur :** Sadé Christian, full-stack basé à Ouagadougou
- **Expérience :** FastAPI, Supabase, WordPress, JavaScript, Node.js, Python, PWA offline-first
- **Style préféré :** code lisible et bien structuré > code astucieux
- **Environnement dev :** Linux/macOS
- **Solo dev :** pas besoin de justifier chaque choix trivial, mais expliquer les choix structurants

---

## Ressources et références

- **APDP Burkina Faso :** https://www.cil.bf (à vérifier au moment de la conformité)
- **Opérateurs télécom :** Orange Burkina, Moov Africa Burkina Faso, Telecel Faso
- **Organismes d'examens :** OCECOS (Office Central des Examens et Concours du Secondaire), DGEC (Direction Générale des Examens et Concours)
- **Documentation FastAPI :** https://fastapi.tiangolo.com
- **Documentation SQLAlchemy 2.0 :** https://docs.sqlalchemy.org/en/20/

---

## Historique des décisions techniques importantes

> Section à maintenir à jour manuellement à chaque décision structurante.
> Format : date, décision, justification.

- **2026-07-03 — `date_naissance` et `lieu_naissance` exclus de l'API publique**
  (`/api/v1/public/results`). Le candidat retrouve déjà son résultat via son
  numéro de PV ; il n'a pas besoin de se voir confirmer sa date/lieu de
  naissance pour ça. Minimisation des données conforme à l'esprit APDP.
  Décision assumée sans étude produit formelle — à revoir si un usage
  démontre le besoin (ex. vérification d'identité renforcée).
- **2026-07-03 — Pas de second facteur anti-scraping en Phase 1** sur la
  recherche publique de résultat (numéro de PV + jury optionnel uniquement).
  Protection actuelle : rate limiting (30 req/min/IP par défaut) + absence
  de tout endpoint de liste/wildcard (il faut déjà connaître un numéro de PV
  précis, aucune énumération possible côté API). Jugé suffisant pour le
  volume et l'usage de la Phase 1. À réévaluer avant un déploiement à grande
  échelle (ex. jour de proclamation du BAC) : envisager une seconde donnée
  de vérification (date de naissance) ou un captcha si des abus sont
  constatés.

---

## Rappel final

**Ce projet n'est pas un exercice technique. Chaque ligne de code peut impacter un élève qui découvre son résultat.**

Fiabilité, clarté, simplicité, respect des données. Dans cet ordre.
