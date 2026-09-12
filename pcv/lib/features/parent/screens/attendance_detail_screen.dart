import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/attendance_detail_model.dart';
import '../services/attendance_detail_service.dart';

class AttendanceDetailScreen extends StatefulWidget {
  const AttendanceDetailScreen({super.key});

  @override
  State<AttendanceDetailScreen> createState() => _AttendanceDetailScreenState();
}

class _AttendanceDetailScreenState extends State<AttendanceDetailScreen> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';
  static const String _month = '05/2024';

  final _service = AttendanceDetailService();
  late Future<_AttendanceData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_AttendanceData> _loadData() async {
    final results = await Future.wait([
      _service.getAttendanceByMonth(_studentId, _month),
      _service.getSummaryByMonth(_studentId, _month),
    ]);
    return _AttendanceData(
      list: results[0] as List<AttendanceDetailModel>,
      summary: results[1] as Map<String, int>,
    );
  }

  void _reload() => setState(() => _dataFuture = _loadData());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios,
              color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Chi tiết điểm danh', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
            tooltip: 'Tải lại',
          ),
        ],
      ),
      body: FutureBuilder<_AttendanceData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          // ── Loading ────────────────────────────────────────────────
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(color: AppColors.primary),
            );
          }

          // ── Error ──────────────────────────────────────────────────
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: const BoxDecoration(
                        color: AppColors.redLight,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.cloud_off_rounded,
                          size: 44, color: AppColors.red),
                    ),
                    const SizedBox(height: 14),
                    const Text('Không thể tải dữ liệu',
                        style: AppTextStyles.heading3),
                    const SizedBox(height: 6),
                    Text(
                      snapshot.error
                          .toString()
                          .replaceFirst('Exception: ', ''),
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
              ),
            );
          }

          final data = snapshot.data!;
          final summary = data.summary;
          final list = data.list
              .where((a) => a.type != 'present')
              .toList(); // chỉ hiện vắng + muộn

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Month header ─────────────────────────────────────
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text('Tháng $_month',
                      style: AppTextStyles.heading3),
                ),
                const SizedBox(height: 14),

                // ── Summary stats ────────────────────────────────────
                AppCard(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _SummaryBox(
                        label: 'Tổng số buổi',
                        value: '${summary['total'] ?? 0}',
                        color: AppColors.textPrimary,
                      ),
                      Container(
                          width: 1, height: 40, color: AppColors.divider),
                      _SummaryBox(
                        label: 'Đã tham gia',
                        value: '${summary['present'] ?? 0}',
                        color: AppColors.green,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                AppCard(
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: [
                      _SummaryBox(
                        label: 'Vắng có phép',
                        value: '${summary['absent_excused'] ?? 0}',
                        color: AppColors.orange,
                      ),
                      Container(
                          width: 1, height: 40, color: AppColors.divider),
                      _SummaryBox(
                        label: 'Vắng không phép',
                        value: '${summary['absent'] ?? 0}',
                        color: AppColors.red,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                AppCard(
                  child: _SummaryBox(
                    label: 'Đi muộn',
                    value: '${summary['late'] ?? 0}',
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(height: 16),

                // ── List vắng + muộn ─────────────────────────────────
                const Text('Danh sách vắng & đi muộn',
                    style: AppTextStyles.heading3),
                const SizedBox(height: 10),

                if (list.isEmpty)
                  AppCard(
                    child: Center(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          children: [
                            const Icon(Icons.check_circle_rounded,
                                size: 40, color: AppColors.green),
                            const SizedBox(height: 8),
                            const Text('Không có buổi vắng nào!',
                                style: AppTextStyles.heading3),
                            const SizedBox(height: 4),
                            const Text('Tháng này chuyên cần tốt',
                                style: AppTextStyles.caption),
                          ],
                        ),
                      ),
                    ),
                  )
                else
                  ...list.map((a) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: AppCard(
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: _bgColor(a.type),
                                  shape: BoxShape.circle,
                                ),
                                child: Icon(
                                  _icon(a.type),
                                  color: _color(a.type),
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment:
                                      CrossAxisAlignment.start,
                                  children: [
                                    Text(a.date,
                                        style: AppTextStyles.caption),
                                    const SizedBox(height: 3),
                                    Text(
                                      a.typeLabel,
                                      style: AppTextStyles.body2.copyWith(
                                        fontWeight: FontWeight.w600,
                                        color: _color(a.type),
                                      ),
                                    ),
                                    if (a.reason.isNotEmpty) ...[
                                      const SizedBox(height: 2),
                                      Text('Lý do: ${a.reason}',
                                          style: AppTextStyles.caption),
                                    ],
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      )),
              ],
            ),
          );
        },
      ),
    );
  }

  Color _color(String type) {
    switch (type) {
      case 'absent_excused':
        return AppColors.orange;
      case 'absent':
        return AppColors.red;
      case 'late':
        return AppColors.primary;
      default:
        return AppColors.green;
    }
  }

  Color _bgColor(String type) {
    switch (type) {
      case 'absent_excused':
        return AppColors.orangeLight;
      case 'absent':
        return AppColors.redLight;
      case 'late':
        return AppColors.accentLight;
      default:
        return AppColors.greenLight;
    }
  }

  IconData _icon(String type) {
    switch (type) {
      case 'absent_excused':
        return Icons.event_busy_rounded;
      case 'absent':
        return Icons.cancel_rounded;
      case 'late':
        return Icons.watch_later_rounded;
      default:
        return Icons.check_circle_rounded;
    }
  }
}

// ─── Data holder ───────────────────────────────────────────────────────────────
class _AttendanceData {
  final List<AttendanceDetailModel> list;
  final Map<String, int> summary;
  _AttendanceData({required this.list, required this.summary});
}

// ─── Summary box ───────────────────────────────────────────────────────────────
class _SummaryBox extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _SummaryBox({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 26,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Text(label, style: AppTextStyles.caption),
      ],
    );
  }
}
