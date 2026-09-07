import 'package:cloud_firestore/cloud_firestore.dart';
import '../models/notification_model.dart';

class NotificationService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  /// Lấy danh sách thông báo của một học sinh.
  /// Sắp xếp theo mới nhất lên đầu.
  Future<List<NotificationModel>> getNotificationsByStudent(
      String studentId) async {
    try {
      final snapshot = await _db
          .collection('notifications')
          .where('studentId', isEqualTo: studentId)
          .orderBy('createdAt', descending: true)
          .get();

      return snapshot.docs.map(NotificationModel.fromFirestore).toList();
    } on FirebaseException catch (e) {
      throw Exception('Lỗi tải thông báo: ${e.message}');
    }
  }

  /// Stream realtime — tự cập nhật khi có thông báo mới.
  Stream<List<NotificationModel>> watchNotificationsByStudent(
      String studentId) {
    return _db
        .collection('notifications')
        .where('studentId', isEqualTo: studentId)
        .orderBy('createdAt', descending: true)
        .snapshots()
        .map((snap) => snap.docs.map(NotificationModel.fromFirestore).toList());
  }

  /// Đếm số thông báo chưa đọc (dùng cho badge).
  Future<int> getUnreadCount(String studentId) async {
    try {
      final snapshot = await _db
          .collection('notifications')
          .where('studentId', isEqualTo: studentId)
          .where('isRead', isEqualTo: false)
          .count()
          .get();
      return snapshot.count ?? 0;
    } on FirebaseException catch (e) {
      throw Exception('Lỗi đếm thông báo: ${e.message}');
    }
  }

  // ── Seed data (dùng 1 lần để tạo dữ liệu mẫu trên Firestore) ──────────────
  Future<void> seedSampleData(String studentId) async {
    final batch = _db.batch();
    final samples = [
      {
        'type': 'teacher',
        'title': 'Thông báo mới từ giáo viên',
        'body':
            'Hôm nay Minh Anh có điểm kiểm tra môn Tiếng Anh xuất sắc trong buổi học Toán.',
        'time': '10 phút trước',
        'tab': 'Thông báo',
        'studentId': studentId,
        'isRead': false,
        'createdAt': Timestamp.fromDate(
            DateTime.now().subtract(const Duration(minutes: 10))),
      },
      {
        'type': 'reminder',
        'title': 'Nhắc nhở',
        'body': 'Hôm nay Minh Anh có tiết kiểm tra môn Tiếng Anh.',
        'time': '2 giờ trước',
        'tab': 'Nhắc nhở',
        'studentId': studentId,
        'isRead': false,
        'createdAt': Timestamp.fromDate(
            DateTime.now().subtract(const Duration(hours: 2))),
      },
      {
        'type': 'report',
        'title': 'Thông báo điểm danh',
        'body': 'Minh Anh vắng mặt buổi học hôm nay.',
        'time': 'Hôm qua',
        'tab': 'Thông báo',
        'studentId': studentId,
        'isRead': true,
        'createdAt': Timestamp.fromDate(
            DateTime.now().subtract(const Duration(days: 1))),
      },
      {
        'type': 'teacher',
        'title': 'Thông báo mới từ giáo viên',
        'body':
            'Minh Anh cần cải thiện mức độ tập trung ở tiết học tuần trước.',
        'time': '2 ngày trước',
        'tab': 'Thông báo',
        'studentId': studentId,
        'isRead': true,
        'createdAt': Timestamp.fromDate(
            DateTime.now().subtract(const Duration(days: 2))),
      },
    ];

    for (final data in samples) {
      final ref = _db.collection('notifications').doc();
      batch.set(ref, data);
    }
    await batch.commit();
  }
}
