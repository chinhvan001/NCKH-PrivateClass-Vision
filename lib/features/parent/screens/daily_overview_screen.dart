import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/attendance_detail_screen.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class DailyOverviewScreen extends StatefulWidget {
  const DailyOverviewScreen({super.key});

  @override
  State<DailyOverviewScreen> createState() => _DailyOverviewScreenState();
}

class _DailyOverviewScreenState extends State<DailyOverviewScreen> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  String _selectedPeriod = 'Tuần này';
  final List<String> _periods = ['Hôm nay', 'Tuần này', 'Tháng này'];

  Future<OverviewStats>? _statsFuture;

  // Bảng màu cho thanh tiến độ từng môn học
  static const List<Color> _palette = [
    AppColors.primary,
    AppColors.green,
    AppColors.orange,
    AppColors.red,
    AppColors.accent,
  ];

  @override
  void initState() {
    super.initState();
    _fetchStats();
  }

  void _fetchStats() {
    final child = _session.selectedChild;
    if (child != null) {
      setState(() {
        _statsFuture = _parentService.getOverviewStats(
          studentId: child.id,
          classIds: child.classes.map((c) => c.id).toList(),
          period: _selectedPeriod,
        );
      });
    } else {
      setState(() {
        _statsFuture = Future.value(const OverviewStats());
      });
    }
  }

  void _onPeriodChanged(String period) {
    if (_selectedPeriod == period) return;
    setState(() {
      _selectedPeriod = period;
    });
    _fetchStats();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios,
            color: AppColors.textPrimary,
            size: 20,
          ),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Tổng quan', style: AppTextStyles.heading2),
      ),
      body: RefreshIndicator(
        onRefresh: () async => _fetchStats(),
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Bộ chọn khoảng thời gian
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
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: selected
                              ? AppColors.primary
                              : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          p,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: selected
                                ? Colors.white
                                : AppColors.textSecondary,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 16),

              FutureBuilder<OverviewStats>(
                future: _statsFuture,
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return const Padding(
                      padding: EdgeInsets.symmetric(vertical: 40),
                      child: Center(child: CircularProgressIndicator()),
                    );
                  }

                  final stats = snapshot.data ?? const OverviewStats();

                  return Column(
                    children: [
                      // Card Mức độ tập trung theo môn
                      AppCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Mức độ tập trung theo môn',
                              style: AppTextStyles.heading3,
                            ),
                            const SizedBox(height: 14),
                            if (stats.subjects.isEmpty)
                              const Padding(
                                padding: EdgeInsets.symmetric(vertical: 16),
                                child: Center(
                                  child: Text(
                                    'Chưa có dữ liệu tập trung trong khoảng thời gian này',
                                    style: AppTextStyles.caption,
                                  ),
                                ),
                              )
                            else
                              ...stats.subjects.asMap().entries.map((entry) {
                                final index = entry.key;
                                final item = entry.value;
                                final color = _palette[index % _palette.length];
                                return SubjectProgressBar(
                                  subject: item.subject,
                                  percent: item.percent,
                                  color: color,
                                );
                              }),
                          ],
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Card Điểm danh
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
                                  value: stats.totalSessions.toString(),
                                  unit: 'buổi',
                                  color: AppColors.textPrimary,
                                ),
                                _AttendanceBox(
                                  label: 'Đã tham gia',
                                  value: stats.attendedSessions.toString(),
                                  unit: 'buổi',
                                  color: AppColors.green,
                                  highlight: stats.attendedSessions > 0,
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                _AttendanceBox(
                                  label: 'Vắng có phép',
                                  value: stats.excusedAbsences.toString(),
                                  unit: 'buổi',
                                  color: AppColors.orange,
                                ),
                                _AttendanceBox(
                                  label: 'Vắng không phép',
                                  value: stats.unexcusedAbsences.toString(),
                                  unit: 'buổi',
                                  color: AppColors.red,
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Align(
                              alignment: Alignment.centerRight,
                              child: GestureDetector(
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (_) => const AttendanceDetailScreen(),
                                    ),
                                  );
                                },
                                child: const Text(
                                  'Xem chi tiết >',
                                  style: AppTextStyles.linkText,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
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
                TextSpan(text: ' $unit', style: AppTextStyles.body2),
              ],
            ),
          ),
        ],
      ),
    );
  }
}