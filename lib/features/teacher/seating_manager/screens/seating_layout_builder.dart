import 'seat_models.dart';

/// Kết quả dựng sơ đồ từ `classes2.seat_map`.
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

  /// Học sinh có tọa độ nằm NGOÀI ma trận hiện tại (row_count/column_count).
  final List<String> outOfRangeIds;

  /// Học sinh trùng ô với người khác (người đến sau bị loại khỏi sơ đồ,
  /// coi như chưa xếp chỗ để giáo viên xếp lại).
  final List<String> conflictIds;
}

/// Dựng sơ đồ từ các phần tử seat_map. Hàm thuần, không phụ thuộc Firestore.
class SeatingLayoutBuilder {
  const SeatingLayoutBuilder._();

  static SeatingLayout fromEntries(
    List<SeatEntry> entries, {
    required int rows,
    required int cols,
  }) {
    final seats = List<String?>.filled(rows * cols, null);
    final outOfRange = <String>[];
    final conflicts = <String>[];
    var placed = 0;

    for (final e in entries) {
      if (e.row <= 0 || e.column <= 0 || e.row > rows || e.column > cols) {
        outOfRange.add(e.studentId);
        continue;
      }
      final index = (e.row - 1) * cols + (e.column - 1);
      if (seats[index] != null) {
        conflicts.add(e.studentId);
        continue;
      }
      seats[index] = e.studentId;
      placed++;
    }

    return SeatingLayout(
      seats: seats,
      placedCount: placed,
      outOfRangeIds: outOfRange,
      conflictIds: conflicts,
    );
  }

  /// "Chữ ký" của seat_map. Chỉ khi chữ ký đổi mới cần dựng lại sơ đồ.
  static String signature(List<SeatEntry> entries) {
    final parts = entries
        .map((e) => '${e.studentId}:${e.row}:${e.column}')
        .toList()
      ..sort();
    return parts.join('|');
  }

  /// Chữ ký mà seat_map SẼ có sau khi lưu [draftSeats] thành công. Dùng ngay
  /// sau khi lưu để màn hình không nháy về dữ liệu cũ trong lúc chờ Firestore
  /// phát lại snapshot mới.
  static String signatureAfterSave(List<String?> draftSeats, int cols) {
    final parts = <String>[
      for (var i = 0; i < draftSeats.length; i++)
        if (draftSeats[i] != null)
          '${draftSeats[i]}:${(i ~/ cols) + 1}:${(i % cols) + 1}',
    ]..sort();
    return parts.join('|');
  }
}
