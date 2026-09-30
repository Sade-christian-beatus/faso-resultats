import 'package:faso_resultats_mobile/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Regression: the app forces the 'fr' locale. Without French Material
/// localizations, the date picker (candidate sign-up) and the bottom
/// navigation bar crashed with "No MaterialLocalizations found".
Widget _app(Widget home) => MaterialApp(
      locale: const Locale('fr'),
      supportedLocales: const [Locale('fr')],
      localizationsDelegates: localisationsApp,
      home: home,
    );

void main() {
  testWidgets('le sélecteur de date s’ouvre en français', (tester) async {
    await tester.pumpWidget(_app(Builder(
      builder: (context) => TextButton(
        onPressed: () => showDatePicker(
          context: context,
          initialDate: DateTime(2008, 3, 15),
          firstDate: DateTime(1990),
          lastDate: DateTime(2020),
        ),
        child: const Text('Date de naissance'),
      ),
    )));

    await tester.tap(find.text('Date de naissance'));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Annuler'), findsOneWidget);
  });

  testWidgets('la barre de navigation se construit en français',
      (tester) async {
    await tester.pumpWidget(_app(Scaffold(
      bottomNavigationBar: NavigationBar(
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home), label: 'Accueil'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Rechercher'),
        ],
      ),
    )));
    await tester.pumpAndSettle();

    expect(tester.takeException(), isNull);
    expect(find.text('Rechercher'), findsOneWidget);
  });
}
