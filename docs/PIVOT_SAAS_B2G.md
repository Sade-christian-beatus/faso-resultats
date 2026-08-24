# PIVOT STRATÉGIQUE — Modèle SaaS B2G multi-tenant

> À intégrer au projet dans `docs/PIVOT_SAAS_B2G.md`.
> Cette note **remplace** partiellement les positionnements antérieurs et introduit un changement d'architecture majeur.

---

## 1. Nouveau positionnement du projet

### Ce que devient Faso Résultats
Une **plateforme SaaS destinée aux administrations publiques burkinabè** chargées de délibérer et de publier les résultats d'examens et de concours nationaux. Chaque administration dispose de son propre compte dédié, gère ses propres examens, ses propres opérateurs, publie ses propres résultats sous sa propre identité visuelle.

### Ce que Faso Résultats N'EST PLUS
- Une plateforme publique agrégatrice qui ingère des PDF pour le compte des candidats
- Un service B2C direct auprès des candidats
- Un concurrent frontal des ministères ou de SIGEC

### Ce que Faso Résultats DEVIENT
- Un **prestataire technique** pour les administrations organisatrices
- Un **outil interne** que ces administrations utilisent pour piloter leurs publications
- L'**infrastructure invisible** derrière plusieurs plateformes gouvernementales de consultation

### Retrait du périmètre CEP
Le CEP est retiré du périmètre projet. Raisons :
- SIGEC-CEP couvre déjà cette fonction pour le MEBAPLN
- Aller reproduire cette capacité serait perçu comme un doublon inutile
- Le focus sur BEPC, BAC, examens professionnels et concours reste largement suffisant en termes de marché

### Administrations cibles (chacune = un tenant potentiel)

| Administration | Périmètre | Statut |
|----------------|-----------|--------|
| **OCECOS** — Office Central des Examens et Concours du Secondaire | BEPC | Cible prioritaire |
| **Office du BAC** (nom exact à confirmer) | Baccalauréat général, technologique, professionnel | Cible prioritaire |
| **DGEC** — Direction Générale des Examens et Concours | Coordination générale, examens professionnels | Cible potentielle |
| **AGRE** — Agence Générale de Recrutement de l'État (MFPTPS) | Concours directs Fonction publique | Cible prioritaire |
| **DRH Ministère de la Santé** | Concours du personnel de santé (dentistes, ingénieurs biomédicaux, etc.) | Cible secondaire |
| **École Nationale de Police** (ENP) | Concours Police Nationale | Cible secondaire |
| **État-major Général des Armées** | Concours Armée et Gendarmerie | Cible secondaire (cycle de vente long) |
| **Direction Générale des Douanes** | Concours Douanes | Cible secondaire |
| **DGEP (Sécurité Pénitentiaire)** | Concours GSP | Cible secondaire |
| **Direction des Eaux et Forêts** | Concours Eaux et Forêts | Cible secondaire |
| **Écoles nationales** (ENAM, ENEP, ENAREF, etc.) | Concours d'entrée respectifs | Cible tertiaire |

---

## 2. Impact sur l'architecture technique

### 2.1 — Multi-tenancy dès le départ

Le système doit être **multi-tenant** dès le MVP. Approche recommandée : **schéma partagé + colonne `administration_id`** sur toutes les tables métier.

**Justification du choix :**
- Simple à mettre en œuvre (pas de multiplication de schémas ou de bases)
- Suffisant en isolation pour des données non concurrentielles entre tenants
- Permet des évolutions faciles (ajout de nouveaux tenants sans migration lourde)
- Compatible avec Supabase / PostgreSQL standard

**Isolation stricte à garantir :**
- Toute requête métier filtre automatiquement sur `administration_id`
- Utiliser un middleware qui injecte l'administration courante dans le contexte de la requête
- Tests d'isolation obligatoires : jamais un opérateur d'administration A ne doit voir un résultat d'administration B

### 2.2 — Nouveau modèle `Administration`

```python
class Administration(Base):
    """Un tenant du SaaS = une administration publique cliente."""
    id: uuid (PK)
    code: str                       # slug interne, ex: "ocecos", "office-bac"
    nom_officiel: str               # "Office Central des Examens et Concours du Secondaire"
    sigle: str                      # "OCECOS"
    ministere_tutelle: str
    logo_url: str | None            # branding personnalisé
    couleur_primaire: str | None    # thème visuel personnalisé
    domaine_personnalise: str | None  # ex: resultats.ocecos.bf en Phase 2
    contact_referent_nom: str
    contact_referent_email: str
    contact_referent_telephone: str
    date_signature_convention: date | None
    convention_active: bool
    plan_abonnement: enum           # STARTER / STANDARD / PREMIUM
    quota_sms_mensuel: int
    quota_examens_annuel: int
    statut: enum                    # ACTIF / SUSPENDU / PILOTE / RESILIE
    created_at, updated_at
```

