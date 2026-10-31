import 'package:cloud_firestore/cloud_firestore.dart';

/// Safe parsing helpers with typo / naming-convention fallbacks.
///
/// Every `fromFirestore` factory in the project should use these
/// helpers so that we never crash on a null / wrong-type field.
class FirestoreParsers {
  FirestoreParsers._();

  // ── Primitive safe casts ────────────────────────────────────────────

  /// Return a non-null [String] from the first truthy key found in [data].
  static String string(
    Map<String, dynamic> data,
    List<String> keys, [
    String fallback = '',
  ]) {
    for (final k in keys) {
      final v = data[k];
      if (v != null && v.toString().isNotEmpty && v.toString() != 'null') {
        return v.toString();
      }
    }
    return fallback;
  }

  /// Return a non-null [int] from the first truthy key found.
  static int integer(
    Map<String, dynamic> data,
    List<String> keys, [
    int fallback = 0,
  ]) {
    for (final k in keys) {
      final v = data[k];
      if (v is num) return v.toInt();
    }
    return fallback;
  }

  /// Return a non-null [double] from the first truthy key found.
  static double decimal(
    Map<String, dynamic> data,
    List<String> keys, [
    double fallback = 0.0,
  ]) {
    for (final k in keys) {
      final v = data[k];
      if (v is num) return v.toDouble();
    }
    return fallback;
  }

  /// Return a [bool] from the first truthy key found (defaults to [fallback]).
  static bool boolean(
    Map<String, dynamic> data,
    List<String> keys, [
    bool fallback = false,
  ]) {
    for (final k in keys) {
      final v = data[k];
      if (v is bool) return v;
    }
    return fallback;
  }

  /// Return a [Map<String, dynamic>] from the first truthy key found.
  static Map<String, dynamic> map(
    Map<String, dynamic> data,
    List<String> keys,
  ) {
    for (final k in keys) {
      final v = data[k];
      if (v is Map) return Map<String, dynamic>.from(v);
    }
    return {};
  }

  /// Return a [DateTime] from the first truthy key found.
  static DateTime dateTime(
    Map<String, dynamic> data,
    List<String> keys, [
    DateTime? fallback,
  ]) {
    for (final k in keys) {
      final v = data[k];
      if (v is Timestamp) return v.toDate();
      if (v is String) {
        final dt = DateTime.tryParse(v);
        if (dt != null) return dt;
      }
      if (v is int) return DateTime.fromMillisecondsSinceEpoch(v);
    }
    return fallback ?? DateTime.now();
  }

  // ── ID cleaner ──────────────────────────────────────────────────────

  /// Strip literal `"null"` strings and whitespace – returns `null` when
  /// the value is essentially empty.
  static String? cleanId(dynamic raw) {
    if (raw == null) return null;
    final s = raw.toString().trim();
    if (s.isEmpty || s == 'null') return null;
    return s;
  }
}
