import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class AttendanceDetailScreen extends StatelessWidget {
  const AttendanceDetailScreen({super.key});

  final List<Map<String, dynamic>> _absences = const [
    {
      'date': '10/05/2024',
      'type': 'Vắng có phép',
      'reason': 'Lý do: Ốm',
    },
    {
      'date': '03/05/2024',
      'type': 'Vắng có phép',
      'reason': 'Lý do: Việc gia đình',
    },
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
        title: const Text('Chi tiết điểm danh', style: AppTextStyles.heading2),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Month header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text('Tháng 05/2024', style: AppTextStyles.heading3),
            ),
            const SizedBox(height: 14),
            // Summary stats
            AppCard(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _SummaryBox(label: 'Tổng số buổi', value: '20', color: AppColors.textPrimary),
                  Container(width: 1, height: 40, color: AppColors.divider),
                  _SummaryBox(label: 'Đã tham gia', value: '18', color: AppColors.green),
                ],
              ),
            ),
            const SizedBox(height: 10),
            AppCard(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _SummaryBox(label: 'Vắng có phép', value: '2', color: AppColors.orange),
                  Container(width: 1, height: 40, color: AppColors.divider),
                  _SummaryBox(label: 'Vắng không phép', value: '0', color: AppColors.red),
                ],
              ),
            ),
            const SizedBox(height: 10),
            AppCard(
              child: _SummaryBox(label: 'Đi muộn', value: '1', color: AppColors.primary),
            ),
            const SizedBox(height: 16),
            // Absence list
            const Text('Danh sách vắng', style: AppTextStyles.heading3),
            const SizedBox(height: 10),
            ..._absences.map((a) => Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: AppCard(
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppColors.orangeLight,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.event_busy,
                            color: AppColors.orange,
                            size: 20,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                a['date'] as String,
                                style: AppTextStyles.caption,
                              ),
                              const SizedBox(height: 3),
                              Text(
                                a['type'] as String,
                                style: AppTextStyles.body2.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.orange,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(a['reason'] as String, style: AppTextStyles.caption),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                )),
          ],
        ),
      ),
    );
  }
}

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
