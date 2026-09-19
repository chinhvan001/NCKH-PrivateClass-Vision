import 'package:cloud_firestore/cloud_firestore.dart';

class MonitoringSessionModel {
  final String id;
  final String classId;
  final String classroomId;
  final String teacherId;
  final String scheduleId;
  final double avgAttentionScore;
  final int presentStudents;
  final String note;

  const MonitoringSessionModel({
    required this.id,
    required this.classId,
    required this.classroomId,
    required this.teacherId,
    required this.scheduleId,
    required this.avgAttentionScore,
    required this.presentStudents,
    required this.note,
  });

  factory MonitoringSessionModel.fromFirestore(DocumentSnapshot doc) {
    final d = doc.data() as Map<String, dynamic>;
    return MonitoringSessionModel(
      id: doc.id,
      classId: d['class_id'] as String? ?? '',
      classroomId: d['classroom_id'] as String? ?? '',
      teacherId: d['teacher_id'] as String? ?? '',
      scheduleId: d['schedule_id'] as String? ?? '',
      avgAttentionScore: (d['avg_attention_score'] as num?)?.toDouble() ?? 0.0,
      presentStudents: (d['present_students'] as num?)?.toInt() ?? 0,
      note: d['note'] as String? ?? '',
    );
  }

  /// % tập trung dạng int để hiển thị
  int get avgAttentionPercent => avgAttentionScore.round();
}
