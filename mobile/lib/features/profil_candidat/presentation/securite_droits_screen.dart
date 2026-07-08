import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:share_plus/share_plus.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/utils/date_formatter.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_indicator.dart';
import 'droits_candidat_provider.dart';
import 'profil_candidat_providers.dart';

class SecuriteDroitsScreen extends ConsumerWidget {
  const SecuriteDroitsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sécurité et mes droits')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'Sessions actives',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 4),
          const Text(
            "Fonctionnalité pas encore disponible : impossible aujourd'hui de "
            'lister ou révoquer individuellement vos sessions.',
            style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
          ),
          const SizedBox(height: 24),
          const Text(
            "Journal d'accès",
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          const _JournalAcces(),
          const SizedBox(height: 24),
          const Text('Mes droits',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          const _MesDroits(),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () => _exporter(context, ref),
            icon: const Icon(Icons.download_outlined),
            label: const Text('Exporter mes données'),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => _confirmerSuppression(context, ref),
            style: OutlinedButton.styleFrom(foregroundColor: AppColors.erreur),
            icon: const Icon(Icons.delete_outline),
            label: const Text('Supprimer mon compte'),
          ),
        ],
      ),
    );
  }

  Future<void> _exporter(BuildContext context, WidgetRef ref) async {
    try {
      final export =
          await ref.read(profilCandidatRepositoryProvider).exporter();
      final texte = 'Export Faso Résultats — ${export.nomComplet}\n'
          'Candidatures : ${export.candidatures.length}\n'
          'Journal : ${export.journal.length} entrées';
      await Share.share(texte);
    } on Exception catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(
            const SnackBar(content: Text("Échec de l'export. Réessayez.")));
      }
    }
  }

  Future<void> _confirmerSuppression(
      BuildContext context, WidgetRef ref) async {
    final premiereConfirmation = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Supprimer votre compte ?'),
        content: const Text(
          'Cette action supprime immédiatement votre profil et vos candidatures. '
          'Elle est irréversible.',
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Annuler')),
          TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Continuer')),
        ],
      ),
    );
    if (premiereConfirmation != true || !context.mounted) return;

    final confirmationFinale = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmation finale'),
        content: const Text(
            'Êtes-vous vraiment sûr ? Cette suppression est définitive.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Annuler')),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: AppColors.erreur),
            child: const Text('Supprimer définitivement'),
          ),
        ],
      ),
    );
    if (confirmationFinale != true || !context.mounted) return;

    await ref.read(profilCandidatRepositoryProvider).supprimerCompte();
    if (context.mounted) context.go(AppRoutes.accueil);
  }
}

class _JournalAcces extends ConsumerWidget {
  const _JournalAcces();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final export = ref.watch(_exportFutureProvider);
    return export.when(
      loading: () => const LoadingIndicator(),
      error: (erreur, _) => ErrorView(
        message: erreur is AppException
            ? erreur.message
            : 'Impossible de charger le journal.',
      ),
      data: (data) {
        if (data.journal.isEmpty) {
          return const Text(
            'Aucune activité enregistrée.',
            style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
          );
        }
        return Column(
          children: data.journal
              .take(20)
              .map(
                (entree) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  leading: const Icon(Icons.history, size: 18),
                  title:
                      Text(entree.action, style: const TextStyle(fontSize: 13)),
                  trailing: Text(
                    DateFormatter.pourAffichage(entree.timestamp),
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.texteAttenue),
                  ),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

final _exportFutureProvider = FutureProvider.autoDispose((ref) {
  return ref.watch(profilCandidatRepositoryProvider).exporter();
});

class _MesDroits extends ConsumerWidget {
  const _MesDroits();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final droits = ref.watch(droitsCandidatProvider);
    return droits.when(
      loading: () => const LoadingIndicator(),
      error: (erreur, _) => const Text(
        'Impossible de charger vos droits.',
        style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
      ),
      data: (data) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          ...data.droits.map(
            (d) => Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Text('• $d', style: const TextStyle(fontSize: 13)),
            ),
          ),
          const SizedBox(height: 8),
          Text('Contact DPO : ${data.contactDpo}',
              style: const TextStyle(fontSize: 13)),
        ],
      ),
    );
  }
}
