# Roadmap — Faso Résultats

> Document de planification. Aucune phase suivante ne doit être démarrée sans
> demande explicite (règle rappelée dans `CLAUDE.md`), même si les choix
> techniques ci-dessous sont déjà tranchés.

## ✅ Livré

- Fondations FastAPI + PostgreSQL + Redis + Docker
- Pipeline d'ingestion PDF avec OCR (Tesseract fra) et parser scan Fonction publique
- Multi-tenancy strict (schéma partagé + `administration_id`), voir `docs/MULTI_TENANCY.md`
- Isolation vérifiée par tests dédiés (tenant-à-tenant et candidat-à-candidat)
- Profil candidat unifié (schéma `plateforme` séparé), voir `docs/PROFIL_CANDIDAT_UNIFIE.md`
- Inscription OTP SMS (stub), dashboard candidat, session 30 jours
- Matching automatique par CNIB (rétroactif à l'inscription et proactif à la publication)
- Chiffrement au repos (Fernet) du CNIB/téléphone/date de naissance, hash déterministe
  pour la recherche — clé de chiffrement désormais obligatoire au démarrage (pas de
  valeur par défaut fonctionnelle), voir `README.md` § Configuration obligatoire
- AuditLog complet (qui a fait quoi, quand, sur quel tenant) sur les actions
  d'authentification et d'ingestion admin
- Endpoints super-admin API pour gérer les `Administration` et provisionner le premier
  utilisateur d'un nouveau tenant (`POST /api/v1/admin/administrations/*`)
- Verrouillage OTP réellement temporisé (clé de verrouillage dédiée, indépendante de la
  génération d'un nouveau code — voir `AuthCandidatService`)
- Détection d'abus (seuil de candidatures rejetées → suspension automatique du profil,
  `candidat_abus_taux_rejet_suspension`)
- Alerte de prise de contrôle de compte (SMS immédiat au numéro utilisé pour créer un
  compte)
- Purge des candidatures orphelines à la résiliation d'une administration (marquage
  immédiat + suppression après 6 mois) et des comptes candidat inactifs
  (`purge_candidats.py`, à planifier via cron — pas de file de tâches en Phase 1)
- UI candidat pour le mécanisme 3 de vérification (fallback OTP quand ni le CNIB ni la
  date de naissance ne figurent dans le résultat publié)
- Fondation API B2B (Phase 4, § dédiée ci-dessous) : modèles `Partenaire`/`ApiKey`,
  gestion super-admin, routes `/api/v1/b2b/exams` et `/api/v1/b2b/results` avec quota
  par clé — pas encore de facturation ni de contrat partenaire réel
- **2026-09-28** — Charte graphique officielle et logo appliqués au web, à l'app mobile
  et aux icônes d'app (`docs/CHARTE_GRAPHIQUE.md`)
- **2026-09-28** — CI backend (lint, tests avec couverture minimale, migrations sur
  PostgreSQL réel) et CI mobile étendue au build APK release
- **2026-09-28** — Points d'audit fermés : chiffrement au repos de la CNIB, de la date
  et du lieu de naissance dans `resultats` (et des copies brutes `donnees_brutes` /
  `apercu_donnees`) ; administrations `SUSPENDU`/`RESILIE` masquées côté public et B2B
- **2026-09-28** — Publication par phase opérationnelle (concours paramilitaires) :
  phase choisie à l'import, ordre imposé, clôture explicite des phases, parcours
  candidat phase par phase (`GET /api/v1/public/results/progress`) — voir
  `docs/ARCHITECTURE.md` § Phases de publication
- **2026-09-28** — Page publique : examens disponibles en bande défilante, résultats
  en frise par phase

## 🚧 En cours / à faire avant un lancement pilote réel

- Restructuration des routes vers l'arborescence cible (`docs/PIVOT_SAAS_B2G.md` § 2.5)
- Intégration réelle des passerelles SMS (Orange Business en priorité, voir détail
  technique ci-dessous) — l'envoi reste un stub journalisé
- Durées de rétention (`candidat_purge_inactivite_jours`, 2 ans par défaut) non
  validées par la CIL — voir `docs/CIL_PROFIL_CANDIDAT.md` § 5

## 📅 Phase 2 — Intégration SMS et notifications proactives

**Objectif :** notifier un candidat par SMS dès que son résultat est publié.

**Fournisseur retenu : Orange Business, offre « API SMS » (sans engagement).**

**2026-08-17 — Grille tarifaire et conditions consultées sur le site Orange Business.**
Confirme que l'API SMS et l'USSD (Phase 4) sont bien **deux offres distinctes** chez
ce fournisseur, pas un seul contrat — la question laissée ouverte plus haut est
tranchée.

