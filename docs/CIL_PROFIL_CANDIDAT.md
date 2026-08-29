# Documentation de traitement — Profil candidat unifié (conformité CIL)

> Document de travail technique, à faire valider par un professionnel du
> droit et/ou directement par la Commission de l'Informatique et des
> Libertés du Burkina Faso (CIL, https://www.cil.bf) avant toute
> mise en production réelle. Il décrit ce que fait le système aujourd'hui ;
> il ne constitue pas à lui seul une déclaration de traitement officielle.
> Les points marqués ⚠️ nécessitent une confirmation juridique.

Ce document couvre spécifiquement le **profil candidat plateforme**
(`docs/PROFIL_CANDIDAT_UNIFIE.md`), transversal à toutes les administrations.
Voir `docs/CIL.md` pour le traitement des données de résultats côté
administration (tenant), qui reste distinct.

Maintenu à jour à chaque évolution touchant ce périmètre, conformément à
`CLAUDE.md`.

---

## 1. Différence de statut avec les données d'examens

Sur les données d'examens (`resultats`, `ingestions`), Faso Résultats est
**sous-traitant** de l'administration cliente (voir `docs/CIL.md`).

Sur le **profil candidat**, la situation change : Faso Résultats est
**responsable de traitement** au sens de la loi n°001-2021/AN du Burkina
Faso, car c'est la plateforme elle-même qui collecte, stocke et exploite
directement ces données (compte candidat, authentification, notifications),
indépendamment de toute administration.

⚠️ À compléter avec l'entité officielle porteuse du projet, comme pour
`docs/CIL.md` § 1.

---

## 2. Données traitées

### 2.1 `plateforme.profils_candidats`

| Donnée | Sensibilité | Protection | Utilisée pour |
|---|---|---|---|
| `numero_cnib` | Identifiante forte, sensible | **Chiffrée au repos** (Fernet/AES, `app.models.encrypted_str.EncryptedStr`) ; recherche/unicité via `numero_cnib_hash` (HMAC-SHA256, jamais la valeur en clair en index) | Vérification de propriété d'un récépissé (mécanisme 1) |
| `date_naissance` | Identifiante, sensible | Chiffrée au repos | Vérification de propriété (mécanisme 2) |
| `telephone` | Identifiante, sensible | Chiffrée au repos ; recherche via `telephone_hash` | Authentification OTP, notifications SMS |
| `nom_complet`, `lieu_naissance`, `sexe` | Identifiante | Non chiffrées (affichage du profil) | Affichage, personnalisation |
| `email` | Identifiante, optionnelle | Non chiffrée | Canal de notification optionnel |
| `mot_de_passe_hash` | Sensible | bcrypt, jamais en clair | Authentification (mode mot de passe optionnel) |
| `consentement_apdp_date`, `consentement_apdp_version` | — | — | Preuve de consentement horodatée et versionnée |

### 2.2 `plateforme.candidatures`

Table de liaison entre un profil et un examen d'une administration.
`administration_id` et `examen_id` sont de simples références (pas de FK
cross-schéma, voir `docs/MULTI_TENANCY.md`) : cette table ne duplique pas
les données de résultat elles-mêmes, seulement un cache minimal
(`dernier_resultat_statut`, `dernier_resultat_phase`) nécessaire à
l'affichage du dashboard sans requête cross-schéma à chaque consultation.

### 2.3 `plateforme.journal_consultations_profil`

Journal d'audit **immuable (append-only)** : chaque connexion, consultation
du dashboard, ajout/suppression de candidature, modification de
préférences. Champs : `action`, `ip`, `user_agent`, `timestamp`. Conservé
tant que le profil existe ; purgé intégralement (cascade ORM explicite, pas
seulement une contrainte de base) à la suppression du compte — voir §5.

---

## 3. Finalités du traitement

1. Permettre à un candidat de retrouver, dans un tableau de bord unique,
   l'ensemble de ses candidatures à travers plusieurs administrations.
2. Le notifier par SMS (stub en Phase 1, voir `docs/ROADMAP.md`) dès qu'un
   résultat le concernant est publié par une administration.
3. Vérifier qu'il est bien le propriétaire du récépissé qu'il déclare
   (CNIB → date de naissance → OTP), pour empêcher qu'un tiers ne rattache
   à son compte les données publiques d'un autre candidat.

Aucune autre finalité (statistiques nominatives, profilage commercial,
revente de données, prospection) n'est mise en œuvre. Les services annexes
évoqués en phase avancée (`docs/PROFIL_CANDIDAT_UNIFIE.md` § 9) restent
non démarrés.

---

## 4. Base légale

⚠️ À confirmer avec la CIL / un juriste. Piste de travail : **consentement
explicite** de la personne concernée (case non pré-cochée, horodatée et
versionnée — `consentement_apdp_date`/`consentement_apdp_version`), recueilli
à l'inscription (`POST /api/v1/candidat/inscription`).

---

## 5. Droit à l'oubli et durée de conservation

- Le candidat peut supprimer son compte à tout moment
  (`DELETE /api/v1/candidat/me`), **avec effet immédiat** : le profil, ses
  candidatures et son journal de consultation sont purgés dans la même
  transaction (cascade ORM `all, delete-orphan` sur les deux relations,
  volontairement **indépendante** de l'`ON DELETE CASCADE` de la base pour
  garantir le comportement même sur un moteur qui n'impose pas les
  contraintes FK — voir les tests d'isolation,
  `tests/test_isolation_profil_candidat.py`).
- La suppression **n'affecte pas** les résultats publiés par les
  administrations, qui restent leur propriété et suivent leur propre
  politique de conservation (`docs/CIL.md`).
- Durée de conservation par défaut (compte inactif, jamais supprimé
  explicitement) : `candidat_purge_inactivite_jours` (2 ans par défaut).
  ⚠️ Valeur provisoire, non validée par la CIL — à trancher avant mise en
  production réelle. Purge effective via `purge_candidats.py`
  (`app/services/candidat/purge_service.py`), à planifier via cron côté
  infrastructure (pas de file de tâches en Phase 1, voir CLAUDE.md).
  L'inactivité se mesure depuis la dernière connexion, ou depuis
  l'inscription si le profil ne s'est jamais reconnecté.
- Interaction avec la résiliation d'une administration
  (`docs/PROFIL_CANDIDAT_UNIFIE.md` § 7) : dès que le statut d'une
  administration passe à `RESILIE` (via
  `PATCH /api/v1/admin/administrations/{id}`), ses candidatures sont
  immédiatement marquées `ADMINISTRATION_RESILIEE` et leur cache de dernier
  résultat (`dernier_resultat_*`) est purgé. `purge_candidats.py` les
  supprime ensuite après `candidat_purge_candidature_resiliee_jours`
  (6 mois par défaut, § 7). ⚠️ Ce mécanisme ne couvre que le volet
  candidat — la politique de conservation des résultats historiques de
  l'administration elle-même reste à trancher (`docs/PIVOT_SAAS_B2G.md`
  § 4, point 4).

