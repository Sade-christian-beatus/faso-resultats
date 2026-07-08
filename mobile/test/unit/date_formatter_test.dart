import 'package:faso_resultats_mobile/core/utils/date_formatter.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() {
  setUpAll(() => initializeDateFormatting('fr_FR'));

  group('DateFormatter', () {
    test('pourAffichage formate en jj/mm/aaaa', () {
      expect(DateFormatter.pourAffichage(DateTime(2026, 3, 7)), '07/03/2026');
    });

    test('pourApi formate en aaaa-mm-jj (ISO, attendu par le backend)', () {
      expect(DateFormatter.pourApi(DateTime(2026, 3, 7)), '2026-03-07');
    });

    test('depuisApi parse une date ISO valide', () {
      expect(DateFormatter.depuisApi('2026-03-07'), DateTime(2026, 3, 7));
    });

    test('depuisApi renvoie null pour une valeur vide ou nulle', () {
      expect(DateFormatter.depuisApi(null), isNull);
      expect(DateFormatter.depuisApi(''), isNull);
    });

    test('depuisApi renvoie null pour une valeur invalide', () {
      expect(DateFormatter.depuisApi('pas une date'), isNull);
    });
  });
}
