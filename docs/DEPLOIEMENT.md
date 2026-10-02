# Mise en production

> Procédure complète pour installer Faso Résultats sur un serveur (VPS) avec
> HTTPS. Testée de bout en bout le 2026-10-02 avec Docker (stack de
> production réelle, certificat auto-signé à la place de Let's Encrypt) :
> redirection HTTPS, en-têtes de sécurité, proxy `/api`, limitation de débit
> par visiteur, création du super-admin, sauvegarde **et restauration**.

## Vue d'ensemble

```
Internet ──► nginx (service "web", ports 80/443 — seul service exposé)
               ├─ fichiers du site (frontend/public)
               └─ /api/* ──► API FastAPI (service "backend", 2 workers)
                                ├─ PostgreSQL (service "db")
                                └─ Redis (cache + compteurs de limitation)
```

Fichiers concernés :

| Fichier | Rôle |
|---------|------|
| `docker-compose.prod.yml` | Stack de production |
| `deploy/production.env.example` | Modèle des réglages et secrets (à copier en `deploy/production.env`, jamais commité) |
| `deploy/nginx/` | Serveur web : HTTPS, en-têtes de sécurité, cache, proxy `/api` |
| `deploy/sauvegarde.sh` | Sauvegarde quotidienne (base + fichiers sources) |
| `backend/creer_super_admin.py` | Création du premier compte super-admin |

## 1. Prérequis

- Un serveur Linux (Ubuntu 22.04/24.04 ou Debian 12), **2 vCPU / 4 Go de RAM
  minimum** (l'OCR des PDF scannés est gourmand), 40 Go de disque.
  Hébergement burkinabè conseillé (souveraineté des données, voir
  `docs/ROADMAP.md` § hébergement — piste IKA Cloud).
- Un accès root (ou sudo) au serveur.
- Un nom de domaine (ex. `fasoresultats.bf`) dont l'enregistrement **A**
  pointe vers l'adresse IP du serveur.
- Ports 80 et 443 ouverts vers le serveur (pare-feu de l'hébergeur).

## 2. Installer Docker sur le serveur

```bash
curl -fsSL https://get.docker.com | sh
docker compose version   # doit afficher une version 2.x ou plus
```

## 3. Récupérer le code et préparer les réglages

```bash
git clone <url-du-depot> /opt/faso-resultats
cd /opt/faso-resultats
cp deploy/production.env.example deploy/production.env
chmod 600 deploy/production.env
```

Remplir **toutes** les valeurs de `deploy/production.env` :

```bash
openssl rand -hex 24    # POSTGRES_PASSWORD
openssl rand -hex 32    # JWT_SECRET_KEY, puis CANDIDAT_HASH_PEPPER, puis API_KEY_PEPPER (une valeur différente pour chacun)
docker run --rm python:3.11-slim sh -c \
  "pip install -q cryptography && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
                         # CANDIDAT_ENCRYPTION_KEY
```

⚠️ **Conserver une copie de `CANDIDAT_ENCRYPTION_KEY` hors du serveur**
(enveloppe scellée, gestionnaire de mots de passe). Sans elle, les données
chiffrées des candidats (CNIB, date de naissance, téléphone) sont
**définitivement illisibles**, sauvegardes comprises.

L'API refuse de démarrer si un secret garde sa valeur de développement :
c'est voulu.

## 4. Obtenir le certificat HTTPS (première fois)

Le site n'est pas encore démarré : le port 80 est libre pour Let's Encrypt.

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/production.env \
  run --rm --service-ports certbot certonly --standalone \
  -d fasoresultats.bf --email contact@exemple.bf --agree-tos --no-eff-email
```

(Remplacer le domaine et l'e-mail ; le domaine doit être exactement celui de
`DOMAINE`.)

## 5. Démarrer la plateforme

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/production.env up -d --build
docker compose -f docker-compose.prod.yml --env-file deploy/production.env ps
```

Attendu : `db`, `redis`, `backend` en `healthy`, `migrate` en `Exited (0)`
(les migrations de la base ont été appliquées), `web` en `Up`.

## 6. Créer le premier compte super-admin

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/production.env \
  run --rm backend python creer_super_admin.py
```

Le mot de passe (12 caractères minimum) est saisi sans s'afficher. **Ne
jamais lancer `seed.py` en production** : il crée des administrations, des
résultats fictifs et des comptes au mot de passe public.

Ensuite, depuis `https://<domaine>/admin.html` : créer les administrations
clientes et leurs comptes admin.

## 7. Vérifier

```bash
curl -I http://fasoresultats.bf             # 301 vers https://
curl -s https://fasoresultats.bf/health     # {"status":"ok"}
curl -sI https://fasoresultats.bf | grep -i -E "strict-transport|content-security"
```

Et depuis un téléphone : ouvrir `https://<domaine>`, faire une recherche.

## 8. Renouvellement automatique du certificat

Les certificats Let's Encrypt durent 90 jours. Tâche `cron` du serveur
(`crontab -e`), deux fois par jour :

```cron
17 3,15 * * * cd /opt/faso-resultats && docker compose -f docker-compose.prod.yml --env-file deploy/production.env run --rm certbot renew --webroot -w /var/www/certbot --quiet && docker compose -f docker-compose.prod.yml --env-file deploy/production.env exec web nginx -s reload
```

## 9. Sauvegardes

```cron
40 2 * * * /opt/faso-resultats/deploy/sauvegarde.sh /var/backups/faso-resultats >> /var/log/faso-sauvegarde.log 2>&1
```

Le script sauvegarde la base (`pg_dump`) et les fichiers sources officiels,
garde 30 jours, et s'arrête en erreur si une sauvegarde est vide. **Copier
régulièrement `/var/backups/faso-resultats` hors du serveur** (autre machine,
disque externe) : une sauvegarde restée sur le même disque disparaît avec lui.

Restaurer la base (à tester au moins une fois, avant d'en avoir besoin) :

```bash
docker compose -f docker-compose.prod.yml --env-file deploy/production.env exec -T db \
  pg_restore -U faso -d faso_resultats --clean --if-exists < /var/backups/faso-resultats/base-AAAAMMJJ-HHMM.dump
```

## 10. Mettre à jour la plateforme

```bash
cd /opt/faso-resultats
deploy/sauvegarde.sh                      # toujours une sauvegarde avant
git pull
docker compose -f docker-compose.prod.yml --env-file deploy/production.env up -d --build
```

Les migrations s'appliquent automatiquement (service `migrate`) avant le
redémarrage de l'API.

## Choix de sécurité de cette configuration

- **Seul nginx est exposé.** La base, Redis et l'API ne publient aucun port :
  ils ne sont joignables que depuis le réseau Docker interne.
- **Limitation de débit par visiteur réel.** nginx remplace l'en-tête
  `X-Forwarded-For` par l'adresse réelle du client (jamais celle envoyée par
  le client), l'API le lit (`--proxy-headers`), et les compteurs sont
  partagés dans Redis entre les workers. Vérifié : un visiteur bloqué après
  30 requêtes/minute ne peut pas contourner la limite en falsifiant l'en-tête,
  et un autre visiteur n'est pas bloqué.
- **Politique de sécurité du contenu (CSP) stricte** : toutes les ressources
  (CSS, polices, scripts, images) viennent de la plateforme elle-même ; aucun
  script ou style inline n'est autorisé.
- **HTTPS obligatoire** (redirection + HSTS d'un an), TLS 1.2/1.3 uniquement.
- La documentation interactive de l'API (`/docs`) n'est pas exposée sur
  Internet.
- L'API tourne sous un utilisateur non-root dans son conteneur.

## Ce qui reste à la charge de l'exploitant

- Les mises à jour de sécurité du système du serveur (`apt upgrade`).
- La copie des sauvegardes hors du serveur.
- La surveillance (au minimum : alerte si `https://<domaine>/health` ne
  répond plus).
