import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/session_model.dart';
import '../controllers/class_detail_controller.dart';

import '../../session_detail/screens/session_detail_screen.dart';
import '../../shared/widgets/shared_session_card.dart';

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
      itemBuilder: (context, index) => SharedSessionCard(
        session: sessions[index],
        onTap: () => _navigateToSessionDetail(context, sessions[index]),
        showClassInfo: false,
      ),
    );
  }

  void _navigateToSessionDetail(
    BuildContext context,
    SessionModel session,
  ) {
    final className = controller.classDetail?.name ?? session.className;
    final room = controller.classroomName;

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => SessionDetailScreen(
          sessionId: session.id,
          classId: session.classId,
          className: className,
          room: room,
          start: session.start,
          end: session.end,
          date: session.date,
          status: session.status,
        ),
      ),
    );
  }
}

