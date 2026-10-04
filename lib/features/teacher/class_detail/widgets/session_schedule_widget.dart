import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/session_model.dart';
import '../controllers/class_detail_controller.dart';

class SessionScheduleWidget extends StatelessWidget {
  final ClassDetailController controller;
  const SessionScheduleWidget({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final sessions = controller.sessions;

    if (sessions.isEmpty) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Container(
          width: double.infinity,
          padding: const EdgeInsets.all(32),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.hair),
          ),
          child: const Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.event_busy_outlined, size: 40, color: AppColors.muted),
              SizedBox(height: 8),
              Text(
                'Chưa có lịch hoặc buổi học nào được ghi nhận.',
                style: TextStyle(fontSize: 13, color: AppColors.muted),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return ListView.separated(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 24),
      itemCount: sessions.length,
      separatorBuilder: (context, index) => const SizedBox(height: 10),
      itemBuilder: (context, index) => _sessionCard(sessions[index]),
    );
  }

  Widget _sessionCard(SessionModel session) {
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

    return Container(
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
