import '../../../../../core/models/student_model.dart';

/// Ném ra khi cố lưu sơ đồ nhưng vẫn còn học sinh chưa có chỗ ngồi.
/// Dùng ở tầng repository như lớp chặn cuối (UI đã vô hiệu hóa nút Lưu,
/// nhưng repository vẫn phải tự bảo vệ để không ghi dữ liệu thiếu).
class IncompleteSeatingException implements Exception {
  const IncompleteSeatingException(this.missingStudentIds);

  final List<String> missingStudentIds;

  int get missingCount => missingStudentIds.length;

  @override
  String toString() =>
      'Còn $missingCount học sinh chưa được xếp chỗ, không thể lưu sơ đồ.';
}

/// Kết quả kiểm tra điều kiện được phép lưu sơ đồ.
class SeatingValidationResult {
  const SeatingValidationResult({
    required this.canSave,
    required this.message,
    required this.missingStudents,
    required this.totalStudents,
    required this.assignedCount,
  });

  /// true khi mọi học sinh trong lớp đều đã có chỗ.
  final bool canSave;

  /// Thông báo hiển thị cho giáo viên (rỗng khi [canSave] = true).
  final String message;

  /// Các học sinh chưa có chỗ (dùng để tô nổi hoặc liệt kê trên UI).
  final List<StudentModel> missingStudents;

  final int totalStudents;
  final int assignedCount;

  int get missingCount => missingStudents.length;
}

/// Quy tắc: PHẢI xếp chỗ cho TẤT CẢ học sinh của lớp thì mới được lưu sơ đồ.
///
/// Hàm thuần (không phụ thuộc Flutter/Firestore) nên dễ kiểm thử.
class SeatingSaveValidator {
  const SeatingSaveValidator._();

  /// Kiểm tra [draftSeats] (danh sách id học sinh theo từng ô, null = ô trống)
  /// so với [roster] (toàn bộ học sinh có enrollment của lớp).
  static SeatingValidationResult validate({
    required List<String?> draftSeats,
    required List<StudentModel> roster,
  }) {
    if (roster.isEmpty) {
      return const SeatingValidationResult(
        canSave: false,
        message: 'Lớp chưa có học sinh nào để xếp chỗ.',
        missingStudents: [],
        totalStudents: 0,
        assignedCount: 0,
      );
    }

    // Số ghế không đủ cho cả lớp -> không thể xếp hết, báo rõ nguyên nhân.
    if (draftSeats.length < roster.length) {
      return SeatingValidationResult(
        canSave: false,
        message: 'Phòng chỉ có ${draftSeats.length} chỗ nhưng lớp có '
            '${roster.length} học sinh. Không đủ chỗ để xếp hết.',
        missingStudents: const [],
        totalStudents: roster.length,
        assignedCount: draftSeats.where((s) => s != null).length,
      );
    }

    // Chỉ tính các id thật sự thuộc roster (bỏ qua id lạ nếu có).
    final rosterIds = roster.map((s) => s.id).toSet();
    final seatedIds = <String>{
      for (final id in draftSeats)
        if (id != null && rosterIds.contains(id)) id,
    };

    final missing =
        roster.where((s) => !seatedIds.contains(s.id)).toList(growable: false);

    if (missing.isEmpty) {
      return SeatingValidationResult(
        canSave: true,
        message: '',
        missingStudents: const [],
        totalStudents: roster.length,
        assignedCount: seatedIds.length,
      );
    }

    return SeatingValidationResult(
      canSave: false,
      message: 'Còn ${missing.length} học sinh chưa xếp chỗ. '
          'Hãy xếp chỗ cho tất cả học sinh trước khi lưu.',
      missingStudents: missing,
      totalStudents: roster.length,
      assignedCount: seatedIds.length,
    );
  }

  /// Kiểm tra theo danh sách id bắt buộc (dùng trong repository, nơi chỉ có
  /// các student_id của enrollments mà không có StudentModel).
  /// Ném [IncompleteSeatingException] nếu còn id chưa có chỗ.
  static void ensureAllAssigned({
    required List<String?> draftSeats,
    required Iterable<String> requiredStudentIds,
  }) {
    final seatedIds = <String>{
      for (final id in draftSeats)
        if (id != null) id,
    };
    final missing =
        requiredStudentIds.where((id) => !seatedIds.contains(id)).toList();
    if (missing.isNotEmpty) {
      throw IncompleteSeatingException(missing);
    }
  }
}
