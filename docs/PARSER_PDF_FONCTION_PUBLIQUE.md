# Spécification technique — Parser PDF Fonction Publique

> À intégrer au projet dans `docs/PARSER_PDF_FONCTION_PUBLIQUE.md`.
> Cette fiche complète `CONTEXTE_METIER.md` avec les observations issues de l'analyse concrète de PDF officiels 2025.

---

## 1. Découverte critique : les PDF officiels sont des SCANS

Les PDF publiés par le Ministère de la Fonction Publique sur `fonction-publique.gov.bf` **ne contiennent pas de couche texte extractible**. Ils sont produits par des scanners professionnels :

- HP Scan Extended Application
- PaperStream Capture 2.1 (Fujitsu)

Vérifié par `pdffonts` (aucune police) et `pdftotext` (aucun texte extrait).

### Conséquences pour l'architecture

1. **L'OCR est obligatoire dès le MVP**, ce n'est pas une phase 2 optionnelle
2. **Tesseract avec pack français (`tesseract-ocr-fra`)** doit être installé sur tous les environnements (Docker, prod, dev)
3. Le pipeline `pdfplumber` seul est insuffisant pour ces sources — il reste utile pour les PDF natifs (Excel exports, LibreOffice, etc.)
4. **Le pipeline doit détecter automatiquement le type de PDF** et router vers le bon parser

### Détection automatique du type de PDF

```python
def detecter_type_pdf(pdf_path: str) -> Literal["NATIF", "SCAN"]:
    """Détermine si un PDF a une couche texte ou est un scan."""
    import subprocess
    result = subprocess.run(
        ["pdffonts", pdf_path], capture_output=True, text=True, check=True
    )
    # pdffonts retourne des lignes de header + polices détectées
    # 2 lignes ou moins = pas de polices = scan
    lignes = [l for l in result.stdout.strip().split("\n") if l.strip()]
    return "SCAN" if len(lignes) <= 2 else "NATIF"
```

---

## 2. Structure observée des PDF Fonction Publique

### En-tête administratif standard

Toutes les publications suivent le même template :

```
MINISTERE DE LA FONCTION PUBLIQUE,          BURKINA FASO
DU TRAVAIL ET DE LA PROTECTION SOCIALE      La Patrie ou la Mort, nous Vaincrons
    SECRETARIAT GENERAL
AGENCE GENERALE DE RECRUTEMENT             Ouagadougou, le [DATE]
       DE L'ETAT
 DIRECTION DE L'ORGANISATION
       DES CONCOURS

N° [NUMERO]/MFPTPS/SG/AGRE/DOC

    LE MINISTRE DE LA FONCTION PUBLIQUE,
    DU TRAVAIL ET DE LA PROTECTION SOCIALE

              COMMUNIQUE

Sous réserve d'un contrôle approfondi, les candidats dont les noms
suivent, sont déclarés admissibles par ordre de mérite au concours
direct de recrutement de [N EN LETTRES] ([N EN CHIFFRES]) [CORPS],
session [ANNEE].

Ce sont :
              [CORPS EN MAJUSCULES]
                  ADMISSIBLES
```

### Tableau des résultats

Format à 4 colonnes strictement stable :

| Colonne | Format | Exemple |
|---------|--------|---------|
| RANG | Chiffre + `°` | `1°`, `4°`, `16°` |
| NOM ET PRÉNOM(s) | Texte en majuscules | `KONATE BEN OUMAR STANISLAS KONABE` |
| RECEPISSE-CODE-CENTRE + N°CNIB | 3 groupes séparés par `-` puis espace + CNIB | `000015-120-03 B18622704` |
| DATE NAISS. | JJ/MM/AA | `03/12/97` |

### Structure du champ RECEPISSE-CODE-CENTRE

`XXXXXX-YYY-ZZ` se décompose en :
- **XXXXXX** (6 chiffres) — numéro de récépissé du candidat = **numéro de PV** utilisé pour la consultation
- **YYY** (2 à 4 chiffres) — code interne du concours (ex: `120` pour Chirurgiens-Dentistes, `109` pour Ingénieurs Biomédical)
- **ZZ** (2 chiffres) — code du centre de composition (ex: `03` pour Ouagadougou vraisemblablement)

**Ce sont les identifiants critiques :**
- Le **numéro de récépissé** est ce que le candidat saisit sur la plateforme pour retrouver son résultat
- Le **code concours** identifie le corps postulé
- Le **code centre** permet de filtrer par lieu de composition

### Gestion des ex-aequo

Les candidats à égalité partagent le même rang, et le rang suivant saute :
- Rangs 1° à 3° : un candidat chacun
- Rangs 4°, 4°, 4° : trois ex-aequo → rang suivant = 7°
- Rangs 7° × 8 : huit ex-aequo → rang suivant = 15° (parfois noté 16° selon le calcul officiel)

