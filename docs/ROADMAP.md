# Feuille de route — Faso Résultats

> Détaille les phases 2 à 4 (Phase 5 supprimée, voir plus bas). Document
> de planification : aucun code de ces phases ne doit être démarré sans
> demande explicite (règle rappelée dans `CLAUDE.md`), même si les choix
> techniques ci-dessous sont déjà tranchés.

## État actuel

Phase 1 terminée et validée de bout en bout (code, tests, Docker Compose,
rendu visuel) — voir `docs/ARCHITECTURE.md`. PR #2 en cours de relecture.

**Décisions de cadrage actées le 2026-07-03** (voir aussi `CLAUDE.md` §
Historique des décisions) :
- SMS et USSD : **Orange Business** (API Bulk SMS), file de tâches **RQ**.
- Préinscription SMS : **le candidat s'inscrit lui-même** sur le site
  public (numéro de PV + téléphone + case de consentement), avant la
  publication des résultats.
- Mobile : **Flutter**.
- Espace établissement : **table normalisée** + **auto-inscription avec
  vérification automatique** contre une liste officielle d'établissements.
- API B2B : confirmée, **payante** (grille tarifaire à définir).
- **Guide d'orientation : supprimé du périmètre du projet.**
- **Expansion sous-régionale UEMOA : supprimée du périmètre du projet.**
  Faso Résultats reste un produit mono-pays (Burkina Faso) de façon
  permanente, pas seulement pour les phases proches.

Deux chantiers transverses restent ouverts indépendamment des phases
suivantes (voir « Chantiers transverses » en fin de document) :
calibrage des parsers PDF/OCR sur de vrais documents, et validation
juridique de `docs/APDP.md`.

---

## Phase 2 — Intégration SMS et notifications proactives

**Objectif :** notifier un candidat par SMS dès que son résultat est publié,
sur préinscription et consentement explicite (case non pré-cochée).

**Fournisseur retenu : Orange Business (API Bulk SMS).** Simplifie le
choix (un seul fournisseur pour SMS et USSD, voir Phase 4), mais ne
couvre que les numéros joignables via son réseau/ses accords
d'interconnexion — ⚠️ à vérifier lors de l'implémentation que la
couverture Moov/Telecel est bien assurée par l'API Orange Business
(interconnexion inter-opérateurs) et pas seulement les numéros Orange.

**File de tâches retenue : RQ** (Redis Queue), cohérent avec « pas de
sur-ingénierie » — Redis est déjà dans la stack (cache), RQ s'appuie
dessus sans ajouter de nouvelle brique d'infrastructure (contrairement à
Celery, plus lourd à opérer pour ce volume).

### Ce qui existe déjà
La table `notifications_preinscription` est en place depuis la Phase 1
(`examen_id`, `telephone`, `numero_pv`, `consentement`, `statut`,
`envoye_at`) mais n'est reliée à aucune route — c'est une réservation de
schéma, pas une fonctionnalité.

### Préinscription — auto-inscription sur le site public

Le candidat s'inscrit lui-même, avant la publication des résultats, via un
formulaire sur `index.html` : numéro de PV + numéro de téléphone + case de
consentement (non pré-cochée, conforme APDP). Pas d'import admin en masse
prévu pour ce flux — toutes les questions de cadrage de cette phase sont
désormais tranchées.

### Étapes techniques
1. `app/services/sms/orange_business.py` : client pour l'API Bulk SMS
   Orange Business, derrière une interface abstraite
   (`envoyer_sms(numero, message) -> bool`) pour ne pas coupler le reste
   du code à ce fournisseur précis (utile si Phase 4/USSD révèle qu'un
   produit distinct est nécessaire, voir plus bas).
2. `worker.py` (ou équivalent) : un worker RQ dédié, lancé comme service
   séparé dans `docker-compose.yml` (nouveau service `worker`, même image
   backend, `command: rq worker`).
3. `POST /api/v1/public/preinscriptions` : le candidat s'inscrit avec son
   numéro de PV + téléphone + consentement, avant la publication. Nécessite
   un formulaire dédié sur `index.html` (nouveau, en plus du formulaire de
   recherche existant) et sa logique JS associée.
4. Déclenchement à la publication : quand `POST
   /api/v1/admin/exams/{id}/publish` passe un examen en `PUBLISHED`, une
   tâche RQ est enfilée par préinscription `EN_ATTENTE` de cet examen
   (texte contenant décision + lien de consultation).
