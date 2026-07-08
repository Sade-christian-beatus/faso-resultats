import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/date_symbol_data_local.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'core/storage/prefs_storage.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Requis par DateFormatter (core/utils/date_formatter.dart) : sans cet
  // appel, tout DateFormat('...', 'fr_FR') lève LocaleDataException au
  // premier usage — bug réel trouvé au jour 10 en écrivant les tests
  // unitaires de DateFormatter, jamais déclenché avant faute de test direct.
  await initializeDateFormatting('fr_FR');
  final sharedPreferences = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [
        sharedPreferencesProvider.overrideWithValue(sharedPreferences),
      ],
      child: const FasoResultatsApp(),
    ),
  );
}
