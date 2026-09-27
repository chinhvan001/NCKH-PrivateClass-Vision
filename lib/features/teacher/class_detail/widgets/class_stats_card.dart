import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../controllers/class_detail_controller.dart';

class ClassStatsCard extends StatelessWidget {
  final ClassDetailController controller;

  const ClassStatsCard({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final int classSize = controller.classDetail?.students ?? 0;
    final int enrolled = controller.totalEnrolled;
    final int active = controller.activeStudentsCount;
    final int seated = controller.seatedStudentsCount;
    final double attention = controller.avgAttentionScore;

    return Row(
      children: [
        Expanded(
          child: _statItem(
            label: 'Sĩ số',
            value: classSize > 0 ? '$enrolled/$classSize' : '$enrolled',
            subLabel: 'học sinh',
            icon: Icons.people_alt_outlined,
            iconColor: AppColors.brand,
            bgColor: AppColors.lightBlue.withValues(alpha: 0.5),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _statItem(
            label: 'Đang học',
            value: '$active',
            subLabel: 'thành viên',
            icon: Icons.check_circle_outline,
            iconColor: const Color(0xFF16A34A),
            bgColor: const Color(0xFFDCFCE7),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _statItem(
            label: 'Đã xếp chỗ',
            value: '$seated',
            subLabel: 'vị trí bàn',
            icon: Icons.chair_alt_outlined,
            iconColor: const Color(0xFFD97706),
            bgColor: const Color(0xFFFEF3C7),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _statItem(
            label: 'Tập trung',
            value: attention > 0 ? '$attention' : '--',
            subLabel: 'điểm TB',
            icon: Icons.insights_outlined,
            iconColor: const Color(0xFF7C3AED),
            bgColor: const Color(0xFFEDE9FE),
          ),
        ),
      ],
    );
  }

  Widget _statItem({
    required String label,
    required String value,
    required String subLabel,
    required IconData icon,
    required Color iconColor,
    required Color bgColor,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.hair),
      ),
      child: Column(
        children: [
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
            ),
            child: Icon(icon, size: 16, color: iconColor),
          ),
          const SizedBox(height: 8),
          Text(
            value,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w800,
              color: AppColors.navy,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AppColors.muted,
            ),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }
}
