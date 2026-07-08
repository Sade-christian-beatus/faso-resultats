import 'package:flutter/material.dart';

import '../../../config/theme.dart';
import '../../consultation_rapide/domain/administration.dart';
import '../../consultation_rapide/domain/examen.dart';
import '../domain/candidature.dart';

class CandidatureCard extends StatelessWidget {
  const CandidatureCard({
    required this.candidature,
    required this.administration,
    required this.examen,
    required this.onTap,
    required this.onRetirer,
    super.key,
  });

  final Candidature candidature;
  final Administration? administration;
  final Examen? examen;
  final VoidCallback onTap;
  final VoidCallback onRetirer;

  @override
  Widget build(BuildContext context) {
    final style = _styleStatut(candidature);

    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      administration?.nomOfficiel ?? 'Administration',
                      style: const TextStyle(
                          fontSize: 13, color: AppColors.texteAttenue),
                    ),
                  ),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: style.$2.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      style.$1,
                      style: TextStyle(
                          color: style.$2,
                          fontWeight: FontWeight.w700,
                          fontSize: 12),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(
                examen?.libelle ?? 'Examen',
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(
                'Récépissé n° ${candidature.numeroRecepisse}',
                style: const TextStyle(
                    fontSize: 13, color: AppColors.texteAttenue),
              ),
              if (candidature.dernierResultatStatut != null) ...[
                const SizedBox(height: 8),
                Text(
                  candidature.dernierResultatStatut!,
                  style: const TextStyle(
                      fontSize: 15, fontWeight: FontWeight.w700),
                ),
              ],
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: onRetirer,
                  child: const Text('Retirer',
                      style: TextStyle(color: AppColors.texteAttenue)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  (String, Color) _styleStatut(Candidature c) {
    if (c.attenteConfirmationOtp) {
      return ('Confirmation par code requise', AppColors.accentOrange);
    }
    return switch (c.statutVerification) {
      StatutVerificationCandidature.verifieAuto ||
      StatutVerificationCandidature.verifieManuel =>
        ('Vérifiée', AppColors.succes),
      StatutVerificationCandidature.enAttente => (
          'En attente',
          AppColors.accentOrange
        ),
      StatutVerificationCandidature.rejete => (
          'Non vérifiée',
          AppColors.erreur
        ),
      StatutVerificationCandidature.administrationResiliee => (
          'Administration résiliée',
          AppColors.texteAttenue,
        ),
    };
  }
}
