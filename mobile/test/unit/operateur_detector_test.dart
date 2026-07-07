import 'package:faso_resultats_mobile/core/utils/operateur_detector.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('OperateurDetector.detecter', () {
    test('détecte Orange sur le préfixe 70', () {
      expect(OperateurDetector.detecter('+22670000001'),
          OperateurTelephone.orange);
    });

    test('détecte Moov sur le préfixe 76', () {
      expect(
          OperateurDetector.detecter('+22676000001'), OperateurTelephone.moov);
    });

    test('détecte Telecel sur le préfixe 60', () {
      expect(OperateurDetector.detecter('+22660000001'),
          OperateurTelephone.telecel);
    });

    test('renvoie inconnu sur un préfixe non reconnu', () {
      expect(OperateurDetector.detecter('+22699000001'),
          OperateurTelephone.inconnu);
    });

    test('fonctionne aussi sans le préfixe +226', () {
      expect(OperateurDetector.detecter('70000001'), OperateurTelephone.orange);
    });
  });
}
