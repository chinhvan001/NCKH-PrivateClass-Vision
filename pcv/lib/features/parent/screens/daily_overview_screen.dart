import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/supervised_student_model.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';

class DailyOverviewScreen extends StatefulWidget {
  const DailyOverviewScreen({super.key});

  @override
  State<DailyOverviewScreen> createState() =>
      _DailyOverviewScreenState();
}

class _DailyOverviewScreenState extends State<DailyOverviewScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_DailyData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_DailyData> _loadData() async {
    final students =
        await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) {
      return _DailyData(supervised: [], stats: null);
    }
    final student = students.first;
    final results = await Future.wait([
      _monitoringService.getSupervisedDataByStudent(student.id),
      _monitoringService.getStudentStats(student.id),
    ]);
    return _DailyData(
      supervised: results[0] as List<SupervisedStudentModel>,
      stats: results[1] as StudentStats,
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
        title: const Text('Tổng quan tập trung',
            style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_DailyData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(
                    color: AppColors.primary));
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off_rounded,
                        size: 48, color: AppColors.red),
                    const SizedBox(height: 12),
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
                      icon: const Icon(Icons.refresh_rounded,
                          size: 18),
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
          final stats = data.stats;
          final supervised = data.supervised;

          if (stats == null || stats.totalSessions == 0) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: const BoxDecoration(
                        color: AppColors.accentLight,
                        shape: BoxShape.circle),
                    child: const Icon(Icons.bar_chart_rounded,
                        size: 44, color: AppColors.primary),
                  ),
                  const SizedBox(height: 14),
                  const Text('Chưa có dữ liệu',
                      style: AppTextStyles.heading3),
                  const SizedBox(height: 6),
                  const Text('Chưa có buổi học nào được ghi nhận',
                      style: AppTextStyles.caption),
                ],
              ),
            );
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Overview stats ──────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tổng quan',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: _StatCard(
                              icon: Icons.psychology_rounded,
                              color: AppColors.primary,
                              bgColor: AppColors.accentLight,
                              label: 'Tập trung TB',
                              value:
                                  '${stats.avgAttentionPercent}%',
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _StatCard(
                              icon: Icons.fact_check_rounded,
                              color: AppColors.green,
                              bgColor: AppColors.greenLight,
                              label: 'Điểm danh',
                              value: stats.attendanceLabel,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          Expanded(
                            child: _StatCard(
                              icon: Icons.visibility_rounded,
                              color: AppColors.orange,
                              bgColor: AppColors.orangeLight,
                              label: 'Buổi tập trung',
                              value:
                                  '${stats.attentionSessions}/${stats.totalSessions}',
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _StatCard(
                              icon: Icons.cancel_rounded,
                              color: AppColors.red,
                              bgColor: AppColors.redLight,
                              label: 'Buổi vắng',
                              value: '${stats.absentSessions}',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Attention progress ──────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tập trung các buổi học',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      if (supervised.isEmpty)
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.all(16),
                            child: Text('Chưa có dữ liệu',
                                style: AppTextStyles.caption),
                          ),
                        )
                      else
                        ...supervised
                            .asMap()
                            .entries
                            .map((entry) {
                          final i = entry.key;
                          final s = entry.value;
                          final color =
                              _percentColor(s.attentionScore);
                          return Padding(
                            padding:
                                const EdgeInsets.symmetric(
                                    vertical: 5),
                            child: Row(
                              children: [
                                SizedBox(
                                  width: 60,
                                  child: Text(
                                    'Buổi ${i + 1}',
                                    style: AppTextStyles.body2,
                                  ),
                                ),
                                Expanded(
                                  child: ClipRRect(
                                    borderRadius:
                                        BorderRadius.circular(4),
                                    child: LinearProgressIndicator(
                                      value:
                                          s.attentionScore / 100,
                                      minHeight: 8,
                                      backgroundColor:
                                          AppColors.divider,
                                      valueColor:
                                          AlwaysStoppedAnimation<
                                              Color>(color),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                SizedBox(
                                  width: 38,
                                  child: Text(
                                    '${s.attentionPercent}%',
                                    style: TextStyle(
                                        fontSize: 12,
                                        fontWeight:
                                            FontWeight.w600,
                                        color: color),
                                    textAlign: TextAlign.right,
                                  ),
                                ),
                              ],
                            ),
                          );
                        }),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Attendance detail ───────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Điểm danh',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      Row(
                        mainAxisAlignment:
                            MainAxisAlignment.spaceBetween,
                        children: [
                          _AttendanceBox(
                            label: 'Tổng số buổi',
                            value: '${stats.totalSessions}',
                            unit: 'buổi',
                            color: AppColors.textPrimary,
                          ),
                          _AttendanceBox(
                            label: 'Đã có mặt',
                            value: '${stats.presentSessions}',
                            unit: 'buổi',
                            color: AppColors.green,
                            highlight: true,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment:
                            MainAxisAlignment.spaceBetween,
                        children: [
                          _AttendanceBox(
                            label: 'Vắng mặt',
                            value: '${stats.absentSessions}',
                            unit: 'buổi',
                            color: AppColors.red,
                          ),
                          _AttendanceBox(
                            label: 'Buổi tập trung',
                            value: '${stats.attentionSessions}',
                            unit: 'buổi',
                            color: AppColors.orange,
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

  Color _percentColor(double p) {
    if (p >= 70) return AppColors.green;
    if (p >= 40) return AppColors.orange;
    return AppColors.red;
  }
}

class _DailyData {
  final List<SupervisedStudentModel> supervised;
  final StudentStats? stats;
  _DailyData({required this.supervised, required this.stats});
}

class _StatCard extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String label;
  final String value;
  const _StatCard(
      {required this.icon,
      required this.color,
      required this.bgColor,
      required this.label,
      required this.value});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
          color: bgColor, borderRadius: BorderRadius.circular(10)),
      child: Row(
        children: [
          Icon(icon, color: color, size: 22),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value,
                    style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: color)),
                Text(label, style: AppTextStyles.small),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AttendanceBox extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  final Color color;
  final bool highlight;
  const _AttendanceBox(
      {required this.label,
      required this.value,
      required this.unit,
      required this.color,
      this.highlight = false});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: (MediaQuery.of(context).size.width - 64) / 2,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: highlight
            ? AppColors.greenLight
            : AppColors.backgroundGrey,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.caption),
          const SizedBox(height: 4),
          RichText(
            text: TextSpan(
              children: [
                TextSpan(
                    text: value,
                    style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: color)),
                TextSpan(
                    text: ' $unit',
                    style: AppTextStyles.body2),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
