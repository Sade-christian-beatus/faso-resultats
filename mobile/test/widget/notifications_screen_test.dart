import 'package:faso_resultats_mobile/features/notifications/presentation/notifications_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('affiche le message « bientôt disponible »', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: NotificationsScreen()),
    );

    expect(
      find.textContaining('Les notifications push arrivent bientôt'),
      findsOneWidget,
    );
  });
}
