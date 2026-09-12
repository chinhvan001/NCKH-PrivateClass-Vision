import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/attendance_detail_model.dart';

class AttendanceDetailService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách điểm danh chi tiết theo studentId.
  Future<List<AttendanceDetailModel>> getAttendanceDetails(
      String studentId) async {
    try {
      final snapshot = await _db
          .collection('attendance_details')
          .where('studentId', isEqualTo: studentId)
          .orderBy('date', descending: true)
          .get();
      return snapshot.docs
          .map(AttendanceDetailModel.fromFirestore)
          .toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải chi tiết điểm danh: ${e.message}');
    }
  }

  /// Lấy theo tháng cụ thể. VD: month = '05/2024'
  Future<List<AttendanceDetailModel>> getAttendanceByMonth(
      String studentId, String month) async {
    try {
      final snapshot = await _db
          .collection('attendance_details')
          .where('studentId', isEqualTo: studentId)
          .where('month', isEqualTo: month)
          .orderBy('date', descending: true)
          .get();
      return snapshot.docs
          .map(AttendanceDetailModel.fromFirestore)
          .toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải điểm danh theo tháng: ${e.message}');
    }
  }

  /// Thống kê nhanh theo tháng
  Future<Map<String, int>> getSummaryByMonth(
      String studentId, String month) async {
    final list = await getAttendanceByMonth(studentId, month);
    return {
      'total': list.length,
      'present': list.where((a) => a.type == 'present').length,
      'absent_excused': list.where((a) => a.type == 'absent_excused').length,
      'absent': list.where((a) => a.type == 'absent').length,
      'late': list.where((a) => a.type == 'late').length,
    };
  }

  // ── Seed data ──────────────────────────────────────────────────────────────
  Future<void> seedSampleData(String studentId) async {
    final batch = _db.batch();
    final samples = [
      {'date': '16/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '15/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '14/05/2024', 'type': 'late', 'reason': 'Kẹt xe', 'month': '05/2024'},
      {'date': '13/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '12/05/2024', 'type': 'absent_excused', 'reason': 'Ốm', 'month': '05/2024'},
      {'date': '10/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '09/05/2024', 'type': 'absent_excused', 'reason': 'Việc gia đình', 'month': '05/2024'},
      {'date': '08/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '07/05/2024', 'type': 'present', 'reason': '', 'month': '05/2024'},
      {'date': '06/05/2024', 'type': 'absent', 'reason': '', 'month': '05/2024'},
    ];
    for (final data in samples) {
      final ref = _db.collection('attendance_details').doc();
      batch.set(ref, {...data, 'studentId': studentId});
    }
    await batch.commit();
  }
}
