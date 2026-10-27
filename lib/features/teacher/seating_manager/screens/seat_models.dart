/// Một học sinh trong sơ đồ: id lấy từ `classes2.seat_map[*].student_id`,
/// tên lấy từ `students2/{id}.full_name`.
class SeatStudent {
  const SeatStudent({
    required this.id,
    required this.name,
    required this.short,
  });

  final String id;
  final String name;

  /// Tên ngắn hiển thị trong ô ghế (từ cuối của họ tên).
  final String short;

  factory SeatStudent.fromName(String id, String? fullName) {
    final name = (fullName == null || fullName.trim().isEmpty)
        ? id
        : fullName.trim();
    final parts = name.split(RegExp(r'\s+'));
    return SeatStudent(id: id, name: name, short: parts.last);
  }
}

/// Một phần tử của `classes2.seat_map` (đã bỏ qua ghế không có student_id).
class SeatEntry {
  const SeatEntry({
    required this.studentId,
    required this.row,
    required this.column,
  });

  final String studentId;
  final int row;
  final int column;
}

/// Mã ghế theo quy ước S01, S02, ... (đánh số theo hàng, từ 1).
String seatIdForIndex(int index) => 'S${(index + 1).toString().padLeft(2, '0')}';
