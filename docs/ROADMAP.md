# Feuille de route — Faso Résultats

> Détaille les phases 2 à 5 déjà annoncées dans `CLAUDE.md`. Document de
> planification : aucun code de ces phases ne doit être démarré sans
> demande explicite (règle rappelée dans `CLAUDE.md`). Chaque phase liste
> les décisions à trancher *avant* de commencer à coder, pas des choix déjà
> faits.

## État actuel

Phase 1 terminée et validée de bout en bout (code, tests, Docker Compose,
rendu visuel) — voir `docs/ARCHITECTURE.md`. PR #2 en cours de relecture.

Deux chantiers transverses restent ouverts indépendamment des phases
suivantes (voir « Chantiers transverses » en fin de document) :
calibrage des parsers PDF/OCR sur de vrais documents, et validation
juridique de `docs/APDP.md`.

---

## Phase 2 — Intégration SMS et notifications proactives

**Objectif :** notifier un candidat par SMS dès que son résultat est publié,
sur préinscription et consentement explicite (case non pré-cochée).

### Ce qui existe déjà
La table `notifications_preinscription` est en place depuis la Phase 1
(`examen_id`, `telephone`, `numero_pv`, `consentement`, `statut`,
`envoye_at`) mais n'est reliée à aucune route — c'est une réservation de
schéma, pas une fonctionnalité.

### Décisions à trancher avant de démarrer
1. **Fournisseur SMS.** Envoi direct auprès de chaque opérateur (Orange,
   Moov, Telecel) ou via un agrégateur unique (type Africa's Talking, ou un
   agrégateur local burkinabè) ? Un agrégateur simplifie l'intégration
   (une seule API pour les trois réseaux) mais ajoute un intermédiaire et
   un coût par SMS ; l'intégration directe est plus complexe (trois API
   différentes) mais peut être moins chère à grand volume. **Nécessite une
   étude commerciale**, pas seulement technique — je peux comparer les
   options techniques une fois les contacts/tarifs opérateurs connus.
2. **Volume attendu au jour J.** Le jour de la proclamation du BAC,
   combien de préinscriptions potentielles ? Ça détermine si de simples
   `BackgroundTasks` FastAPI suffisent ou s'il faut une vraie file de
   tâches (Redis est déjà dans la stack — RQ serait le choix le plus
   simple, cohérent avec « pas de sur-ingénierie »).
3. **Où se fait la préinscription ?** Sur `index.html` (candidat coche une
   case avant la publication) ou uniquement via un import admin en masse
   (numéros collectés hors-ligne) ? Change complètement l'UI à prévoir.

