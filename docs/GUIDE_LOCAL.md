# Guide d'exploitation locale — Faso Résultats

Toutes les commandes pour lancer la plateforme sur un poste de développement,
gérer les comptes (admins, candidats, partenaires B2B) et changer les mots de
passe et secrets. Commandes écrites pour Linux/macOS (bash/zsh) ; les
équivalents Windows sont indiqués quand ils diffèrent.

> Toutes les commandes de ce guide ont été exécutées contre un vrai PostgreSQL 16
> et un vrai Redis le 2026-10-05 (chemin « sans Docker »). Le chemin Docker
> utilise exactement les mêmes commandes, préfixées par
> `docker compose exec backend`.

---

## Sommaire

1. [Vue d'ensemble](#1-vue-densemble)
2. [Premier lancement avec Docker (recommandé)](#2-premier-lancement-avec-docker-recommandé)
3. [Lancement sans Docker](#3-lancement-sans-docker)
4. [Comptes de démonstration](#4-comptes-de-démonstration)
5. [Gérer les comptes admin et les mots de passe](#5-gérer-les-comptes-admin-et-les-mots-de-passe)
6. [Administrations, utilisateurs de tenant et clés API (via l'API)](#6-administrations-utilisateurs-de-tenant-et-clés-api-via-lapi)
7. [Comptes candidats (connexion par OTP)](#7-comptes-candidats-connexion-par-otp)
8. [Changer les secrets et le mot de passe PostgreSQL](#8-changer-les-secrets-et-le-mot-de-passe-postgresql)
9. [Opérations courantes](#9-opérations-courantes)
10. [Tests et qualité](#10-tests-et-qualité)
11. [Application mobile](#11-application-mobile)
12. [Dépannage](#12-dépannage)
13. [Aide-mémoire](#13-aide-mémoire)

---

## 1. Vue d'ensemble

| Service | Rôle | URL locale |
|---|---|---|
| `frontend` (nginx) | Site public, espace admin, espace candidat | http://localhost:8080 |
| `backend` (FastAPI) | API | http://localhost:8000 |
| `db` (PostgreSQL 15) | Base de données | `localhost:5432` |
| `redis` | Cache, rate limiting, verrouillages | interne à Docker (non exposé) |

Pages utiles :

| Page | URL |
|---|---|
| Site public | http://localhost:8080 |
| Espace admin | http://localhost:8080/admin.html |
| Espace candidat | http://localhost:8080/candidat.html |
| Documentation interactive de l'API (Swagger) | http://localhost:8000/docs |
| Santé de l'API | http://localhost:8000/health |

---

## 2. Premier lancement avec Docker (recommandé)

**Prérequis :** Docker et Docker Compose (Docker Desktop sur macOS/Windows).

### 2.1 Créer la configuration `backend/.env`

Le fichier `backend/.env` n'est jamais commité. On part du modèle :

```bash
cp backend/.env.example backend/.env       # Windows : copy backend\.env.example backend\.env
```

Puis **générer la clé de chiffrement obligatoire** (l'application refuse de
démarrer sans elle). Sans Python installé sur la machine, on la génère dans une
image Python jetable :

```bash
docker run --rm python:3.11-slim sh -c \
  "pip -q install cryptography && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
```

Avec Python et `cryptography` installés localement :

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Coller la valeur obtenue dans `backend/.env` :

```dotenv
CANDIDAT_ENCRYPTION_KEY=<la clé générée>
```

Les autres valeurs de `.env.example` fonctionnent telles quelles en local. Pour
remplacer les secrets de développement (recommandé dès qu'on montre la
plateforme à quelqu'un), voir [§ 8](#8-changer-les-secrets-et-le-mot-de-passe-postgresql).

### 2.2 Démarrer les services

```bash
docker compose up --build -d     # construit l'image backend et démarre les 4 services
docker compose ps                # vérifier que tout est "running" / "healthy"
```

### 2.3 Créer le schéma de base et les données de démonstration

```bash
docker compose exec backend alembic upgrade head   # applique toutes les migrations
docker compose exec backend python seed.py         # comptes + examens de démonstration
```

`seed.py` est idempotent : le relancer ne duplique rien.

### 2.4 Vérifier

```bash
curl http://localhost:8000/health                  # → {"status":"ok"}
curl http://localhost:8000/api/v1/public/exams     # → liste des examens publiés
```

Puis ouvrir http://localhost:8080 et http://localhost:8080/admin.html.

### 2.5 Arrêter, redémarrer, tout remettre à zéro

```bash
docker compose stop              # arrête sans rien supprimer
docker compose start             # redémarre
docker compose down              # supprime les conteneurs, GARDE les données
docker compose down -v           # supprime AUSSI la base, Redis et les fichiers uploadés
```

Après un `down -v`, refaire [§ 2.2](#22-démarrer-les-services) et
[§ 2.3](#23-créer-le-schéma-de-base-et-les-données-de-démonstration).

Le code du backend est monté dans le conteneur avec `--reload` : une
modification d'un fichier Python est prise en compte sans redémarrage. Il faut
en revanche **reconstruire** après une modification de `requirements.txt` :

```bash
docker compose up --build -d backend
```

---

## 3. Lancement sans Docker

Utile pour déboguer le backend directement. Prérequis : Python 3.11+,
PostgreSQL 15+, Redis (facultatif : sans Redis, le cache bascule en mémoire),
et pour l'OCR `tesseract` (langue `fra`) + `poppler`.

### 3.1 Base de données

```bash
sudo -u postgres psql -c "CREATE USER faso WITH PASSWORD 'faso_secret';"
sudo -u postgres psql -c "CREATE DATABASE faso_resultats OWNER faso;"
```

### 3.2 Environnement Python

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows : venv\Scripts\activate
pip install -r requirements.txt
```

### 3.3 Configuration

```bash
cp .env.example .env
```

Dans `backend/.env`, remplacer les noms de services Docker par `localhost` et
le dossier d'upload par un dossier local :

```dotenv
DATABASE_URL=postgresql+asyncpg://faso:faso_secret@localhost:5432/faso_resultats
REDIS_URL=redis://localhost:6379/0
UPLOADS_DIR=./uploads
CANDIDAT_ENCRYPTION_KEY=<générée comme au § 2.1>
```

### 3.4 Migrations, données, démarrage

```bash
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

Le frontend est en HTML/JS statique : n'importe quel serveur statique suffit,
**sur le port 8080** (seule origine autorisée par `CORS_ORIGINS` en local).
Dans un second terminal, depuis la racine du dépôt :

```bash
python3 -m http.server 8080 --directory frontend/public
```

---

## 4. Comptes de démonstration

Créés par `backend/seed.py`. **Mot de passe commun : `ChangeMe123!`** — à changer
avant toute démonstration (voir [§ 5.2](#52-changer-un-mot-de-passe)).

### Espace admin (http://localhost:8080/admin.html)

| Compte | Email | Rôle | Périmètre |
|---|---|---|---|
| Super-admin | `superadmin@faso-resultats.bf` | `SUPER_ADMIN` | Toute la plateforme |
| Admin OCECOS | `admin@ocecos.bf` | `ADMIN_ADMINISTRATION` | BEPC 2026 |
| Admin Office du BAC | `admin@office-bac.bf` | `ADMIN_ADMINISTRATION` | BAC 2026 - Série D |
| Admin AGRE | `admin@agre.bf` | `ADMIN_ADMINISTRATION` | Concours direct catégorie A 2026 |

### Espace candidat (http://localhost:8080/candidat.html)

Connexion par numéro de téléphone + code OTP (voir [§ 7](#7-comptes-candidats-connexion-par-otp)) :

| Candidat | Téléphone |
|---|---|
| TRAORE Awa | `+22670000001` |
| KABORE Issa | `+22670000002` |
| SANOU Richard | `+22670000003` |

### Résultats consultables sur le site public

| Examen | N° PV | Jury |
|---|---|---|
| BEPC 2026 (OCECOS) | `000101`, `000102` | `Ouagadougou 1`, `Bobo-Dioulasso` |
| BAC 2026 - Série D (Office du BAC) | `000201`, `000202` | `Ouagadougou 1`, `Koudougou` |
| Concours direct catégorie A 2026 (AGRE) | `000015`, `000042` | `03` |

---

## 5. Gérer les comptes admin et les mots de passe

L'API ne propose **aucun endpoint** pour changer un mot de passe ou créer un
super-admin. Ces opérations passent par le script `backend/gerer_comptes.py`,
à lancer comme `seed.py`. Le mot de passe est toujours **demandé au clavier**
(deux fois), jamais passé en argument : il ne reste ni dans l'historique du
shell ni dans la liste des processus. Minimum 8 caractères.

Avec Docker, préfixer chaque commande par `docker compose exec backend` ;
sans Docker, la lancer depuis `backend/` avec le venv activé.

### 5.1 Lister les comptes

```bash
docker compose exec backend python gerer_comptes.py lister
```

```
admin@agre.bf                            ADMIN_ADMINISTRATION     agre            actif
admin@ocecos.bf                          ADMIN_ADMINISTRATION     ocecos          actif
admin@office-bac.bf                      ADMIN_ADMINISTRATION     office-bac      actif
superadmin@faso-resultats.bf             SUPER_ADMIN              (plateforme)    actif
```

### 5.2 Changer un mot de passe

```bash
docker compose exec backend python gerer_comptes.py mot-de-passe superadmin@faso-resultats.bf
# Nouveau mot de passe :
# Confirmer le mot de passe :
# Mot de passe de superadmin@faso-resultats.bf modifié.
```

Changer le mot de passe lève aussi un éventuel verrouillage du compte.

Pour changer tous les mots de passe de démonstration d'un coup :

```bash
for email in superadmin@faso-resultats.bf admin@ocecos.bf admin@office-bac.bf admin@agre.bf; do
  docker compose exec backend python gerer_comptes.py mot-de-passe "$email"
done
```

> Les jetons JWT déjà émis restent valables jusqu'à leur expiration
> (`JWT_EXPIRE_MINUTES`, 60 min par défaut) : il n'existe pas de révocation de
> jeton. Pour déconnecter tout le monde immédiatement, changer `JWT_SECRET_KEY`
> ([§ 8.1](#81-secrets-de-lapplication)).

### 5.3 Créer un nouveau super-admin

```bash
docker compose exec backend python gerer_comptes.py creer-super-admin \
  christian@faso-resultats.bf --nom "Sadé Christian"
```

Les comptes rattachés à une administration (admin, opérateurs, lecteur) se
créent eux via l'API, avec un compte super-admin : voir [§ 6.3](#63-créer-un-utilisateur-dans-une-administration).

### 5.4 Désactiver / réactiver un compte

```bash
docker compose exec backend python gerer_comptes.py desactiver admin@agre.bf
docker compose exec backend python gerer_comptes.py activer admin@agre.bf
```

Un compte désactivé ne peut plus se connecter (le message reste « Email ou mot
de passe incorrect », sans révéler que le compte existe). Il n'y a pas de
suppression de compte : désactiver suffit et préserve le journal d'audit.

### 5.5 Débloquer un compte verrouillé

Après 5 échecs de connexion (`ADMIN_LOGIN_MAX_TENTATIVES`), le compte est
verrouillé 15 minutes (`ADMIN_LOGIN_LOCKOUT_MINUTES`), message « Trop de
tentatives échouées ». Pour débloquer sans attendre :

```bash
docker compose exec backend python gerer_comptes.py debloquer admin@ocecos.bf
```

> Les opérations de `gerer_comptes.py` ne sont **pas** inscrites dans le
> journal d'audit (`audit_logs`) : c'est un outil d'exploitant, réservé à qui a
> accès au serveur.

---

## 6. Administrations, utilisateurs de tenant et clés API (via l'API)

Ces opérations sont réservées au **SUPER_ADMIN** et passent par l'API. Le plus
simple est Swagger : http://localhost:8000/docs → bouton **Authorize**. Les
commandes `curl` équivalentes sont données ci-dessous.

### 6.1 Obtenir un jeton super-admin

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/admin/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"superadmin@faso-resultats.bf","password":"ChangeMe123!"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

curl -s http://localhost:8000/api/v1/admin/me -H "Authorization: Bearer $TOKEN"
```

### 6.2 Lister / créer / modifier une administration

```bash
# Lister (récupérer l'id d'une administration)
curl -s http://localhost:8000/api/v1/admin/administrations -H "Authorization: Bearer $TOKEN"

# Créer
curl -s -X POST http://localhost:8000/api/v1/admin/administrations \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{
        "code": "dgec",
        "nom_officiel": "Direction Générale des Examens et Concours",
        "sigle": "DGEC",
        "ministere_tutelle": "Ministère de l'\''Éducation nationale",
        "contact_referent_nom": "À désigner",
        "contact_referent_email": "contact@dgec.bf",
        "contact_referent_telephone": "+22600000000"
      }'

# Changer le statut (PILOTE, ACTIF, SUSPENDU, RESILIE)
ADMIN_ID=<id de l'administration>
curl -s -X PATCH http://localhost:8000/api/v1/admin/administrations/$ADMIN_ID \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"statut":"ACTIF"}'
```

Une administration `SUSPENDU` ou `RESILIE` disparaît du site public et de l'API B2B.

### 6.3 Créer un utilisateur dans une administration

Rôles possibles : `ADMIN_ADMINISTRATION`, `OPERATEUR_INGESTION`,
`OPERATEUR_PUBLICATION`, `LECTEUR`.

```bash
curl -s -X POST http://localhost:8000/api/v1/admin/administrations/$ADMIN_ID/utilisateurs \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{
        "email": "operateur@ocecos.bf",
        "password": "UnMotDePasseSolide-2026",
        "nom_complet": "Opérateur OCECOS",
        "role": "OPERATEUR_INGESTION"
      }'
```

Le mot de passe passe ici en clair dans la commande : le changer ensuite avec
`gerer_comptes.py mot-de-passe` si la commande a été tapée sur une machine
partagée.

### 6.4 Partenaires B2B et clés API

```bash
# Créer un partenaire
curl -s -X POST http://localhost:8000/api/v1/admin/partenaires \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"nom":"Partenaire test","contact_nom":"Contact","contact_email":"contact@partenaire.bf"}'

# Émettre une clé (la clé en clair n'est affichée QU'UNE SEULE FOIS : la noter)
PARTENAIRE_ID=<id du partenaire>
curl -s -X POST http://localhost:8000/api/v1/admin/partenaires/$PARTENAIRE_ID/api-keys \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"tier":"STANDARD","quota_quotidien":1000}'

# Lister les clés d'un partenaire (préfixe seulement, jamais la clé complète)
curl -s http://localhost:8000/api/v1/admin/partenaires/$PARTENAIRE_ID/api-keys \
  -H "Authorization: Bearer $TOKEN"

# Révoquer une clé
curl -s -X POST \
  http://localhost:8000/api/v1/admin/partenaires/$PARTENAIRE_ID/api-keys/<api_key_id>/revoke \
  -H "Authorization: Bearer $TOKEN"

# Utiliser une clé (côté partenaire)
curl -s http://localhost:8000/api/v1/b2b/exams -H "X-API-Key: frb_live_..."
```

Une clé perdue ne se récupère pas : la révoquer et en émettre une nouvelle.

---

## 7. Comptes candidats (connexion par OTP)

Les candidats n'ont **pas de mot de passe** : ils se connectent avec leur
numéro de téléphone et un code à 6 chiffres. Aucun SMS n'est envoyé tant que la
Phase 2 n'est pas démarrée. **Hors production**, le code est renvoyé dans la
réponse de l'API (`code_otp_debug`), donc :

- **dans le navigateur** : outils de développement (F12) → onglet Réseau →
  réponse de la requête `login` ;
- **en ligne de commande** :

```bash
curl -s -X POST http://localhost:8000/api/v1/candidat/login \
  -H 'Content-Type: application/json' -d '{"telephone":"+22670000001"}'
# {"message":"Si un compte existe pour ce numéro, un code a été envoyé par SMS.","code_otp_debug":"971006"}

curl -s -X POST http://localhost:8000/api/v1/candidat/otp/verify \
  -H 'Content-Type: application/json' -d '{"telephone":"+22670000001","code":"971006"}'
```

Le code expire après 5 minutes (`CANDIDAT_OTP_EXPIRE_MINUTES`). Après 3 codes
faux (`CANDIDAT_OTP_MAX_TENTATIVES`), le numéro est bloqué 15 minutes ; pour le
débloquer en local sans attendre, vider Redis ([§ 9.4](#94-vider-le-cache-redis)).

Avec `ENVIRONMENT=production`, `code_otp_debug` n'est jamais renvoyé.

---

## 8. Changer les secrets et le mot de passe PostgreSQL

Après chaque modification de `backend/.env`, recréer le conteneur backend (un
simple `restart` ne relit pas `env_file`) :

```bash
docker compose up -d --force-recreate backend
```

Sans Docker : arrêter puis relancer `uvicorn`.

### 8.1 Secrets de l'application

Générer une valeur aléatoire :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
# ou : openssl rand -base64 48
```

| Variable | Conséquence d'un changement | Quand le changer |
|---|---|---|
| `JWT_SECRET_KEY` | Tous les admins et candidats sont déconnectés (jetons invalides) | Librement ; c'est la façon de « déconnecter tout le monde » |
| `API_KEY_PEPPER` | **Toutes les clés API B2B deviennent invalides** (à réémettre) | Avant d'avoir émis des clés |
| `CANDIDAT_HASH_PEPPER` | Les profils candidats ne sont plus retrouvables par téléphone/CNIB | Uniquement sur une base vide (avant `seed.py`) ou avec `down -v` |
| `CANDIDAT_ENCRYPTION_KEY` | **Toutes les données chiffrées deviennent illisibles** (CNIB, dates de naissance, téléphones, données brutes) | Uniquement sur une base vide ; il n'existe pas de rotation de clé |

Pour changer `CANDIDAT_HASH_PEPPER` ou `CANDIDAT_ENCRYPTION_KEY` en local, on
repart de zéro :

```bash
docker compose down -v
# modifier backend/.env
docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py
```

> ⚠️ Sauvegarder `CANDIDAT_ENCRYPTION_KEY` hors du serveur dès qu'il y a des
> données réelles : sa perte rend ces données définitivement illisibles.

### 8.2 Mot de passe PostgreSQL

Le mot de passe est défini à **trois** endroits qui doivent rester cohérents :

1. `POSTGRES_PASSWORD` dans `docker-compose.yml` (lu **uniquement** à la toute
   première création du volume) ;
2. le mot de passe réel dans PostgreSQL ;
3. `DATABASE_URL` dans `backend/.env`.

**Sur une base existante** (on garde les données) :

```bash
# 1. Changer le mot de passe dans PostgreSQL
docker compose exec db psql -U faso -d faso_resultats \
  -c "ALTER USER faso WITH PASSWORD 'NouveauMotDePassePg';"

# 2. Reporter la valeur dans backend/.env :
#    DATABASE_URL=postgresql+asyncpg://faso:NouveauMotDePassePg@db:5432/faso_resultats
# 3. Reporter la valeur dans docker-compose.yml (POSTGRES_PASSWORD), pour le jour
#    où le volume sera recréé.

# 4. Recharger le backend
docker compose up -d --force-recreate backend
```

**Sur une base neuve** : modifier `POSTGRES_PASSWORD` et `DATABASE_URL`, puis
`docker compose down -v && docker compose up -d` (et refaire migrations + seed).

Éviter les caractères `@ : / ? #` dans ce mot de passe : ils cassent
`DATABASE_URL` (ou les encoder, ex. `@` → `%40`).

### 8.3 Autres réglages courants de `backend/.env`

| Variable | Défaut | Rôle |
|---|---|---|
| `ENVIRONMENT` | `development` | `development`, `staging` ou `production`. En `production`, refuse de démarrer avec les secrets par défaut et masque le code OTP |
| `CORS_ORIGINS` | `http://localhost:8080` | Origines autorisées, séparées par des virgules |
| `JWT_EXPIRE_MINUTES` | `60` | Durée de session admin |
| `CANDIDAT_JWT_EXPIRE_MINUTES` | `43200` | Durée de session candidat (30 jours) |
| `CACHE_TTL_SECONDS` | `300` | Durée de cache des consultations publiques |
| `RATE_LIMIT_PUBLIC` | `30/minute` | Limite par IP sur les routes publiques |
| `RATE_LIMIT_LOGIN` | `5/minute` | Limite par IP sur la connexion admin |
| `MAX_UPLOAD_SIZE_MB` | `20` | Taille maximale d'un fichier importé |

Pour des tests intensifs en local, augmenter `RATE_LIMIT_PUBLIC` (ex.
`1000/minute`) évite les erreurs 429.

---

## 9. Opérations courantes

### 9.1 Journaux

```bash
docker compose logs -f backend          # suivre les logs de l'API
docker compose logs --tail=100 db       # 100 dernières lignes de PostgreSQL
```

### 9.2 Console PostgreSQL

```bash
docker compose exec db psql -U faso -d faso_resultats
```

Quelques requêtes utiles :

```sql
\dt                                                   -- tables
SELECT email, role, actif FROM utilisateurs;          -- comptes admin
SELECT code, statut FROM administrations;             -- tenants
SELECT libelle, statut FROM examens;                  -- examens
SELECT action, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 20;
```

Ne jamais modifier `mot_de_passe_hash` à la main : utiliser `gerer_comptes.py`.

### 9.3 Sauvegarde et restauration

```bash
docker compose exec -T db pg_dump -U faso -d faso_resultats > sauvegarde_$(date +%F).sql
docker compose exec -T db psql -U faso -d faso_resultats < sauvegarde_2026-10-05.sql
```

Une sauvegarde n'est utilisable qu'avec la même `CANDIDAT_ENCRYPTION_KEY` et le
même `CANDIDAT_HASH_PEPPER` : les sauvegarder ensemble.

### 9.4 Vider le cache Redis

Efface le cache, les compteurs de rate limiting et tous les verrouillages
(admin et OTP candidat). Sans conséquence sur les données.

```bash
docker compose exec redis redis-cli FLUSHALL
```

### 9.5 Migrations

```bash
docker compose exec backend alembic current          # version actuelle
docker compose exec backend alembic history          # historique
docker compose exec backend alembic upgrade head     # appliquer les nouvelles
docker compose exec backend alembic downgrade -1     # annuler la dernière
docker compose exec backend alembic revision --autogenerate -m "description"  # en créer une (toujours la relire)
```

### 9.6 Purge des données candidats (conformité CIL)

```bash
docker compose exec backend python purge_candidats.py
```

Supprime les candidatures orphelines expirées et les profils inactifs. En
production, à planifier quotidiennement par cron.

### 9.7 Modèle Excel d'import

Téléchargeable depuis l'espace admin, ou :

```bash
curl -s -o modele.xlsx http://localhost:8000/api/v1/admin/ingestions/template \
  -H "Authorization: Bearer $TOKEN"
```

---

## 10. Tests et qualité

```bash
docker compose exec backend pytest                         # suite complète
docker compose exec backend pytest --cov=app               # avec couverture
docker compose exec backend pytest tests/test_auth.py -v   # un fichier
docker compose exec backend ruff check .                   # lint
docker compose exec backend black --check .                # format (black . pour corriger)
```

Les tests utilisent SQLite en mémoire : ils ne touchent pas à la base locale.
La même vérification tourne en CI (`.github/workflows/backend-ci.yml`) à
chaque push touchant `backend/`.

---

## 11. Application mobile

Détail complet dans `mobile/README.md`. Résumé, avec le backend déjà lancé :

```bash
cd mobile
flutter pub get
flutter run --dart-define=ENV=dev                                              # émulateur Android
flutter run --dart-define=ENV=dev --dart-define=API_BASE_URL=http://192.168.1.20:8000  # téléphone sur le même Wi-Fi
flutter build apk --release
```

Remplacer `192.168.1.20` par l'adresse IP locale de l'ordinateur (`ip addr` ou
`ifconfig`). Connexion avec les téléphones de démonstration du [§ 4](#4-comptes-de-démonstration).

---

## 12. Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `RuntimeError: CANDIDAT_ENCRYPTION_KEY manquante ou invalide` | Clé absente ou mal copiée dans `backend/.env` | La générer ([§ 2.1](#21-créer-la-configuration-backendenv)) puis `docker compose up -d --force-recreate backend` |
| `ENVIRONMENT=production mais JWT_SECRET_KEY… garde sa valeur de développement` | Secrets par défaut en mode production | Les remplacer ([§ 8.1](#81-secrets-de-lapplication)) ou repasser en `development` |
| `password authentication failed for user "faso"` | `DATABASE_URL` ne correspond plus au mot de passe PostgreSQL | Voir [§ 8.2](#82-mot-de-passe-postgresql) |
| `relation "..." does not exist` | Migrations non appliquées | `docker compose exec backend alembic upgrade head` |
| Admin : « Email ou mot de passe incorrect » avec le bon mot de passe | Compte désactivé | `gerer_comptes.py lister` puis `activer` |
| Admin : « Trop de tentatives échouées » | Compte verrouillé | `gerer_comptes.py debloquer <email>` |
| Erreur 429 sur le site public | Rate limiting | Attendre 1 minute, vider Redis, ou augmenter `RATE_LIMIT_PUBLIC` |
| Le site s'affiche mais aucune donnée (erreur CORS dans la console) | Frontend servi sur un autre port que 8080 | Servir le frontend sur 8080, ou ajouter l'origine à `CORS_ORIGINS` |
| `port is already allocated` (5432, 8000 ou 8080) | Un autre service occupe le port | Arrêter le service local (ex. `sudo systemctl stop postgresql`) ou changer le port publié dans `docker-compose.yml` |
| Une modification de `.env` n'est pas prise en compte | `docker compose restart` ne relit pas `env_file` | `docker compose up -d --force-recreate backend` |
| Examen publié invisible sur le site | Cache public (5 min max) ou administration suspendue | Vider Redis ; vérifier le statut de l'administration |

---

## 13. Aide-mémoire

```bash
# Premier lancement
cp backend/.env.example backend/.env           # puis renseigner CANDIDAT_ENCRYPTION_KEY
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python seed.py

# Comptes admin
docker compose exec backend python gerer_comptes.py lister
docker compose exec backend python gerer_comptes.py mot-de-passe <email>
docker compose exec backend python gerer_comptes.py creer-super-admin <email> --nom "Nom"
docker compose exec backend python gerer_comptes.py desactiver|activer|debloquer <email>

# Quotidien
docker compose logs -f backend
docker compose exec db psql -U faso -d faso_resultats
docker compose exec redis redis-cli FLUSHALL
docker compose exec backend pytest

# Remise à zéro complète
docker compose down -v
```
