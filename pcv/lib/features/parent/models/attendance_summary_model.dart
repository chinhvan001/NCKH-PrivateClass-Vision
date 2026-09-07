/// Model tổng hợp thống kê điểm danh — tính toán từ collection sessions.
class AttendanceSummaryModel {
  final int totalSessions;
  final int presentSessions;
  final int absentSessions;
  final int lateSessions;
  final int excusedSessions;
  final int avgFocusPercent;

  const AttendanceSummaryModel({
    required this.totalSessions,
    required this.presentSessions,
    required this.absentSessions,
    required this.lateSessions,
    required this.excusedSessions,
    required this.avgFocusPercent,
  });

  /// Tỉ lệ có mặt (%) — dùng cho progress circle
  double get attendanceRate =>
      totalSessions > 0 ? presentSessions / totalSessions : 0.0;

  /// Chuỗi hiển thị điểm danh: "9/10"
  String get attendanceLabel => '$presentSessions/$totalSessions';
}