| Volume | Durée | Prix unitaire TTC |
|---|---|---|
| 100 SMS | 7 jours | 9 F |
| 1 000 SMS | 30 jours | 8 F |
| 5 000 SMS | 30 jours | 18 F |
| 10 000 SMS | 30 jours | 17 F |

⚠️ Le palier « 5 000 SMS » (18 F) est plus cher que le palier inférieur (1 000 SMS,
8 F) et le palier supérieur (10 000 SMS, 17 F) — ne suit pas la dégressivité attendue
par volume. Probable coquille sur la page Orange, à faire confirmer avant de
bâtir un budget dessus. Le prix de revente prévu (~50 F/SMS, `docs/PIVOT_SAAS_B2G.md`
§ 3) laisse dans tous les cas une marge confortable sur ces tarifs.

**Conditions à réunir pour souscrire** (documents à fournir à la demande) :
- Courriel de demande du client, RCCM, IFU, pièce d'identité du premier responsable
- Selon le statut du souscripteur : récépissé (association/fondation/ONG), **acte de
  création** (structure publique), accord de siège (représentation diplomatique), ou
  attestation d'ordre professionnel (profession libérale)
- Contrat d'1 an avec tacite reconduction

**⚠️ Nouveau point bloquant identifié : RCCM et IFU supposent une structure
juridique enregistrée.** Faso Résultats n'en a pas encore (voir `docs/PIVOT_SAAS_B2G.md`
§ 9, SARL/SAS non tranché) — la question de la structure juridique n'est donc plus
une simple case à cocher mais un **prérequis pour signer ce contrat**. Deux options :
créer la structure avant de signer, ou faire souscrire directement par la première
administration cliente (OCECOS) au titre de « structure publique » (acte de création),
Faso Résultats opérant alors l'intégration technique pour son compte.

**File de tâches retenue : RQ** (Redis Queue) — Redis est déjà dans la stack (cache),
RQ s'appuie dessus sans nouvelle brique d'infrastructure.

Ce qui existe déjà côté code, prêt à être branché à un vrai fournisseur :
- `NotificationEngine.envoyer_sms()` (stub actuel, à remplacer)
- `NotificationEngine.formater_message_resultat()` (format du message, déjà utilisé)
- La table `notifications_preinscription` (historique, hors profil candidat unifié)

Étapes techniques restantes : client Orange Business derrière l'interface
`envoyer_sms(numero, message) -> bool` déjà en place, worker RQ dédié (nouveau service
`docker-compose.yml`), retry sur échec, garde-fou de quota mensuel, report différé
d'une notification tombant dans la plage silencieuse 22h-6h (aujourd'hui abandonnée,
pas mise en file).

## 🟡 Phase 3 — Application mobile Android puis iOS, espace établissement (démarrée, partielle)

**Mise à jour du 2026-08-17 (audit) :** ce chantier a en fait déjà démarré (12
commits `feat(mobile)` mergés sur `main`) sans que cette page ne soit tenue à jour.
État réel :

- ✅ App Flutter (`mobile/`) : authentification candidat (OTP), dashboard, ajout/
  retrait de candidature, consultation rapide sans compte, cache hors-ligne des
  résultats déjà consultés. Réutilise l'API candidat (`/api/v1/candidat/*`) et
  publique (`/api/v1/public/*`) existante.
- 🔒 Notifications push et consultation par SMS : écrans présents mais
  volontairement désactivés (`gated`), dépendants de la Phase 2 (SMS) non
  démarrée.
- 🔒 Build release Android : infrastructure de signature en place, pas de
  keystore de production généré. iOS jamais testé (pas d'environnement Xcode
  disponible en session).
- ✅ **2026-09-28** : la release Android déclare enfin la permission `INTERNET`
  (sans elle, un APK release ne joignait pas l'API) ; HTTP local autorisé en debug
  uniquement (API de dev en `http://`) ; build release vérifié en CI. Procédure de
  lancement détaillée dans `mobile/README.md`.
- 📅 Brancher l'app sur `GET /api/v1/public/results/progress` pour afficher
  « publication en cours » / « ne figure pas sur la liste » (l'app affiche déjà la
  phase et la prochaine étape via `/results`).
- 📅 Espace établissement : pas commencé — nouvelle table normalisée +
  vérification automatique contre une liste officielle d'établissements (liste
  des établissements privés déjà reçue, liste des établissements publics
  encore à obtenir).
- 📅 Portails cobrandés par administration (sous-domaines dédiés) — alternative
  ou complément au portail unique actuel (`docs/PIVOT_SAAS_B2G.md` § 2.6, option
  A) : pas commencé.