**Contrainte modèle de données :** l'index unique `(examen_id, numero_recepisse, jury)` reste correct car le récépissé est unique par candidat. Le `rang` peut être identique pour plusieurs résultats — c'est normal.

### Pied du communiqué

```
Arrêté la présente liste à [N] admissible(s).

Par ailleurs, les candidats admissibles ont dix (10) jours ouvrables,
à compter de la date de publication du résultat d'admissibilité, pour
déposer leurs dossiers physiques à [ADRESSE].

              Pour le Ministre et par délégation,
                    le Secrétaire Général
                    [SIGNATURE + TAMPON]
                    [NOM DU SIGNATAIRE]
                    Chevalier de l'Ordre du Mérite
                    de l'Administration et du Travail
```

**Le nombre d'admissibles déclaré** en pied doit être comparé au nombre de résultats effectivement extraits — c'est le **contrôle qualité principal** de l'ingestion.

---

## 3. Volume attendu

Sur la seule session 2025 des concours directs, la page officielle liste **224 fichiers PDF** distincts, un par corps de métier / catégorie de handicap.

Répartition observée :
- Concours "grand public" (ingénieurs, médecins, dentistes, administrateurs) : PDF de 5 à 20+ pages
- Concours "personnes vivant avec un handicap" (PVH auditif/physique/visuel) : PDF de 1 à 3 pages, très courts
- Concours enseignants (professeurs certifiés) : PDF moyens

**Volume total estimé pour une session :** entre 15 000 et 50 000 candidats admissibles répartis sur 224 fichiers.