### 2.3 — Refonte des utilisateurs

Le modèle `admins` initial devient trop simple. Il faut distinguer plusieurs rôles :

```python
class Utilisateur(Base):
    id: uuid (PK)
    administration_id: uuid | None (FK)   # NULL pour super-admins Faso Résultats
    email: str (unique)
    mot_de_passe_hash: str
    nom_complet: str
    telephone: str | None
    role: RoleUtilisateur                  # voir enum ci-dessous
    actif: bool
    derniere_connexion: timestamp | None
    created_at, updated_at

class RoleUtilisateur(str, Enum):
    # Rôles Faso Résultats (plateforme)
    SUPER_ADMIN = "SUPER_ADMIN"            # équipe Faso Résultats, accès total multi-tenant
    SUPPORT = "SUPPORT"                     # support client, lecture seule sur tous les tenants

    # Rôles administration (tenant)
    ADMIN_ADMINISTRATION = "ADMIN_ADMINISTRATION"   # dirigeant de l'administration, tous droits sur son tenant
    OPERATEUR_INGESTION = "OPERATEUR_INGESTION"     # importe et valide les résultats
    OPERATEUR_PUBLICATION = "OPERATEUR_PUBLICATION" # décide de publier / dépublier
    LECTEUR = "LECTEUR"                             # consultation interne uniquement
```

**Séparation des pouvoirs importante côté administration** : celui qui importe les données ne doit pas forcément être celui qui les publie officiellement. C'est un principe de gouvernance apprécié dans le secteur public.

### 2.4 — Toutes les tables métier gagnent un `administration_id`

Ajouter `administration_id` (FK NOT NULL) sur :
- `examens`
- `resultats`
- `ingestions`
- `notifications_preinscription`
- Toute nouvelle table métier

Index à créer :
- `(administration_id, statut)` sur `examens`
- `(administration_id, examen_id, numero_recepisse)` sur `resultats`
- `(administration_id, created_at)` sur `ingestions`

### 2.5 — API restructurée par tenant

Les routes admin passent d'un modèle flat à un modèle scoped :

```
POST   /api/v1/auth/login                    # authentification universelle
GET    /api/v1/me                            # utilisateur courant + son administration
GET    /api/v1/administrations               # (super-admin uniquement) liste des tenants

# Routes scoped sur l'administration courante (déduite du JWT)
GET    /api/v1/admin/examens
POST   /api/v1/admin/examens
POST   /api/v1/admin/ingestions/upload
GET    /api/v1/admin/utilisateurs
POST   /api/v1/admin/utilisateurs
GET    /api/v1/admin/statistiques

# Routes publiques scoped par sous-domaine ou paramètre
GET    /api/v1/public/{administration_code}/examens
GET    /api/v1/public/{administration_code}/resultats
```

### 2.6 — Consultation publique multi-tenant

Deux options possibles, à choisir avec Sadé :

**Option A — Un portail unique Faso Résultats.** Une seule URL (`fasoresultats.bf`), l'utilisateur sélectionne d'abord l'administration (OCECOS, Office du BAC, AGRE...), puis son examen. Simple, peu coûteux, mais dilue la marque de chaque administration.

**Option B — Portails cobrandés par administration.** Chaque administration a son propre sous-domaine (`resultats.ocecos.bf`, `bac.education.bf`) avec son logo et ses couleurs. Techniquement, c'est le même moteur avec un middleware qui identifie le tenant depuis le sous-domaine et applique le thème. Plus complexe mais **beaucoup plus vendeur** face au ministère.

**Recommandation :** implémenter l'**Option A dans le MVP** (simple), avec l'architecture prête pour l'**Option B en phase 2** (thème par administration déjà en base, il ne reste qu'à câbler les sous-domaines).

---

## 3. Impact sur le modèle économique

### Nouveau modèle de facturation

Passage d'un modèle B2C flou à un modèle B2G structuré à trois piliers :

**a) Abonnement SaaS annuel par administration**

| Plan | Cible | Prix indicatif FCFA/an |
|------|-------|------------------------|
| STARTER | Petite administration, 1-3 examens/an, <5 000 candidats | 3 000 000 à 5 000 000 |
| STANDARD | Administration moyenne, jusqu'à 20 000 candidats | 8 000 000 à 12 000 000 |
| PREMIUM | Grande administration (Office BAC, AGRE), >50 000 candidats, features avancées | 20 000 000 à 30 000 000 |

**b) Facturation à l'usage SMS**

Modèle à la consommation, refacturé par-dessus le coût opérateur avec marge : ~50 FCFA / SMS envoyé aux candidats. À la charge de l'administration cliente (peut ou non le répercuter sur les candidats via SMS surtaxés).

**c) Prestations d'intégration**

