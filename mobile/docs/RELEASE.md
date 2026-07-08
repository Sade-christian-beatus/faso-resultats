# Release Android — signature et publication

> Aucun keystore de production n'existe à ce jour. Ce document décrit la
> procédure à suivre le jour où une vraie release doit être publiée — il ne
> remplace pas la décision (et les identifiants) du responsable du projet.

## 1. Générer le keystore de production (une seule fois)

```bash
keytool -genkey -v \
  -keystore faso-resultats-upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload
```

Conserver ce fichier et son mot de passe **hors du dépôt Git**, dans un
gestionnaire de secrets (jamais par email ou chat). Sa perte empêche toute
mise à jour future de l'app sur le Play Store sous la même signature.

## 2. Build local signé

1. Copier `mobile/android/key.properties.example` vers
   `mobile/android/key.properties` (déjà ignoré par Git — voir
   `mobile/android/.gitignore`).
2. Remplacer les valeurs par les vraies (mot de passe du store, alias, mot
   de passe de la clé, chemin absolu vers le `.jks` généré à l'étape 1).
3. `flutter build appbundle --release` (format attendu par le Play Store)
   ou `flutter build apk --release` pour un test hors store.

`android/app/build.gradle` détecte automatiquement la présence de
`key.properties` : s'il est absent (cas de tout build CI aujourd'hui), le
build de release retombe sur la signature debug plutôt que d'échouer.

## 3. Signature en CI (à mettre en place au moment de la première release)

Non fait à ce jour : `.github/workflows/mobile-ci.yml` ne construit qu'un
APK debug. Pour ajouter un job de release signée :

1. Encoder le `.jks` en base64 (`base64 -i faso-resultats-upload-keystore.jks`)
   et le stocker dans un secret GitHub Actions (`ANDROID_KEYSTORE_BASE64`),
   avec `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`,
   `ANDROID_KEY_PASSWORD` à côté.
2. Dans le job, reconstruire `key.properties` et le `.jks` à partir des
   secrets avant `flutter build appbundle --release` :
   ```yaml
   - run: echo "$ANDROID_KEYSTORE_BASE64" | base64 -d > android/upload-keystore.jks
   - run: |
       cat > android/key.properties <<EOF
       storePassword=$ANDROID_KEYSTORE_PASSWORD
       keyPassword=$ANDROID_KEY_PASSWORD
       keyAlias=$ANDROID_KEY_ALIAS
       storeFile=upload-keystore.jks
       EOF
   ```
3. Ne jamais logger le contenu de ces fichiers (`set +x` autour de ces
   étapes si le workflow active le mode verbeux ailleurs).

## 4. Taille de l'APK

Objectif du prompt : < 15 Mo. Non mesuré sur un build release réel dans cet
environnement (pas de SDK Android/NDK installé ici — voir
`docs/ARCHITECTURE.md` § Tests jour 10 pour le détail des vérifications qui
n'ont pas pu être faites dans ce conteneur). À mesurer avec
`flutter build apk --release --analyze-size` sur un poste avec le SDK
Android complet avant la première publication.
