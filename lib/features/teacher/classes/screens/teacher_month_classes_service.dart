import 'package:cloud_firestore/cloud_firestore.dart';

/// Lấy các lớp mà giáo viên có buổi dạy (monitoring_sessions) trong một tháng.
///
/// Cách làm:
/// 1. Truy vấn `monitoring_sessions` theo giáo viên đăng nhập.
/// 2. Lọc các buổi có thời gian bắt đầu nằm trong tháng (lọc ở phía app nên
///    không cần tạo composite index trên Firestore).
/// 3. Gom các class_id (loại trùng) rồi đọc các document tương ứng trong `classes`.
class TeacherMonthClassesService {
  TeacherMonthClassesService({FirebaseFirestore? firestore})
      : _db = firestore ?? FirebaseFirestore.instance;

  final FirebaseFirestore _db;

  // ---- Tên field trong collection `monitoring_sessions` ----
  // Đối chiếu với Firestore Console và sửa tại đây nếu tên thật khác.
  static const String teacherField = 'teacher_id';
  static const String startField = 'start_time';
  static const String classField = 'class_id';

  // Giới hạn số phần tử của một truy vấn `whereIn` trên Firestore.
  static const int _whereInChunkSize = 30;

  /// Stream danh sách lớp (đã sắp theo tên) có buổi dạy của [teacherId]
  /// trong tháng của [month] (mặc định là tháng hiện tại).
  /// Tự cập nhật khi `monitoring_sessions` thay đổi.
  Stream<List<QueryDocumentSnapshot<Map<String, dynamic>>>> classesOfMonthStream(
    String teacherId, {
    DateTime? month,
  }) {
    final base = month ?? DateTime.now();
    final monthStart = DateTime(base.year, base.month);
    final nextMonthStart = DateTime(base.year, base.month + 1);

    return _db
        .collection('monitoring_sessions')
        .where(teacherField, isEqualTo: teacherId)
        .snapshots()
        .asyncMap((snap) async {
      final classIds = <String>{};

      for (final doc in snap.docs) {
        final data = doc.data();

        final start = _toDateTime(data[startField]);
        if (start == null) continue;
        if (start.isBefore(monthStart) || !start.isBefore(nextMonthStart)) {
          continue; // ngoài tháng đang xét
        }

        final classId = data[classField];
        if (classId is String && classId.trim().isNotEmpty) {
          classIds.add(classId.trim());
        }
      }

      return _fetchClasses(classIds.toList()..sort());
    });
  }

  Future<List<QueryDocumentSnapshot<Map<String, dynamic>>>> _fetchClasses(
    List<String> classIds,
  ) async {
    if (classIds.isEmpty) return [];

    final chunks = <List<String>>[
      for (var i = 0; i < classIds.length; i += _whereInChunkSize)
        classIds.sublist(
          i,
          i + _whereInChunkSize > classIds.length
              ? classIds.length
              : i + _whereInChunkSize,
        ),
    ];

    final results = await Future.wait(
      chunks.map(
        (chunk) => _db
            .collection('classes')
            .where(FieldPath.documentId, whereIn: chunk)
            .get(),
      ),
    );

    final docs = [for (final r in results) ...r.docs];
    docs.sort((a, b) {
      final nameA = (a.data()['class_name'] ?? '').toString();
      final nameB = (b.data()['class_name'] ?? '').toString();
      return nameA.compareTo(nameB);
    });
    return docs;
  }

  /// Chấp nhận Timestamp, DateTime, chuỗi ISO-8601 hoặc số mili-giây.
  static DateTime? _toDateTime(dynamic value) {
    if (value is Timestamp) return value.toDate();
    if (value is DateTime) return value;
    if (value is String) return DateTime.tryParse(value)?.toLocal();
    if (value is num) {
      return DateTime.fromMillisecondsSinceEpoch(value.toInt());
    }
    return null;
  }
}
