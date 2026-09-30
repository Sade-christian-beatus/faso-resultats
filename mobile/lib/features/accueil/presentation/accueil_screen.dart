import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../config/constants.dart';
import '../../../config/routes.dart';
import '../../../config/theme.dart';
import '../../../core/storage/prefs_storage.dart';
import '../../../core/widgets/contact_support_sheet.dart';
import '../../consultation_rapide/domain/categorie_examen.dart';
import '../../consultation_rapide/domain/examen.dart';
import '../../consultation_rapide/presentation/consultation_providers.dart';
import 'navigation_principale.dart';

/// Home screen, laid out after the mobile blueprint of 2026-09-30: header,
/// hero carousel, 8 shortcuts, candidate space banner, recent results. The
/// bottom navigation comes from [NavigationPrincipale].
///
/// Consulting a result never requires an account (both paths stay equally
/// visible). On the very first launch, a versioned information notice is
/// shown (day 8): this is the only screen guaranteed to be seen before any
/// candidate account is created (the splash goes straight to the dashboard
/// when a token already exists).
class AccueilScreen extends ConsumerStatefulWidget {
  const AccueilScreen({super.key});

  @override
  ConsumerState<AccueilScreen> createState() => _AccueilScreenState();
}

class _AccueilScreenState extends ConsumerState<AccueilScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance
        .addPostFrameCallback((_) => _verifierConsentement());
  }

  Future<void> _verifierConsentement() async {
    final prefs = ref.read(prefsStorageProvider);
    if (prefs.versionConsentementAcceptee == AppInfo.versionConsentementApp) {
      return;
    }
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: const Text('Avant de continuer'),
        content: const Text(
          'Faso Résultats vous permet de consulter vos résultats sans '
          'créer de compte. Si vous créez un espace candidat, vos données '
          '(CNIB, téléphone, date de naissance) sont chiffrées et utilisées '
          'uniquement pour vérifier votre identité et vous notifier de vos '
          'résultats. Vous pouvez les consulter ou les supprimer à tout '
          'moment.',
        ),
        actions: [
          TextButton(
            onPressed: () => context.push(AppRoutes.politiqueConfidentialite),
            child: const Text('En savoir plus'),
          ),
          FilledButton(
            onPressed: () async {
              await ref
                  .read(prefsStorageProvider)
                  .enregistrerConsentement(AppInfo.versionConsentementApp);
              if (context.mounted) Navigator.of(context).pop();
            },
            child: const Text("J'ai compris"),
          ),
        ],
      ),
    );
  }

  Future<void> _rafraichir() async {
    ref
      ..invalidate(examensPublicsProvider)
      ..invalidate(administrationsPubliquesProvider);
    await ref.read(examensPublicsProvider.future).catchError((_) => <Examen>[]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: RefreshIndicator(
        onRefresh: _rafraichir,
        child: ListView(
          padding: EdgeInsets.zero,
          children: const [
            _EnTete(),
            SizedBox(height: 16),
            _Carrousel(),
            SizedBox(height: 20),
            _GrilleRaccourcis(),
            SizedBox(height: 20),
            _BanniereEspaceCandidat(),
            SizedBox(height: 24),
            _ResultatsRecents(),
            SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

// --- 1. Header ---

class _EnTete extends ConsumerWidget {
  const _EnTete();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.vertFonce, Color(0xFF00612F)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 10, 8, 14),
          child: Row(
            children: [
              // The official logo only exists for light backgrounds
              // (docs/CHARTE_GRAPHIQUE.md): it sits on a white plate.
              DecoratedBox(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  child: Image.asset(
                    'assets/images/logo.webp',
                    height: 46,
                    semanticLabel: 'Faso Résultats — Vos résultats en un clic',
                  ),
                ),
              ),
              const Spacer(),
              IconButton(
                onPressed: () => context.go(AppRoutes.notifications),
                tooltip: 'Notifications',
                icon: const Icon(Icons.notifications_none,
                    color: Colors.white, size: 28),
              ),
              IconButton(
                onPressed: () =>
                    ouvrirEspaceCandidat(context, ref, AppRoutes.profil),
                tooltip: 'Mon compte',
                icon: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                  ),
                  child: const Icon(Icons.person, color: Colors.white),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// --- 2. Hero carousel ---

class _Carrousel extends StatefulWidget {
  const _Carrousel();

  @override
  State<_Carrousel> createState() => _CarrouselState();
}

class _CarrouselState extends State<_Carrousel> {
  // Swipe only, no auto-play: nothing moves under a finger that is reading,
  // and no timer drains a low-end phone's battery.
  final _controleur = PageController(viewportFraction: 0.92);
  int _page = 0;

  @override
  void dispose() {
    _controleur.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final diapositives = [
      _Diapositive(
        titre: 'Consultez vos résultats',
        titreAccent: 'en quelques clics',
        texte: 'BAC, BEPC, CAP, concours… tous vos résultats au même '
            'endroit !',
        action: 'Rechercher un résultat',
        icone: Icons.search,
        onPressed: () => context.go(AppRoutes.consultationRapide),
        photo: 'assets/images/hero.webp',
      ),
      _Diapositive(
        titre: 'Un seul compte',
        titreAccent: 'pour tous vos concours',
        texte: 'Suivez vos examens et concours depuis votre espace candidat.',
        action: 'Créer mon espace',
        icone: Icons.person_add_alt_1,
        onPressed: () => context.go(AppRoutes.authCandidat),
        illustration: Icons.how_to_reg,
      ),
      _Diapositive(
        titre: 'Pas de connexion ?',
        titreAccent: 'Consultez par SMS',
        texte: 'Bientôt : votre résultat par simple SMS, même sans '
            'smartphone.',
        action: 'Consulter par SMS',
        icone: Icons.sms_outlined,
        onPressed: () => context.go(AppRoutes.consultationSms),
        illustration: Icons.sms,
      ),
      _Diapositive(
        titre: "Besoin d'aide ?",
        titreAccent: 'Nous vous répondons',
        texte:
            'Appelez le ${ContactSupport.telephones.map(ContactSupport.formater).join(' ou le ')}.',
        action: 'Nous appeler',
        icone: Icons.call,
        onPressed: () => afficherContactSupport(context),
        illustration: Icons.support_agent,
      ),
    ];

    return Column(
      children: [
        SizedBox(
          height: 200,
          child: PageView(
            controller: _controleur,
            onPageChanged: (page) => setState(() => _page = page),
            children: diapositives,
          ),
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            for (var i = 0; i < diapositives.length; i++)
              AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.symmetric(horizontal: 3),
                width: i == _page ? 18 : 7,
                height: 7,
                decoration: BoxDecoration(
                  color: i == _page
                      ? AppColors.vertFonce
                      : AppColors.vertFonce.withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(4),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

class _Diapositive extends StatelessWidget {
  const _Diapositive({
    required this.titre,
    required this.titreAccent,
    required this.texte,
    required this.action,
    required this.icone,
    required this.onPressed,
    this.photo,
    this.illustration,
  });

  final String titre;
  final String titreAccent;
  final String texte;
  final String action;
  final IconData icone;
  final VoidCallback onPressed;
  final String? photo;
  final IconData? illustration;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4),
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFE8F8EF), Color(0xFFF7FBF9)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFC6EED7)),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(18),
          child: Row(
            children: [
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 14, 8, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        titre,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 18, fontWeight: FontWeight.w800),
                      ),
                      Text(
                        titreAccent,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w800,
                          color: AppColors.vertFonce,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        texte,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                            fontSize: 12.5, color: AppColors.texteAttenue),
                      ),
                      const SizedBox(height: 10),
                      FilledButton.icon(
                        onPressed: onPressed,
                        icon: Icon(icone, size: 18),
                        label: Text(action),
                        style: FilledButton.styleFrom(
                          backgroundColor: AppColors.vertFonce,
                          visualDensity: VisualDensity.compact,
                          shape: const StadiumBorder(),
                          textStyle: const TextStyle(
                              fontSize: 13, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              if (photo != null)
                Image.asset(photo!,
                    width: 118, height: double.infinity, fit: BoxFit.cover)
              else
                Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: CircleAvatar(
                    radius: 40,
                    backgroundColor: AppColors.vertFaso.withValues(alpha: 0.15),
                    child: Icon(illustration,
                        size: 42, color: AppColors.vertFonce),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

// --- 3. Shortcut grid ---

class _Raccourci {
  const _Raccourci(this.libelle, this.icone, this.couleur, this.onTap,
      {this.couleurIcone = Colors.white});

  final String libelle;
  final IconData icone;
  final Color couleur;
  final Color couleurIcone;
  final void Function(BuildContext context, WidgetRef ref) onTap;
}

void _ouvrirCategorie(BuildContext context, CategorieExamen categorie) =>
    context.go(AppRoutes.consultationFiltree(categorie: categorie));

final _raccourcis = [
  _Raccourci('Examens', Icons.school, AppColors.vertFonce,
      (c, _) => _ouvrirCategorie(c, CategorieExamen.examens)),
  _Raccourci('Concours', Icons.assignment, const Color(0xFF1D4E89),
      (c, _) => _ouvrirCategorie(c, CategorieExamen.concours)),
  _Raccourci('Fonction publique', Icons.account_balance, AppColors.jauneFaso,
      (c, _) => _ouvrirCategorie(c, CategorieExamen.fonctionPublique),
      couleurIcone: AppColors.bleuNuit),
  _Raccourci('Paramili­taires', Icons.shield, const Color(0xFF6D28D9),
      (c, _) => _ouvrirCategorie(c, CategorieExamen.paramilitaires)),
  _Raccourci('Recherche par numéro', Icons.search, AppColors.bleuNuit,
      (c, _) => c.go(AppRoutes.consultationRapide)),
  _Raccourci('Mes résultats', Icons.fact_check, AppColors.rougeFaso,
      (c, r) => ouvrirEspaceCandidat(c, r, AppRoutes.dashboard)),
  _Raccourci('Questions fréquentes', Icons.help_outline,
      const Color(0xFF0E7490), (c, _) => c.push(AppRoutes.aide)),
  _Raccourci('Assistance', Icons.headset_mic, const Color(0xFFEA580C),
      (c, _) => afficherContactSupport(c)),
];

class _GrilleRaccourcis extends ConsumerWidget {
  const _GrilleRaccourcis();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: GridView.count(
        crossAxisCount: 4,
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        mainAxisSpacing: 10,
        crossAxisSpacing: 10,
        childAspectRatio: 0.78,
        children: [
          for (final raccourci in _raccourcis)
            Material(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              child: InkWell(
                borderRadius: BorderRadius.circular(14),
                onTap: () => raccourci.onTap(context, ref),
                child: Ink(
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFFE7EAEE)),
                  ),
                  padding: const EdgeInsets.fromLTRB(4, 10, 4, 6),
                  child: Column(
                    children: [
                      CircleAvatar(
                        radius: 21,
                        backgroundColor: raccourci.couleur,
                        child: Icon(raccourci.icone,
                            color: raccourci.couleurIcone, size: 22),
                      ),
                      const SizedBox(height: 6),
                      Expanded(
                        child: _LibelleRaccourci(raccourci.libelle),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Tile label: up to two lines; a single long word ("Paramilitaires") is
/// scaled down to fit rather than broken in the middle.
class _LibelleRaccourci extends StatelessWidget {
  const _LibelleRaccourci(this.libelle);

  final String libelle;

  @override
  Widget build(BuildContext context) {
    const style = TextStyle(
      fontSize: 11.5,
      fontWeight: FontWeight.w600,
      height: 1.2,
    );
    if (!libelle.contains(' ')) {
      return Align(
        alignment: Alignment.topCenter,
        child: FittedBox(
          fit: BoxFit.scaleDown,
          child: Text(libelle, maxLines: 1, style: style),
        ),
      );
    }
    return Text(
      libelle,
      textAlign: TextAlign.center,
      maxLines: 2,
      overflow: TextOverflow.ellipsis,
      style: style,
    );
  }
}

// --- 4. Candidate space banner (replaces the blueprint's promo banner) ---

class _BanniereEspaceCandidat extends StatelessWidget {
  const _BanniereEspaceCandidat();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppColors.vertFonce, Color(0xFF004B25)],
          ),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Suivez vos concours',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Tous vos examens et concours dans un seul espace '
                      'candidat.',
                      style: TextStyle(color: Color(0xFFC6EED7), fontSize: 13),
                    ),
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: () => context.go(AppRoutes.authCandidat),
                      icon: const Icon(Icons.arrow_forward, size: 18),
                      label: const Text('Créer mon espace'),
                      style: OutlinedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: AppColors.vertFonce,
                        side: BorderSide.none,
                        minimumSize: const Size(0, 40),
                        shape: const StadiumBorder(),
                        textStyle: const TextStyle(
                            fontSize: 14, fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              const _DrapeauBurkina(),
            ],
          ),
        ),
      ),
    );
  }
}

/// Burkina Faso flag drawn with widgets (no image asset to ship).
class _DrapeauBurkina extends StatelessWidget {
  const _DrapeauBurkina();

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(6),
      child: SizedBox(
        width: 72,
        height: 48,
        child: Stack(
          alignment: Alignment.center,
          children: [
            Column(
              children: [
                Expanded(child: Container(color: AppColors.rougeFaso)),
                Expanded(child: Container(color: AppColors.vertFaso)),
              ],
            ),
            const Icon(Icons.star, color: AppColors.jauneFaso, size: 22),
          ],
        ),
      ),
    );
  }
}

// --- 5. Recent results ---

const _nombreResultatsRecents = 4;

class _ResultatsRecents extends ConsumerWidget {
  const _ResultatsRecents();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final examens = ref.watch(examensPublicsProvider);
    final administrations =
        ref.watch(administrationsPubliquesProvider).valueOrNull ?? [];
    final sigles = {for (final a in administrations) a.id: a.sigle};

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              const Icon(Icons.campaign, color: AppColors.vertFonce),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Résultats récents',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                ),
              ),
              TextButton(
                onPressed: () => context.go(AppRoutes.consultationRapide),
                child: const Text('Voir tout'),
              ),
            ],
          ),
          const SizedBox(height: 4),
          examens.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (_, __) => Row(
              children: [
                const Expanded(
                  child: Text(
                    'Impossible de charger les résultats. Vérifiez votre '
                    'connexion.',
                    style: TextStyle(color: AppColors.erreur, fontSize: 13),
                  ),
                ),
                TextButton(
                  onPressed: () => ref.invalidate(examensPublicsProvider),
                  child: const Text('Réessayer'),
                ),
              ],
            ),
            data: (liste) {
              if (liste.isEmpty) {
                return const Padding(
                  padding: EdgeInsets.symmetric(vertical: 16),
                  child: Text(
                    'Aucun résultat publié pour le moment.',
                    style: TextStyle(color: AppColors.texteAttenue),
                  ),
                );
              }
              return Column(
                children: [
                  for (final examen in liste.take(_nombreResultatsRecents))
                    _CarteResultatRecent(
                        examen: examen, sigle: sigles[examen.administrationId]),
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

const _iconesCategorie = {
  CategorieExamen.examens: (Icons.school, AppColors.vertFonce, Colors.white),
  CategorieExamen.concours: (Icons.assignment, Color(0xFF1D4E89), Colors.white),
  CategorieExamen.fonctionPublique: (
    Icons.account_balance,
    AppColors.jauneFaso,
    AppColors.bleuNuit,
  ),
  CategorieExamen.paramilitaires: (
    Icons.shield,
    Color(0xFF6D28D9),
    Colors.white,
  ),
  CategorieExamen.autres: (Icons.more_horiz, Color(0xFF475569), Colors.white),
};

class _CarteResultatRecent extends StatelessWidget {
  const _CarteResultatRecent({required this.examen, required this.sigle});

  final Examen examen;
  final String? sigle;

  @override
  Widget build(BuildContext context) {
    final (icone, fond, couleurIcone) =
        _iconesCategorie[CategorieExamen.de(examen)]!;
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: ListTile(
        contentPadding: const EdgeInsets.fromLTRB(12, 6, 8, 6),
        onTap: () =>
            context.go(AppRoutes.consultationFiltree(examenId: examen.id)),
        leading: CircleAvatar(
          radius: 22,
          backgroundColor: fond,
          child: Icon(icone, color: couleurIcone),
        ),
        title: Text(
          '${libelleTypeExamen(examen.typeExamen)} ${examen.annee}',
          style: const TextStyle(fontWeight: FontWeight.w700),
        ),
        subtitle: Text(
          [examen.libelle, if (sigle != null) sigle].join(' · '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 12.5),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: const Color(0xFFE8F8EF),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFF93DFB4)),
              ),
              child: const Text(
                'Disponible',
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF00612F),
                ),
              ),
            ),
            const Icon(Icons.chevron_right, color: AppColors.texteAttenue),
          ],
        ),
      ),
    );
  }
}