## 🟡 Phase 4 — USSD, API B2B (fondation API B2B démarrée)

**2026-08-17 :** l'USSD reste bloqué par le même prérequis que la Phase 2 (contrat
Orange Business, non signé). La fondation technique de l'**API B2B**, elle,
n'en dépendait pas — démarrée sur demande explicite pendant l'attente du contrat :

- ✅ Modèles `Partenaire`/`ApiKey` : clé en clair générée une seule fois (jamais
  stockée, seul son hash HMAC — pepper dédié `api_key_pepper`, distinct de celui du
  candidat), préfixe non sensible pour l'identification.
- ✅ Endpoints super-admin `POST/GET/PATCH /api/v1/admin/partenaires`,
  `POST /api/v1/admin/partenaires/{id}/api-keys`, `.../revoke` — gestion
  transversale (pas liée à une administration cliente), cohérent avec le modèle
  actuel des `Administration`.
- ✅ Routes `GET /api/v1/b2b/exams`, `GET /api/v1/b2b/results` : mêmes champs que
  l'API publique (pas d'accès élargi aux données sensibles pour l'instant — décision
  du 2026-08-17), authentifiées par `X-API-Key`, quota quotidien par clé (compteur
  cache, non atomique — comme le verrouillage OTP candidat) au lieu d'un rate-limit
  par IP.
- 🔒 Pas de facturation automatisée : `tier`/`quota_quotidien` configurables
  manuellement par le SUPER_ADMIN à l'émission de la clé, grille tarifaire toujours
  non tranchée.
