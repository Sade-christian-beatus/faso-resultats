# Multi-tenancy

> Architecture d'isolation multi-tenant introduite par le pivot SaaS B2G
> (voir `docs/PIVOT_SAAS_B2G.md`). Un tenant = une administration cliente
> (OCECOS, Office du BAC, AGRE, etc.).

## 1. Modèle retenu

**Schéma partagé + colonne `administration_id`** sur chaque table métier,
et non des schémas ou bases séparés par tenant (`docs/PIVOT_SAAS_B2G.md`
§ 2.1). Justification : nombre de tenants modeste (dizaines, pas
milliers), volumétrie par tenant faible, et une seule base à opérer reste
cohérent avec le principe directeur « pas de sur-ingénierie » du projet.

## 2. Les deux entités clés

### `Administration`
Un tenant. Champs notables : `code` (identifiant technique unique,
slug), `nom_officiel`, `sigle`, `ministere_tutelle`, personnalisation
(`logo_url`, `couleur_primaire`, `domaine_personnalise`), contact
référent, `plan_abonnement`, `statut` (`ACTIF` / `SUSPENDU` / `PILOTE` /
`RESILIE`).

**Visibilité publique selon le statut** : seules les administrations `ACTIF`
et `PILOTE` (`STATUTS_ADMINISTRATION_VISIBLES`) apparaissent côté public et B2B
— liste des administrations, examens (`/exams`) et résultats (`/results`).
Un tenant `SUSPENDU` ou `RESILIE` disparaît entièrement de ces routes (un
résultat recherché renvoie le même 404 qu'un examen non publié, sans révéler
le statut). Les listes en cache sont invalidées au changement de statut ; une
recherche de résultat déjà en cache peut rester servie jusqu'à
`cache_ttl_seconds` (5 min par défaut). Une réactivation (`ACTIF`) rend tout à
nouveau visible, rien n'est supprimé.

### `Utilisateur` (anciennement `Admin`)
Tout compte de connexion à l'espace admin. `administration_id` est
**nullable** — c'est le seul cas où NULL est légitime dans tout le
schéma multi-tenant, réservé aux rôles plateforme :

| Rôle | `administration_id` | Portée |
|------|---------------------|--------|
| `SUPER_ADMIN` | NULL | Équipe Faso Résultats, accès plateforme |
| `SUPPORT` | NULL | Support client, lecture seule tous tenants |
| `ADMIN_ADMINISTRATION` | requis | Dirigeant du tenant, tous droits sur son périmètre |
| `OPERATEUR_INGESTION` | requis | Importe et corrige les résultats |
| `OPERATEUR_PUBLICATION` | requis | Publie / dépublie |
| `LECTEUR` | requis | Consultation interne uniquement |

## 3. Tables tenant-scopées

`examens`, `ingestions`, `resultats`, `notifications_preinscription`
portent toutes une colonne `administration_id` (FK `administrations.id`,
`ON DELETE CASCADE`, NOT NULL). Chacune a un index composite ou simple
sur `administration_id` pour que le filtrage par tenant reste performant
(`ix_examens_administration_statut`, `ix_ingestions_administration_created`,
`ix_resultats_administration`).

**Exception délibérée : les routes publiques de consultation**
(`app/routes/public/results.py`) ne sont **pas** filtrées par tenant —
c'est un portail unique cross-tenant assumé (`docs/PIVOT_SAAS_B2G.md`
§ 2.6, option A retenue pour le MVP). Un candidat cherche un résultat par
numéro de PV sans avoir à connaître ni choisir une administration.

## 4. Mécanisme d'isolation

Pas de middleware ASGI global : l'isolation passe par une dépendance
FastAPI, cohérente avec le reste du code qui utilise déjà `Depends()`
pour l'auth.

```
get_current_utilisateur()   # décode le JWT, charge l'Utilisateur (déjà existant)
        ↓
get_current_administration()  # app/core/deps.py
```

