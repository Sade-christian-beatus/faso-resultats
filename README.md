# Faso Résultats

Plateforme de consultation de résultats d'examens nationaux du Burkina Faso (CEP, BEPC, BAC, concours de la Fonction publique).

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

Identifiants admin par défaut : `admin@faso-resultats.bf` / `ChangeMe123!`

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