---

## 6. Sécurité des données

Mesures en place :

- **Chiffrement au repos** du CNIB, du téléphone et de la date de naissance
  (Fernet/AES-128, clé applicative `CANDIDAT_ENCRYPTION_KEY`), avec
  recherche/unicité via un hash déterministe (HMAC-SHA256,
  `CANDIDAT_HASH_PEPPER`) plutôt que sur la valeur en clair.
- **Authentification par OTP SMS** : code à 6 chiffres, valide
  `CANDIDAT_OTP_EXPIRE_MINUTES` (5 min par défaut), invalidé après usage,
  verrouillé après `CANDIDAT_OTP_MAX_TENTATIVES` (3) tentatives infructueuses
  — verrouillage porté par une clé dédiée (`candidat_otp_lockout_minutes`,
  15 min par défaut), indépendante de la génération d'un nouveau code : le
  redemander pendant la fenêtre de verrouillage ne débloque plus le numéro.
- **Audience JWT dédiée** (`aud=candidat`, distincte de `aud=admin`) : un
  token émis pour l'espace admin ne peut jamais authentifier une route
  candidat, et inversement — voir `app/core/security.py` et les tests
  `test_token_admin_ne_fonctionne_pas_sur_les_routes_candidat` /
  `test_token_candidat_ne_fonctionne_pas_sur_les_routes_admin`.
- **Anti-énumération** : `POST /api/v1/candidat/login` répond un message
  générique identique, que le numéro soit inscrit ou non.
- **Anti-abus sur l'ajout de candidature** : au-delà de 5 tentatives
  rejetées par jour et par profil, les nouvelles tentatives sont bloquées
  (429). Au-delà de `candidat_abus_minimum_tentatives` (5) et d'un taux de
  rejet supérieur à `candidat_abus_taux_rejet_suspension` (30%), le profil
  est suspendu automatiquement (`docs/PROFIL_CANDIDAT_UNIFIE.md` § 8) — voir
  `app/routes/candidat/candidatures.py`.
