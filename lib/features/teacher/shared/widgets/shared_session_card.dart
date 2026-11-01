import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/session_model.dart';

class SharedSessionCard extends StatelessWidget {
  final SessionModel session;
  final VoidCallback onTap;
  final bool showClassInfo;

  const SharedSessionCard({
    super.key,
    required this.session,
    required this.onTap,
    this.showClassInfo = false,
  });

  @override
  Widget build(BuildContext context) {
    final bool isFinished = session.status == 'Đã kết thúc';
    final bool isLive = session.status == 'Đang diễn ra';

    final Color badgeBg = isLive
        ? const Color(0xFFDCFCE7)
        : isFinished
        ? AppColors.appBg
        : const Color(0xFFFEF3C7);

    final Color badgeColor = isLive
        ? const Color(0xFF16A34A)
        : isFinished
        ? AppColors.muted
        : const Color(0xFFD97706);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.hair),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.lightBlue,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    session.date,
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                      color: AppColors.brand,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  '${session.start} - ${session.end}',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppColors.navy,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: badgeBg,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    session.status,
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: badgeColor,
                    ),
                  ),
                ),
              ],
            ),
            
            if (showClassInfo) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  const Icon(Icons.class_outlined, size: 14, color: AppColors.muted),
                  const SizedBox(width: 4),
                  Text(
                    session.className,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.navy,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Icon(Icons.meeting_room_outlined, size: 14, color: AppColors.muted),
                  const SizedBox(width: 4),
                  Text(
                    session.room,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: AppColors.navy,
                    ),
                  ),
                ],
              ),
            ],
            
            const SizedBox(height: 12),
            Row(
              children: [
                _metric(
                  Icons.people_outline,
                  'Có mặt: ${session.presentStudent}/${session.size}',
                ),
                const SizedBox(width: 16),
                _metric(
                  Icons.insights_outlined,
                  'Tập trung: ${session.avgAttentionScore > 0 ? session.avgAttentionScore : "--"}',
                ),
              ],
            ),
            if (session.note.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                'Ghi chú: ${session.note}',
                style: const TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: AppColors.muted,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _metric(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AppColors.muted),
        const SizedBox(width: 4),
        Text(
          text,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: AppColors.navy,
          ),
        ),
      ],
    );
  }
}
