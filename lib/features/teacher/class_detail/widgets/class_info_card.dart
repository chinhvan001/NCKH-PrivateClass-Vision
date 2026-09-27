import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../controllers/class_detail_controller.dart';

class ClassInfoCard extends StatelessWidget {
  final ClassDetailController controller;

  const ClassInfoCard({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final classDetail = controller.classDetail;
    final teacherData = controller.teacherData;
    final String teacherName = teacherData?['name']?.toString() ?? 'Chưa phân công';
    final String teacherSubject = teacherData?['subject']?.toString() ?? '';
    final String cameraStatus = controller.cameraStatus;
    final bool isCameraActive = cameraStatus.toLowerCase().contains('active') ||
        cameraStatus.toLowerCase().contains('online') ||
        cameraStatus.toLowerCase().contains('hoạt');

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.hair),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(
                  Icons.info_outline,
                  color: AppColors.brand,
                  size: 20,
                ),
              ),
              const SizedBox(width: 10),
              const Text(
                'Thông tin phòng học & Lớp',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: AppColors.navy,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          const Divider(height: 1, color: AppColors.hair),
          const SizedBox(height: 12),
          _row(Icons.meeting_room_outlined, 'Phòng học:', controller.classroomName),
          const SizedBox(height: 10),
          _row(
            Icons.grid_view_outlined,
            'Sơ đồ lớp:',
            '${controller.classroomRows} hàng × ${controller.classroomColumns} cột',
          ),
          const SizedBox(height: 10),
          _row(
            Icons.person_outline,
            'Giáo viên:',
            teacherSubject.isNotEmpty ? '$teacherName ($teacherSubject)' : teacherName,
          ),
          if (classDetail != null && classDetail.schoolYear > 0) ...[
            const SizedBox(height: 10),
            _row(
              Icons.calendar_today_outlined,
              'Năm học:',
              '${classDetail.schoolYear} - ${classDetail.schoolYear + 1}',
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(Icons.videocam_outlined, size: 18, color: AppColors.muted),
              const SizedBox(width: 8),
              const Text(
                'Camera:',
                style: TextStyle(fontSize: 13, color: AppColors.muted),
              ),
              const Spacer(),
              Text(
                controller.cameraName,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.navy,
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                decoration: BoxDecoration(
                  color: isCameraActive ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  cameraStatus,
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: isCameraActive ? const Color(0xFF16A34A) : const Color(0xFFDC2626),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _row(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 18, color: AppColors.muted),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(fontSize: 13, color: AppColors.muted),
        ),
        const Spacer(),
        Text(
          value,
          style: const TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: AppColors.navy,
          ),
        ),
      ],
    );
  }
}
