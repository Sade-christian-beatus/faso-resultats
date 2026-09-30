import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../config/constants.dart';
import '../../config/theme.dart';

/// Bottom sheet listing the support phone numbers ([ContactSupport]), each
/// one opening the phone dialer.
Future<void> afficherContactSupport(BuildContext context) {
  return showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    builder: (context) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Assistance Faso Résultats',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 4),
            const Text(
              "Un problème avec l'application ? Appelez-nous. Pour une "
              'question sur une décision (admis, ajourné…), rapprochez-vous '
              "de l'organisateur de l'examen.",
              style: TextStyle(color: AppColors.texteAttenue),
            ),
            const SizedBox(height: 12),
            for (final numero in ContactSupport.telephones)
              ListTile(
                contentPadding: EdgeInsets.zero,
                leading: const CircleAvatar(
                  backgroundColor: AppColors.vertFonce,
                  foregroundColor: Colors.white,
                  child: Icon(Icons.call),
                ),
                title: Text(
                  ContactSupport.formater(numero),
                  style: const TextStyle(
                      fontSize: 17, fontWeight: FontWeight.w600),
                ),
                subtitle: const Text('Appuyer pour appeler'),
                onTap: () => appelerSupport(context, numero),
              ),
          ],
        ),
      ),
    ),
  );
}

Future<void> appelerSupport(BuildContext context, String numero) async {
  final messenger = ScaffoldMessenger.maybeOf(context);
  bool ouvert;
  try {
    ouvert = await launchUrl(ContactSupport.uriAppel(numero));
  } on Exception {
    // No dialer (tablet, emulator): fall back to showing the number.
    ouvert = false;
  }
  if (!ouvert) {
    messenger?.showSnackBar(SnackBar(
      content: Text('Appelez le ${ContactSupport.formater(numero)}'),
    ));
  }
}
