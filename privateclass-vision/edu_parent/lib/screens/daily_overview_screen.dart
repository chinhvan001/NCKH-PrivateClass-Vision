import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';

class DailyOverviewScreen extends StatefulWidget {
  const DailyOverviewScreen({super.key});

  @override
  State<DailyOverviewScreen> createState() => _DailyOverviewScreenState();
}

class _DailyOverviewScreenState extends State<DailyOverviewScreen> {
  String _selectedPeriod = 'Tuần này';
  final List<String> _periods = ['Hôm nay', 'Tuần này', 'Tháng này'];

  final List<Map<String, dynamic>> _subjects = [
    {'name': 'Toán', 'percent': 85, 'color': AppColors.primary},
    {'name': 'Tiếng Việt', 'percent': 75, 'color': AppColors.green},
    {'name': 'Tiếng Anh', 'percent': 70, 'color': AppColors.orange},
    {'name': 'Khoa học', 'percent': 80, 'color': AppColors.red},
    {'name': 'Lịch sử & Địa lí', 'percent': 65, 'color': AppColors.accent},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Tổng quan', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.access_time, color: AppColors.textSecondary),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Period selector
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
                    onTap: () => setState(() => _selectedPeriod = p),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
                      decoration: BoxDecoration(
                        color: selected ? AppColors.primary : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        p,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: selected ? Colors.white : AppColors.textSecondary,
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 16),
            // Focus section
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Mức độ tập trung theo môn', style: AppTextStyles.heading3),
                  const SizedBox(height: 14),
                  ..._subjects.map((s) => SubjectProgressBar(
                        subject: s['name'],
                        percent: s['percent'],
                        color: s['color'],
                      )),
                ],
              ),
            ),
            const SizedBox(height: 14),
            // Attendance section
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
                        value: '10',
                        unit: 'buổi',
                        color: AppColors.textPrimary,
                      ),
                      _AttendanceBox(
                        label: 'Đã tham gia',
                        value: '9',
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
                        value: '1',
                        unit: 'buổi',
                        color: AppColors.orange,
                      ),
                      _AttendanceBox(
                        label: 'Vắng không phép',
                        value: '0',
                        unit: 'buổi',
                        color: AppColors.red,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: GestureDetector(
                      onTap: () {},
                      child: const Text('Xem chi tiết >', style: AppTextStyles.linkText),
                    ),
                  ),
                ],
              ),
            ),
          ],
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