Setup initial, formation des opérateurs, personnalisation graphique, connexion à d'autres SI de l'administration : 2 à 5 millions FCFA par déploiement.

### Projection révisée sur 3 ans

Hypothèse conservatrice : 1 administration cliente en année 1, 3 en année 2, 6 en année 3.

| | Année 1 | Année 2 | Année 3 |
|--|---------|---------|---------|
| Nombre de tenants | 1 (pilote gratuit) | 3 | 6 |
| Revenus abonnement | 0 | ~24 000 000 | ~60 000 000 |
| Revenus SMS | ~3 000 000 | ~15 000 000 | ~35 000 000 |
| Revenus intégration | 0 | ~10 000 000 | ~20 000 000 |
| **Revenu total** | **~3 000 000** | **~49 000 000** | **~115 000 000** |

Le modèle SaaS est **plus rentable et plus prévisible** que l'ancien modèle B2C. La seule difficulté est le cycle de vente long (6 à 18 mois par administration).

### Pilote gratuit — stratégie inchangée mais recadrée

Proposition à faire à la première administration cible (idéalement OCECOS pour le BEPC 2027) :
- Déploiement gratuit pour une session
- En échange : convention de partenariat, droit de communiquer, engagement de considérer un contrat pérenne si le pilote fonctionne
- Une fois OCECOS convaincu, effet domino attendu vers Office du BAC, AGRE, etc.

---

## 4. Impact sur les canaux de sortie (SMS, mobile, web)

### Le SMS reste un différenciateur clé

Chaque administration peut activer le canal SMS pour ses examens. Deux modèles techniques possibles :

- **Numéro court partagé** (ex: `3737`) : le candidat envoie `OCECOS 12345` ou `BAC 67890`, le premier mot identifie l'administration. Économique, mais moins branded.
- **Numéros courts dédiés** : chaque administration a son propre numéro court (ex: `3730` pour OCECOS, `3731` pour Office BAC). Plus cher mais chaque administration garde son identité.

**Recommandation MVP :** numéro court unique partagé, avec préfixe d'identification. Passage en dédié possible en phase 2 pour les gros clients.

### L'app mobile devient multi-tenant

L'app publique doit permettre à l'utilisateur de :
- Chercher tous ses résultats à travers toutes les administrations en une seule action (via CNIB ou numéro de récépissé)
- Configurer des alertes par administration

Techniquement, cela suppose une API publique unifiée qui interroge tous les tenants en respectant la visibilité (résultats publiés uniquement).

---

## 5. Impact sur le pipeline d'ingestion

Le pipeline reste largement le même (voir `PARSER_PDF_FONCTION_PUBLIQUE.md`), mais :

1. **Chaque ingestion est isolée par administration.** Un opérateur OCECOS ne peut jamais uploader un PDF pour l'Office BAC.
2. **Les templates de parsing sont scoped par administration.** L'AGRE a un format PDF standardisé (celui qu'on a analysé) ; OCECOS aura probablement le sien. Prévoir une table `TemplateParsing` liée à chaque administration.
3. **La validation reste locale à l'administration.** Chaque administration valide et publie ses propres résultats en autonomie.

### Nouveau modèle `TemplateParsing`

```python
class TemplateParsing(Base):
    id: uuid (PK)
    administration_id: uuid (FK)
    nom: str                        # "PDF AGRE Concours Directs 2025"
    type_source: enum               # SCAN_PDF, NATIVE_PDF, EXCEL
    regex_lignes: str               # regex à appliquer
    regex_metadata: json            # dict de regex pour extraire header/footer
    prétraitement_ocr: json         # config OpenCV (deskew, denoise, etc.)
    exemples_pdf_urls: list[str]    # PDF de référence pour tests
    version: int
    actif: bool
```

Cela permet à chaque administration de calibrer son propre template sans affecter les autres, et à Faso Résultats de proposer une bibliothèque de templates prêts à l'emploi.

---

## 6. Impact sur la conformité CIL

Le nouveau modèle **clarifie considérablement** la position vis-à-vis de la CIL (Commission de l'Informatique et des Libertés, l'autorité burkinabè de protection des données à caractère personnel) :

- **Faso Résultats est sous-traitant au sens de la réglementation CIL**, pas responsable de traitement
- Chaque administration reste **responsable de traitement** de ses propres données
- Une **convention de sous-traitance conforme aux exigences de la CIL** doit être signée avec chaque administration cliente (obligatoire, non négociable)
- Faso Résultats fournit des **garanties techniques** : chiffrement au repos, chiffrement en transit, isolation multi-tenant, journal des accès, purge sur demande, notification en cas de violation
- Chaque administration conserve la **maîtrise éditoriale** : quand publier, quoi publier, quoi purger

Cela simplifie énormément le rendez-vous avec la CIL et la communication institutionnelle.

