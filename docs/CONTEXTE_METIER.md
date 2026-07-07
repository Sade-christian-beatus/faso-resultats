# Contexte métier — Faso Résultats

> Document de référence sur le paysage concurrentiel (plateformes gouvernementales
> existantes) et la cartographie complète des examens et concours au Burkina Faso.
>
> ⚠️ **Ce document précède le pivot SaaS B2G du 2026-07-05.** Ses conclusions de
> pitch (ex. "Faso Résultats devient LA plateforme de consultation individuelle
> pour 95% du marché") reflètent le positionnement B2C d'origine, remplacé depuis
> par un positionnement SaaS B2G — voir `docs/PIVOT_SAAS_B2G.md` pour le
> positionnement actuel qui fait autorité. La cartographie du paysage concurrentiel
> ci-dessous (quel examen est couvert par quelle plateforme) reste valable et utile ;
> seule la conclusion stratégique sur ce qu'en fait Faso Résultats est obsolète.
> Le CEP, en particulier, reste hors périmètre du projet dans les deux
> positionnements (voir `docs/PIVOT_SAAS_B2G.md` et `docs/ROADMAP.md`).

---

## 1. Nouvelle donnée concurrentielle : SIGEC-CEP

### Ce qui a changé
Le **Ministère de l'Enseignement de Base, de l'Alphabétisation et de la Promotion des Langues Nationales (MEBAPLN)** a lancé le **13 juin 2026** une plateforme officielle de consultation des résultats accessible à l'adresse :

**https://www.resultats.examens.gov.bf/** (nom du système : **SIGEC-CEP**)

Il existe également **https://www.econcours-pro.gov.bf/** pour l'inscription en ligne aux concours professionnels.

### Périmètre actuel de SIGEC-CEP (juillet 2026)
- Consultation **uniquement du CEP** (Certificat d'Études Primaires), session 2026
- Saisie de : numéro de PV + date de naissance + session
- Tableau de bord de statistiques globales
- Canal web uniquement

### Ce que SIGEC-CEP ne fait PAS (fenêtre d'opportunité)
- Aucun canal SMS
- Aucune application mobile
- Aucune notification proactive (l'utilisateur doit rafraîchir la page manuellement)
- Aucun canal USSD
- Aucune vérification d'authenticité par QR code
- Aucune couverture du BEPC, du BAC, des examens professionnels ou des concours
- Aucune valeur ajoutée post-résultat (orientation, calendrier des concours à venir, etc.)

### Cartographie complète des canaux gouvernementaux existants

Au-delà de SIGEC-CEP, l'écosystème actuel de publication des résultats au Burkina Faso est **fragmenté entre plusieurs plateformes et canaux distincts**, chacun rattaché à un ministère différent. Cette fragmentation est un problème pour l'usager final et une opportunité pour Faso Résultats en tant qu'agrégateur unifié.

**Examens scolaires (DGEC / MENAPLN / MEBAPLN)**

| Examen | Plateforme actuelle | Format |
|--------|---------------------|--------|
| CEP | https://www.resultats.examens.gov.bf/ (SIGEC-CEP) | Consultation individuelle en ligne (PV + date de naissance + session) |
| BEPC | https://www.education.gov.bf/accueil (annonces) + affichage physique dans les centres | Communiqués + listes papier |
| BAC | https://www.education.gov.bf/accueil (annonces) + affichage physique dans les centres | Communiqués + listes papier |

**Concours Fonction publique (Ministère de la Fonction Publique)**

- Site institutionnel : https://www.fonction-publique.gov.bf/
- Plateforme e-Concours : https://www.econcours.gov.bf/ — **gère UNIQUEMENT les inscriptions** aux concours (pas la publication des résultats)
- Plateforme e-Concours-Pro : https://www.econcours-pro.gov.bf/ — inscriptions aux concours professionnels de promotion interne
- Publication des résultats : **communiqués officiels PDF téléchargeables** depuis fonction-publique.gov.bf, classés par centre de composition et par ordre de mérite ou alphabétique. **Aucune plateforme de consultation individuelle de résultats n'existe côté Fonction publique.**

⚠️ **Clarification cruciale** : `econcours.gov.bf` et `econcours-pro.gov.bf` sont des plateformes d'**inscription en ligne**, pas de consultation de résultats. Un candidat qui a passé un concours doit aujourd'hui télécharger un PDF potentiellement long (des milliers de noms) et y chercher le sien manuellement. **C'est un point de douleur utilisateur massif** et une opportunité produit majeure pour Faso Résultats.

**Corps paramilitaires — cartographie détaillée par corps**

| Corps | Ministère de tutelle | Publication des résultats (⚠️ pas les inscriptions) |
|-------|---------------------|-----------------------------------------------------|
| Douanes | Fonction Publique + Finances | PDF sur fonction-publique.gov.bf uniquement |
| Sécurité Pénitentiaire (GSP) | Fonction Publique + Justice | PDF sur fonction-publique.gov.bf uniquement |
| Eaux et Forêts | Fonction Publique + Environnement | PDF sur fonction-publique.gov.bf uniquement |
| Police Nationale | Ministère de la Sécurité | https://www.securite.gov.bf/ + Facebook officielle (https://www.facebook.com/msecubf/) |
| Armée Nationale | Ministère de la Défense | Communiqués RTB/Sidwaya + affichage physique dans camps et gouvernorats |
| Gendarmerie Nationale | Ministère de la Défense | Idem Armée (piloté par État-major Général des Armées) |

**Points remarquables :**
- **Aucun corps paramilitaire ni concours de la Fonction publique ne dispose aujourd'hui d'une plateforme de consultation individuelle de résultats**. Les candidats doivent télécharger de longs PDF et y chercher manuellement leur nom. Cette absence est massive et couvre l'intégralité du périmètre des concours nationaux.
- La **Police Nationale utilise Facebook** comme canal officiel de diffusion — canal social, non structuré, difficile à consulter a posteriori
- L'**Armée et la Gendarmerie n'ont AUCUN canal en ligne** — publication uniquement par voie de presse (RTB, Sidwaya) et affichage physique dans les camps militaires et gouvernorats des chefs-lieux de région
- **Le paysage se résume ainsi** : SIGEC-CEP a couvert un seul examen (CEP) au format consultation individuelle. Tout le reste — CEP inclus dans les autres années, BEPC, BAC, examens professionnels, concours directs, concours professionnels, tous les corps paramilitaires — reste au format PDF téléchargeable ou communiqué. **Le marché de la consultation individuelle par PV est donc à 95% ouvert.**

### Implications stratégiques pour Faso Résultats

Après clarification que `econcours.gov.bf` gère uniquement les inscriptions et non les résultats, le positionnement du projet se simplifie et se renforce :

1. **Faso Résultats devient LA plateforme de consultation individuelle** pour tout ce qui n'est pas le CEP — soit 95% du marché des examens et concours nationaux
2. Le CEP reste couvert par SIGEC ; Faso Résultats peut soit proposer une couche complémentaire (SMS, notifications, mobile) via partenariat, soit simplement rediriger vers SIGEC avec transparence
3. **La proposition de valeur est claire et défendable** : transformer les PDF officiels illisibles sur mobile en une consultation individuelle instantanée par numéro de PV, avec canal SMS et notifications proactives

**Formulation du pitch simplifiée** : *"Aujourd'hui, un candidat au BAC ou à un concours doit télécharger un PDF de plusieurs mégaoctets et y chercher son nom parmi des milliers. Faso Résultats transforme ces PDF en consultation instantanée par numéro de PV, avec réponse par SMS. C'est le complément naturel des inscriptions e-concours et de SIGEC-CEP."*

**Conséquence pour l'architecture technique :** le pipeline d'ingestion PDF devient **le cœur stratégique du projet**. Chaque PDF publié sur `fonction-publique.gov.bf`, `securite.gov.bf` ou dans la presse doit pouvoir être ingéré rapidement, parsé, structuré, validé et publié. La qualité et la vitesse de ce pipeline sont l'avantage compétitif principal. L'abstraction `ResultsSource` reste pertinente mais l'implémentation prioritaire est `FileImportSource` avec un parser PDF robuste, et éventuellement `EconcoursPdfScraperSource` (surveillance automatique des nouvelles publications PDF) en phase 2.

---

## 2. Cartographie complète du périmètre métier

Le projet doit couvrir un écosystème plus large que ce qui avait été initialement documenté. Voici la taxonomie officielle des examens et concours au Burkina Faso.

### 2.1 — Examens scolaires et universitaires
Supervisés par la **DGEC (Direction Générale des Examens et Concours)** au sein du Ministère de l'Éducation nationale.

| Code | Libellé | Niveau | Statut concurrentiel |
|------|---------|--------|----------------------|
| CEP | Certificat d'Études Primaires | Fin du primaire | ⚠️ Couvert par SIGEC-CEP |
| BEPC | Brevet d'Études du Premier Cycle | Fin du 1er cycle secondaire | ✅ Non couvert |
| BEP | Brevet d'Études Professionnelles | Enseignement technique | ✅ Non couvert |
| CAP | Certificat d'Aptitude Professionnelle | Formation professionnelle | ✅ Non couvert |
| BAC | Baccalauréat (Général, Technologique, Professionnel) | Fin du secondaire | ✅ Non couvert |
| CQP | Certificat de Qualification Professionnelle | Qualification pro | ✅ Non couvert |
| BQP | Brevet de Qualification Professionnelle | Qualification pro | ✅ Non couvert |
| BPT | Brevet Professionnel de Technicien | Qualification pro | ✅ Non couvert |

**Note sur le BAC :** trois séries à gérer distinctement — Générale (A, C, D, E), Technologique (F, G, H) et Professionnelle. Chaque série a ses propres épreuves et son propre calendrier.

### 2.2 — Concours de la Fonction Publique
Gérés par le **Ministère de la Fonction Publique, du Travail et de la Protection sociale**. Ouverts selon les besoins budgétaires annuels.

**a) Concours Directs** (accès direct à l'emploi public, ouverts à tout candidat éligible)

| Catégorie | Niveau de diplôme requis | Exemples de corps |
|-----------|--------------------------|-------------------|
| A | Enseignement supérieur (Master, Licence) | Administrateurs civils, Inspecteurs, Enseignants du supérieur, Ingénieurs |
| B | BAC | Secrétaires de direction, Contrôleurs |
| C | BEPC | Adjoints administratifs, Agents de bureau |
| D | CEP | Agents de recouvrement, Plantons |

**b) Concours Professionnels** (promotion interne pour les agents de l'État déjà en poste, souhaitant changer de grade ou progresser dans leur corps)

⚠️ La plateforme `econcours-pro.gov.bf` est déjà positionnée sur l'**inscription** aux concours professionnels. À vérifier si elle couvre aussi la **publication des résultats** — si oui, périmètre partiellement concurrentiel ; si non, opportunité claire pour Faso Résultats.

### 2.3 — Concours Paramilitaires et Spécifiques
Chaque corps organise ses propres concours, avec critères d'aptitude physique et d'âge spécifiques. Ces concours sont **hautement demandés** par la jeunesse burkinabè et constituent probablement le segment le plus rentable pour un service SMS.

- Armée / Forces Armées Nationales
- Police Nationale
- Douanes
- Gendarmerie Nationale
- Eaux et Forêts
- Sécurité Pénitentiaire

Chacun a son ministère de tutelle et son propre jury — pas de centralisation. Ce sont potentiellement **6 partenariats distincts** à négocier, mais aussi 6 opportunités de valeur unitaire.

### 2.4 — Publication séquentielle des concours paramilitaires (critique pour le modèle de données)

Contrairement aux examens scolaires qui ont un résultat unique (admis/ajourné/second tour), les concours paramilitaires se déroulent en **trois phases successives**, chacune donnant lieu à une publication distincte :

1. **Résultats des épreuves sportives / physiques** — liste des candidats aptes admis à composer pour les épreuves écrites
2. **Résultats d'admissibilité (après l'écrit)** — liste des candidats retenus pour passer la visite médicale d'incorporation
3. **Résultats d'admission définitive** — liste finale des candidats déclarés admis, sous réserve d'une enquête de moralité positive

**Conséquence pour le modèle de données :** un candidat à un concours paramilitaire n'a pas un seul résultat, mais **potentiellement trois états successifs** au fil d'une même session. Un candidat peut apparaître dans la publication 1 (apte au sport), disparaître de la publication 2 (échec à l'écrit) — la plateforme doit refléter fidèlement cette temporalité et permettre à un candidat de consulter son statut à chaque phase.

Cela implique :
- Une notion de **phase de publication** attachée à chaque résultat
- Un mécanisme d'**historique** permettant de conserver toutes les publications intermédiaires
- Une capacité à **notifier proactivement** à chaque nouvelle phase (fonctionnalité SMS clé)
- Une **UX claire** côté utilisateur pour comprendre à quelle phase il se trouve et quelles sont les phases restantes

---

## 3. Impact sur le modèle de données

Le modèle initialement prévu était trop générique. Voici les ajustements à apporter aux modèles SQLAlchemy et aux migrations Alembic.

### 3.1 — Enum `TypeExamen` à enrichir

Remplacer l'enum initial par une hiérarchie plus fine :

```python
class CategorieExamen(str, Enum):
    EXAMEN_SCOLAIRE = "EXAMEN_SCOLAIRE"
    CONCOURS_DIRECT = "CONCOURS_DIRECT"
    CONCOURS_PROFESSIONNEL = "CONCOURS_PROFESSIONNEL"
    CONCOURS_PARAMILITAIRE = "CONCOURS_PARAMILITAIRE"

class TypeExamen(str, Enum):
    # Scolaires
    CEP = "CEP"
    BEPC = "BEPC"
    BEP = "BEP"
    CAP = "CAP"
    BAC_GENERAL = "BAC_GENERAL"
    BAC_TECHNOLOGIQUE = "BAC_TECHNOLOGIQUE"
    BAC_PROFESSIONNEL = "BAC_PROFESSIONNEL"
    CQP = "CQP"
    BQP = "BQP"
    BPT = "BPT"
    # Concours directs Fonction publique
    CD_CATEGORIE_A = "CD_CATEGORIE_A"
    CD_CATEGORIE_B = "CD_CATEGORIE_B"
    CD_CATEGORIE_C = "CD_CATEGORIE_C"
    CD_CATEGORIE_D = "CD_CATEGORIE_D"
    # Concours professionnels (promotion interne)
    CONCOURS_PROFESSIONNEL = "CONCOURS_PROFESSIONNEL"
    # Concours paramilitaires
    ARMEE = "ARMEE"
    POLICE = "POLICE"
    DOUANES = "DOUANES"
    GENDARMERIE = "GENDARMERIE"
    EAUX_FORETS = "EAUX_FORETS"
    SECURITE_PENITENTIAIRE = "SECURITE_PENITENTIAIRE"
    # Extensible
    AUTRE = "AUTRE"
```

### 3.2 — Nouveaux champs sur `examens`

- `categorie` (CategorieExamen) — pour filtrer par grande famille
- `type` (TypeExamen) — précis
- `serie` (text, nullable) — utile pour BAC (A, C, D, E, F, G, H) et concours (corps spécifique)
- `ministere_tutelle` (text) — traçabilité de l'organisme responsable
- `source_donnees` (enum: SIGEC_API, FILE_IMPORT, GOUV_PDF_MONITOR, FACEBOOK_SCRAPING, PRESS_MONITORING, MANUAL) — d'où viennent les résultats
- `partenariat_officiel` (boolean) — indique si le contenu est officiellement reconnu par un partenariat signé
- `phases_publication` (jsonb) — liste des phases prévues pour ce type d'examen (voir 3.4)

### 3.3 — Nouvel enum `PhasePublication`

Pour gérer la temporalité des concours paramilitaires (voir section 2.4) :

```python
class PhasePublication(str, Enum):
    RESULTAT_UNIQUE = "RESULTAT_UNIQUE"        # Examens scolaires simples
    EPREUVES_SPORTIVES = "EPREUVES_SPORTIVES"  # Phase 1 paramilitaires
    ADMISSIBILITE = "ADMISSIBILITE"             # Phase 2 (après écrit)
    ADMISSION_DEFINITIVE = "ADMISSION_DEFINITIVE"  # Phase 3 (finale)
    SECOND_TOUR = "SECOND_TOUR"                 # BEPC/BAC uniquement
```

### 3.4 — Modifications du modèle `resultats`

Ajouter :
- `phase` (PhasePublication) — indispensable pour distinguer les 3 étapes des concours paramilitaires
- `date_publication_phase` (timestamp) — moment où cette phase a été publiée
- `phase_suivante_attendue` (PhasePublication, nullable) — pour informer l'utilisateur des prochaines étapes

Contrainte : l'index unique existant `(examen_id, numero_pv, jury)` doit devenir `(examen_id, numero_pv, jury, phase)` pour permettre plusieurs enregistrements d'un même candidat au fil des phases.

### 3.5 — Nouveau modèle `Corps` (optionnel mais utile)

Pour les concours (surtout paramilitaires et directs), un candidat postule à un **corps précis** (ex: "Inspecteur des Impôts", "Sous-officier Gendarmerie"). Prévoir une table `corps` référencée par les résultats de concours simplifie les recherches et statistiques ultérieures. À implémenter en phase 2 uniquement pour ne pas alourdir le MVP.

---

## 4. Ajustements de la roadmap

### 4.1 — Priorisation des segments à couvrir (actualisée)

Puisque `econcours.gov.bf` gère uniquement les inscriptions, TOUS les concours restent à consulter au format PDF. La priorisation dépend donc du volume de candidats et de la facilité d'accès aux fichiers sources :

1. **BEPC et BAC** — 🟢 segments les plus massifs (dizaines de milliers de candidats/an), aucune consultation individuelle en ligne aujourd'hui, forte médiatisation. Point d'entrée MVP idéal si accès aux listes officielles OCECOS/DGEC obtenu.
2. **Armée et Gendarmerie (Ministère de la Défense)** — 🟢 forte opportunité : aucun canal en ligne actuellement (uniquement RTB, Sidwaya et affichage physique dans les camps). Milliers de candidats concernés à chaque recrutement. Modèle SMS particulièrement pertinent (les candidats sont souvent hors de Ouagadougou).
3. **Police Nationale** — 🟢 diffusion actuelle via Facebook et site du Ministère de la Sécurité, sans consultation individuelle structurée. Forte volumétrie, forte demande.
4. **Concours paramilitaires civils (Douanes, GSP, Eaux et Forêts)** — 🟢 aucune consultation individuelle en ligne, uniquement PDF sur fonction-publique.gov.bf. Contrairement à ce qui était initialement supposé, `econcours.gov.bf` ne diffuse pas ces résultats.
5. **Concours directs Fonction publique (catégories A, B, C, D)** — 🟢 même situation : PDF uniquement sur fonction-publique.gov.bf, aucune consultation individuelle. Volumes importants, très forte tension autour des résultats.
6. **Examens professionnels (BEP, CAP, CQP, BQP, BPT)** — 🟡 peu couverts médiatiquement, opportunité d'être seul acteur mais volumes plus faibles
7. **Concours professionnels (promotion interne)** — 🟡 econcours-pro.gov.bf gère les inscriptions ; les résultats sont probablement au même format PDF que les autres, donc opportunité similaire à confirmer
8. **CEP** — 🔴 SIGEC-CEP couvre déjà le web ; approche uniquement en couche SMS complémentaire via partenariat MEBAPLN

**Conclusion stratégique importante :** avec la clarification sur econcours.gov.bf, le marché adressable de Faso Résultats est **beaucoup plus large que prévu**. À l'exception du CEP (couvert par SIGEC), aucun examen ni concours du Burkina Faso ne dispose aujourd'hui d'une consultation individuelle par numéro de PV. Le projet peut viser l'ensemble de cet écosystème sans concurrence directe.

### 4.2 — Abstraction de source de données (élargie)

Le pipeline d'ingestion doit être conçu comme une interface `ResultsSource` avec plusieurs implémentations possibles, reflétant la diversité des canaux gouvernementaux :

```python
from abc import ABC, abstractmethod

class ResultsSource(ABC):
    """Abstraction pour la récupération des résultats, permettant d'unifier
    l'ingestion depuis toutes les sources gouvernementales existantes."""

    @abstractmethod
    async def fetch_results(self, examen_id: str) -> list[ResultatBrut]:
        ...

class FileImportSource(ResultsSource):
    """Ingestion par upload manuel de fichiers PDF ou Excel — cas principal du MVP."""
    ...

class SigecApiSource(ResultsSource):
    """Consommation de l'API SIGEC-CEP si un partenariat officiel est conclu.
    À implémenter uniquement si accord signé avec le MEBAPLN."""
    ...

class GouvPdfMonitorSource(ResultsSource):
    """Surveillance automatique des publications PDF officielles.
    NB : econcours.gov.bf gère uniquement les inscriptions, pas les résultats.
    Les vrais canaux de résultats à surveiller sont :
    - fonction-publique.gov.bf (concours directs, professionnels, paramilitaires civils)
    - securite.gov.bf (Police Nationale)
    - education.gov.bf (annonces BEPC/BAC — souvent redirigent vers PDF)
    Un scraper poli (respect robots.txt, délai entre requêtes) identifie les
    nouveaux PDF et déclenche le pipeline d'ingestion standard.
    À valider juridiquement avant activation."""
    ...

class FacebookMonitorSource(ResultsSource):
    """Surveillance de la page Facebook officielle du Ministère de la Sécurité
    (msecubf) qui publie régulièrement les résultats de la Police Nationale
    avec les liens de téléchargement. À évaluer : Graph API vs scraping,
    fiabilité, conformité aux CGU Facebook.
    Alternative pragmatique : monitoring manuel par un opérateur admin."""
    ...

class PressMonitoringSource(ResultsSource):
    """Suivi des publications RTB et Sidwaya pour les résultats Armée/Gendarmerie
    qui ne sont diffusés que par voie de presse. En pratique, un opérateur
    admin ingère manuellement les communiqués — cette classe formalise la
    traçabilité de la source."""
    ...
```

**Recommandation MVP :** implémenter uniquement `FileImportSource` en phase 1. Les autres sources sont documentées comme classes abstraites ou stubs pour ne pas contraindre l'architecture future, mais leur implémentation dépend d'analyses juridiques, techniques et de partenariats à établir.

**Point d'attention légal :** le scraping de sites gouvernementaux est **toléré** tant qu'il respecte les CGU et ne surcharge pas les serveurs, mais il vaut mieux formaliser une convention avec les ministères concernés avant tout déploiement en production.

### 4.3 — Positionnement du canal SMS renforcé

Le canal SMS devient un **différenciateur stratégique majeur** face à SIGEC. Il doit être :

- Priorisé dès la phase 2 (et non repoussé en phase tardive)
- Documenté comme un argument commercial dans tous les supports (note conceptuelle, pitch aux ministères)
- Conçu pour être proposable en marque blanche (option "SMS Faso Résultats powered by [nom société]" ou intégration silencieuse)

### 4.4 — Nouvelle fonctionnalité : agrégation et suivi longitudinal

Puisque un candidat passe généralement plusieurs examens et concours dans sa vie (CEP → BEPC → BAC → concours), prévoir dès le modèle de données la possibilité d'associer plusieurs résultats à un **profil candidat unifié** (identifié par nom + date de naissance + numéro d'identification s'il existe). Utile pour :

- La fonctionnalité de pré-inscription aux notifications qui devient plus riche
- Les futures fonctionnalités d'orientation post-résultat
- Un service B2B d'analyse de parcours pour les écoles

À prévoir dans le modèle de données mais à ne pas exposer côté utilisateur avant qu'une politique claire de gestion du consentement APDP soit établie.

---

## 5. Impact sur le positionnement commercial

Reformulation du pitch à intégrer dans les futurs supports (note conceptuelle, présentations, README public) :

**Ancien pitch :** *"Une plateforme de consultation des résultats d'examens et concours au Burkina Faso, accessible via web, mobile et SMS."*

**Nouveau pitch :** *"Une couche complémentaire d'accès aux résultats d'examens et concours, couvrant le BEPC, le BAC, les examens professionnels et les concours administratifs et paramilitaires non desservis par les plateformes officielles existantes, avec les canaux SMS et mobile que celles-ci ne proposent pas. Compatible en partenariat avec SIGEC pour le CEP."*

Cette formulation permet de :
- Reconnaître explicitement l'existant (crédibilité)
- Se positionner sur le complément et non la concurrence
- Justifier techniquement la valeur ajoutée (SMS, mobile, périmètre étendu)

---

## 6. Ce que Claude Code doit intégrer concrètement

1. **Créer ou mettre à jour `docs/CONTEXTE_METIER.md`** avec le contenu de cette note.
2. **Adapter le modèle `examens`** : ajouter `categorie`, `type` (nouveau enum), `serie`, `ministere_tutelle`, `source_donnees` (avec toutes les valeurs), `partenariat_officiel`, `phases_publication`.
3. **Étendre l'enum `TypeExamen`** avec la taxonomie complète listée en section 3.1.
4. **Créer le nouvel enum `PhasePublication`** décrit en section 3.3.
5. **Modifier le modèle `resultats`** pour intégrer les champs `phase`, `date_publication_phase`, `phase_suivante_attendue`, et adapter l'index unique en `(examen_id, numero_pv, jury, phase)`.
6. **Introduire l'abstraction `ResultsSource`** dans `app/services/sources/` avec :
   - `FileImportSource` implémenté (cas actuel, cœur stratégique du projet)
   - `SigecApiSource`, `GouvPdfMonitorSource`, `FacebookMonitorSource`, `PressMonitoringSource` en classes abstraites documentées, non implémentées, avec docstrings expliquant leur rationale
7. **Mettre à jour le seed** pour créer au moins :
   - Un CEP (source SIGEC_API, marqué comme partenaire potentiel)
   - Un BEPC et un BAC (source FILE_IMPORT, priorité MVP)
   - Un concours direct catégorie A (source FILE_IMPORT)
   - Un concours paramilitaire Armée avec **les trois phases** représentées (sportives, admissibilité, admission définitive) pour tester le modèle temporel
   - Un concours Police avec source FACEBOOK_SCRAPING pour valider l'énumération
8. **Créer un référentiel statique** `app/data/reference/organismes.py` avec la table des ministères de tutelle par type d'examen (utile pour affichage et statistiques).
9. **Mettre à jour `README.md`** avec le nouveau pitch de positionnement.
10. **Ajouter dans `docs/ARCHITECTURE.md`** :
    - La section "Sources de données" expliquant l'abstraction `ResultsSource` et sa raison d'être stratégique
    - La section "Phases de publication" expliquant le modèle temporel des concours paramilitaires
    - La cartographie complète des plateformes gouvernementales existantes (référence pour comprendre le positionnement du produit)
11. **Ne rien changer** au reste de la stack ni aux fonctionnalités déjà décidées — le repositionnement n'invalide pas les choix techniques précédents, il les précise.

---

## 7. Bonus : impact UX à intégrer côté frontend

Ces éléments ne sont pas prioritaires pour la première session de dev, mais à garder à l'esprit pour les itérations UI :

- **Sélecteur d'examen à deux niveaux** : catégorie (scolaire / concours direct / concours paramilitaire) puis type précis. Évite un menu déroulant de 20 lignes.
- **Indicateur de phase** pour les concours paramilitaires : bandeau clair "Vous êtes à l'étape 2 sur 3 — épreuves écrites. La visite médicale est la prochaine étape."
- **Message pédagogique** quand un candidat cherche un CEP : "Le CEP est également consultable sur la plateforme officielle du ministère : resultats.examens.gov.bf" — transparence + crédibilité.
- **Lien vers la source officielle** dans chaque résultat : renforce la confiance et évite les accusations de falsification.
- **Affichage clair du canal officiel** pour les corps non couverts numériquement : "Pour l'Armée, la publication officielle se fait dans les camps militaires. Nous relayons ici les listes publiées par communiqué de presse."

---

*Version 1.0 — 2026-07-04.*
