import 'package:flutter/material.dart';

import '../../../config/constants.dart';
import '../../../config/theme.dart';

class AProposScreen extends StatelessWidget {
  const AProposScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('À propos')),
      body: const Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Faso Résultats',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
            ),
            SizedBox(height: 4),
            Text(
              'Version ${AppInfo.version}',
              style: TextStyle(fontSize: 13, color: AppColors.texteAttenue),
            ),
            SizedBox(height: 16),
            Text(
              'Plateforme de consultation des résultats '
              "d'examens et concours nationaux du Burkina Faso, en "
              'partenariat avec les administrations organisatrices.',
              style: TextStyle(fontSize: 14, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }
}
