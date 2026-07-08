import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/errors/exceptions.dart';
import '../../../core/widgets/error_view.dart';
import '../../../core/widgets/loading_indicator.dart';
import '../../auth_candidat/presentation/auth_candidat_providers.dart';
import 'profil_candidat_providers.dart';

class ProfilScreen extends ConsumerWidget {
  const ProfilScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profil = ref.watch(profilCandidatNotifierProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Mon profil')),
      body: profil.when(
        loading: () => const LoadingIndicator(),
        error: (erreur, _) => ErrorView(
          message: erreur is AppException
              ? erreur.message
              : 'Une erreur est survenue.',
          onRetry: () => ref.invalidate(profilCandidatNotifierProvider),
        ),
        data: (p) => ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(p.nomComplet,
                style:
                    const TextStyle(fontSize: 20, fontWeight: FontWeight.w700)),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(
                  p.telephoneVerifie ? Icons.check_circle : Icons.error_outline,
                  size: 16,
                  color:
                      p.telephoneVerifie ? AppColors.succes : AppColors.erreur,
                ),
                const SizedBox(width: 6),
                const Text(
                  'Téléphone vérifié',
                  style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
                ),
              ],
            ),
            const SizedBox(height: 24),
            _ChampEmail(emailActuel: p.email),
            const SizedBox(height: 16),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Notifications par SMS'),
              value: p.notificationsSms,
              onChanged: (v) => ref
                  .read(profilCandidatNotifierProvider.notifier)
                  .mettreAJour(notificationsSms: v),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Notifications push'),
              value: p.notificationsPush,
              onChanged: (v) => ref
                  .read(profilCandidatNotifierProvider.notifier)
                  .mettreAJour(notificationsPush: v),
            ),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('Notifications par email'),
              value: p.notificationsEmail,
              onChanged: (v) => ref
                  .read(profilCandidatNotifierProvider.notifier)
                  .mettreAJour(notificationsEmail: v),
            ),
            const SizedBox(height: 24),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.notifications_outlined),
              title: const Text('Notifications'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push(AppRoutes.notifications),
            ),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.shield_outlined),
              title: const Text('Sécurité et mes droits'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => context.push(AppRoutes.securiteDroits),
            ),
            const SizedBox(height: 24),
            OutlinedButton(
              onPressed: () async {
                await ref.read(authCandidatRepositoryProvider).deconnecter();
                if (context.mounted) context.go(AppRoutes.accueil);
              },
              child: const Text('Se déconnecter'),
            ),
          ],
        ),
      ),
    );
  }
}

class _ChampEmail extends StatefulWidget {
  const _ChampEmail({required this.emailActuel});

  final String? emailActuel;

  @override
  State<_ChampEmail> createState() => _ChampEmailState();
}

class _ChampEmailState extends State<_ChampEmail> {
  late final _controller = TextEditingController(text: widget.emailActuel);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, _) {
        return TextField(
          controller: _controller,
          keyboardType: TextInputType.emailAddress,
          decoration: InputDecoration(
            labelText: 'Email',
            suffixIcon: IconButton(
              icon: const Icon(Icons.check),
              onPressed: () => ref
                  .read(profilCandidatNotifierProvider.notifier)
                  .mettreAJour(email: _controller.text.trim()),
            ),
          ),
        );
      },
    );
  }
}
