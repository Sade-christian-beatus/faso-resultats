# Analyse de marché — Faso Résultats

> Rédigée le 2026-11-17 à partir de sources publiques (presse burkinabè, DataReportal).
> Les chiffres viennent de la presse et pas de publications officielles consolidées :
> **les revérifier sur les communiqués des ministères avant de les mettre dans un
> document remis à une administration.** Chaque chiffre renvoie à sa source (§ 8).

---

## 1. Résumé en 5 points

1. **Le volume est réel et récurrent** : ~106 000 candidats au BAC, ~218 000 au BEPC,
   ~374 000 candidats aux examens de l'enseignement secondaire, et **plus de 2,4 millions
   de candidatures** aux concours directs de la Fonction publique en 2025. Chaque année,
   aux mêmes périodes (juin–octobre).
2. **L'État a commencé à numériser lui-même** : depuis juin 2026, les résultats du **CEP**
   sont consultables sur un portail officiel (`resultats.examens.gov.bf`, PV + date de
   naissance). Les concours de la Fonction publique ont déjà leur plateforme
   (`concours.gov.bf` / `econcours.gov.bf`). **Faso Résultats ne peut pas se présenter
   comme « le premier portail de résultats » : ce serait faux et perçu comme un doublon.**
3. **Le trou réel est ailleurs** : environ **78 % de la population n'utilise pas
   Internet** (22,4 % de pénétration fin 2025) alors qu'il y a **29 millions de lignes
   mobiles**. Aucune source trouvée ne mentionne de canal SMS/USSD officiel pour les
   résultats au Burkina. C'est l'avantage différenciant à mettre en avant.
4. **Le second trou : les petits organisateurs** (écoles nationales, concours
   paramilitaires à plusieurs phases, entreprises publiques qui recrutent par test,
   ex. SONABEL) qui publient encore par PDF/affichage, sans outil de publication.
5. **Le prix est marginal pour l'État** : les examens scolaires 2026 ont mobilisé plus de
   **27 milliards de FCFA**. Un abonnement STANDARD (8–12 M FCFA/an,
   `docs/PIVOT_SAAS_B2G.md` § 3) représente ~0,04 % de ce budget, soit **~46 FCFA par
   candidat au BEPC**.

**Recommandation centrale :** se positionner comme **brique complémentaire** de ce que
l'État a déjà (canal SMS/USSD, application mobile, outil de publication pour les
organisateurs non équipés, tenue de charge) et non comme un portail concurrent.

---

## 2. Taille du marché (volumes de candidats)

| Examen / concours | Session | Candidats | Remarques |
|---|---|---|---|
| BAC | 2025 | 112 985 | |
| BAC | 2026 | 105 984 | 433 jurys, baisse d'environ 7 000 |
| BEPC | 2025 | 206 216 | |
| BEPC | 2026 | 218 049 | taux de réussite 54,06 % (record annoncé) |
| Examens du secondaire (BEPC + BEP + CAP…) | 2026 | 373 631 | total ministère |
| Tous examens scolaires (avec CEP) | 2026 | ~759 000 | CEP hors périmètre (SIGEC-CEP) |
| Concours directs Fonction publique | 2025 | ~2,4 M candidatures | 154 concours, 7 056 postes annoncés, 5 744 pourvus |
| Concours professionnels | 2025 | 50 940 candidatures | 4 348 postes |

**Lecture :**
- **Le pic de charge le plus fort n'est pas le BAC, c'est la Fonction publique** : des
  millions de candidatures (un même candidat postule à plusieurs concours, parfois plus
  de 40), publiées par vagues d'admissibilité puis d'admission.
- Le **BEPC** est le plus gros examen du périmètre (CEP exclu), donc le meilleur
  argument « volume » auprès du ministère de l'Enseignement secondaire.
- Hors périmètre de ce tableau, mais réels : écoles nationales (ENAM, ENAREF, ENEP…),
  concours paramilitaires (police, douanes, eaux et forêts, GSP), tests de
  recrutement des entreprises publiques.

## 3. Contexte numérique

