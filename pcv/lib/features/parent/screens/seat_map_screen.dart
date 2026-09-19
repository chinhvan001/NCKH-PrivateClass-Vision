import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../models/supervised_student_model.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';

class SeatMapScreen extends StatefulWidget {
  const SeatMapScreen({super.key});

  @override
  State<SeatMapScreen> createState() => _SeatMapScreenState();
}

class _SeatMapScreenState extends State<SeatMapScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_SeatMapData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_SeatMapData> _loadData() async {
    final students = await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) return _SeatMapData(myRow: 0, myCol: 0, allSeats: []);

    final student = students.first;
    // Lấy tất cả supervised_students trong buổi học gần nhất
    final supervised =
        await _monitoringService.getSupervisedDataByStudent(student.id);
    if (supervised.isEmpty) {
      return _SeatMapData(myRow: 0, myCol: 0, allSeats: []);
    }

    // Lấy buổi mới nhất
    final latest = supervised.last;
    final myRow = latest.row;
    final myCol = latest.column;

    // Lấy tất cả học sinh trong cùng buổi đó
    List<_SeatInfo> allSeats = [];
    if (latest.monitoringSessionId.isNotEmpty) {
      final snapshot = await FirebaseFirestore.instance
          .collection('supervised_students')
          .where('monitoring_session_id',
              isEqualTo: latest.monitoringSessionId)
          .get();
      for (final doc in snapshot.docs) {
        final s = SupervisedStudentModel.fromFirestore(doc);
        allSeats.add(_SeatInfo(
          row: s.row,
          col: s.column,
          isPresent: s.isPresent,
          isAttention: s.isAttention,
          attentionScore: s.attentionScore,
          isMe: s.studentId == student.id,
        ));
      }
    }

    return _SeatMapData(myRow: myRow, myCol: myCol, allSeats: allSeats);
  }

  void _reload() => setState(() => _dataFuture = _loadData());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Navigator.canPop(context)
            ? IconButton(
                icon: const Icon(Icons.arrow_back_ios,
                    color: AppColors.textPrimary, size: 20),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: const Text('Sơ đồ chỗ ngồi', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_SeatMapData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: AppColors.primary));
          }
          if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.cloud_off_rounded,
                      size: 48, color: AppColors.red),
                  const SizedBox(height: 12),
                  Text(
                    snapshot.error.toString().replaceFirst('Exception: ', ''),
                    style: AppTextStyles.caption,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _reload,
                    icon: const Icon(Icons.refresh_rounded, size: 18),
                    label: const Text('Thử lại'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10)),
                    ),
                  ),
                ],
              ),
            );
          }

          final data = snapshot.data!;

          if (data.allSeats.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: const BoxDecoration(
                        color: AppColors.accentLight, shape: BoxShape.circle),
                    child: const Icon(Icons.chair_rounded,
                        size: 44, color: AppColors.primary),
                  ),
                  const SizedBox(height: 14),
                  const Text('Chưa có dữ liệu', style: AppTextStyles.heading3),
                  const SizedBox(height: 6),
                  const Text('Chưa có buổi học nào được ghi nhận',
                      style: AppTextStyles.caption),
                ],
              ),
            );
          }

          // Tính max row + col
          final maxRow =
              data.allSeats.map((s) => s.row).reduce((a, b) => a > b ? a : b);
          final maxCol =
              data.allSeats.map((s) => s.col).reduce((a, b) => a > b ? a : b);

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Legend ──────────────────────────────────────────
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: const [
                      BoxShadow(
                          color: Color(0x0F000000),
                          blurRadius: 6,
                          offset: Offset(0, 2))
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Chú thích', style: AppTextStyles.heading3),
                      const SizedBox(height: 10),
                      Wrap(
                        spacing: 16,
                        runSpacing: 8,
                        children: [
                          _LegendItem(
                              color: AppColors.primary, label: 'Vị trí của con'),
                          _LegendItem(
                              color: AppColors.green, label: 'Tập trung tốt'),
                          _LegendItem(
                              color: AppColors.orange, label: 'Tập trung TB'),
                          _LegendItem(color: AppColors.red, label: 'Mất tập trung'),
                          _LegendItem(
                              color: AppColors.divider, label: 'Vắng mặt'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // ── Bảng ────────────────────────────────────────────
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    boxShadow: const [
                      BoxShadow(
                          color: Color(0x0F000000),
                          blurRadius: 6,
                          offset: Offset(0, 2))
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Bảng (bảng đen/giáo viên)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          color: AppColors.textPrimary,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Center(
                          child: Text('BẢNG',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13)),
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Sơ đồ chỗ ngồi
                      for (int r = 1; r <= maxRow; r++) ...[
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            for (int c = 1; c <= maxCol; c++) ...[
                              _buildSeat(data.allSeats, r, c),
                              if (c < maxCol) const SizedBox(width: 8),
                            ],
                          ],
                        ),
                        if (r < maxRow) const SizedBox(height: 8),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // ── My seat info ─────────────────────────────────────
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.accentLight,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.primary, width: 1.5),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.primary,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.chair_rounded,
                            color: Colors.white, size: 22),
                      ),
                      const SizedBox(width: 12),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('Vị trí của con',
                              style: AppTextStyles.heading3),
                          const SizedBox(height: 2),
                          Text(
                            'Hàng ${data.myRow} · Cột ${data.myCol}',
                            style: AppTextStyles.caption
                                .copyWith(color: AppColors.primary),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildSeat(List<_SeatInfo> seats, int row, int col) {
    final seat = seats.where((s) => s.row == row && s.col == col).firstOrNull;

    Color bgColor;
    Color borderColor;
    Widget child;

    if (seat == null) {
      // Ghế trống
      bgColor = AppColors.backgroundGrey;
      borderColor = AppColors.divider;
      child = const Icon(Icons.chair_alt_rounded,
          size: 16, color: AppColors.textHint);
    } else if (seat.isMe) {
      bgColor = AppColors.primary;
      borderColor = AppColors.primary;
      child = const Icon(Icons.person_rounded, size: 16, color: Colors.white);
    } else if (!seat.isPresent) {
      bgColor = AppColors.backgroundGrey;
      borderColor = AppColors.divider;
      child =
          const Icon(Icons.person_off_rounded, size: 16, color: AppColors.textHint);
    } else {
      final score = seat.attentionScore;
      if (score >= 70) {
        bgColor = AppColors.greenLight;
        borderColor = AppColors.green;
      } else if (score >= 40) {
        bgColor = AppColors.orangeLight;
        borderColor = AppColors.orange;
      } else {
        bgColor = AppColors.redLight;
        borderColor = AppColors.red;
      }
      child = Text(
        '${score.round()}',
        style: TextStyle(
          fontSize: 9,
          fontWeight: FontWeight.bold,
          color: borderColor,
        ),
      );
    }

    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: borderColor, width: 1.5),
      ),
      child: Center(child: child),
    );
  }
}

class _SeatMapData {
  final int myRow;
  final int myCol;
  final List<_SeatInfo> allSeats;
  _SeatMapData(
      {required this.myRow, required this.myCol, required this.allSeats});
}

class _SeatInfo {
  final int row;
  final int col;
  final bool isPresent;
  final bool isAttention;
  final double attentionScore;
  final bool isMe;
  _SeatInfo({
    required this.row,
    required this.col,
    required this.isPresent,
    required this.isAttention,
    required this.attentionScore,
    required this.isMe,
  });
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 14,
          height: 14,
          decoration: BoxDecoration(
              color: color, borderRadius: BorderRadius.circular(3)),
        ),
        const SizedBox(width: 5),
        Text(label, style: AppTextStyles.small),
      ],
    );
  }
}
