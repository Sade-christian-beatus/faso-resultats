import 'package:faso_resultats_mobile/core/utils/validators.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Validators.telephone', () {
    test('accepte un numéro burkinabè bien formé', () {
      expect(Validators.telephone('+22670000001'), isNull);
    });

    test('rejette un numéro sans indicatif', () {
      expect(Validators.telephone('70000001'), isNotNull);
    });

    test('rejette un champ vide', () {
      expect(Validators.telephone(''), isNotNull);
      expect(Validators.telephone(null), isNotNull);
    });
  });

  group('Validators.codeOtp', () {
    test('accepte un code à 6 chiffres', () {
      expect(Validators.codeOtp('123456'), isNull);
    });

    test('rejette un code trop court', () {
      expect(Validators.codeOtp('123'), isNotNull);
    });

    test('rejette un code non numérique', () {
      expect(Validators.codeOtp('abcdef'), isNotNull);
    });
  });

  group('Validators.numeroRecepisse', () {
    test('accepte un récépissé valide', () {
      expect(Validators.numeroRecepisse('000123'), isNull);
    });

    test('rejette un champ vide', () {
      expect(Validators.numeroRecepisse(''), isNotNull);
    });

    test('rejette un récépissé trop long (> 20 caractères, limite API)', () {
      expect(Validators.numeroRecepisse('A' * 21), isNotNull);
    });
  });

  group('Validators.cnib', () {
    test('accepte un CNIB valide', () {
      expect(Validators.cnib('B14863543'), isNull);
    });

    test('rejette un champ vide', () {
      expect(Validators.cnib(''), isNotNull);
    });
  });
}