| Indicateur (fin 2025) | Valeur |
|---|---|
| Utilisateurs d'Internet | 5,42 millions (22,4 % de la population) |
| Lignes mobiles actives | 29,3 millions (~118 % de la population, multi-SIM) |
| Part des lignes « haut débit » (3G/4G/5G) | ~91 % (début 2025) |
| Identités actives sur les réseaux sociaux | 3,4 millions (début 2025) |

**Conséquences produit :**
- Le web et l'app ne touchent qu'**environ un Burkinabè sur cinq**. Le SMS (et plus tard
  l'USSD) n'est pas un « plus », c'est le canal majoritaire → la Phase 2 est le cœur de
  la proposition de valeur, pas un bonus.
- Beaucoup de lignes sont 3G-capables mais l'usage data reste limité (coût) : garder le
  web léger (objectif < 500 Ko déjà fixé dans `CLAUDE.md`) est un argument de vente.
- Facebook et WhatsApp sont les canaux de communication grand public (voir § 6).

## 4. Paysage concurrentiel et existant

| Acteur / dispositif | Ce qu'il fait | Menace / opportunité |
|---|---|---|
| **`resultats.examens.gov.bf`** (portail officiel, MEBAPLN) | Résultats du CEP 2026 en ligne (PV + date de naissance + session), tableau de bord statistique | **Menace principale** : l'État sait déjà faire un portail web et pourrait l'étendre au BEPC/BAC. **Opportunité** : il ne propose pas de SMS/USSD ni d'app. Savoir **qui l'a construit et l'exploite** (ministère, ANPTIC, prestataire ?) avant toute audience |
| **`concours.gov.bf` / `econcours.gov.bf`** (Fonction publique) | Inscriptions en ligne, publication des résultats d'admissibilité | Le ministère a sa plateforme. Se proposer en complément : notification proactive par SMS, consultation sans connexion, gestion des phases |
| **Presse en ligne** (lefaso.net, burkina24, Sidwaya, Wakat Séra…) | Publie les listes jury par jury, les taux régionaux | Partenaires de diffusion, pas concurrents |
| **Sites agrégateurs non officiels** (resultats-en-ligne, zemamra, simoon-cv, kamerpower…) | Captent le trafic de recherche (« résultat BAC 2026 Burkina ») | Montre la demande, mais brouille la confiance |
| **Arnaques « résultats avant l'heure »** (WhatsApp, Telegram, payants) | Fraude signalée par la presse et le ministère | **Argument fort** : un canal officiel unique et vérifiable protège les familles |
| **Proclamation physique** (affichage dans les centres) | Reste le canal par défaut, notamment pour le BEPC 2026 (aucune consultation en ligne d'après une source, à confirmer) | Le déplacement et l'affluence sont la douleur que Faso Résultats supprime |

**Point d'attention pour le pitch :** au CEP, l'État a lui-même choisi **PV + date de
naissance** comme clé de consultation. C'est exactement la « seconde donnée de
vérification » différée dans `CLAUDE.md` (décision du 2026-07-03). Être aligné sur ce
standard officiel est un argument et ne coûterait qu'un champ dans le formulaire.

## 5. Analyse SWOT

**Forces**
- Produit déjà fonctionnel : ingestion PDF/Excel/OCR, validation humaine avant
  publication, multi-tenant, app mobile, API B2B, publication par phase.
- Données chiffrées au repos, rapprochement candidat sans énumération, audit complet —
  déjà présentés à la CIL.
- Coût marginal pour l'État (§ 1, point 5), hébergement prévu au Burkina.
- *(Ajout 2026-11-20)* Lauréat du Concours National d'Innovation Digitale « Le Faso
  Digital » : reconnaissance nationale utile face à la faiblesse « aucune référence »
  (intitulé exact à récupérer, voir `docs/FINANCEMENT.md`).

**Faiblesses**
- **Pas de structure juridique** : bloque la déclaration CIL, la saisine ANSSI, le
  contrat Orange Business et toute convention (`docs/PIVOT_SAAS_B2G.md` § 9).
- Aucune référence client, aucun pilote réel.
- Pas de test de charge à grande échelle sur infrastructure réelle (`docs/ROADMAP.md`).
- SMS non branché (stub) : le différenciant principal n'existe pas encore en vrai.
- Développeur solo : risque de continuité perçu par l'administration.

**Opportunités**
- 78 % de la population hors Internet → SMS/USSD.
- Organisateurs non équipés (écoles, paramilitaires, entreprises publiques).
- Politique publique de transformation digitale active (contrat d'objectifs du
  ministère de la Transition digitale réalisé à 91 % en 2025) : thème porteur.
- Lutte contre les arnaques aux faux résultats : argument de service public.

**Menaces**
- Extension du portail officiel `resultats.examens.gov.bf` au BEPC/BAC par l'État
  lui-même.
- Préférence de l'administration pour un développement interne (ANPTIC) ou pour un
  prestataire déjà référencé.
- Cycles de décision longs (6 à 18 mois) et calendrier budgétaire annuel.
- Modèle « SMS surtaxé » mal perçu quand l'État insiste sur la gratuité de la
  consultation officielle.

## 6. Recommandations

### 6.1 Positionnement
- **Message :** « Faso Résultats amène le résultat officiel jusqu'au téléphone de chaque
  candidat, même sans Internet, sans que l'administration change ses outils. »
- **Ne jamais écrire** « plateforme officielle », « gratuit pour tous » ou des chiffres
  de capacité non mesurés tant qu'aucune convention ni test de charge réel n'existe.
- Présenter le web comme **un** canal parmi d'autres, et proposer l'intégration avec
  les portails existants (marque blanche, API) plutôt que leur remplacement.

### 6.2 Cible du premier pilote (à trancher)
`docs/PIVOT_SAAS_B2G.md` vise l'OCECOS / le BEPC 2027. Alternative à considérer :
**commencer par un organisateur plus petit** (concours d'une école nationale, concours
paramilitaire à phases, test de recrutement d'une entreprise publique). Avantages :
décision plus rapide, enjeu politique moindre, référence obtenue avant le BEPC/BAC.
Inconvénient : moins de visibilité. Les deux démarches peuvent être menées en parallèle.

### 6.3 Modèle économique
- Privilégier **l'abonnement payé par l'administration** (le SMS inclus ou refacturé à
  l'administration) plutôt que le SMS surtaxé payé par les familles : cohérent avec le
  discours officiel de gratuité et plus simple à défendre en audience.
- Argument chiffré : coût par candidat (~46 FCFA au BEPC sur un plan STANDARD) comparé
  au coût d'un déplacement vers un centre de proclamation.

### 6.4 Communication grand public (après signature d'un pilote seulement)
- Facebook (canal dominant) + WhatsApp (partage de la marche à suivre).
- Partenariats presse en ligne (lefaso.net, burkina24) : lien vers le canal officiel
  dans leurs articles de résultats.
- Radios locales en langues nationales pour le canal SMS (public hors Internet).
- Thème récurrent : « Ne payez jamais pour un faux résultat avant l'heure ».

## 7. Plan de lancement indicatif (calé sur le calendrier des examens)

| Période | Actions |
|---|---|
| **Nov.–déc. 2026** | Créer la structure juridique (SAS ou SARL, CEFORE/Maison de l'Entreprise) → RCCM, IFU. Déclaration CIL en ligne. Courrier de saisine ANSSI. Serveur de recette au Burkina (IKA Cloud ou autre devis) + domaine `.bf`. Envoi des demandes d'audience (`docs/courriers/`). Formation marketing digital des lauréats Faso Digital (26 nov., ABDI) ; profil investisseurs Carrefour Innovations (`docs/FINANCEMENT.md`). |
| **Janv.–févr. 2027** | Audiences et démonstrations. Proposer une convention de pilote. Version iOS en TestFlight, APK Android signé. Identifier l'opérateur de `resultats.examens.gov.bf`. |
| **Mars–avr. 2027** | Contrat Orange Business (nécessite le RCCM). Test de charge réel (k6/locust) sur l'infrastructure de production. Formation des opérateurs de l'administration pilote. |
| **Mai–juil. 2027** | Pilote réel : BEPC (juin), BAC (fin juin–juillet) ou concours selon la cible obtenue. |
| **Juil.–oct. 2027** | Concours directs Fonction publique (pic de charge). Bilan chiffré du pilote → second tour de prospection avec une référence. |

## 8. Sources

- BAC 2025 (112 985 candidats) : [Sidwaya](https://www.sidwaya.info/?p=145346), [Wakat Séra](https://www.wakatsera.com/?p=120779)
- BAC 2026 (105 984 candidats, 433 jurys) : [Wakat Séra](https://www.wakatsera.com/?p=142692), [L'Économiste du Faso](https://leconomistedufaso.com/?p=23492)
- BEPC 2026 (218 049 candidats, 54,06 %), total secondaire 373 631 : [Wakat Séra](https://www.wakatsera.com/burkina-bepc-2026-un-taux-de-reussite-historique-de-5406-une-premiere-en-cinquante-ans/), [La Tribune du Faso](https://www.latribunedufaso.net/?p=30058), [Ouaganews](https://ouaganews.net/burkina-examens-du-bepc-bep-et-cap-2026-des-resultats-en-nette-progression/)
- BEPC 2026 sans consultation en ligne (source unique, à confirmer) : [Le Léphant](https://lelephantci.com/actualite/2026/06/09/proclamation-des-resultats-bepc-burkina-faso-session-2026/)
- 759 000 candidats aux examens scolaires 2026 : [APA News](https://fr.apanews.net/education/burkina-759-000-candidats-attendus-aux-examens-scolaires-de-2026/)
- Budget des examens 2026 (plus de 27 milliards FCFA) : [Wakat Séra](https://www.wakatsera.com/burkina-examens-scolaires-2026-plus-de-27-milliards-f-mobilises-des-innovations-annoncees/), [Burkina24](https://burkina24.com/?p=442517)
- Portail officiel des résultats du CEP 2026 : [APA News](https://fr.apanews.net/technologies/burkina-les-resultats-du-cep-2026-desormais-consultables-en-ligne/), [YOP L-FRII](https://yop.l-frii.com/burkina-faso-les-resultats-du-cep-2026-desormais-accessibles-en-ligne-consultez-les-ici/), [Wakat Séra](https://www.wakatsera.com/?p=141978)
- Concours directs 2025 : [Burkina24 (2 093 118 candidatures)](https://burkina24.com/2025/07/13/burkina-faso-pour-les-154-concours-directs-ouverts-pour-la-session-2025-le-ministere-de-la-fonction-publique-enregistre-2-093-118-de-candidatures/), [Africa24 (2 401 977 / 7 056 postes)](https://africa24tv.com/?p=161256), [AllAfrica (bilan, 5 744 postes pourvus)](https://fr.allafrica.com/stories/202510130397.html), [Burkina24 (40 concours par candidat)](https://burkina24.com/?p=410293)
- Concours professionnels 2025 : [AllAfrica](https://fr.allafrica.com/stories/202503170302.html)
- Plateforme des concours : [YOP L-FRII (résultats sur concours.gov.bf)](https://yop.l-frii.com/formations/burkina-faso-communique-relatif-a-la-publication-de-tous-les-resultats-dadmissibilites-des-concours-directs-de-la-fonction-publique-session-2025/), [AllAfrica (inscriptions 2026 sur econcours.gov.bf)](https://fr.allafrica.com/stories/202605220422.html)
- Numérique : [DataReportal Digital 2025](https://datareportal.com/reports/digital-2025-burkina-faso), [DataReportal Digital 2026](https://datareportal.com/reports/digital-2026-burkina-faso)
- Ministère de la Transition digitale (91 % du contrat d'objectifs 2025) : [We Are Tech](https://www.wearetech.africa/fr/fils/actualites/tech/burkina-faso-370-localites-connectees-et-un-contrat-d-objectifs-realise-a-91)
- Arnaques aux faux résultats et canaux de diffusion du BAC 2026 (source secondaire) : [Simoon CV](https://simoon-cv.com/burkina-faso/blog/resultats-bac-2026-burkina-faso)
- Tests de recrutement d'entreprises publiques (ex. SONABEL) : [Burkina24](https://burkina24.com/?p=428964)