`get_current_administration()` :
1. Dépend de `get_current_utilisateur()`.
2. Si `utilisateur.administration_id is None` → `HTTPException(400)` —
   un compte plateforme (SUPER_ADMIN/SUPPORT) n'a pas d'administration
   à filtrer et ne peut donc pas utiliser les routes tenant-scopées en
   l'état (voir § 6 « Limites actuelles »).
3. Sinon, charge l'`Administration` correspondante et la renvoie.

Chaque route admin tenant-scopée déclare
`administration: Administration = Depends(get_current_administration)`
et l'utilise pour :
- **Filtrer les listes** : `where(Table.administration_id == administration.id)`.
- **Filtrer les accès unitaires** via un helper `_get_<ressource>_ou_404`
  (`app/routes/admin/exams.py`, `app/routes/admin/ingestions.py`) qui
  compare `ressource.administration_id != administration.id`.
- **Renseigner `administration_id`** à la création de toute nouvelle
  ressource.

## 5. Règle d'or : 404, jamais 403

Une ressource d'un autre tenant renvoie **404** ("introuvable"), jamais
403 ("interdit"). Un 403 confirme l'existence de la ressource à un
attaquant qui devine un UUID ; un 404 ne révèle rien. C'est le même
comportement quel que soit le vecteur d'accès (URL manipulée, JWT valide
mais d'un autre tenant, etc.) : dans tous les cas, la ressource n'existe
tout simplement pas du point de vue de l'administration courante.

## 6. Limites actuelles (assumées, à lever si besoin)

- **Journal d'audit** (`AuditLog`, `app/models/audit_log.py`) : trace login,
  création/publication d'examen, upload/correction/publication/rejet
  d'ingestion, création/modification d'administration, avec `utilisateur_id`,
  `administration_id`, action, timestamp, IP. Les FK utilisent
  `ondelete="SET NULL"` (pas `CASCADE`) pour que l'historique survive à la
  suppression de l'entité référencée.
- **Endpoints super-admin** pour gérer les `Administration` via l'API
  (`POST/GET/PATCH /api/v1/admin/administrations`, `POST .../utilisateurs`
  pour provisionner le premier `ADMIN_ADMINISTRATION` d'un tenant) — voir
  `app/routes/admin/administrations.py`. `seed.py` reste utile pour amorcer
  un environnement de développement, mais n'est plus le seul chemin.
- Pas encore de **restructuration des routes** vers l'arborescence cible
  de la section 2.5 du pivot (`/api/v1/auth/login`, `/api/v1/me`,
  `/api/v1/administrations`, namespace public par `administration_code`)
  — différé (`docs/PIVOT_SAAS_B2G.md` § 8, item 7). Les routes actuelles
  (`/api/v1/admin/exams`, `/api/v1/admin/ingestions`) restent
  fonctionnellement tenant-scopées, seule la convention d'URL n'a pas
  encore été alignée.
- Un compte `SUPER_ADMIN`/`SUPPORT` ne peut aujourd'hui **pas du tout**
  utiliser les routes admin tenant-scopées (il reçoit un 400) : il n'y a
  pas encore de mécanisme d'« impersonation » ou de sélection explicite
  d'un tenant pour le support. À construire avec les endpoints
  super-admin ci-dessus.

## 7. Tests d'isolation

`backend/tests/test_isolation_multi_tenant.py` couvre, pour un opérateur
de l'administration A tentant d'agir sur des ressources de
l'administration B :

- lister les examens (`GET /api/v1/admin/exams`) : ne voit que les siens
- publier un examen d'un autre tenant (`POST .../publish`) : 404
- uploader une ingestion sur un examen d'un autre tenant : 404
- lire, corriger, publier, rejeter une ingestion d'un autre tenant : 404
  dans tous les cas
- lister les ingestions : ne voit que celles de son propre tenant
- un compte sans `administration_id` (rôle plateforme) reçoit 400 sur
  les routes tenant-scopées

Fixtures : `tests/conftest.py` fournit `admin_headers` (tenant
`tenant-test`) et `autre_administration_headers` (tenant `autre-tenant`)
pour tout nouveau test d'isolation à écrire.