**Impact opérationnel :** l'admin devra ingérer et valider ~224 fichiers en quelques heures/jours autour de la publication. Le pipeline doit être :
- Rapide (traitement d'un PDF en < 30 secondes)
- Robuste (pas de plantage sur un PDF mal scanné)
- Assisté (validation groupée par lot, pas ligne par ligne)
- Traçable (chaque résultat lié à son fichier source)

---

## 4. Nommage anarchique des fichiers PDF

**Pas de convention** dans les noms de fichier sur fonction-publique.gov.bf :

```
0000_Resultat_cd_2025_chirurgiens-dentistes_generalistes.pdf
YYY_U9-RESULTAT_CD_2025_INGENIEURS_EN_GENIE_BIOMEDICAL.pdf
ZZ_ZZZZAresultat_cd_2025_ADH_visuel_5.pdf
VV_Vc-1-RESULTAT_CD_2025_ASSISTANTS_DE_SECURITE_PENITENTIAIRE-FEMMES_ADMISSIBLES.pdf
```

**Conséquence pour le scraping automatique** : impossible de déterminer le contenu d'un PDF depuis son nom de fichier. Il faut obligatoirement OCR-er l'en-tête pour identifier le corps concerné. C'est un point à documenter dans l'admin : **le corps du concours doit être détecté depuis l'en-tête du PDF**, pas depuis le nom de fichier.

---

## 5. Code du parser POC (validé à 100% sur 2 PDF)

Voir le fichier `parser_poc.py` livré séparément. Résultats du POC :

| PDF | Admissibles déclarés | Extraits | Cohérence |
|-----|---------------------|----------|-----------|
| Chirurgiens-Dentistes (1 page) | 7 | 7 | ✅ |
| Ingénieurs Biomédical (5 pages) | 120 | 120 | ✅ |

Points forts du POC :
- Détection automatique OCR + regex robustes
- Extraction propre des rangs, noms, récépissés, CNIB, dates
- Gestion des ex-aequo (rangs répétés)
- Validation par comparaison au total déclaré en pied de page
- Trace des lignes non parsées pour audit admin

Points à améliorer avant intégration :
- Extraction fiable du **numéro de communiqué** (regex à durcir, l'OCR déforme parfois `°` en `€`)
- Extraction de la **date du communiqué** (format `22 JUIL 2025` avec mois abrégé en français)
- Extraction du **titre exact du corps** depuis la ligne en majuscules du header
- Prétraitement d'image avant OCR (déskew, débruitage) pour PDF de mauvaise qualité
- Gestion des PDF avec en-têtes légèrement différents (Ministère de la Santé, Ministère de la Sécurité pour Police)

---

## 6. Implications pour le modèle de données

### Ajustements au modèle `resultats`

À intégrer en plus des champs déjà prévus :

```python
# Champs spécifiques à ajouter au modèle Resultat
numero_recepisse: str          # 6 chiffres - c'est ce que le candidat saisit
code_concours: str             # 2-4 chiffres, ex: "120"
code_centre: str               # 2 chiffres, ex: "03"
numero_cnib: str | None        # optionnel, utile pour désambiguïser homonymes
rang_numerique: int            # rang absolu (utile pour tri)
rang_affiche: str              # "1°", "16°" pour affichage utilisateur
donnees_brutes_ligne: str      # ligne OCR d'origine, pour audit
```

### Nouveau modèle `Centre` (facultatif, phase 2)

```python
class Centre(Base):
    id: uuid
    code: str          # "03"
    libelle: str       # "Ouagadougou"
    ville: str
    region: str
```

Le code centre `03` revient dans les deux PDF observés. Une table de correspondance permettra d'afficher `"Composé à Ouagadougou"` plutôt qu'un simple `03` opaque pour l'utilisateur.

### Nouveau modèle `Concours` (facultatif, phase 2)

```python
class Concours(Base):
    id: uuid
    code: str                  # "120", "109"
    libelle: str               # "Chirurgien-Dentiste Généraliste"
    ministere_organisateur: str
    categorie: str             # A, B, C, D
```

---

## 7. Champs de recherche recommandés côté utilisateur

Pour la consultation publique, l'utilisateur doit pouvoir chercher son résultat avec le minimum d'infos possible. Combinaisons recommandées :

**Méthode principale :**
- Sélection du concours (par corps)
- Saisie du numéro de récépissé (6 chiffres)
- Validation par date de naissance (JJ/MM/AAAA) — sert de "second facteur" pour éviter qu'un tiers ne consulte des résultats

**Méthode alternative :**
- Saisie du N°CNIB uniquement — retourne tous les résultats liés à cette pièce d'identité (permet à un candidat qui a postulé à plusieurs corps de tout voir d'un coup)

**Ne PAS utiliser :**
- Le nom seul — trop d'homonymes possibles au Burkina, source d'erreurs
- Le code concours + code centre seuls — sans récépissé, ça retourne tous les candidats du centre

---

## 8. Ce que Claude Code doit intégrer concrètement

1. **Ajouter la dépendance `tesseract-ocr` + `tesseract-ocr-fra`** au `Dockerfile` du backend
2. **Ajouter la dépendance Python `pytesseract`** au `requirements.txt`
3. **Créer `app/services/parsers/scan_pdf_parser.py`** en s'inspirant du POC fourni (`parser_poc.py`)
4. **Créer `app/services/parsers/pdf_type_detector.py`** avec la fonction `detecter_type_pdf`
5. **Créer `app/services/parsers/native_pdf_parser.py`** avec `pdfplumber` pour les PDF natifs (Excel exports, etc.)
6. **Router automatiquement** dans `FileImportSource` selon le type détecté :
   ```python
   type_pdf = detecter_type_pdf(chemin)
   if type_pdf == "SCAN":
       resultats = ScanPdfParser().parse(chemin)
   else:
       resultats = NativePdfParser().parse(chemin)
   ```
7. **Ajouter les nouveaux champs** au modèle `resultats` (voir section 6)
8. **Renommer `numero_pv`** en `numero_recepisse` dans tout le code — c'est le nom officiel
9. **Créer une interface admin d'ingestion en lot** capable de traiter 50+ PDF en série avec :
    - Barre de progression
    - Prévisualisation groupée
    - Détection des PDF douteux (nombre d'extraits ≠ nombre déclaré)
    - Validation en un clic pour les PDF cohérents
    - Correction manuelle uniquement pour ceux en écart
10. **Mettre à jour `docs/ARCHITECTURE.md`** avec une section "Pipeline d'ingestion PDF" décrivant ce workflow

---

## 9. Précisions à obtenir sur le terrain

Deux inconnues à valider avant d'aller trop loin :

**Q1 — Résolution des scans :** les deux PDF observés sont à 200-300 DPI. Est-ce standard sur toutes les publications ? Si certains ministères produisent des scans à 72 DPI, le taux d'erreur OCR va exploser et il faudra du prétraitement OpenCV agressif.

**Q2 — Cas des noms accentués :** aucun accent observé dans les noms des 127 candidats testés (les noms burkinabè n'en portent pas généralement). Mais pour des noms comme "TRAORÉ" ou "ZOUNGRANA/TRAORÉ", vérifier que Tesseract les lit correctement — sinon activer `--oem 1` ou un post-traitement de normalisation.

**Q3 — Publications multi-phases :** les PDF fournis sont tous des **résultats d'ADMISSIBILITÉ** (phase 2 pour les paramilitaires). Il faudra obtenir un exemplaire de résultat d'**ADMISSION DÉFINITIVE** (phase 3) pour vérifier que le template est identique — probable mais à confirmer.

---

*Fin de la spécification — version 1.0 — Basée sur analyse de 2 PDF officiels 2025 et 224 liens indexés.*
