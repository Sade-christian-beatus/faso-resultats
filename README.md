# Faso Résultats

Faso Résultats — la plateforme SaaS de publication des résultats d'examens et
concours pour les administrations burkinabè. Chaque administration cliente
(OCECOS, Office du BAC, AGRE, etc.) dispose de son propre espace : elle importe
ses résultats, les valide, et les publie sous sa propre identité, pendant que
les candidats consultent leur résultat par numéro de PV sur un portail unique.

Voir `docs/PIVOT_SAAS_B2G.md` pour le positionnement détaillé et
`docs/MULTI_TENANCY.md` pour l'architecture d'isolation entre administrations.
Le CEP est hors périmètre (couvert par SIGEC-CEP) ; voir `docs/CONTEXTE_METIER.md`
pour la cartographie complète du paysage concurrentiel.

## Configuration obligatoire

L'application **refuse de démarrer** sans ces variables (`backend/.env`, jamais
commité) :

| Variable | Rôle | Génération |
|---|---|---|
| `JWT_SECRET_KEY` | Signature des tokens admin et candidat | Chaîne aléatoire quelconque |
| `CANDIDAT_ENCRYPTION_KEY` | Chiffrement au repos (CNIB, téléphone, date de naissance du profil candidat) | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CANDIDAT_HASH_PEPPER` | Pepper des hash de recherche (CNIB, téléphone) | Chaîne aléatoire quelconque |

`CANDIDAT_ENCRYPTION_KEY` doit être une **vraie clé Fernet** (32 octets
base64 url-safe) : sans elle, ou avec une valeur invalide, `app.config.get_settings()`
lève une `RuntimeError` explicite au premier import de l'application (donc
avant même de démarrer `uvicorn`, `alembic` ou `seed.py`). Ne jamais réutiliser
la même clé entre environnements (dev/staging/prod), ne jamais la committer en
clair.

`JWT_SECRET_KEY` et `CANDIDAT_HASH_PEPPER` ont une valeur par défaut de
développement (`change-me-in-production`, publique dans le code source) pour
que l'app démarre sans `.env` local. **Ce défaut est refusé si
`ENVIRONMENT=production`** (audit 2026-07-08, `app.config._valider_secrets_production`)
: un déploiement production qui oublierait de les surcharger ne démarre pas
plutôt que de tourner silencieusement avec des secrets publics (tokens
forgeables, pepper de hash connu).

## Démarrage rapide (Docker)

**Prérequis :** Docker Desktop installé et démarré sur Windows 11.

```powershell
# 1. Cloner le dépôt
git clone <repo-url>
cd faso-resultats

# 2. Lancer tous les services
docker compose up --build -d

# 3. Appliquer les migrations
docker compose exec backend alembic upgrade head

# 4. Peupler la base avec des données de test
docker compose exec backend python seed.py
```

Les services disponibles :

| Service   | URL                         |
|-----------|-----------------------------|
| Frontend  | http://localhost:8080        |
| Admin     | http://localhost:8080/admin.html |
| API docs  | http://localhost:8000/docs   |
| Health    | http://localhost:8000/health |

Depuis un téléphone sur le même Wi-Fi : `http://<IP du PC>:8080` (nginx
transmet `/api` au backend, comme en production).

**Mise en production** (serveur, HTTPS, sauvegardes) : voir
[`docs/DEPLOIEMENT.md`](docs/DEPLOIEMENT.md). Ne jamais lancer `seed.py` en
production.

Identifiants créés par le seed (voir `backend/seed.py`) :

| Compte | Email | Mot de passe |
|--------|-------|--------------|
| Super-admin plateforme | `superadmin@faso-resultats.bf` | `ChangeMe123!` |
| Admin OCECOS | `admin@ocecos.bf` | `ChangeMe123!` |
| Admin Office du BAC | `admin@office-bac.bf` | `ChangeMe123!` |
| Admin AGRE | `admin@agre.bf` | `ChangeMe123!` |

## Développement local sans Docker

```powershell
# Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate   # Windows

cd backend
pip install -r requirements.txt

# Copier la config
copy .env.example .env
# Adapter DATABASE_URL pour pointer vers votre PostgreSQL local
# Générer une vraie clé pour CANDIDAT_ENCRYPTION_KEY (obligatoire, voir ci-dessus) :
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ... puis coller le résultat dans .env

# Migrations
alembic upgrade head

# Seed
python seed.py

# Démarrer l'API
uvicorn app.main:app --reload
```

## Styles du site web

Le CSS des pages (`frontend/public/css/app.css`) est pré-généré avec Tailwind.
Après toute modification du HTML, du JS ou de `frontend/src/app.css` :

```bash
cd frontend
npm install        # une seule fois
npm run build:css  # ou npm run watch:css pendant le développement
```

Committer `public/css/app.css` : la CI échoue s'il n'est pas à jour.

## Tests

```powershell
cd backend
pytest
```

Les tests d'OCR nécessitent `tesseract` (avec la langue `fra`) et `poppler`
installés sur la machine, comme dans l'image Docker. `CANDIDAT_ENCRYPTION_KEY`
doit être définie (dans `backend/.env` ou l'environnement).

Chaque push touchant `backend/` déclenche la CI (`.github/workflows/backend-ci.yml`) :
`ruff` + `black --check`, la suite `pytest` avec une couverture minimale de
60 %, et les migrations Alembic sur un vrai PostgreSQL 16 (upgrade, `alembic
check`, downgrade complet, ré-upgrade).

## Structure

```
faso-resultats/
├── backend/           FastAPI + SQLAlchemy
├── frontend/          HTML/CSS/JS vanilla (CSS Tailwind pré-généré)
├── deploy/            Production : nginx, réglages, sauvegarde
├── docker-compose.prod.yml
├── docs/              Documentation technique
└── docker-compose.yml
```

Voir `docs/ARCHITECTURE.md` pour le détail technique.
