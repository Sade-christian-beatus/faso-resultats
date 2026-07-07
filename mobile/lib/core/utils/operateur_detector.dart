/// Détection de l'opérateur téléphonique burkinabè depuis le préfixe, pour un
/// affichage informatif uniquement (ex. logo opérateur) — n'affecte jamais la
/// validation ni l'envoi des requêtes.
///
/// ⚠️ Préfixes fournis par le prompt d'origine, **non vérifiés** auprès des
/// opérateurs (Orange/Moov/Telecel Burkina Faso) — les plans de numérotation
/// évoluent. À confirmer avant tout affichage trompeur en production.
enum OperateurTelephone { orange, moov, telecel, inconnu }

class OperateurDetector {
  const OperateurDetector._();

  static const _prefixesOrange = ['70', '71', '72', '73', '74', '75'];
  static const _prefixesMoov = ['76', '77', '78'];
  static const _prefixesTelecel = ['60', '61', '62', '63', '64', '65', '66'];

  static OperateurTelephone detecter(String telephoneComplet) {
    final sansIndicatif = telephoneComplet.trim().replaceFirst('+226', '');
    if (sansIndicatif.length < 2) return OperateurTelephone.inconnu;

    final prefixe = sansIndicatif.substring(0, 2);
    if (_prefixesOrange.contains(prefixe)) return OperateurTelephone.orange;
    if (_prefixesMoov.contains(prefixe)) return OperateurTelephone.moov;
    if (_prefixesTelecel.contains(prefixe)) return OperateurTelephone.telecel;
    return OperateurTelephone.inconnu;
  }
}
