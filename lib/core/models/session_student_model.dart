// File: lib/core/models/session_student_model.dart

class SessionStudentModel {
  final String studentId;
  final int row;
  final int column;
  final bool isPresent;
  final bool isAttention;
  final double? attentionScore;
  final String note;

  const SessionStudentModel({
    required this.studentId,
    required this.row,
    required this.column,
    required this.isPresent,
    required this.isAttention,
    this.attentionScore,
    this.note = '',
  });

  factory SessionStudentModel.fromJson(Map<String, dynamic> json) {
    return SessionStudentModel(
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
    String? studentId,
    int? row,
    int? column,
    bool? isPresent,
    bool? isAttention,
    double? attentionScore,
    String? note,
  }) {
    return SessionStudentModel(
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
