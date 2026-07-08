import 'package:flutter/material.dart';

import '../../../config/theme.dart';
import '../../consultation_rapide/domain/administration.dart';
import '../../consultation_rapide/domain/examen.dart';
import '../domain/candidature.dart';

Future<void> ouvrirDetailCandidature(
  BuildContext context, {
  required Candidature candidature,
  required Administration? administration,
  required Examen? examen,
}) {
  return showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    builder: (context) => Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            examen?.libelle ?? 'Examen',
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          Text(
            administration?.nomOfficiel ?? '',
            style: const TextStyle(fontSize: 14, color: AppColors.texteAttenue),
          ),
          const SizedBox(height: 16),
          _Ligne('Récépissé', candidature.numeroRecepisse),
          _Ligne('Statut', candidature.statutVerification.libelle),
          if (candidature.methodeVerification != null)
            _Ligne('Méthode de vérification', candidature.methodeVerification!),
          if (candidature.dernierResultatStatut != null)
            _Ligne('Résultat', candidature.dernierResultatStatut!),
          if (candidature.dernierResultatPhase != null)
            _Ligne('Phase', candidature.dernierResultatPhase!),
          const SizedBox(height: 12),
        ],
      ),
    ),
  );
}

class _Ligne extends StatelessWidget {
  const _Ligne(this.label, this.valeur);

  final String label;
  final String valeur;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(label,
                style: const TextStyle(
                    color: AppColors.texteAttenue, fontSize: 13)),
          ),
          Expanded(
            child: Text(valeur,
                style:
                    const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}
