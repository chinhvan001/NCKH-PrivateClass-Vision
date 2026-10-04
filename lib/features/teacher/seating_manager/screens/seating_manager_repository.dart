import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter_privateclass_vision/features/teacher/seating_manager/screens/seating_save_validator.dart';

import '../../../../core/services/student_service.dart';
import '../../../../../core/models/student_model.dart';

/// Ném ra khi giáo viên hiện tại không phải chủ sở hữu (`teacher_id`) của
/// lớp học đang mở. Đây là lớp bảo vệ Ở TẦNG ỨNG DỤNG (UX) — không thay thế
/// cho Firestore Security Rules. Rules trên collection `classes`/`enrollments`/
/// `students` vẫn PHẢI tự kiểm tra `request.auth.uid == resource.data.teacher_id`
/// (hoặc tương đương) để chặn truy cập trực tiếp ngoài app.
class ClassAccessDeniedException implements Exception {
  const ClassAccessDeniedException(this.classId);

  final String classId;

  @override
  String toString() => 'Không có quyền truy cập lớp học "$classId".';
}
/// Ném ra khi giáo viên không là `teacher_id` của lớp nào trong `classes`.
class NoClassFoundException implements Exception {
  const NoClassFoundException();

  @override
  String toString() => 'Không tìm thấy lớp học nào của giáo viên này.';
}
/// Thông tin lớp học + phòng học, dùng để dựng header và kích thước ma trận.
///
/// [rows]/[cols] lấy từ `classrooms/{classroomId}.row_number/column_number`
/// (kích thước THẬT của phòng), không còn cố định 5x8.
class ClassInfo {
  const ClassInfo({
    required this.className,
    required this.roomName,
    required this.rows,
    required this.cols,
    required this.classSize,
  });

  final String className;
  final String roomName;
  final int rows;
  final int cols;

  /// Sĩ số khai báo của lớp (`classes.class_size`) - KHÔNG PHẢI số học sinh
  /// đang có enrollment. Dùng để đối chiếu: nếu số học sinh có enrollment
  /// (roster) ít hơn classSize, tức có học sinh thuộc lớp nhưng chưa được
  /// ghi nhận enrollment (bug ở luồng thêm học sinh vào lớp, không thuộc
  /// phạm vi màn hình sơ đồ chỗ ngồi) - xem SeatingCompletion.missingEnrollment.
  ///
  /// 0 nghĩa là "không biết sĩ số" (field trống/thiếu) -> bỏ qua đối chiếu
  /// này, không coi là thiếu enrollment.
  final int classSize;

  static const fallback = ClassInfo(
    className: 'Lớp học',
    roomName: 'Chưa cập nhật',
    rows: 5,
    cols: 8,
    classSize: 0,
  );
}

/// Gom toàn bộ thao tác Firestore của màn hình Sơ đồ chỗ ngồi vào một nơi.
/// UI (SeatingManagerScreen) không gọi Firestore trực tiếp, chỉ dùng
/// các stream/method của repository này.
class SeatingManagerRepository {
  SeatingManagerRepository({StudentService? studentService})
    : _studentService = studentService ?? StudentService();

  final StudentService _studentService;
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;

  /// Stream thông tin lớp học:
  /// - Tên lớp (`class_name`) lấy trực tiếp từ document `classes/{classId}`.
  /// - `classroom_id` trong document lớp là con trỏ tới `classrooms/{classroomId}`,
  ///   từ đó lấy tên phòng thật (`classroom_name`) và kích thước ma trận
  ///   (`row_number`, `column_number`).
  /// - [teacherId] PHẢI khớp với `classData['teacher_id']`, nếu không stream
  ///   sẽ báo lỗi [ClassAccessDeniedException] thay vì trả về dữ liệu.
  Stream<ClassInfo> classInfoStream(
    String classId, {
    required String teacherId,
  }) {
    return _firestore
        .collection('classes')
        .doc(classId)
        .snapshots()
        .asyncMap((doc) => _resolveClassInfo(doc, teacherId));
  }

  Future<String> findClassIdByTeacher(String teacherId) async {
    final snap = await _firestore
        .collection('classes')
        .where('teacher_id', isEqualTo: teacherId)
        .get();

    if (snap.docs.isEmpty) throw const NoClassFoundException();

    final ids = snap.docs.map((d) => d.id).toList()..sort();
    return ids.first;
    }

