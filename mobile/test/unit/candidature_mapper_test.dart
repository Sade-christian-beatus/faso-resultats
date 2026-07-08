import 'package:faso_resultats_mobile/features/candidatures/data/candidature_mapper.dart';
import 'package:faso_resultats_mobile/features/candidatures/domain/candidature.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('CandidatureMapper', () {
    test('convertit une candidature vérifiée', () {
      final json = {
        'id': 'c-1',
        'administration_id': 'admin-1',
        'examen_id': 'examen-1',
        'numero_recepisse': '000123',
        'statut_verification': 'VERIFIE_AUTO',
        'methode_verification': 'CNIB_MATCH_AUTO',
        'notifications_activees': true,
        'dernier_resultat_statut': 'ADMIS',
        'dernier_resultat_phase': 'RESULTAT_UNIQUE',
        'dernier_resultat_publie_at': '2026-07-01T10:00:00Z',
      };

      final candidature = json.versCandidature();

      expect(candidature.statutVerification,
          StatutVerificationCandidature.verifieAuto);
      expect(candidature.dernierResultatStatut, 'ADMIS');
      expect(candidature.attenteConfirmationOtp, isFalse);
    });

    test('détecte une candidature en attente de confirmation OTP (mécanisme 3)',
        () {
      final json = {
        'id': 'c-2',
        'administration_id': 'admin-1',
        'examen_id': 'examen-1',
        'numero_recepisse': '000124',
        'statut_verification': 'EN_ATTENTE',
        'methode_verification': 'OTP_SMS',
        'notifications_activees': true,
        'dernier_resultat_statut': null,
        'dernier_resultat_phase': null,
        'dernier_resultat_publie_at': null,
      };

      final candidature = json.versCandidature();

      expect(candidature.attenteConfirmationOtp, isTrue);
    });
  });
}
