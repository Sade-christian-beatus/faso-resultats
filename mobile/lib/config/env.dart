/// Deux environnements possibles, choisis au lancement via
/// `flutter run --dart-define=ENV=dev` (par défaut) ou `ENV=prod`.
enum Env { dev, prod }

class EnvConfig {
  const EnvConfig._();

  static final Env current = _parseEnv();

  static Env _parseEnv() {
    const raw = String.fromEnvironment('ENV', defaultValue: 'dev');
    return raw == 'prod' ? Env.prod : Env.dev;
  }

  /// URL de base de l'API. En dev, `10.0.2.2` est l'alias que l'émulateur
  /// Android utilise pour joindre `localhost` de la machine hôte — un
  /// appareil physique devra pointer vers une IP réelle ou un tunnel (ngrok).
  static String get apiBaseUrl {
    switch (current) {
      case Env.dev:
        return const String.fromEnvironment(
          'API_BASE_URL',
          defaultValue: 'http://10.0.2.2:8000',
        );
      case Env.prod:
        return 'https://api.fasoresultats.bf';
    }
  }
}
