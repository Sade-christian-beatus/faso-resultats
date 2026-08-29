# Documentation de traitement — Données de résultats d'examens et concours

**Projet :** Faso Résultats
**Périmètre couvert :** données de résultats et d'ingestion gérées pour le compte des administrations clientes (`examens`, `resultats`, `ingestions`, `administrations`, `utilisateurs`)
**Périmètre exclu :** le compte candidat plateforme (authentification, profil, candidatures) suit un régime différent — voir `docs/CIL_PROFIL_CANDIDAT.md`
**Dernière mise à jour :** 2026-08-17
**Statut :** document de travail technique — voir avertissement ci-dessous

> Ce document est rédigé par l'équipe technique du projet. Il décrit fidèlement
> ce que le système fait aujourd'hui et sert de base de discussion avec la
> **CIL** (Commission de l'Informatique et des Libertés du Burkina Faso,
> https://www.cil.bf), l'autorité burkinabè de protection des données à
> caractère personnel. Il ne constitue pas à lui seul une déclaration de
> traitement officielle et ne remplace pas un avis juridique. Les points
> marqués ⚠️ sont identifiés comme nécessitant une confirmation de la CIL et/ou
> d'un professionnel du droit avant toute mise en production avec des données
> réelles de candidats.

---

## Résumé pour un lecteur non technique

Faso Résultats est une plateforme qui permet à des administrations publiques
burkinabè (offices d'examens, ministères organisateurs de concours) de publier
leurs résultats et à un candidat de consulter **son propre résultat**, en
saisissant un numéro de dossier qu'il possède déjà (numéro de PV ou de
récépissé), éventuellement complété du nom du jury ou centre d'examen.

Il n'existe **aucun moyen de parcourir ou de lister** les candidats : sans
connaître au préalable un numéro de dossier précis, aucune donnée n'est
accessible. Les données affichées publiquement sont volontairement réduites au
strict nécessaire (nom, prénom, décision, moyenne — jamais la date de
naissance, le lieu de naissance ou le numéro de pièce d'identité).

Faso Résultats agit comme **prestataire technique (sous-traitant)** pour le
compte de chaque administration cliente, qui reste seule responsable de
traitement de ses propres données de résultats.

---

## 1. Rôles et responsabilités

### 1.1 Faso Résultats — sous-traitant

Faso Résultats héberge et exploite techniquement la plateforme pour le compte
d'administrations clientes. Il ne décide ni de la finalité ni des moyens du
traitement : chaque administration décide quand publier, quoi publier, et
conserve la maîtrise éditoriale de ses résultats.

Cela implique, une fois le cadre commercial et juridique formalisé :

- une **convention de sous-traitance conforme aux exigences de la CIL** signée
  avec chaque administration cliente, précisant les garanties ci-dessous ;
- que Faso Résultats ne traite les données que sur instruction documentée de
  l'administration (import, publication, correction, purge) ;
- une notification à l'administration en cas d'incident de sécurité affectant
  ses données.

### 1.2 Administration cliente — responsable de traitement

Chaque administration (OCECOS, Office du BAC, AGRE, ou toute autre
administration cliente — voir `docs/PIVOT_SAAS_B2G.md` § 1) est responsable de
traitement de ses propres résultats : elle en détermine la finalité, décide de
leur publication, et répond des demandes d'exercice de droits de ses
candidats.

### 1.3 ⚠️ Point à formaliser avant tout traitement de données réelles

L'entité juridique porteuse de Faso Résultats (structure SARL/SAS — voir
`docs/PIVOT_SAAS_B2G.md` § 9) n'est pas encore arrêtée. Tant que ce n'est pas
fait, ce document reste un cadre de travail technique et non une déclaration
formelle opposable.

---

## 2. Données traitées

### 2.1 Résultats de candidats (table `resultats`)

| Donnée | Sensibilité | Exposée à l'API publique ? |
|---|---|---|
| `numero_pv`, `jury` | Non sensible — identifiant de dossier | Oui (nécessaire à la recherche) |
| `nom`, `prenom` | Identifiante | Oui |
| `decision`, `moyenne`, `etablissement` | Résultat scolaire | Oui |
| `rang_numerique`, `rang_affiche`, `phase` | Résultat de concours (classement, étape) | Oui |
| `date_naissance`, `lieu_naissance` | Identifiante, sensible | **Non** — conservée pour traçabilité uniquement |
| `numero_cnib` | Identifiante forte, sensible (concours directs uniquement — absente pour les examens scolaires) | **Non** |
| `numero_recepisse`, `code_concours`, `code_centre` | Identifiants de dossier (concours de la Fonction publique) | Oui |
| `donnees_brutes` (jsonb) | Copie intégrale de la ligne source du fichier importé | Non — accessible uniquement aux administrateurs habilités, pour audit et traçabilité en cas de contestation |

### 2.2 Comptes administrateurs (table `utilisateurs`)

| Donnée | Sensibilité | Usage |
|---|---|---|
| `email` | Identifiante | Connexion |
| `mot_de_passe_hash` | Sensible — jamais en clair (bcrypt) | Authentification |
| `nom_complet`, `telephone` (optionnel) | Identifiante | Contact interne |
| `administration_id`, `role` | — | Rattachement au tenant et permissions |

### 2.3 Fichiers sources importés

Les fichiers PDF/Excel/scans importés par les administrateurs peuvent contenir
les mêmes données que `donnees_brutes`, ainsi que toute donnée superflue
présente dans le document d'origine (colonnes non reconnues, mise en page).
Conservés en l'état pour permettre un nouveau traitement en cas d'erreur de
parsing, jamais exposés en dehors des routes d'administration.

### 2.4 Préinscriptions SMS (table `notifications_preinscription`)

Table créée par anticipation de la Phase 2 (notifications SMS), **non encore
utilisée** : aucune route ne la lit ni ne l'écrit à ce jour. Contiendra, une
fois active : `telephone`, `numero_pv`, et un champ `consentement` (booléen,
`False` par défaut) portant la preuve d'un consentement explicite et non
pré-coché.

---

## 3. Finalités du traitement

1. Permettre à un candidat de consulter son propre résultat via son numéro de
   dossier (et le jury/centre, en cas d'ambiguïté).
2. Assurer la traçabilité de chaque résultat publié jusqu'à son fichier
   source et à l'administrateur ayant réalisé l'import, en cas de
   contestation ou d'erreur.
3. *(Phase 2, non active)* Notifier un candidat par SMS de la disponibilité
   de son résultat, sur préinscription et consentement explicite.

Aucune autre finalité — statistiques agrégées, profilage, prospection,
revente de données à un tiers — n'est mise en œuvre.

---

## 4. Base légale

⚠️ À confirmer avec la CIL et/ou un professionnel du droit. Piste de travail
retenue : **mission de service public** pour la publication de résultats
d'examens et de concours par des organismes officiels, et **consentement
explicite** pour les notifications SMS de la Phase 2.

---

## 5. Minimisation des données

- L'API publique (`GET /api/v1/public/results`) n'expose jamais
  `date_naissance`, `lieu_naissance` ni `numero_cnib` — ce filtrage est
  appliqué par construction (schéma de réponse explicite, indépendant du
  contenu réel de la base) et vérifié par des tests automatisés.
- Aucun endpoint public ne permet de lister ou de parcourir des candidats :
  la recherche exige un numéro de dossier déjà connu. Aucune recherche par
  nom, aucune énumération possible.
- Les logs applicatifs ne contiennent aucune donnée personnelle sensible
  (nom, date de naissance, téléphone) — voir §7.

---

## 6. Durée de conservation

⚠️ Durée légale à confirmer avec la CIL. **Aucun mécanisme de purge
automatique n'existe à ce jour** pour la table `resultats` — c'est un manque
identifié, à combler avant toute mise en production réelle (voir §9).

Piste de travail à valider : conserver les résultats publiés pendant une
durée alignée sur leur usage administratif réel (les résultats d'examens et
de concours sont couramment redemandés plusieurs années après — dossiers
d'embauche, poursuite d'études), avec purge ou archivage au-delà. Aucun
chiffre n'est encore arrêté ; il doit être proposé par chaque administration
responsable de traitement et validé avec la CIL.

---

## 7. Sécurité des données

### 7.1 Mesures déjà en place

- Mots de passe administrateurs hashés (bcrypt), jamais stockés ni loggés en
  clair.
- Authentification par JWT à audience dédiée (un token émis pour l'espace
  admin ne peut pas être utilisé sur une autre surface de l'API), routes
  d'écriture toutes protégées et scopées par administration
  (`docs/MULTI_TENANCY.md`).
- **Verrouillage de compte administrateur** après tentatives de connexion
  répétées (indépendant du rate limiting par IP), avec journalisation de
  chaque échec.
- Rate limiting sur le login (5/min/IP par défaut) et les routes publiques
  (30/min/IP par défaut).
- CORS restreint aux origines déclarées.
- Isolation stricte entre administrations clientes (multi-tenant), vérifiée
  par des tests automatisés dédiés — un opérateur d'une administration ne
  peut jamais accéder aux données d'une autre.
- Journal d'audit (`AuditLog`) de toutes les actions sensibles : connexions
  (réussies et échouées), création/modification d'examen, upload/correction/
  publication/rejet d'ingestion, gestion des comptes et des administrations —
  qui a fait quoi, quand, depuis quelle adresse IP.
- Secrets sensibles (clé de signature JWT, peppers de hachage) exclusivement
  via variables d'environnement ; le démarrage en production est bloqué si
  l'un d'eux a conservé sa valeur de développement par défaut.
- Données affichées publiquement systématiquement échappées avant affichage
  (protection contre l'injection de code dans un nom ou un établissement mal
  nettoyé à la source).

### 7.2 ⚠️ À compléter avant toute exposition à des données réelles

- **Chiffrement au repos du CNIB et de la date de naissance** dans
  `resultats` : ces champs sont aujourd'hui en clair en base, alors que les
  mêmes catégories de données sont chiffrées côté profil candidat
  (`docs/CIL_PROFIL_CANDIDAT.md`) — incohérence à résoudre.
- **Purge des données** au terme de la durée de conservation (§6), une fois
  celle-ci définie.
- **HTTPS** — la plateforme tourne aujourd'hui en environnement de
  développement (HTTP local/Docker) ; le chiffrement en transit est
  obligatoire avant toute ouverture au public.
- **Hébergement sur serveurs situés au Burkina Faso** — principe retenu par
  le projet dès son origine (souveraineté des données), à concrétiser au
  moment du choix d'infrastructure de production.
- **Rotation des mots de passe par défaut** créés par le script
  d'initialisation (`seed.py`) avant toute exposition publique du service.

---

## 8. Destinataires et sous-traitants

- **Administrateurs habilités** d'une administration : accès aux données de
  leur propre administration uniquement, pour l'import et la correction —
  jamais aux données d'une autre administration.
- **Hébergeur de production** : ⚠️ à préciser une fois l'infrastructure
  choisie ; doit être situé au Burkina Faso (§7.2). Une fois choisi, ce
  prestataire devient lui-même sous-traitant ultérieur et doit être couvert
  par une clause contractuelle adéquate.
- **Opérateurs télécom** (Orange, Moov, Telecel) : concernera le numéro de
  téléphone à partir de la Phase 2 (envoi SMS) — non applicable aujourd'hui.
- **Partenaires de l'API B2B** (Phase 4, fondation technique posée) : accès
  strictement identique à l'API publique — aucune donnée sensible
  supplémentaire n'est exposée à un partenaire tiers.
- Aucune donnée n'est partagée avec un tiers en dehors de ce périmètre.

---

## 9. Droits des personnes concernées

Un canal de contact dédié existe (`GET /api/v1/public/droits-candidat`) et
liste explicitement les droits exerçables : accès, portabilité, rectification
des préférences, effacement (pour un compte candidat plateforme), et
rectification d'identité sur demande auprès du contact désigné pour les
champs non modifiables en libre-service.

⚠️ Reste à préciser : la procédure de correction d'un résultat déjà publié
(aujourd'hui, seule une ingestion encore au statut « prévisualisation » est
directement corrigible — une correction après publication passerait par une
nouvelle ingestion corrective, à documenter comme procédure formelle).

---

## 10. Consentement SMS *(Phase 2, non active)*

Le modèle `NotificationPreinscription.consentement` (booléen, `False` par
défaut) est prêt à porter la preuve d'un consentement explicite et non
pré-coché. Aucune collecte n'a lieu tant que la Phase 2 n'a pas démarré —
elle reste conditionnée à la signature d'un contrat avec un opérateur
télécom (voir `docs/ROADMAP.md` § Phase 2).

---

## 11. Historique des vérifications de sécurité

Deux revues de sécurité indépendantes du code ont été menées le 2026-08-17.
Cinq anomalies critiques ont été corrigées dans la foulée (dont une
inversion silencieuse de décision sur les résultats scannés, et une
possibilité de rapprocher un candidat au mauvais résultat). Le verrouillage
de compte administrateur et l'échappement systématique des données publiques
(§7.1) ont été ajoutés à la suite de cette même revue. Le détail complet est
tenu à jour dans `CLAUDE.md` § Historique des décisions techniques.

---

## 12. Prochaines étapes avant une mise en production réelle

1. Faire valider ce document par la CIL et/ou un professionnel du droit
   (base légale, durée de conservation, responsable de traitement formalisé
   par administration cliente).
2. Chiffrer `numero_cnib` et `date_naissance` dans `resultats` (§7.2).
3. Implémenter un mécanisme de purge des résultats après la durée de
   conservation confirmée par la CIL (§6).
4. Mettre en place HTTPS et un hébergement situé au Burkina Faso avant toute
   ouverture au public avec des données réelles.
5. Changer les mots de passe administrateurs par défaut créés par `seed.py`.
6. Signer la convention de sous-traitance avec la première administration
   cliente (§1.1).
