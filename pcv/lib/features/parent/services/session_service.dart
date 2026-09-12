import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/session_model.dart';
import '../models/attendance_summary_model.dart';

class SessionService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách buổi học của một học sinh theo studentId.
  /// Sắp xếp theo ngày mới nhất lên đầu.
  Future<List<SessionModel>> getSessionsByStudent(String studentId) async {
    try {
      final snapshot = await _db
          .collection('sessions')
          .where('studentId', isEqualTo: studentId)
          .orderBy('createdAt', descending: true)
          .get();

      return snapshot.docs.map(SessionModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải buổi học: ${e.message}');
    }
  }

  /// Stream realtime — dùng nếu muốn tự cập nhật khi data thay đổi.
  Stream<List<SessionModel>> watchSessionsByStudent(String studentId) {
    return _db
        .collection('sessions')
        .where('studentId', isEqualTo: studentId)
        .orderBy('createdAt', descending: true)
        .snapshots()
        .map((snap) => snap.docs.map(SessionModel.fromFirestore).toList());
  }

  /// Lấy chi tiết 1 buổi học theo id.
  Future<SessionModel?> getSessionById(String sessionId) async {
    try {
      final doc = await _db.collection('sessions').doc(sessionId).get();
      if (!doc.exists) return null;
      return SessionModel.fromFirestore(doc);
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải chi tiết buổi học: ${e.message}');
    }
  }

  /// Thống kê điểm danh của học sinh (tổng hợp từ collection sessions).
  Future<AttendanceSummaryModel> getAttendanceSummary(String studentId) async {
    try {
      final snapshot = await _db
          .collection('sessions')
          .where('studentId', isEqualTo: studentId)
          .get();

      final sessions = snapshot.docs.map(SessionModel.fromFirestore).toList();

      final total = sessions.length;
      final present = sessions.where((s) => s.status == 'present').length;
      final absent = sessions.where((s) => s.status == 'absent').length;
      final late = sessions.where((s) => s.status == 'late').length;
      final excused = sessions.where((s) => s.status == 'excused').length;

      final avgFocus = total > 0
          ? (sessions.map((s) => s.percent).reduce((a, b) => a + b) / total)
              .round()
          : 0;

      return AttendanceSummaryModel(
        totalSessions: total,
        presentSessions: present,
        absentSessions: absent,
        lateSessions: late,
        excusedSessions: excused,
        avgFocusPercent: avgFocus,
      );
    } on FirebaseException catch (e) {
      throw Exception('Lỗi thống kê điểm danh: ${e.message}');
    }
  }

  // ── Seed data (dùng 1 lần để tạo dữ liệu mẫu trên Firestore) ──────────────
  Future<void> seedSampleData(String studentId) async {
    final batch = _db.batch();
    final samples = [
      {
        'date': 'Thứ 6, 16/05/2024',
        'time': '08:00 - 09:30',
        'subject': 'Toán',
        'room': 'P.201',
        'percent': 85,
        'status': 'present',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 16)),
      },
      {
        'date': 'Thứ 5, 15/05/2024',
        'time': '08:00 - 09:30',
        'subject': 'Toán',
        'room': 'P.201',
        'percent': 85,
        'status': 'present',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 15)),
      },
      {
        'date': 'Thứ 4, 14/05/2024',
        'time': '10:00 - 11:30',
        'subject': 'Tiếng Việt',
        'room': 'P.101',
        'percent': 75,
        'status': 'present',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 14)),
      },
      {
        'date': 'Thứ 3, 13/05/2024',
        'time': '10:00 - 11:30',
        'subject': 'Tiếng Anh',
        'room': 'P.203',
        'percent': 60,
        'status': 'late',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 13)),
      },
      {
        'date': 'Thứ 2, 12/05/2024',
        'time': '10:00 - 11:30',
        'subject': 'Khoa học',
        'room': 'P.205',
        'percent': 80,
        'status': 'absent',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 12)),
      },
      {
        'date': 'Thứ 6, 10/05/2024',
        'time': '08:00 - 09:30',
        'subject': 'Lịch sử',
        'room': 'P.102',
        'percent': 70,
        'status': 'present',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 10)),
      },
      {
        'date': 'Thứ 5, 09/05/2024',
        'time': '11:00 - 12:30',
        'subject': 'Địa lý',
        'room': 'P.102',
        'percent': 70,
        'status': 'present',
        'studentId': studentId,
        'createdAt': Timestamp.fromDate(DateTime(2024, 5, 9)),
      },
    ];

    for (final data in samples) {
      final ref = _db.collection('sessions').doc();
      batch.set(ref, data);
    }
    await batch.commit();
  }
}
