# Documentation de traitement — Profil candidat unifié (conformité APDP)

> Document de travail technique, à faire valider par un professionnel du
> droit et/ou directement par l'Autorité de Protection des Données à
> caractère Personnel du Burkina Faso (APDP, https://www.cil.bf) avant toute
> mise en production réelle. Il décrit ce que fait le système aujourd'hui ;
> il ne constitue pas à lui seul une déclaration de traitement officielle.
> Les points marqués ⚠️ nécessitent une confirmation juridique.

Ce document couvre spécifiquement le **profil candidat plateforme**
(`docs/PROFIL_CANDIDAT_UNIFIE.md`), transversal à toutes les administrations.
Voir `docs/APDP.md` pour le traitement des données de résultats côté
administration (tenant), qui reste distinct.

Maintenu à jour à chaque évolution touchant ce périmètre, conformément à
`CLAUDE.md`.

---

## 1. Différence de statut avec les données d'examens

Sur les données d'examens (`resultats`, `ingestions`), Faso Résultats est
**sous-traitant** de l'administration cliente (voir `docs/APDP.md`).

Sur le **profil candidat**, la situation change : Faso Résultats est
**responsable de traitement** au sens de la loi n°001-2021/AN du Burkina
Faso, car c'est la plateforme elle-même qui collecte, stocke et exploite
directement ces données (compte candidat, authentification, notifications),
indépendamment de toute administration.

⚠️ À compléter avec l'entité officielle porteuse du projet, comme pour
`docs/APDP.md` § 1.

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

⚠️ À confirmer avec l'APDP / un juriste. Piste de travail : **consentement
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
  politique de conservation (`docs/APDP.md`).
- ⚠️ Durée de conservation par défaut (compte inactif, jamais supprimé
  explicitement) non encore définie — à trancher avec l'APDP. **Non
  implémenté à ce jour** : aucun job de purge automatique des comptes
  inactifs n'existe (Phase 1).
- Interaction avec la résiliation d'une administration
  (`docs/PROFIL_CANDIDAT_UNIFIE.md` § 7) : les candidatures liées à une
  administration résiliée devraient être marquées et purgées après un
  délai — **non implémenté à ce jour**, à construire quand le premier cas
  réel se présentera.

---

## 6. Sécurité des données

Mesures en place :

- **Chiffrement au repos** du CNIB, du téléphone et de la date de naissance
  (Fernet/AES-128, clé applicative `CANDIDAT_ENCRYPTION_KEY`), avec
  recherche/unicité via un hash déterministe (HMAC-SHA256,
  `CANDIDAT_HASH_PEPPER`) plutôt que sur la valeur en clair.
- **Authentification par OTP SMS** : code à 6 chiffres, valide
  `CANDIDAT_OTP_EXPIRE_MINUTES` (5 min par défaut), invalidé après usage,
  verrouillé après `CANDIDAT_OTP_MAX_TENTATIVES` (3) tentatives infructueuses.
- **Audience JWT dédiée** (`aud=candidat`, distincte de `aud=admin`) : un
  token émis pour l'espace admin ne peut jamais authentifier une route
  candidat, et inversement — voir `app/core/security.py` et les tests
  `test_token_admin_ne_fonctionne_pas_sur_les_routes_candidat` /
  `test_token_candidat_ne_fonctionne_pas_sur_les_routes_admin`.
- **Anti-énumération** : `POST /api/v1/candidat/login` répond un message
  générique identique, que le numéro soit inscrit ou non.
- **Anti-abus sur l'ajout de candidature** : au-delà de 5 tentatives
  rejetées par jour et par profil, les nouvelles tentatives sont bloquées
  (429) — voir `app/routes/candidat/candidatures.py`.
- **Journal d'audit immuable** de chaque accès/modification (§2.3).
- **Isolation stricte** : aucune route admin ne permet de lister ou
  d'interroger les profils candidats plateforme ; un candidat ne peut
  jamais voir les candidatures d'un autre candidat — voir
  `tests/test_isolation_profil_candidat.py`.

Limites connues, à traiter avant une mise en production réelle :

- ⚠️ **Détection d'abus avancée non implémentée** : le seuil « 30% de
  candidatures rejetées → suspension automatique » décrit dans
  `docs/PROFIL_CANDIDAT_UNIFIE.md` § 8 n'est pas construit ; seule la limite
  simple de 5 rejets/jour l'est.
- ⚠️ **Pas d'alerte de prise de contrôle de compte** : le mécanisme
  "un compte vient d'être créé avec votre CNIB, si ce n'est pas vous..."
  (§ 8, risque 2) n'est pas implémenté — un tiers connaissant le CNIB et le
  téléphone d'une victime pourrait aujourd'hui créer un compte à sa place
  sans que la victime en soit avertie.
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
  choisie (doit être burkinabè, cf. `CLAUDE.md`), comme pour `docs/APDP.md`.

---

## 8. Droits des personnes concernées

- **Droit d'accès** : `GET /api/v1/candidat/me`.
- **Droit de rectification** : `PATCH /api/v1/candidat/me` (préférences,
  email) — les données d'identité (CNIB, nom, date de naissance) ne sont
  volontairement pas modifiables par cette route ; leur correction
  nécessiterait un canal de support dédié (⚠️ non implémenté).
- **Droit à l'effacement** : `DELETE /api/v1/candidat/me` (§5).
- **Droit à la portabilité** : ⚠️ non implémenté à ce jour (pas d'export des
  données du profil dans un format structuré).
- ⚠️ Aucun canal de contact dédié aux demandes d'exercice de droits qui ne
  passeraient pas par ces endpoints (ex. demande formulée par une tierce
  personne) — à prévoir avant mise en production.

---

## 9. Prochaines étapes avant une vraie mise en production

1. Faire valider ce document par l'APDP ou un professionnel du droit (base
   légale, durée de conservation par défaut, responsable de traitement).
2. Implémenter la détection d'abus avancée et l'alerte de prise de contrôle
   de compte (§6).
3. Remplacer le stub SMS par une intégration réelle (Orange/Moov/Telecel,
   Phase 2) et supprimer tout renvoi de code OTP dans les réponses HTTP.
4. Définir et implémenter une durée de conservation par défaut pour les
   comptes inactifs, avec purge automatique.
5. Construire le traitement des candidatures orphelines à la résiliation
   d'une administration (§5).