- **Alerte de prise de contrôle de compte** (§ 8, risque 2) : un SMS est
  envoyé immédiatement au numéro utilisé pour créer un compte, qu'il soit ou
  non l'auteur de l'inscription — voir
  `NotificationEngine.formater_message_alerte_creation_compte()`. ⚠️ Portée
  limitée : ne protège pas contre un attaquant qui contrôle déjà le
  téléphone lui-même (SIM swap), faute de second canal indépendant (email).
- **Journal d'audit immuable** de chaque accès/modification (§2.3).
- **Isolation stricte** : aucune route admin ne permet de lister ou
  d'interroger les profils candidats plateforme ; un candidat ne peut
  jamais voir les candidatures d'un autre candidat — voir
  `tests/test_isolation_profil_candidat.py`.

Limites connues, à traiter avant une mise en production réelle :

- ⚠️ Le code OTP n'est jamais envoyé par un vrai canal SMS en Phase 1 (stub,
  voir `app/services/candidat/notification_engine.py`) : il est renvoyé
  dans la réponse HTTP (`code_otp_debug`) uniquement quand
  `ENVIRONMENT != production`, pour permettre les tests de bout en bout.
  **Ce champ doit être absent en production** — vérifié par la configuration
  (`settings.environment`), mais à re-tester explicitement avant toute mise
  en ligne.
- ⚠️ Sans file de tâches (RQ, Phase 2), une notification tombant dans la
  plage silencieuse (22h-6h) est abandonnée plutôt que différée — voir
  `app/services/candidat/notification_engine.py`.

---

## 7. Destinataires et sous-traitants

- **Aucune administration cliente** n'a accès aux profils candidats
  plateforme — l'isolation est vérifiée par test automatisé.
- **Opérateurs télécom** (Orange, Moov, Telecel) : concernera le numéro de
  téléphone dès l'intégration SMS réelle (Phase 2) — non applicable tant
  que `NotificationEngine.envoyer_sms` reste un stub.
- **Hébergeur** : ⚠️ à préciser une fois l'infrastructure de production
  choisie (doit être burkinabè, cf. `CLAUDE.md`), comme pour `docs/CIL.md`.

---

## 8. Droits des personnes concernées

- **Droit d'accès** : `GET /api/v1/candidat/me`.
- **Droit de rectification** : `PATCH /api/v1/candidat/me` (préférences,
  email) — les données d'identité (CNIB, nom, date de naissance) restent
  volontairement non modifiables par cette route ; leur correction passe par
  le canal de contact ci-dessous.
- **Droit à l'effacement** : `DELETE /api/v1/candidat/me` (§5).
- **Droit à la portabilité** : `GET /api/v1/candidat/me/export` — renvoie le
  profil déchiffré (identité, candidatures, journal de consultation) dans un
  format JSON structuré, distinct de `GET /me` qui n'expose que les champs
  utiles au dashboard courant.
- **Canal de contact dédié** : `GET /api/v1/public/droits-candidat` (endpoint
  public, non authentifié) renvoie l'email de contact DPO
  (`candidat_dpo_contact_email`, ⚠️ valeur placeholder à remplacer par une
  vraie adresse avant mise en production) et la liste des droits exerçables,
  pour les demandes qui ne passent pas par les endpoints en libre-service
  ci-dessus (ex. rectification d'identité, demande formulée par un tiers).

---

## 9. Prochaines étapes avant une vraie mise en production

1. Faire valider ce document par la CIL ou un professionnel du droit (base
   légale, durée de conservation par défaut — notamment
   `candidat_purge_inactivite_jours`, actuellement une valeur provisoire non
   validée — responsable de traitement).
2. Remplacer le stub SMS par une intégration réelle (Orange/Moov/Telecel,
   Phase 2) et supprimer tout renvoi de code OTP dans les réponses HTTP
   (`code_otp_debug`, présent sur les réponses d'inscription/connexion et
   sur l'ajout de candidature via le mécanisme 3).
3. Planifier `purge_candidats.py` via cron une fois l'infrastructure de
   production choisie (§5).
4. Remplacer `candidat_dpo_contact_email` (placeholder) par une vraie adresse
   de contact avant mise en production (§8).
