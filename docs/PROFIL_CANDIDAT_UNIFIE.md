# PROFIL CANDIDAT UNIFIÉ

> À intégrer au projet dans `docs/PROFIL_CANDIDAT_UNIFIE.md`.
> Cette fonctionnalité est **transversale à tous les tenants** et vit au niveau plateforme, non au niveau administration.
> Elle constitue le principal différenciateur de Faso Résultats vis-à-vis de toute solution mono-administration.

---

## 1. Concept et proposition de valeur

### Le problème résolu

Un candidat burkinabè typique postule à plusieurs examens et concours dans la même année : rattrapage BAC, concours direct AGRE, concours d'entrée ENAM, concours paramilitaire Douanes. Il obtient **plusieurs numéros de récépissé différents**, gérés par **plusieurs administrations différentes**, avec **des calendriers de publication différents**.

Résultat aujourd'hui : le candidat court après plusieurs canaux, rate des publications, ignore les phases suivantes des concours à étapes, et vit une expérience morcelée et stressante.

### La solution

Un **compte candidat unique** au niveau de la plateforme Faso Résultats (pas au niveau d'une administration) qui permet de :

1. Voir en un seul tableau de bord toutes ses candidatures de l'année
2. Recevoir des notifications automatiques (SMS, push mobile) dès qu'un résultat le concernant est publié, quelle que soit l'administration
3. Suivre l'avancement des concours à phases multiples (paramilitaires notamment)
4. Consulter l'historique de ses examens sur plusieurs années
5. Ajouter des candidatures futures et être alerté au moment de leurs publications

### Pourquoi c'est structurant pour le business

Cette fonctionnalité change la dynamique commerciale : chaque **nouvelle administration cliente hérite d'un pool de candidats déjà inscrits et notifiables**. Concrètement, dire à la troisième administration prospectée *"vous rejoignez une plateforme où 40 000 candidats de la région ont déjà un compte actif"* est un argument bien plus puissant que *"nous avons un beau logiciel"*. C'est un effet réseau qui joue en ta faveur à chaque signature.

### Ce que ce n'est PAS

- Ce n'est pas un compte imposé pour consulter un résultat. La consultation par simple numéro de récépissé + date de naissance reste possible **sans compte** — c'est la voie rapide, pour les utilisateurs occasionnels.
- Ce n'est pas un profil éditorial ni un réseau social. Aucun contenu généré par l'utilisateur, aucune interaction publique.
- Ce n'est pas un service payant. L'inscription et l'usage sont **gratuits pour le candidat**. Le modèle économique repose sur les administrations, pas sur les candidats.

---

## 2. Positionnement architectural

### Le profil candidat vit HORS des tenants

C'est le point crucial. Toutes les autres données (examens, résultats, ingestions, utilisateurs administratifs) sont **scopées par administration**. Le profil candidat, lui, est **transversal à la plateforme**.

```
┌─────────────────────────────────────────────────────┐
│           NIVEAU PLATEFORME (transversal)           │
│                                                     │
│   ProfilCandidat  ────  Candidature  ─────┐         │
│   (identifié par CNIB)                    │         │
└───────────────────────────────────────────┼─────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────┐
│      NIVEAU TENANT (scopé par administration)       │
│                                                     │
│   OCECOS ── examens ── resultats                    │
│   Office BAC ── examens ── resultats                │
│   AGRE ── examens ── resultats                      │
└─────────────────────────────────────────────────────┘
```

### L'isolation multi-tenant reste intacte

- Chaque administration ne peut lire ou modifier que **ses propres résultats**
- Aucune administration ne peut lister les profils candidats plateforme
- Aucune administration ne peut voir "combien de candidats du tenant B ont aussi une candidature chez nous"

Seul le **candidat lui-même** peut agréger ses propres résultats, en s'authentifiant sur son profil plateforme.

### Le respect de l'autonomie éditoriale

Une administration reste **maîtresse de sa publication** :
- Elle décide quand publier
- Elle décide quoi publier
- Ses résultats non publiés (statut DRAFT) ne remontent **jamais** dans le dashboard candidat
- Elle peut à tout moment dépublier un résultat, il disparaît instantanément du dashboard candidat

Le profil candidat est **un consommateur passif** des publications officielles, pas un accès parallèle aux données.

---

## 3. Modèle de données

### Nouveau modèle `ProfilCandidat`

Vit dans un schéma `plateforme` séparé des schémas tenants pour marquer clairement la distinction.

```python
class ProfilCandidat(Base):
    __tablename__ = "profils_candidats"
    __table_args__ = {"schema": "plateforme"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Identifiants
    numero_cnib: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    # Le CNIB est l'identifiant unique national — parfait pour désambiguïser

    # Identité (chiffrée au repos si possible)
    nom_complet: Mapped[str] = mapped_column(String(200))
    date_naissance: Mapped[date] = mapped_column(Date)
    lieu_naissance: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sexe: Mapped[str | None] = mapped_column(String(1), nullable=True)  # M/F, optionnel

    # Contacts
    telephone: Mapped[str] = mapped_column(String(20), index=True)
    telephone_verifie: Mapped[bool] = mapped_column(default=False)
    operateur_telephone: Mapped[str | None]  # ORANGE / MOOV / TELECEL — détecté depuis le préfixe
    email: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    email_verifie: Mapped[bool] = mapped_column(default=False)

    # Auth
    mot_de_passe_hash: Mapped[str | None]  # optionnel : auth par OTP SMS par défaut
    derniere_connexion: Mapped[datetime | None]

    # Préférences de notification
    notifications_sms: Mapped[bool] = mapped_column(default=True)
    notifications_push: Mapped[bool] = mapped_column(default=False)
    notifications_email: Mapped[bool] = mapped_column(default=False)

    # État
    statut: Mapped[str] = mapped_column(default="ACTIF")  # ACTIF / SUSPENDU / SUPPRIME
    consentement_apdp_date: Mapped[datetime]  # obligatoire, horodaté
    consentement_apdp_version: Mapped[str]     # version des CGU acceptées

    created_at, updated_at

    # Relations
    candidatures: Mapped[list["Candidature"]] = relationship(back_populates="profil")
```

### Nouveau modèle `Candidature`

Une candidature est le **lien** entre un profil candidat et un examen d'une administration. C'est la table qui traverse la frontière plateforme/tenant.

```python
class Candidature(Base):
    __tablename__ = "candidatures"
    __table_args__ = {"schema": "plateforme"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # Références
    profil_candidat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plateforme.profils_candidats.id"), index=True
    )
    administration_id: Mapped[uuid.UUID]  # référence, pas FK cross-schema
    examen_id: Mapped[uuid.UUID]           # référence, pas FK cross-schema
    numero_recepisse: Mapped[str] = mapped_column(String(20), index=True)

    # État de la candidature
    statut_verification: Mapped[str] = mapped_column(default="EN_ATTENTE")
    # EN_ATTENTE / VERIFIE_AUTO / VERIFIE_MANUEL / REJETE
    date_verification: Mapped[datetime | None]
    methode_verification: Mapped[str | None]
    # CNIB_MATCH_AUTO / DATE_NAISSANCE / OTP_SMS / VALIDATION_MANUELLE

    # Notifications
    notifications_activees: Mapped[bool] = mapped_column(default=True)
    derniere_notification_envoyee: Mapped[datetime | None]

    # Cache des résultats (dénormalisation pour performance)
    dernier_resultat_id: Mapped[uuid.UUID | None]
    dernier_resultat_phase: Mapped[str | None]
    dernier_resultat_statut: Mapped[str | None]  # ADMIS / AJOURNE / EN_ATTENTE / etc.
    dernier_resultat_publie_at: Mapped[datetime | None]

    created_at, updated_at

    # Contraintes
    __table_args__ = (
        UniqueConstraint("administration_id", "numero_recepisse", name="uq_candidature_recepisse"),
        # Un même récépissé ne peut être lié qu'à un seul profil
    )

    # Relations
    profil: Mapped["ProfilCandidat"] = relationship(back_populates="candidatures")
```

### Table de journalisation `JournalConsultationProfil`

Pour la conformité CIL, chaque consultation du profil doit être tracée :

```python
class JournalConsultationProfil(Base):
    __tablename__ = "journal_consultations_profil"
    __table_args__ = {"schema": "plateforme"}

    id, profil_candidat_id, action, ip, user_agent, timestamp
    # Actions : LOGIN / VIEW_DASHBOARD / ADD_CANDIDATURE / DELETE_ACCOUNT / etc.
```

---

## 4. Parcours utilisateur (UX)

### 4.1 — Inscription au profil

Le parcours est **léger et mobile-first**. Aucun besoin d'email, aucun besoin de mot de passe complexe.

```
Étape 1 : "Créer mon espace candidat"
   ↓
Étape 2 : Saisie du numéro CNIB
   ↓
Étape 3 : Saisie du nom complet + date de naissance
   ↓
Étape 4 : Saisie du numéro de téléphone
   ↓
Étape 5 : Réception d'un code OTP par SMS
   ↓
Étape 6 : Validation OTP → compte créé
   ↓
Étape 7 : Acceptation des CGU / consentement protection des données (une seule case, texte clair)
   ↓
Étape 8 : Redirection vers le dashboard vide
   ↓
Étape 9 : Suggestion "Ajouter une candidature"
```

**Le compte est utilisable en moins de 90 secondes**, sur téléphone bas de gamme, sur 3G. C'est un critère non négociable.

### 4.2 — Connexion ultérieure

Deux modes proposés, l'utilisateur choisit à la première connexion :

- **Mode SMS-OTP** (par défaut, recommandé) : à chaque connexion, saisie du téléphone → OTP par SMS → connecté. Pas de mot de passe à retenir.
- **Mode mot de passe** : pour ceux qui préfèrent, avec récupération par SMS-OTP.

Session persistante 30 jours sur le même appareil (cookie ou app mobile).

### 4.3 — Ajouter une candidature

```
Étape 1 : Bouton "Ajouter une candidature"
   ↓
Étape 2 : Sélection de l'administration (OCECOS, Office BAC, AGRE...)
   ↓
Étape 3 : Sélection de l'examen ou concours dans la liste de cette administration
   ↓
Étape 4 : Saisie du numéro de récépissé
   ↓
Étape 5 : Vérification automatique de propriété (voir section 5)
   ↓
Étape 6 : Candidature ajoutée au dashboard
```

### 4.4 — Le dashboard candidat

Vue synthétique en cartes, une par candidature. Chaque carte indique :

- Le logo et le nom de l'administration
- Le libellé de l'examen ou du concours
- Le numéro de récépissé
- Le **statut actuel** (En attente de publication / Publié — voir résultat / Prochaine phase attendue)
- L'action recommandée (Voir le détail / Attendre / etc.)

Filtres possibles : année, statut, administration.

### 4.5 — Auto-découverte au moment de la publication

Deux scénarios se produisent en pratique :

**Scénario A : le candidat s'inscrit AVANT la publication.** Il ajoute sa candidature avec son numéro de récépissé. Au moment de la publication par l'administration, un job de matching détecte que sa candidature correspond à un résultat publié, met à jour le cache dans `Candidature`, et déclenche la notification.

**Scénario B : le candidat s'inscrit APRÈS la publication.** Il crée son profil avec son CNIB. Un job de matching **rétroactif** cherche dans tous les résultats déjà publiés (toutes administrations confondues) ceux qui contiennent son CNIB, et crée automatiquement les candidatures correspondantes, marquées `VERIFIE_AUTO` par correspondance CNIB.

Ce scénario B est **magique côté UX** : le candidat crée son compte, et voit apparaître instantanément tous ses résultats déjà publiés sans rien avoir à saisir. C'est un effet "wow" qui vend le service à lui seul.

---

## 5. Vérification de propriété d'un récépissé

C'est le point de sécurité le plus délicat : **empêcher qu'un tiers ne lie à son compte les récépissés d'un autre candidat**. Sans cette vérification, le service devient un outil de fouille des données personnelles publiques.

### Trois mécanismes de vérification, par ordre de préférence

**Mécanisme 1 — Correspondance CNIB automatique (préféré)**

Si les données de résultats publiées contiennent le CNIB (cas des concours Fonction publique observés dans les PDF AGRE), et si le CNIB du profil correspond au CNIB du résultat associé au récépissé saisi, la vérification est automatique et instantanée. Statut : `VERIFIE_AUTO`.

C'est la voie idéale. Elle repose sur le fait que le CNIB est présent dans les publications officielles.

**Mécanisme 2 — Correspondance date de naissance**

Si les données de résultats contiennent la date de naissance (cas des PDF observés), et que le profil candidat déclare cette même date, la vérification est validée. Statut : `VERIFIE_AUTO` avec méthode `DATE_NAISSANCE`.

Sécurité modérée : la date de naissance seule est plus facile à deviner que le CNIB, mais combinée à la connaissance du numéro de récépissé (qu'un tiers a peu de raison de connaître), c'est acceptable.

**Mécanisme 3 — Fallback OTP**

Si aucune des données précédentes n'est disponible dans les résultats publiés (cas d'examens scolaires plus légers, format libre), on demande au candidat de confirmer par un OTP envoyé sur son téléphone. Statut : `VERIFIE_MANUEL`.

Sécurité minimale : n'empêche pas un utilisateur de lier volontairement un récépissé qui n'est pas le sien. **Mesure d'atténuation :** limiter le nombre de candidatures par profil (par exemple max 20 par an) et surveiller les comptes qui accumulent des récépissés étrangers.

### Gestion des rejets

Si la vérification échoue (CNIB différent, date de naissance différente), la candidature est marquée `REJETE` et **n'apparaît pas dans le dashboard**. Un message clair invite le candidat à vérifier son numéro de récépissé ou à contacter le support.

**Anti-spam** : pas plus de 5 tentatives d'ajout de candidature en échec par jour et par profil, pour éviter les scripts d'énumération.

### Cas particulier : les administrations qui ne publient pas le CNIB

Certaines administrations peuvent choisir de publier les résultats sans mention du CNIB (protection de la vie privée). Dans ce cas, le mécanisme 1 ne peut pas être appliqué, on tombe sur mécanisme 2 ou 3. C'est un point à discuter au cas par cas dans les conventions administration.

---

## 6. Moteur de notifications

### Architecture du moteur

Un service `NotificationEngine` fonctionne en arrière-plan (Celery worker ou équivalent) et surveille deux événements :

**Événement 1 : publication d'un examen**
Quand un opérateur publie un examen dans une administration :
- Le moteur récupère toutes les candidatures associées à cet examen
- Pour chaque candidature, il vérifie si un résultat correspondant au récépissé existe
- Si oui, il met à jour le cache dans `Candidature` (`dernier_resultat_*`)
- Il envoie une notification via les canaux activés par le profil (SMS, push, email)

**Événement 2 : création d'un nouveau profil**
Quand un candidat crée son profil :
- Le moteur cherche rétroactivement les résultats déjà publiés dans toutes les administrations qui contiennent son CNIB
- Il crée automatiquement les candidatures (`VERIFIE_AUTO` par CNIB)
- Il NE renvoie PAS de notifications rétroactives pour ces résultats (ils sont déjà passés, pas de raison de spammer)
- Le candidat voit les résultats dans son dashboard dès la connexion

### Formatage des messages SMS

Le SMS est le canal principal, doit être clair et concis (160 caractères). Exemples :

```
Faso Resultats: Vos resultats BAC 2027 sont publies !
Recepisse #000456 (Office du BAC) : consultez sur
fasoresultats.bf/r/AB12
```

```
Faso Resultats: Concours AGRE Cat B - ADMISSIBLE !
Rang 12/50. Prochaine etape : epreuves ecrites le 15/08.
Details : fasoresultats.bf/r/CD34
```

Le lien court `fasoresultats.bf/r/AB12` mène directement au résultat détaillé, avec ou sans connexion selon les préférences du profil.

### Fréquence et anti-spam

- Une notification par publication d'examen, pas plus
- Regroupement possible si plusieurs examens publiés le même jour pour un candidat
- Respect strict des horaires (pas de SMS après 22h, pas avant 6h)
- Possibilité pour le candidat de désactiver totalement les notifications par candidature

---

## 7. Conformité CIL

### Statut de Faso Résultats vis-à-vis du profil candidat

Ici, la situation change par rapport aux données d'examens (où Faso Résultats est sous-traitant). Sur le **profil candidat**, Faso Résultats est **responsable de traitement** au sens de la loi 001-2021, car c'est la plateforme qui collecte, stocke et utilise directement ces données.

Cela implique :

- **Déclaration obligatoire à la CIL** avant tout lancement en production
- **Politique de confidentialité** claire et accessible
- **Consentement explicite** du candidat au moment de l'inscription (horodaté et versionné)
- **Droit d'accès, de rectification, de portabilité et de suppression** activables depuis le compte
- **Notification de violation** à la CIL dans les 72 heures en cas d'incident

### Données particulièrement sensibles

Le **numéro CNIB** est une donnée sensible. Il doit être :
- Chiffré au repos (colonne chiffrée, ou base entière chiffrée)
- Jamais loggué en clair
- Jamais transmis à un tiers en dehors du processus de matching
- Purgé à la suppression du compte

Idem pour la **date de naissance**.

### Droit à l'oubli

Le candidat peut à tout moment supprimer son compte depuis son dashboard. La suppression :

- Supprime immédiatement le profil et ses candidatures
- Supprime le journal des consultations liées à ce profil
- N'affecte PAS les résultats publiés par les administrations (qui restent la propriété des administrations, gérées selon leur propre politique)

### Interaction avec la politique de résiliation d'administration

Rappel : quand une administration résilie son contrat, **ses résultats historiques sont supprimés**.

Impact sur les profils candidats : les candidatures liées à cette administration deviennent orphelines. Traitement :
- Les candidatures liées sont marquées `ADMINISTRATION_RESILIEE`
- Le cache des résultats (`dernier_resultat_*`) est purgé
- Le candidat voit un message clair : *"Les résultats de cet examen ne sont plus disponibles sur Faso Résultats. Contactez [administration] directement."*
- La candidature elle-même est conservée 6 mois puis supprimée, sauf action du candidat

---

## 8. Sécurité

### Points critiques

- **Bcrypt** pour les mots de passe (si utilisés)
- **Chiffrement au repos** du CNIB, date de naissance, téléphone (colonne chiffrée AES-256)
- **OTP SMS** : codes à 6 chiffres, valides 5 minutes, invalidés après usage, max 3 tentatives
- **Rate limiting sévère** sur les endpoints d'inscription et d'ajout de candidature
- **Détection d'énumération** : compte qui ajoute plus de 5 candidatures par jour ou qui a plus de 30% de candidatures rejetées → suspension automatique pour investigation
- **Logs d'audit complets** : chaque accès au dashboard, chaque modification, chaque tentative d'ajout de candidature
- **Isolation session** : un token de session lié à un device fingerprint, pas juste à un cookie

### Anti-abus

Deux risques majeurs à couvrir :

**Risque 1 — Scraping de données personnelles.** Un acteur malveillant crée des profils avec des CNIB aléatoires pour extraire des données. Mesures : vérification téléphone obligatoire, un profil par CNIB, un profil par numéro de téléphone, limitation stricte des tentatives.

**Risque 2 — Prise de contrôle de compte.** Un attaquant obtient le CNIB et le téléphone d'une victime, crée un compte à sa place. Mesures : lors de la première connexion, alerte au vrai propriétaire par SMS *"Un compte vient d'être créé avec votre CNIB. Si ce n'est pas vous, cliquez ici."* + double vérification lors des actions sensibles.

---

## 9. Implications business

### Pour les administrations

Le profil candidat devient un **argument commercial supplémentaire** face aux administrations prospectées :

*"En rejoignant Faso Résultats, vos publications atteindront immédiatement les X 000 candidats déjà inscrits sur la plateforme, sans effort de communication supplémentaire de votre part."*

Pour la première administration signée (OCECOS ou Office du BAC), cet argument ne joue pas encore. Mais à partir de la 3ème administration, l'effet réseau devient un vrai levier de vente.

### Pour les candidats

Le service est **gratuit et opt-in**. Cela évite toute perception de contrainte. Un candidat qui préfère la consultation anonyme par récépissé continue de pouvoir le faire.

### Monétisation possible en phase avancée

En phase 3+ , le profil candidat peut ouvrir des services annexes payants (opt-in), toujours dans le respect des exigences de la CIL :

- **Alertes sur nouveaux concours à venir** : *"Un concours ENAM catégorie B est ouvert du 15/07 au 30/07. Inscrivez-vous."*
- **Orientation post-résultat** : recommandations d'écoles, aide au dossier
- **Attestations vérifiables** avec QR code, générées à la demande
- **Coaching de préparation aux concours** en partenariat avec des écoles privées (revenus d'affiliation)

Ces services doivent rester **facultatifs** et ne jamais compromettre l'usage de base.

---

## 10. Impact sur le MVP et la roadmap

### En MVP (phase 1) — l'essentiel

- Modèle `ProfilCandidat` et `Candidature` complets
- Inscription par CNIB + téléphone + OTP SMS
- Dashboard candidat basique
- Ajout de candidature avec vérification par CNIB ou date de naissance
- Auto-découverte des résultats déjà publiés par matching CNIB
- Notifications SMS lors des publications futures (dépend de l'implémentation SMS déjà en phase 2)

### Repoussé en phase 2

- Notifications push mobile (nécessite l'app mobile)
- Notifications email
- Mode mot de passe classique (le mode OTP-only suffit au MVP)
- Statistiques et graphiques dans le dashboard

### Repoussé en phase 3

- Services annexes payants
- Attestations vérifiables avec QR code
- Alertes proactives sur les concours à venir

### Volume à anticiper

Estimation conservatrice : si 5% des candidats aux grands examens s'inscrivent en année 1, cela représente :
- BAC ~80 000 × 5% = 4 000 profils
- BEPC ~120 000 × 5% = 6 000 profils
- Concours ~30 000 × 5% = 1 500 profils
- **Total année 1 : ~10 000 à 15 000 profils actifs**

En année 3, avec effet réseau et 6 administrations clientes, on peut viser **100 000 à 200 000 profils actifs**. La plateforme doit être dimensionnée en conséquence dès le MVP (indexes, cache, dénormalisation dans `Candidature`).

---

## 11. Ce que Claude Code doit intégrer concrètement

Ordre de travail recommandé, à réaliser **après le pivot multi-tenant** décrit dans `PIVOT_SAAS_B2G.md` :

1. **Créer un schéma PostgreSQL séparé `plateforme`** distinct des schémas tenants
2. **Créer les modèles `ProfilCandidat`, `Candidature`, `JournalConsultationProfil`** dans le schéma `plateforme`
3. **Ajouter le chiffrement au repos** des champs `numero_cnib`, `date_naissance`, `telephone` avec une bibliothèque type `sqlalchemy-utils` (StringEncryptedType) ou une extension PostgreSQL comme `pgcrypto`
4. **Créer le service `AuthCandidatService`** avec :
   - Génération et envoi d'OTP SMS (stub pour l'instant, à intégrer avec le vrai fournisseur SMS en phase 2)
   - Validation d'OTP
   - Création de session avec JWT dédié (aud = "candidat", distinct de l'aud "admin")
5. **Créer les endpoints publics candidat** :
   - `POST /api/v1/candidat/inscription` (étapes 1-6 du parcours)
   - `POST /api/v1/candidat/login` (envoi OTP)
   - `POST /api/v1/candidat/otp/verify`
   - `GET /api/v1/candidat/me` (profil courant)
   - `PATCH /api/v1/candidat/me` (préférences notifications, etc.)
   - `DELETE /api/v1/candidat/me` (droit à l'oubli — cascade sur candidatures et journal)
   - `GET /api/v1/candidat/candidatures` (dashboard)
   - `POST /api/v1/candidat/candidatures` (ajout)
   - `DELETE /api/v1/candidat/candidatures/{id}` (suppression manuelle)
6. **Créer le `VerificationService`** avec les trois mécanismes de la section 5, dans l'ordre CNIB → date de naissance → OTP fallback
7. **Créer le `MatchingService`** qui :
   - À la publication d'un examen : parcourt les candidatures liées, met à jour les caches
   - À la création d'un profil : parcourt les résultats déjà publiés dans tous les tenants pour matcher par CNIB (rétroactif)
8. **Créer le `NotificationEngine`** avec :
   - Un stub d'envoi SMS (à remplacer en phase 2 par l'intégration Orange/Moov/Telecel)
   - Respect des horaires (pas entre 22h et 6h)
   - Deduplication (une seule notif par événement par candidature)
9. **Créer un frontend candidat minimal** : page d'inscription, page de connexion OTP, dashboard avec cartes candidature. UX mobile-first, léger.
10. **Créer les tests d'isolation supplémentaires** :
    - Un profil candidat peut voir SES résultats à travers tous les tenants ✅
    - Un profil candidat NE peut PAS voir les résultats d'un autre candidat ❌
    - Une administration NE peut PAS lister les profils candidats plateforme ❌
    - La suppression d'un profil purge bien toutes ses candidatures et son journal ✅
11. **Créer `docs/CIL_PROFIL_CANDIDAT.md`** documentant la conformité CIL pour ce périmètre spécifique (base légale, finalité, durée de conservation, exercice des droits)
12. **Mettre à jour le seed** avec 3 profils candidat fictifs et 5-6 candidatures liées aux administrations du seed (dont une qui matche automatiquement par CNIB avec un résultat déjà publié)

### Points d'attention pour l'implémentation

- Le chiffrement au repos ne doit pas compromettre les recherches par CNIB (indexer sur un hash déterministe du CNIB, pas sur le CNIB en clair)
- La suppression d'un profil doit être **effective sous 24h** (job de purge quotidien), pas une simple mise à jour de statut
- Le journal d'audit doit être **immutable** (append-only, jamais modifié ni supprimé sauf via la purge du profil)
- L'accès aux endpoints candidat doit être totalement isolé des routes admin (deux middlewares d'authentification distincts)

---

*Fin de la spécification — version 1.0. Cette fonctionnalité est probablement le différenciateur principal du produit sur son marché.*
