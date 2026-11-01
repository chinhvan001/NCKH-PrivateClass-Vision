// File: lib/core/models/session_student_model.dart
//
// Conceptually "MonitoredStudentModel" matching the new schema.
// Class name kept as SessionStudentModel for UI backward-compat.

import '../utils/firestore_parsers.dart';

class SessionStudentModel {
  final String seatId; // key in the mnoitored_student map, e.g. "R1C2"
  final String studentId;
  final int row;
  final int column;
  final bool isPresent;
  final bool isAttention;
  final double? attentionScore;
  final String note;

  const SessionStudentModel({
    this.seatId = '',
    required this.studentId,
    required this.row,
    required this.column,
    required this.isPresent,
    required this.isAttention,
    this.attentionScore,
    this.note = '',
  });

  // ── Parse from a single entry inside the `mnoitored_student` Map ──
  factory SessionStudentModel.fromMapEntry(
      String key, Map<String, dynamic> json) {
    final cleanSid = FirestoreParsers.cleanId(json['student_id']);
    return SessionStudentModel(
      seatId: key,
      studentId: cleanSid ?? '',
      row: (json['row'] as num?)?.toInt() ?? 0,
      column: (json['column'] as num?)?.toInt() ?? 0,
      isPresent: json['is_present'] == true,
      isAttention: json['is_attention'] != false,
      attentionScore: (json['attention_score'] as num?)?.toDouble(),
      note: json['note']?.toString() ?? '',
    );
  }

  // ── Legacy: parse from a List element (old `students` array) ──
  factory SessionStudentModel.fromJson(Map<String, dynamic> json) {
    return SessionStudentModel(
      seatId: json['seat_id']?.toString() ?? '',
      studentId: json['student_id']?.toString() ?? '',
      row: (json['row'] as num?)?.toInt() ?? 0,
      column: (json['column'] as num?)?.toInt() ?? 0,
      isPresent: json['is_present'] == true,
      isAttention: json['is_attention'] != false,
      attentionScore: (json['attention_score'] as num?)?.toDouble(),
      note: json['note']?.toString() ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = {
      'seat_id': seatId,
      'student_id': studentId,
      'row': row,
      'column': column,
      'is_present': isPresent,
      'is_attention': isAttention,
      'note': note,
    };
    if (attentionScore != null) {
      data['attention_score'] = attentionScore;
    }
    return data;
  }

  SessionStudentModel copyWith({
    String? seatId,
    String? studentId,
    int? row,
    int? column,
    bool? isPresent,
    bool? isAttention,
    double? attentionScore,
    String? note,
  }) {
    return SessionStudentModel(
      seatId: seatId ?? this.seatId,
      studentId: studentId ?? this.studentId,
      row: row ?? this.row,
      column: column ?? this.column,
      isPresent: isPresent ?? this.isPresent,
      isAttention: isAttention ?? this.isAttention,
      attentionScore: attentionScore ?? this.attentionScore,
      note: note ?? this.note,
    );
  }
}
