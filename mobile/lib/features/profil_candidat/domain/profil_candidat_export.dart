/// Correspond à `CandidatureExport` côté backend — volontairement distinct de
/// `Candidature` (features/candidatures/domain) : champs et usage différents
/// (export brut vs affichage dashboard), pas de bénéfice à partager le type.
class CandidatureExportEntree {
  const CandidatureExportEntree({
    required this.numeroRecepisse,
    required this.statutVerification,
    required this.createdAt,
  });

  final String numeroRecepisse;
  final String statutVerification;
  final DateTime createdAt;
}

class JournalEntree {
  const JournalEntree({required this.action, required this.timestamp, this.ip});

  final String action;
  final String? ip;
  final DateTime timestamp;
}

/// Correspond à `ProfilCandidatExport` côté backend (droit à la portabilité).
class ProfilCandidatExport {
  const ProfilCandidatExport({
    required this.numeroCnib,
    required this.nomComplet,
    required this.dateNaissance,
    required this.telephone,
    required this.consentementApdpDate,
    required this.consentementApdpVersion,
    required this.createdAt,
    required this.candidatures,
    required this.journal,
    this.email,
  });

  final String numeroCnib;
  final String nomComplet;
  final String dateNaissance;
  final String telephone;
  final String? email;
  final DateTime consentementApdpDate;
  final String consentementApdpVersion;
  final DateTime createdAt;
  final List<CandidatureExportEntree> candidatures;
  final List<JournalEntree> journal;
}
