import 'package:cloud_firestore/cloud_firestore.dart';

import '../models/student_model.dart';

/// Lấy danh sách học sinh của một lớp, ghép cùng tọa độ ghế hiện tại
/// (row/column) đọc từ bảng trung gian `enrollments`.
///
/// Nguồn danh sách là `enrollments`, không phải `class_members`: chỉ những
/// học sinh ĐÃ có enrollment cho đúng lớp này mới xuất hiện trong stream.
/// Học sinh chưa có enrollment (mới thêm vào lớp, chưa từng lưu sơ đồ lần
/// nào) sẽ không xuất hiện cho tới khi có một enrollment được tạo ở nơi khác
/// (SeatingManagerRepository.saveSeats() cố tình KHÔNG tự tạo enrollment mới).
class StudentService {
  final FirebaseFirestore _db = FirebaseFirestore.instance;

  // Giới hạn số phần tử tối đa của một truy vấn `whereIn` trên Firestore.
  static const int _whereInChunkSize = 30;

  Stream<List<StudentModel>> getStudentsStream(String classId) {
    return _db
        .collection('enrollments')
        .where('class_id', isEqualTo: classId)
        .snapshots()
        .asyncMap(_buildRoster);
  }

  Future<List<StudentModel>> _buildRoster(
    QuerySnapshot<Map<String, dynamic>> enrollmentSnap,
  ) async {
    if (enrollmentSnap.docs.isEmpty) return [];

    // Map tọa độ theo student_id: { studentId: {'row': x, 'col': y} }.
    // Dùng Map (key là student_id) để tự loại trùng nếu lỡ có 2 enrollment
    // rác cùng student_id cho cùng 1 lớp.
    final Map<String, Map<String, int>> seatPositions = {};

    for (final doc in enrollmentSnap.docs) {
      final data = doc.data();
      final studentId = data['student_id'];

      // Ép kiểu an toàn: bỏ qua nếu field bị lưu sai kiểu thay vì crash.
      if (studentId is! String || studentId.isEmpty) continue;

      seatPositions[studentId] = {
        'row': (data['row'] as num?)?.toInt() ?? 0,
        'col': (data['column'] as num?)?.toInt() ?? 0,
      };
    }

    if (seatPositions.isEmpty) return [];

    final studentIds = seatPositions.keys.toList();

    // Chia thành các chunk tối đa 30 phần tử (giới hạn whereIn của Firestore).
    final chunks = <List<String>>[
      for (var i = 0; i < studentIds.length; i += _whereInChunkSize)
        studentIds.sublist(
          i,
          i + _whereInChunkSize > studentIds.length
              ? studentIds.length
              : i + _whereInChunkSize,
        ),
    ];

    // Chạy các chunk SONG SONG (Future.wait) thay vì tuần tự -> giảm độ trễ
    // đáng kể khi lớp có nhiều hơn 30 học sinh (nhiều hơn 1 chunk).
    final chunkResults = await Future.wait(
      chunks.map(
        (chunk) => _db
            .collection('students')
            .where(FieldPath.documentId, whereIn: chunk)
            .get(),
      ),
    );

    final studentList = <StudentModel>[];
    for (final studentsSnap in chunkResults) {
      for (final doc in studentsSnap.docs) {
        final sData = doc.data();
        final pos = seatPositions[doc.id];
        if (pos == null) continue; // an toàn, lý thuyết không nên xảy ra

        final fullName = (sData['student_name'] ??
                sData['full_name'] ??
                sData['name'] ??
                'Học sinh')
            .toString();

        // Tự lấy từ cuối cùng làm tên ngắn nếu không có trường short_name.
        final shortName = sData['short_name'] ??
            (fullName.trim().isNotEmpty
                ? fullName.trim().split(' ').last
                : 'HS');

        studentList.add(
          StudentModel(
            id: doc.id,
            name: fullName,
            short: shortName,
            row: pos['row'] ?? 0,
            column: pos['col'] ?? 0,
          ),
        );
      }
    }

    // Sắp xếp ổn định theo tên -> danh sách (đặc biệt là picker chọn học
    // sinh) không bị đảo lộn thứ tự giữa các lần Firestore emit lại.
    studentList.sort((a, b) {
      String firstNameA = a.name.trim().split(' ').last;
      String firstNameB = b.name.trim().split(' ').last;
      return firstNameA.compareTo(firstNameB);
    });
    return studentList;
  }
}