5. Suivi des échecs : `statut=ECHEC` déjà prévu au modèle — ajouter une
   route admin de relance manuelle/automatique, et une file RQ de retry
   (RQ gère nativement les jobs échoués).
6. Plafond de coût : un garde-fou simple (compteur de SMS envoyés vs quota
   mensuel configuré) pour éviter une facture incontrôlée.
7. Tests : mock du client Orange Business, aucun vrai envoi en tests ;
   tests du worker RQ avec `rq` en mode synchrone (`is_async=False`) pour
   rester rapides en CI.

### Risques identifiés
- Couverture réseau de l'API Bulk SMS Orange Business sur les numéros
  Moov/Telecel — à vérifier avant de s'engager (voir ci-dessus).
- Coût par SMS à grande échelle (des dizaines de milliers de candidats un
  jour de proclamation) — à chiffrer avec Orange Business avant mise en
  production.
- Fiabilité de livraison variable selon opérateur/réseau — prévoir un
  indicateur de taux de succès visible côté admin.

---

## Phase 3 — Application mobile Flutter et espace établissement

### Application mobile — Flutter

- Réutilisation complète de l'API existante (JWT côté admin non
  pertinent pour l'app candidat — seules les routes publiques comptent).
- Authentification candidat : aucune aujourd'hui (recherche par PV, pas de
  compte). À cadrer si l'app veut un compte léger pour retrouver ses
  recherches passées — pas obligatoire pour un premier jet.
- Mode hors-ligne : cache local des résultats déjà consultés, cohérent
  avec le contexte 3G faible du Burkina Faso.
- Distribution : Play Store (compte développeur Google, process de
  review) — première publication à anticiper en avance (délais de
  validation Google variables).

### Espace établissement — table normalisée + vérification automatique

Nécessite une refonte partielle du modèle de données : aujourd'hui,
`etablissement` sur `Resultat` est un simple champ texte libre extrait du
fichier source, pas une entité normalisée.

1. Nouvelle table `etablissements` (nom, code, contact, statut de
   vérification).
2. Nouveau type de compte (au-delà du seul `Admin` actuel), avec des
   permissions restreintes à son propre établissement — vue agrégée en
   lecture seule des résultats de leurs élèves.
3. **Flux d'auto-inscription, vérification automatique** : un
   établissement crée son compte lui-même ; le nom déclaré est comparé
   automatiquement à une liste officielle d'établissements, le compte
   n'est activé qu'en cas de correspondance. **Prérequis partiellement
   comblé le 2026-07-03** : liste officielle reçue (« II-3 — Liste
   nominative des établissements post-primaires et secondaires
   d'enseignement général privés reconnus », 17 pages, colonnes
   Région/Nom/Provinces/Communes/Secteur). ⚠️ Deux limites à noter avant
   de coder dessus :
   - Cette liste ne couvre que les établissements **privés** — les
     établissements publics (probablement majoritaires côté CEP/BEPC/BAC)
     ne sont pas dans ce document. Une liste complémentaire sera
     nécessaire.
   - La liste contient de vraies anomalies de saisie (des noms
     d'établissement coupés sur deux lignes numérotées consécutives,
     ex. lignes 523/524 : « ...française) » / « ...arabe) » qui sont
     manifestement la suite d'un seul nom) — la logique de correspondance
     automatique devra tolérer ce genre de coupure plutôt que supposer
     une ligne = un établissement propre.
4. Réconciliation entre le texte libre historique (`Resultat.etablissement`)
   et la nouvelle table normalisée — les fichiers PV n'utilisent pas
   forcément une orthographe/un code établissement cohérent d'un import à
   l'autre. Un travail de nettoyage/mapping sera nécessaire, pas juste une
   migration de schéma.

---

## Phase 4 — USSD, application iOS, API B2B

### USSD — Orange Business

Même fournisseur que la Phase 2. ⚠️ **Point technique à vérifier tôt** :
chez la plupart des opérateurs, l'API Bulk SMS et l'API/le service USSD
sont deux produits distincts (contrats, endpoints et parfois équipes
commerciales séparés), même chez un même fournisseur — à confirmer
directement avec Orange Business avant de supposer qu'un seul contrat
couvre les deux besoins. Flux fonctionnel envisagé : candidat compose un
code USSD, entre son numéro de PV, reçoit sa décision directement à
l'écran (pas besoin de connexion internet — pertinent pour les téléphones
basiques et les zones à connectivité limitée).

### Application iOS

