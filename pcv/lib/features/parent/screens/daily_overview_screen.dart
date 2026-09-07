import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/subject_focus_model.dart';
import '../models/attendance_summary_model.dart';
import '../services/subject_focus_service.dart';
import '../services/session_service.dart';

class DailyOverviewScreen extends StatefulWidget {
  const DailyOverviewScreen({super.key});

  @override
  State<DailyOverviewScreen> createState() => _DailyOverviewScreenState();
}

class _DailyOverviewScreenState extends State<DailyOverviewScreen> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';

  final _focusService = SubjectFocusService();
  final _sessionService = SessionService();

  String _selectedPeriod = 'Tuần này';
  final List<String> _periods = ['Hôm nay', 'Tuần này', 'Tháng này'];

  // Map UI label → Firestore period value
  static const Map<String, String> _periodMap = {
    'Hôm nay': 'today',
    'Tuần này': 'week',
    'Tháng này': 'month',
  };

  late Future<_DailyData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData(_selectedPeriod);
  }

  Future<_DailyData> _loadData(String periodLabel) async {
    final period = _periodMap[periodLabel] ?? 'week';
    final results = await Future.wait([
      _focusService.getSubjectFocus(studentId: _studentId, period: period),
      _sessionService.getAttendanceSummary(_studentId),
    ]);
    return _DailyData(
      subjects: results[0] as List<SubjectFocusModel>,
      summary: results[1] as AttendanceSummaryModel,
    );
  }

  void _onPeriodChanged(String label) {
    setState(() {
      _selectedPeriod = label;
      _dataFuture = _loadData(label);
    });
  }

  void _reload() => setState(() => _dataFuture = _loadData(_selectedPeriod));

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
        title: const Text('Tổng quan', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
            tooltip: 'Tải lại',
          ),
        ],
      ),
      body: FutureBuilder<_DailyData>(
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
          final subjects = data.subjects;
          final summary = data.summary;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Period selector ──────────────────────────────────
                Container(
                  padding: const EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: AppColors.divider),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: _periods.map((p) {
                      final selected = p == _selectedPeriod;
                      return GestureDetector(
                        onTap: () => _onPeriodChanged(p),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 7),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primary
                                : Colors.transparent,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: AnimatedDefaultTextStyle(
                            duration: const Duration(milliseconds: 200),
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                              color: selected
                                  ? Colors.white
                                  : AppColors.textSecondary,
                            ),
                            child: Text(p),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
                const SizedBox(height: 16),

                // ── Focus section ────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Mức độ tập trung theo môn',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      if (subjects.isEmpty)
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.symmetric(vertical: 16),
                            child: Text('Chưa có dữ liệu',
                                style: AppTextStyles.caption),
                          ),
                        )
                      else
                        ...subjects.asMap().entries.map((entry) {
                          final i = entry.key;
                          final s = entry.value;
                          return SubjectProgressBar(
                            subject: s.subject,
                            percent: s.percent,
                            color: SubjectFocusModel.colorForIndex(i),
                          );
                        }),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Attendance section ───────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Điểm danh', style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _AttendanceBox(
                            label: 'Tổng số buổi',
                            value: '${summary.totalSessions}',
                            unit: 'buổi',
                            color: AppColors.textPrimary,
                          ),
                          _AttendanceBox(
                            label: 'Đã tham gia',
                            value: '${summary.presentSessions}',
                            unit: 'buổi',
                            color: AppColors.green,
                            highlight: true,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          _AttendanceBox(
                            label: 'Vắng có phép',
                            value: '${summary.excusedSessions}',
                            unit: 'buổi',
                            color: AppColors.orange,
                          ),
                          _AttendanceBox(
                            label: 'Vắng không phép',
                            value: '${summary.absentSessions}',
                            unit: 'buổi',
                            color: AppColors.red,
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      // Đi muộn
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: AppColors.backgroundGrey,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Đi muộn', style: AppTextStyles.caption),
                            const SizedBox(height: 4),
                            RichText(
                              text: TextSpan(
                                children: [
                                  TextSpan(
                                    text: '${summary.lateSessions}',
                                    style: const TextStyle(
                                      fontSize: 22,
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.orange,
                                    ),
                                  ),
                                  const TextSpan(
                                    text: ' buổi',
                                    style: AppTextStyles.body2,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
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
}

// ─── Data holder ───────────────────────────────────────────────────────────────
class _DailyData {
  final List<SubjectFocusModel> subjects;
  final AttendanceSummaryModel summary;
  _DailyData({required this.subjects, required this.summary});
}

// ─── Attendance box ────────────────────────────────────────────────────────────
class _AttendanceBox extends StatelessWidget {
  final String label;
  final String value;
  final String unit;
  final Color color;
  final bool highlight;

  const _AttendanceBox({
    required this.label,
    required this.value,
    required this.unit,
    required this.color,
    this.highlight = false,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: (MediaQuery.of(context).size.width - 64) / 2,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: highlight ? AppColors.greenLight : AppColors.backgroundGrey,
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
                    color: color,
                  ),
                ),
                TextSpan(
                  text: ' $unit',
                  style: AppTextStyles.body2,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
