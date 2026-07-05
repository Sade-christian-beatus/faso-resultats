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

# Migrations
alembic upgrade head

# Seed
python seed.py

# Démarrer l'API
uvicorn app.main:app --reload
```

## Tests

```powershell
cd backend
pytest
```

## Structure

```
faso-resultats/
├── backend/           FastAPI + SQLAlchemy
├── frontend/          HTML/CSS/JS vanilla
├── docs/              Documentation technique
└── docker-compose.yml
```

Voir `docs/ARCHITECTURE.md` pour le détail technique.
