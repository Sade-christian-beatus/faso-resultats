/// Erreurs métier renvoyées par les repositories vers la couche presentation.
/// Toujours accompagnées d'un message déjà en français, prêt à afficher
/// (prompt § UX : "pas de jargon technique, pas de Error 500").
sealed class Failure {
  const Failure(this.message);

  final String message;
}

class EchecServeur extends Failure {
  const EchecServeur(super.message);
}

class EchecReseau extends Failure {
  const EchecReseau(super.message);
}

class EchecAuthentification extends Failure {
  const EchecAuthentification(super.message);
}

class EchecValidation extends Failure {
  const EchecValidation(super.message);
}

class EchecInconnu extends Failure {
  const EchecInconnu(super.message);
}
