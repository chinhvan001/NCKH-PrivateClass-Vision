/// Centralized Firestore collection names & field-name constants.
///
/// Single Source of Truth – every service/model must reference these
/// constants instead of hard-coding collection names.
class FirestoreConstants {
  FirestoreConstants._(); // prevent instantiation

  // ── Collection names ────────────────────────────────────────────────
  static const String classes = 'classes2';
  static const String sessions = 'sessions';
  static const String students = 'students2';
  static const String parents = 'parents';
  static const String teachers = 'teachers';
  static const String admins = 'admins';
  static const String cameras = 'cameras';
  static const String cameraConfigs = 'camera_configs';
  static const String sessionResults = 'session_results';
  static const String sessionEvaluations = 'session_evaluations';
  static const String classMembers = 'class_members';
  static const String edgeNodes = 'edge_nodes';

  /// Giữ lại alias cho backward-compat – mọi nơi dùng `enrollments`
  /// sẽ tự trỏ sang `class_members`.
  static const String enrollments = classMembers;
}
