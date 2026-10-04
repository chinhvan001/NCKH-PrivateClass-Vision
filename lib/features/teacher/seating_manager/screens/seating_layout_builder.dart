import '../../../../../core/models/student_model.dart';

/// Kết quả dựng sơ đồ từ tọa độ (row/column) đã lưu trong enrollments.
class SeatingLayout {
  const SeatingLayout({
    required this.seats,
    required this.placedCount,
    required this.outOfRangeIds,
    required this.conflictIds,
  });

  /// Danh sách id học sinh theo từng ô (null = ô trống), độ dài = rows * cols.
  final List<String?> seats;

  /// Số học sinh đã được đặt lên sơ đồ.
  final int placedCount;

  /// Học sinh có tọa độ > 0 nhưng nằm NGOÀI ma trận phòng hiện tại.
  final List<String> outOfRangeIds;

  /// Học sinh trùng ô với người khác (người đến sau bị loại khỏi sơ đồ,
  /// coi như chưa xếp chỗ để giáo viên xếp lại).
  final List<String> conflictIds;
}

/// Dựng sơ đồ từ danh sách học sinh. Hàm thuần, không phụ thuộc Firestore.
class SeatingLayoutBuilder {
  const SeatingLayoutBuilder._();

  static SeatingLayout fromRoster(
    List<StudentModel> roster, {
    required int rows,
    required int cols,
  }) {
    final seats = List<String?>.filled(rows * cols, null);
    final outOfRange = <String>[];
    final conflicts = <String>[];
    var placed = 0;

    for (final student in roster) {
      final r = student.row ?? 0;
      final c = student.column ?? 0;
      if (r <= 0 || c <= 0) continue; // chưa xếp chỗ

      if (r > rows || c > cols) {
        outOfRange.add(student.id);
        continue;
      }

      final index = (r - 1) * cols + (c - 1);
      if (seats[index] != null) {
        conflicts.add(student.id);
        continue;
      }
      seats[index] = student.id;
      placed++;
    }

    return SeatingLayout(
      seats: seats,
      placedCount: placed,
      outOfRangeIds: outOfRange,
      conflictIds: conflicts,
    );
  }

  /// "Chữ ký" của dữ liệu tọa độ trong roster. Chỉ khi chữ ký đổi mới cần
  /// dựng lại sơ đồ, nhờ vậy không ghi đè sơ đồ một cách không cần thiết.
  static String signature(List<StudentModel> roster) {
    final parts = roster
        .map((s) => '${s.id}:${s.row ?? 0}:${s.column ?? 0}')
        .toList()
      ..sort();
    return parts.join('|');
  }

  /// Chữ ký mà roster SẼ có sau khi lưu [draftSeats] thành công.
  /// Dùng ngay sau khi lưu để màn hình không bị nháy về dữ liệu cũ trong lúc
  /// chờ Firestore phát lại snapshot mới.
  static String signatureAfterSave(
    List<StudentModel> roster,
    List<String?> draftSeats,
    int cols,
  ) {
    final indexById = <String, int>{
      for (var i = 0; i < draftSeats.length; i++)
        if (draftSeats[i] != null) draftSeats[i]!: i,
    };

    final parts = roster.map((s) {
      final index = indexById[s.id];
      final row = index == null ? 0 : (index ~/ cols) + 1;
      final col = index == null ? 0 : (index % cols) + 1;
      return '${s.id}:$row:$col';
    }).toList()
      ..sort();
    return parts.join('|');
  }
}