Flutter (choix de la Phase 3) couvre iOS et Android depuis la même base
de code — coût marginal une fois l'app Android livrée, plutôt qu'un
développement natif séparé. Publication App Store à anticiper (compte
développeur Apple, process de review généralement plus strict que Google
Play).

### API B2B — confirmée

Ouvrir une partie de l'API publique à des partenaires (écoles privées,
médias, ONG) avec :
- Un nouveau modèle `ApiKey`/`Partenaire` (clé API, quota, contact).
- Rate limiting par clé plutôt que par IP (le mécanisme slowapi actuel
  est déjà extensible dans ce sens).
- Documentation publique (FastAPI génère déjà `/docs` — à restreindre ou
  dupliquer en version publique selon ce qui doit rester interne).
- **Modèle économique : payant.** Reste à définir la grille tarifaire
  exacte (par requête, par quota mensuel, convention forfaitaire) au
  moment de concevoir la table de facturation — pas bloquant pour le
  cadrage technique.

---

## Hors périmètre (décisions actées le 2026-07-03)

- **Guide d'orientation** : supprimé. Ce module (répertoire de
  formations/établissements post-bac) sortait de toute façon du domaine
  des résultats d'examens et aurait nécessité une source de données et un
  partenariat séparés (Ministère de l'Enseignement supérieur plutôt
  qu'OCECOS/DGEC) — non poursuivi.
- **Expansion sous-régionale UEMOA** : supprimée. Faso Résultats reste
  scopé au Burkina Faso de façon permanente, pas seulement le temps des
  phases 2-4. Les champs/enums actuellement pensés pour un seul pays
  (`TypeExamen`, absence de champ `pays` sur `Examen`) n'ont donc pas
  besoin d'être généralisés — décision qui simplifie durablement le
  modèle de données.

---

## Chantiers transverses (indépendants des phases)

Ces points ne bloquent aucune phase mais devraient progresser en continu :

1. **Calibrage des parsers sur de vrais documents.** Le parser Excel a été
   calibré le 2026-07-03 sur un vrai PV de concours direct (Assistants des
   Douanes), révélant 3 lacunes corrigées depuis (décision par défaut,
   colonne nom+prénom combinée, champ N°CNIB) — voir
   `docs/ARCHITECTURE.md` § Calibrage. Le parser **PDF natif** a été testé
   le 2026-07-04 contre un vrai PDF gouvernemental (liste des
   établissements, 62 pages) : robustesse de l'extraction confirmée (pas de
   crash, pas de perte de ligne, mauvais format correctement rejeté), et
   une corruption de texte source rarissime (1 ligne/2029) documentée comme
   couverte par la relecture humaine obligatoire plutôt que par un
   correctif automatique. Ce document n'étant pas un PV de résultats, la
   calibration champ-par-champ (mapping des colonnes d'examen) reste à
   faire sur un vrai PV au format PDF natif. **L'OCR reste non calibré** —
   aucun spécimen de PV scanné/photo n'est disponible actuellement (celui
   partagé le 2026-07-03 n'a pas été conservé après compactage de la
   conversation) ; à refaire dès qu'un nouveau spécimen sera fourni.
2. **Validation juridique de `docs/APDP.md`** — plusieurs points (base
   légale, responsable de traitement, durée de conservation) explicitement
   marqués comme non tranchés dans le document.
3. **Tests de charge réalistes** avant un vrai jour de proclamation
   (CLAUDE.md exige <200 ms en cache chaud ; mesuré en conditions de
   développement légères jusqu'ici, jamais sous charge réaliste de
   centaines de milliers de requêtes).
4. **Mise en production réelle** : hébergement burkinabè (souveraineté des
   données), HTTPS, rotation du mot de passe admin par défaut — tout
   tourne encore en dev/Docker local à ce stade.

---

## Ordre de priorité suggéré

```
Phase 2 (SMS, Orange Business + RQ)
   └─→ Phase 4 / USSD (même fournisseur, vérifier si même contrat ou non)
Phase 3 (mobile Flutter + établissement)
   └─→ Phase 4 / iOS (gratuit une fois l'app Flutter Android livrée)
Phase 4 / API B2B : indépendante, peut démarrer à tout moment une fois
   la Phase 1 stable — seul le modèle économique reste à trancher
```

Chaque phase reste conditionnée à une demande explicite avant de démarrer
le code, conformément à `CLAUDE.md`, même si les choix techniques
ci-dessus sont déjà actés.