- 📅 USSD (Orange Business, offre « USSD » — distincte de l'API SMS, voir Phase 2) :
  candidat compose un code, entre son numéro de PV, reçoit sa décision à l'écran —
  pertinent pour les téléphones basiques et zones à connectivité limitée. Toujours
  bloqué par le contrat opérateur, avec des prérequis plus lourds qu'un simple
  abonnement API :
  - **Code USSD dédié à obtenir auprès de l'ARCEP** (régulateur télécom burkinabè) —
    démarche administrative distincte du contrat Orange lui-même, à démarrer tôt car
    son délai n'est pas connu.
  - **Connexion sécurisée dédiée (HTTPS ou VPN)**, avec des frais de mise en place
    significatifs : 500 000 F (mise en service) + 200 000 F (VPN) + 400 000 F/mois
    (internet dédié 2 Mbps) — un engagement d'infrastructure, pas juste un abonnement.
  - Coût à la transaction, une fois en service : 2 F/transaction USSD ; 1 F/SMS on-net
    et 2 F/SMS off-net pour les SMS envoyés via ce canal (tarification différente de
    l'offre API SMS de la Phase 2).
  - Mêmes conditions administratives que l'API SMS (RCCM/IFU ou acte de création,
    voir Phase 2) pour souscrire.

## Hors périmètre (décisions actées le 2026-07-03)

- **CEP (Certificat d'Études Primaires)** : couvert par la plateforme officielle
  SIGEC-CEP, ne fait pas partie du périmètre Faso Résultats.
- **Guide d'orientation** : supprimé du périmètre.
- **Expansion sous-régionale UEMOA** : supprimée. Faso Résultats reste un produit
  mono-pays (Burkina Faso) de façon permanente.

## Chantiers transverses (indépendants des phases)

1. **Validation juridique de `docs/CIL.md` et `docs/CIL_PROFIL_CANDIDAT.md`** —
   plusieurs points (base légale, responsable de traitement, durée de conservation)
   explicitement marqués comme non tranchés.

   **2026-08-29 — Premier rendez-vous à la CIL effectué.** Deux actions concrètes
   demandées, à traiter avant toute mise en production réelle :
   - **Déclaration en ligne obligatoire** sur le portail CIL, formulaire
     « collecte de données sur site web » :
     https://plainte-declaration.cil.bf/statements/create/website-data-collection.
     Cette déclaration attend probablement les mêmes informations que celles déjà
     réunies dans `docs/CIL.md` (finalités, catégories de données, mesures de
     sécurité, durée de conservation, responsable de traitement) — reste à
     confirmer le contenu exact des champs du formulaire une fois ouvert.
   - **Démarche complémentaire auprès de l'ANSSI** (Agence Nationale de Sécurité
     des Systèmes d'Information, https://anssi.bf/) pour obtenir les exigences de
     sécurité applicables à une plateforme traitant des données d'examens
     officiels. L'ANSSI a recommandé un **courrier officiel** de saisine plutôt
     qu'une simple prise de contact — voir la lettre type préparée pour ce
     courrier (à finaliser avec l'identité juridique de l'expéditeur, encore non
     tranchée, voir `docs/PIVOT_SAAS_B2G.md` § 9).
2. **Tests de charge à grande échelle** — première mesure réelle effectuée le
   2026-07-07 (client `httpx` async local contre un serveur `uvicorn` mono-processus,
   sur `GET /api/v1/public/results` en cache chaud) :

   | Concurrence client | Débit | p50 | p95 | p99 |
   |---|---|---|---|---|
   | 10 | 576 req/s | 10 ms | 48 ms | 119 ms |
   | 25 | 404 req/s | 40 ms | 181 ms | 287 ms |
   | 50 | 255-315 req/s | 105-135 ms | 450-575 ms | 800-940 ms |

   L'objectif <200 ms est tenu à concurrence modérée (10-25 clients) mais dépassé au
   p95/p99 à 50. Point important : le processus `uvicorn` restait à ~23-30% CPU même
   au pic — ce n'est **pas** le serveur qui sature, c'est le générateur de charge
   (client asyncio mono-processus sur la même machine, seul cœur disponible pour lui).
   Le débit qui *baisse* quand la concurrence *augmente* (576→255 req/s) est la
   signature classique d'un client saturé, pas d'un serveur saturé. **Donc toujours
   pas de mesure fiable de la vraie limite serveur** — il faut un outil de charge
   dédié (k6, locust, plusieurs machines clientes) contre un déploiement réel avant un
   vrai jour de proclamation. Ce qui est acquis : le chemin cache chaud fonctionne
   sans erreur sous charge, et le serveur a manifestement de la marge CPU non utilisée
   à explorer (ex. `uvicorn --workers N`).
3. **Mise en production réelle** : hébergement burkinabè (souveraineté des données),
   HTTPS, rotation des mots de passe par défaut créés par `seed.py`.

   **2026-08-17 — Piste d'hébergeur burkinabè identifiée : IKA Cloud.**
   Datacenter Tier III à Ouagadougou, architecture haute disponibilité N+2. Offres
   VPS consultées (tarifs mensuels) :

   | Offre | Prix/mois | Disque | CPU | RAM |
   |---|---|---|---|---|
   | VPS Starter | 45 700 F | 30 Go SSD | 1 cœur | 2 Go |
   | VPS Pro | 70 800 F | 60 Go SSD | 2 cœurs | 4 Go |
   | VPS Premium | 83 300 F | 80 Go SSD | 4 cœurs | 8 Go |

   Commun aux trois : IPv4 fixe dédiée, firewall managé, sauvegarde globale du VPS,
   bande passante illimitée, supervision 24/7, gestion infogérée. Le nom de domaine
   `faso-resultats.bf` est disponible chez le même prestataire (16 900 F, à confirmer
   si prix d'enregistrement ou annuel). Reste à faire : confirmer que la stack Docker
   Compose (PostgreSQL + Redis + backend + frontend) tient dans le tier Starter pour
   un pilote, et vérifier les conditions d'accès root/SSH (« infogéré » peut signifier
   accès restreint selon les offres — à clarifier avant de s'engager). Aucun autre
   devis burkinabè comparé à ce stade — à mettre en concurrence si le temps le permet.
4. **Calibrage OCR** : aucun spécimen de PV scanné/photo n'est disponible actuellement
   pour calibrer le parser OCR — à refaire dès qu'un nouveau spécimen sera fourni.
5. **Intégration SMS réelle (Orange Business)** : nécessite un contrat et des
   identifiants API que ce projet n'a pas encore — `NotificationEngine.envoyer_sms`
   reste un stub journalisé en attendant. Voir Phase 2 pour la grille tarifaire
   consultée et le nouveau prérequis de structure juridique (RCCM/IFU) identifiés le
   2026-08-17.

6. **Points restants de l'audit du 2026-08-17 et des chantiers du 2026-09-28** :
   révocation des sessions (token candidat valable 30 jours sans révocation) ;
   `erreurs_fichier` (écart de comptage OCR) non bloquant à la publication ;
   notifications perdues en heure silencieuse (22h-6h) sans nouvel essai ; alias
   `"mention"` → `decision` sans garde-fou ; aucune purge de la table `resultats` ;
   fichiers sources importés en clair sur disque et sauvegarde/rotation de la clé
   de chiffrement (`docs/CIL.md` § 7.2) ; auto-hébergement de Poppins et de
   Tailwind avant la production.

Chaque phase reste conditionnée à une demande explicite avant de démarrer le code,
conformément à `CLAUDE.md`, même si les choix techniques ci-dessus sont déjà actés.