  Future<ClassInfo> _resolveClassInfo(
    DocumentSnapshot<Map<String, dynamic>> classDoc,
    String teacherId,
  ) async {
    final classData = classDoc.data();
    if (!classDoc.exists || classData == null) return ClassInfo.fallback;

    // Chỉ giáo viên đứng lớp (teacher_id khớp) mới được xem/sửa sơ đồ lớp này.
    // Thiếu field teacher_id -> mặc định TỪ CHỐI (an toàn hơn là mặc định cho phép).
    final classTeacherId = classData['teacher_id'] as String?;
    if (classTeacherId == null || classTeacherId != teacherId) {
      throw ClassAccessDeniedException(classDoc.id);
    }

    final className = classData['class_name'] ?? 'Lớp học';
    final classroomId = classData['classroom_id'] as String?;
    // Sĩ số khai báo của lớp - dùng để đối chiếu với số enrollment thực tế
    // (xem giải thích ở ClassInfo.classSize). 0 nếu field thiếu/sai kiểu.
    final classSize = _asInt(classData['class_size']) ?? 0;

    // Lớp chưa được gán phòng học -> dùng kích thước mặc định.
    if (classroomId == null || classroomId.isEmpty) {
      return ClassInfo(
        className: className,
        roomName: 'Chưa cập nhật',
        rows: ClassInfo.fallback.rows,
        cols: ClassInfo.fallback.cols,
        classSize: classSize,
      );
    }

    // Truy vấn sang collection `classrooms` để lấy tên phòng + ma trận thật.
    final classroomDoc = await _firestore
        .collection('classrooms')
        .doc(classroomId)
        .get();
    final classroomData = classroomDoc.data();

    if (!classroomDoc.exists || classroomData == null) {
      return ClassInfo(
        className: className,
        roomName: classroomId,
        rows: ClassInfo.fallback.rows,
        cols: ClassInfo.fallback.cols,
        classSize: classSize,
      );
    }

    return ClassInfo(
      className: className,
      roomName: classroomData['classroom_name'] ?? classroomId,
      rows: _asInt(classroomData['row_number']) ?? ClassInfo.fallback.rows,
      cols: _asInt(classroomData['column_number']) ?? ClassInfo.fallback.cols,
      classSize: classSize,
    );
  }

  int? _asInt(dynamic value) {
    if (value is int) return value;
    if (value is num) return value.toInt();
    return null;
  }

  /// Stream danh sách học sinh thuộc lớp (ủy quyền cho StudentService).
  /// Mỗi StudentModel mang theo tọa độ hiện tại lấy từ enrollment:
  /// - Chưa xếp chỗ -> row = 0, column = 0.
  /// - Đã xếp chỗ    -> row = x, column = y.
  ///
  /// LƯU Ý: hàm này KHÔNG tự kiểm tra teacher_id. UI (SeatingManagerScreen)
  /// chỉ được subscribe stream này SAU KHI `classInfoStream` đã xác nhận
  /// giáo viên hiện tại sở hữu lớp (không ném ClassAccessDeniedException).
  
  Stream<List<StudentModel>> studentsStream(String classId) {
    return _studentService.getStudentsStream(classId);
  }

  /// Lưu sơ đồ chỗ ngồi vào bảng `enrollments`:
  /// - Học sinh đã có enrollment và đang có mặt trên sơ đồ -> cập nhật row/column.
  /// - Học sinh đã có enrollment nhưng không còn trên sơ đồ -> reset về (0, 0).
  /// - KHÔNG tạo enrollment mới cho học sinh chưa có bản ghi trong lớp
  ///   (những học sinh này bị bỏ qua, không lưu được vị trí cho tới khi
  ///   có enrollment hợp lệ được tạo bằng luồng khác).
  ///
  /// LƯU Ý: cũng như studentsStream, hàm này không tự kiểm tra teacher_id;
  /// chỉ nên được gọi từ màn hình đã qua bước xác thực ở classInfoStream.
  Future<void> saveSeats({
    required String classId,
    required List<String?> draftSeats,
    required int cols,
    required Iterable<String> requiredStudentIds,
  }) async {
    SeatingSaveValidator.ensureAllAssigned(
      draftSeats: draftSeats,
      requiredStudentIds: requiredStudentIds,
    );
    final enrollmentsRef = _firestore.collection('enrollments');
    final querySnap = await enrollmentsRef
        .where('class_id', isEqualTo: classId)
        .get();

    final existingByStudent = <String, DocumentReference>{};
    for (final doc in querySnap.docs) {
      final studentId = doc.data()['student_id'] as String?;
      if (studentId != null) existingByStudent[studentId] = doc.reference;
    }
    final batch = _firestore.batch();
    final assignedStudentIds = <String>{};

    for (int index = 0; index < draftSeats.length; index++) {
      final studentId = draftSeats[index];
      if (studentId == null) continue;

      final existingRef = existingByStudent[studentId];
      if (existingRef == null) {
        // Không có enrollment sẵn -> không tạo mới, bỏ qua học sinh này.
        continue;
      }

      assignedStudentIds.add(studentId);
      final newRow = (index ~/ cols) + 1;
      final newCol = (index % cols) + 1;
      batch.update(existingRef, {'row': newRow, 'column': newCol});
    }

    // Học sinh có enrollment nhưng không còn trên sơ đồ -> reset (0, 0).
    for (final entry in existingByStudent.entries) {
      if (!assignedStudentIds.contains(entry.key)) {
        batch.update(entry.value, {'row': 0, 'column': 0});
      }
    }

    await batch.commit();
  }
}
