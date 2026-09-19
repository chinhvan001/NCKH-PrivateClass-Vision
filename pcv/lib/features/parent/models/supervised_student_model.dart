import 'package:cloud_firestore/cloud_firestore.dart';

class SupervisedStudentModel {
  final String id;
  final String studentId;
  final String monitoringSessionId;
  final double attentionScore;
  final bool isAttention;
  final bool isPresent;
  final int row;
  final int column;
  final String note;

  const SupervisedStudentModel({
    required this.id,
    required this.studentId,
    required this.monitoringSessionId,
    required this.attentionScore,
    required this.isAttention,
    required this.isPresent,
    required this.row,
    required this.column,
    required this.note,
  });

  factory SupervisedStudentModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return SupervisedStudentModel(
      id: doc.id,
      studentId: d['student_id'] as String? ?? '',
      monitoringSessionId: d['monitoring_session_id'] as String? ?? '',
      attentionScore: (d['attention_score'] as num?)?.toDouble() ?? 0.0,
      isAttention: d['is_attention'] as bool? ?? false,
      isPresent: d['is_present'] as bool? ?? false,
      row: (d['row'] as num?)?.toInt() ?? 0,
      column: (d['column'] as num?)?.toInt() ?? 0,
      note: d['note'] as String? ?? '',
    );
  }

  /// % tập trung dạng int
  int get attentionPercent => attentionScore.round();

  /// Trạng thái điểm danh dạng string
  String get attendanceStatus => isPresent ? 'present' : 'absent';
}