### Étapes techniques (une fois les décisions ci-dessus prises)
1. `app/services/sms/` : interface abstraite d'envoi (`envoyer_sms(numero,
   message) -> bool`), une implémentation par fournisseur retenu — permet
   de changer de fournisseur sans toucher au reste du code.
2. `POST /api/v1/public/preinscriptions` : le candidat s'inscrit avec son
   numéro de PV + téléphone + consentement, avant la publication.
3. Déclenchement à la publication : quand `POST
   /api/v1/admin/exams/{id}/publish` passe un examen en `PUBLISHED`, une
   tâche parcourt les préinscriptions `EN_ATTENTE` de cet examen et
   envoie les SMS (texte contenant décision + lien de consultation).
4. Suivi des échecs : `statut=ECHEC` déjà prévu au modèle — ajouter une
   route admin de relance manuelle/automatique.
5. Plafond de coût : un garde-fou simple (compteur de SMS envoyés vs quota
   mensuel configuré) pour éviter une facture incontrôlée.
6. Tests : mock du client SMS abstrait, aucun vrai envoi en tests.

### Risques identifiés
- Coût par SMS à grande échelle (des dizaines de milliers de candidats un
  jour de proclamation) — à chiffrer avant de s'engager sur un fournisseur.
- Fiabilité de livraison variable selon opérateur/réseau — prévoir un
  indicateur de taux de succès visible côté admin.

---

## Phase 3 — Application mobile Android et espace établissement

### Application mobile

**Décision à trancher avant de démarrer :** Flutter, React Native, ou
**PWA** (non listée dans la roadmap actuelle mais cohérente avec le profil
du développeur — expérience PWA offline-first déjà mentionnée dans
`CLAUDE.md`). Une PWA réutiliserait directement `frontend/public/` (déjà
en HTML/CSS/JS vanilla) avec un service worker pour le mode hors-ligne et
un manifest pour l'installation — coût de développement nettement
inférieur à une vraie app native, au prix d'un accès plus limité aux
fonctionnalités du téléphone (notifications push moins fiables selon
l'OS). À poser comme vraie question de cadrage avant de choisir.

Si Flutter ou React Native est retenu malgré tout :
- Réutilisation complète de l'API existante (JWT côté admin non
  pertinent pour l'app candidat — seules les routes publiques comptent).
- Authentification candidat : aucune aujourd'hui (recherche par PV, pas de
  compte). Une app mobile pourrait vouloir un compte léger pour retrouver
  ses recherches passées — à cadrer, ce n'est pas obligatoire.
- Mode hors-ligne : cache local des résultats déjà consultés, cohérent
  avec le contexte 3G faible du Burkina Faso.

### Espace établissement

Nécessite une refonte partielle du modèle de données : aujourd'hui,
`etablissement` sur `Resultat` est un simple champ texte libre extrait du
fichier source, pas une entité normalisée. Pour donner à un établissement
un accès à ses propres résultats agrégés, il faut :
1. Une table `etablissements` normalisée (nom, code, contact).
2. Un nouveau type de compte (au-delà du seul `Admin` actuel), avec des
   permissions restreintes à son propre établissement.
3. Une réconciliation entre le texte libre historique et cette nouvelle
   table (les fichiers PV n'utilisent pas forcément une orthographe/un
   code établissement cohérent d'un import à l'autre — vrai risque de
   qualité de données à anticiper).

**Décision à trancher :** qui crée les comptes établissement (auto-inscription
avec vérification, ou création manuelle par l'admin OCECOS/DGEC) ?

---

## Phase 4 — USSD, application iOS, API B2B, guide d'orientation

### USSD
Intégration opérateur (souvent via un agrégateur télécom, ex. Africa's
Talking USSD, ou directement avec chaque opérateur burkinabè). Flux texte
simple : candidat compose un code, entre son numéro de PV, reçoit sa
décision par SMS ou directement à l'écran USSD. Intérêt majeur pour le
contexte burkinabè : fonctionne sur téléphone basique, sans connexion
internet. Dépend du fournisseur retenu en Phase 2 (souvent le même
agrégateur gère SMS et USSD).

### Application iOS
Coût dépend entièrement du choix fait en Phase 3 : quasi gratuit si
Flutter/React Native retenu (déploiement cross-platform), développement
séparé si PWA (une PWA fonctionne aussi sur iOS Safari, avec des
limitations connues sur les notifications push).

### API B2B
Ouvrir une partie de l'API publique à des partenaires (écoles privées,
médias, ONG) avec :
- Un nouveau modèle `ApiKey`/`Partenaire` (clé API, quota, contact).
- Rate limiting par clé plutôt que par IP (le mécanisme slowapi actuel
  est déjà extensible dans ce sens).
- Documentation publique (FastAPI génère déjà `/docs` — à restreindre ou
  dupliquer en version publique selon ce qui doit rester interne).
- **Décision à trancher :** modèle économique (gratuit avec quota, payant,
  convention par partenaire) — question commerciale avant tout.

### Guide d'orientation
Change de nature par rapport au reste du produit : il s'agit d'un
répertoire de formations/établissements post-bac, pas de résultats
d'examens. À cadrer comme un module fonctionnel distinct (nouveau domaine
de données : `formations`, `filieres`, `etablissements_enseignement`),
avec sans doute une source de données différente (partenariat avec le
Ministère de l'Enseignement supérieur plutôt qu'OCECOS/DGEC).

---

## Phase 5 — Expansion sous-régionale UEMOA

Chantier le plus structurant du roadmap : implique une vraie décision
d'architecture, à ne pas improviser à ce stade.

### Questions de fond à trancher avant tout code
1. **Multi-tenance légère vs déploiements séparés par pays.** Un seul
   déploiement avec un champ `pays` sur `Examen` est plus simple à
   maintenir, mais chaque pays UEMOA a probablement sa propre autorité de
   protection des données (équivalent APDP) avec ses propres exigences de
   souveraineté — un déploiement séparé par pays peut être *obligatoire*
   légalement, pas juste une préférence technique.
2. **Diversité des types d'examens.** `TypeExamen` (CEP/BEPC/BAC/CONCOURS_DIRECT)
   est actuellement un enum fixe pensé pour le système burkinabè — les
   autres pays UEMOA n'ont pas forcément la même nomenclature d'examens.
3. **Partenariats par pays.** Chaque pays a son propre organisme
   d'examens (équivalent OCECOS/DGEC) — nécessite une relation
   contractuelle indépendante par pays, hors périmètre technique.

Cette phase ne devrait être cadrée techniquement qu'une fois ces
questions structurantes tranchées au niveau produit/business — le détail
technique dépend entièrement de la réponse à la question 1.

---

## Chantiers transverses (indépendants des phases)

Ces points ne bloquent aucune phase mais devraient progresser en continu :

1. **Calibrage des parsers PDF natif et OCR** sur de vrais spécimens
   OCECOS/DGEC — identifié comme limitation connue depuis la Phase 1,
   aucun vrai document disponible pour le moment.
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

Pas de calendrier imposé par `CLAUDE.md`, mais un ordre de dépendances
techniques logique si les phases sont abordées dans l'ordre annoncé :

```
Phase 2 (SMS)
   └─→ Phase 4 / USSD (réutilise le même fournisseur télécom)
Phase 3 (mobile + établissement)
   └─→ Phase 4 / iOS (réutilise le choix technique mobile de la Phase 3)
Phase 4 / API B2B et guide d'orientation : indépendants, peuvent démarrer
   à tout moment une fois la Phase 1 stable
Phase 5 (UEMOA) : nécessite des décisions produit/business en amont,
   probablement la phase la plus tardive quel que soit l'avancement
   technique des autres
```

Chaque phase reste conditionnée à une demande explicite avant de démarrer
le code, conformément à `CLAUDE.md`.
