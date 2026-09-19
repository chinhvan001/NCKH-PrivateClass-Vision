import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/monitoring_session_model.dart';
import '../models/supervised_student_model.dart';

class MonitoringSessionService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy tất cả buổi học theo classId
  Future<List<MonitoringSessionModel>> getSessionsByClass(
      String classId) async {
    try {
      final snapshot = await _db
          .collection('monitoring_sessions')
          .where('class_id', isEqualTo: classId)
          .get();
      return snapshot.docs
          .map(MonitoringSessionModel.fromFirestore)
          .toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải buổi học: ${e.message}');
    }
  }

  /// Lấy dữ liệu tập trung + điểm danh của 1 học sinh
  Future<List<SupervisedStudentModel>> getSupervisedDataByStudent(
      String studentId) async {
    try {
      final snapshot = await _db
          .collection('supervised_students')
          .where('student_id', isEqualTo: studentId)
          .get();
      return snapshot.docs
          .map(SupervisedStudentModel.fromFirestore)
          .toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải dữ liệu học sinh: ${e.message}');
    }
  }

  /// Lấy dữ liệu học sinh trong 1 buổi học cụ thể
  Future<SupervisedStudentModel?> getSupervisedDataByStudentAndSession(
      String studentId, String monitoringSessionId) async {
    try {
      final snapshot = await _db
          .collection('supervised_students')
          .where('student_id', isEqualTo: studentId)
          .where('monitoring_session_id', isEqualTo: monitoringSessionId)
          .limit(1)
          .get();
      if (snapshot.docs.isEmpty) return null;
      return SupervisedStudentModel.fromFirestore(snapshot.docs.first);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải dữ liệu buổi học: ${e.message}');
    }
  }

  /// Tính thống kê tổng hợp cho 1 học sinh từ supervised_students
  Future<StudentStats> getStudentStats(String studentId) async {
    final list = await getSupervisedDataByStudent(studentId);
    if (list.isEmpty) {
      return StudentStats(
        totalSessions: 0,
        presentSessions: 0,
        absentSessions: 0,
        avgAttentionScore: 0,
        attentionSessions: 0,
      );
    }
    final total = list.length;
    final present = list.where((s) => s.isPresent).length;
    final absent = total - present;
    final attention = list.where((s) => s.isAttention).length;
    final avgScore =
        list.map((s) => s.attentionScore).reduce((a, b) => a + b) / total;
    return StudentStats(
      totalSessions: total,
      presentSessions: present,
      absentSessions: absent,
      avgAttentionScore: avgScore,
      attentionSessions: attention,
    );
  }

  /// Stream realtime dữ liệu học sinh
  Stream<List<SupervisedStudentModel>> watchSupervisedDataByStudent(
      String studentId) {
    return _db
        .collection('supervised_students')
        .where('student_id', isEqualTo: studentId)
        .snapshots()
        .map((snap) =>
            snap.docs.map(SupervisedStudentModel.fromFirestore).toList());
  }
}

/// Model tổng hợp thống kê học sinh
class StudentStats {
  final int totalSessions;
  final int presentSessions;
  final int absentSessions;
  final double avgAttentionScore;
  final int attentionSessions;

  StudentStats({
    required this.totalSessions,
    required this.presentSessions,
    required this.absentSessions,
    required this.avgAttentionScore,
    required this.attentionSessions,
  });

  int get avgAttentionPercent => avgAttentionScore.round();
  String get attendanceLabel => '$presentSessions/$totalSessions';
  double get attendanceRate =>
      totalSessions > 0 ? presentSessions / totalSessions : 0.0;
}
