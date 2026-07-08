import 'package:faso_resultats_mobile/features/consultation_sms/presentation/consultation_sms_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('affiche le message « pas encore disponible »', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: ConsultationSmsScreen()),
    );

    expect(
      find.textContaining("n'est pas encore disponible"),
      findsOneWidget,
    );
  });
}
