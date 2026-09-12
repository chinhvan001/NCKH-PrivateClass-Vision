import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/schedule_model.dart';

class ScheduleService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy lịch học sắp tới (từ hiện tại trở đi), sắp xếp tăng dần.
  Future<List<ScheduleModel>> getUpcomingSchedules(String studentId) async {
    try {
      final now = Timestamp.now();
      final snapshot = await _db
          .collection('schedules')
          .where('studentId', isEqualTo: studentId)
          .where('scheduledAt', isGreaterThanOrEqualTo: now)
          .orderBy('scheduledAt', descending: false)
          .get();
      return snapshot.docs.map(ScheduleModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải lịch học: ${e.message}');
    }
  }

  /// Stream realtime lịch học sắp tới.
  Stream<List<ScheduleModel>> watchUpcomingSchedules(String studentId) {
    final now = Timestamp.now();
    return _db
        .collection('schedules')
        .where('studentId', isEqualTo: studentId)
        .where('scheduledAt', isGreaterThanOrEqualTo: now)
        .orderBy('scheduledAt', descending: false)
        .snapshots()
        .map((snap) => snap.docs.map(ScheduleModel.fromFirestore).toList());
  }

  /// Lấy tất cả lịch (bao gồm đã qua) để xem lịch sử.
  Future<List<ScheduleModel>> getAllSchedules(String studentId) async {
    try {
      final snapshot = await _db
          .collection('schedules')
          .where('studentId', isEqualTo: studentId)
          .orderBy('scheduledAt', descending: false)
          .get();
      return snapshot.docs.map(ScheduleModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải lịch học: ${e.message}');
    }
  }

  // ── Seed data ──────────────────────────────────────────────────────────────
  Future<void> seedSampleData(String studentId) async {
    final batch = _db.batch();
    final now = DateTime.now();
    final samples = [
      {
        'studentId': studentId,
        'date': 'Thứ 2, ${_formatDate(now.add(const Duration(days: 1)))}',
        'time': '08:00 - 09:30',
        'subject': 'Toán',
        'room': 'P.201',
        'teacherName': 'Nguyễn Văn A',
        'scheduledAt': Timestamp.fromDate(now.add(const Duration(days: 1))),
      },
      {
        'studentId': studentId,
        'date': 'Thứ 3, ${_formatDate(now.add(const Duration(days: 2)))}',
        'time': '10:00 - 11:30',
        'subject': 'Tiếng Việt',
        'room': 'P.101',
        'teacherName': 'Trần Thị B',
        'scheduledAt': Timestamp.fromDate(now.add(const Duration(days: 2))),
      },
      {
        'studentId': studentId,
        'date': 'Thứ 4, ${_formatDate(now.add(const Duration(days: 3)))}',
        'time': '08:00 - 09:30',
        'subject': 'Tiếng Anh',
        'room': 'P.203',
        'teacherName': 'Lê Văn C',
        'scheduledAt': Timestamp.fromDate(now.add(const Duration(days: 3))),
      },
      {
        'studentId': studentId,
        'date': 'Thứ 5, ${_formatDate(now.add(const Duration(days: 4)))}',
        'time': '13:30 - 15:00',
        'subject': 'Khoa học',
        'room': 'P.205',
        'teacherName': 'Phạm Thị D',
        'scheduledAt': Timestamp.fromDate(now.add(const Duration(days: 4))),
      },
      {
        'studentId': studentId,
        'date': 'Thứ 6, ${_formatDate(now.add(const Duration(days: 5)))}',
        'time': '08:00 - 09:30',
        'subject': 'Lịch sử & Địa lí',
        'room': 'P.102',
        'teacherName': 'Hoàng Văn E',
        'scheduledAt': Timestamp.fromDate(now.add(const Duration(days: 5))),
      },
    ];

    for (final data in samples) {
      final ref = _db.collection('schedules').doc();
      batch.set(ref, data);
    }
    await batch.commit();
  }

  String _formatDate(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
}
