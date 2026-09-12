import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/subject_focus_model.dart';

class SubjectFocusService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách tập trung theo môn của học sinh, lọc theo kỳ.
  /// [period]: 'today' | 'week' | 'month'
  Future<List<SubjectFocusModel>> getSubjectFocus({
    required String studentId,
    required String period,
  }) async {
    try {
      final snapshot = await _db
          .collection('subject_focus')
          .where('studentId', isEqualTo: studentId)
          .where('period', isEqualTo: period)
          .orderBy('percent', descending: true)
          .get();

      return snapshot.docs.map(SubjectFocusModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải dữ liệu tập trung theo môn: ${e.message}');
    }
  }

  /// Stream realtime tập trung theo môn.
  Stream<List<SubjectFocusModel>> watchSubjectFocus({
    required String studentId,
    required String period,
  }) {
    return _db
        .collection('subject_focus')
        .where('studentId', isEqualTo: studentId)
        .where('period', isEqualTo: period)
        .orderBy('percent', descending: true)
        .snapshots()
        .map((snap) =>
            snap.docs.map(SubjectFocusModel.fromFirestore).toList());
  }

  // ── Seed data (dùng 1 lần để tạo dữ liệu mẫu trên Firestore) ──────────────
  Future<void> seedSampleData(String studentId) async {
    final batch = _db.batch();

    final subjects = ['Toán', 'Tiếng Việt', 'Tiếng Anh', 'Khoa học', 'Lịch sử & Địa lí'];
    final periods = ['today', 'week', 'month'];

    // Dữ liệu mẫu theo từng kỳ
    final Map<String, List<int>> percents = {
      'today': [90, 80, 70, 85, 65],
      'week': [85, 75, 70, 80, 65],
      'month': [82, 73, 68, 78, 63],
    };

    for (final period in periods) {
      for (int i = 0; i < subjects.length; i++) {
        final ref = _db.collection('subject_focus').doc();
        batch.set(ref, {
          'studentId': studentId,
          'subject': subjects[i],
          'percent': percents[period]![i],
          'period': period,
        });
      }
    }

    await batch.commit();
  }
}