---

## 7. Priorisation actualisée du MVP

Avec ce pivot, la priorité n°1 change : ce n'est plus la consultation publique la plus jolie, c'est **l'espace administration le plus solide**.

### Nouveau MVP (fonctions essentielles)

1. **Modèle multi-tenant** complet avec middleware d'isolation
2. **Gestion des utilisateurs** avec les 5 rôles définis
3. **Espace administration** : création d'examens, upload de PDF, validation, publication
4. **Pipeline d'ingestion PDF-scan** (parser Fonction Publique déjà validé, extensible)
5. **Consultation publique unifiée** (Option A : portail unique avec sélection d'administration)
6. **Journal d'audit** de toutes les actions sensibles (obligation CIL)

### Repoussé en phase 2

- SMS multi-opérateurs
- App mobile
- Portails cobrandés par administration (Option B)
- Notifications proactives
- Templates de parsing custom par administration (le parser générique suffit au départ)
- Statistiques publiques agrégées

### Repoussé en phase 3

- USSD
- API B2B pour partenaires tiers (médias, écoles)
- Analytics et BI par administration
- Automatisation OCR avancée (surveillance de PDF publiés par scraper)

---

## 8. Ce que Claude Code doit intégrer concrètement

Priorité : refondre l'architecture actuelle en multi-tenant AVANT d'aller plus loin sur les fonctionnalités.

1. **Créer le modèle `Administration`** avec tous les champs listés en section 2.2
2. **Renommer et refondre le modèle `admins`** en `Utilisateur` avec le nouvel enum `RoleUtilisateur`
3. **Ajouter `administration_id` (FK NOT NULL)** sur tous les modèles métier existants
4. **Créer un middleware `TenantMiddleware`** qui :
   - Extrait l'administration courante du JWT à chaque requête admin
   - Injecte l'objet `Administration` dans le contexte de la requête FastAPI
   - Refuse toute requête admin sans administration (sauf pour SUPER_ADMIN)
5. **Créer un dependency FastAPI `get_current_administration()`** utilisé dans toutes les routes admin
6. **Adapter toutes les requêtes SQLAlchemy** existantes pour filtrer sur `administration_id` automatiquement
7. **Restructurer les routes** selon la nouvelle arborescence de la section 2.5
8. **Créer les endpoints super-admin** pour gérer les administrations (CRUD `Administration` + création utilisateur initial ADMIN_ADMINISTRATION)
9. **Mettre à jour le seed** pour créer :
   - 1 super-admin Faso Résultats
   - 3 administrations : OCECOS, Office BAC, AGRE
   - 1 utilisateur ADMIN_ADMINISTRATION par tenant
   - 1 examen par administration avec quelques résultats fictifs
10. **Supprimer le CEP** de toutes les seed data et documentations
11. **Ajouter un journal d'audit** (`AuditLog`) qui trace : login, création/modif utilisateur, upload de PDF, publication, dépublication, avec `user_id`, `administration_id`, action, timestamp, IP
12. **Créer `docs/MULTI_TENANCY.md`** documentant l'architecture multi-tenant, les règles d'isolation, les tests d'isolation à écrire
13. **Écrire des tests d'isolation** obligatoires : vérifier qu'un opérateur d'administration A ne peut EN AUCUN CAS accéder aux données de l'administration B (même par manipulation de paramètres, JWT falsifié, etc.)
14. **Mettre à jour `README.md`** avec le nouveau pitch : *"Faso Résultats — la plateforme SaaS de publication des résultats d'examens et concours pour les administrations burkinabè."*

### Ce qui reste inchangé

- Stack technique (FastAPI, PostgreSQL, Redis, etc.)
- Pipeline d'ingestion PDF (le parser Fonction Publique reste pertinent)
- Contraintes de performance et de sécurité
- Hébergement sur serveurs burkinabè
- Conformité CIL (mais clarifiée : sous-traitance au lieu de responsable direct)

---

## 9. Questions ouvertes à trancher rapidement

1. **Nommage du domaine** : `fasoresultats.bf` en portail unifié, ou repositionnement en nom plus "infrastructure" (`resultats-bf.com`, `deliverance.bf`, etc.) ? Le nouveau modèle B2G peut justifier un nom moins grand public.

2. **Modèle de facturation SMS** : refacturé au coût réel + marge, ou forfait mensuel inclus dans l'abonnement ? À arbitrer avec les premiers prospects.

3. **Structure juridique** : SARL ou SAS ? Le B2G préfère souvent les SAS pour leur souplesse et leur crédibilité "société de tech". À valider avec un conseil juridique.

4. **Politique de données historiques** : quand une administration résilie son contrat, que devient l'historique de ses résultats déjà publiés ? Suppression, export, migration ? À clarifier dans le contrat type.

---

*Fin de la note de pivot — version 1.0.*
