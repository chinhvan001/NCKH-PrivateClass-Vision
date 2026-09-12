import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/schedule_model.dart';
import '../services/schedule_service.dart';

class UpcomingScheduleScreen extends StatefulWidget {
  const UpcomingScheduleScreen({super.key});

  @override
  State<UpcomingScheduleScreen> createState() => _UpcomingScheduleScreenState();
}

class _UpcomingScheduleScreenState extends State<UpcomingScheduleScreen> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';

  final _service = ScheduleService();
  late Future<List<ScheduleModel>> _schedulesFuture;

  @override
  void initState() {
    super.initState();
    _schedulesFuture = _service.getUpcomingSchedules(_studentId);
  }

  void _reload() => setState(
      () => _schedulesFuture = _service.getUpcomingSchedules(_studentId));

  // Màu theo môn học
  Color _subjectColor(String subject) {
    switch (subject) {
      case 'Toán':
        return AppColors.primary;
      case 'Tiếng Việt':
        return AppColors.green;
      case 'Tiếng Anh':
        return AppColors.orange;
      case 'Khoa học':
        return AppColors.red;
      default:
        return AppColors.accent;
    }
  }

  Color _subjectBg(String subject) {
    switch (subject) {
      case 'Toán':
        return AppColors.accentLight;
      case 'Tiếng Việt':
        return AppColors.greenLight;
      case 'Tiếng Anh':
        return AppColors.orangeLight;
      case 'Khoa học':
        return AppColors.redLight;
      default:
        return AppColors.accentLight;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Navigator.canPop(context)
            ? IconButton(
                icon: const Icon(Icons.arrow_back_ios,
                    color: AppColors.textPrimary, size: 20),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: const Text('Lịch học sắp tới', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
            tooltip: 'Tải lại',
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.divider),
        ),
      ),
      body: FutureBuilder<List<ScheduleModel>>(
        future: _schedulesFuture,
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
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: const BoxDecoration(
                        color: AppColors.redLight,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.cloud_off_rounded,
                          size: 44, color: AppColors.red),
                    ),
                    const SizedBox(height: 14),
                    const Text('Không thể tải dữ liệu',
                        style: AppTextStyles.heading3),
                    const SizedBox(height: 6),
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

          final schedules = snapshot.data ?? [];

          // ── Empty ──────────────────────────────────────────────────
          if (schedules.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: const BoxDecoration(
                      color: AppColors.accentLight,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.event_available_rounded,
                        size: 44, color: AppColors.primary),
                  ),
                  const SizedBox(height: 14),
                  const Text('Không có lịch học sắp tới',
                      style: AppTextStyles.heading3),
                  const SizedBox(height: 6),
                  const Text('Hiện chưa có buổi học nào được lên lịch',
                      style: AppTextStyles.caption),
                ],
              ),
            );
          }

          return Column(
            children: [
              // ── Count ──────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: Row(
                  children: [
                    const Icon(Icons.calendar_month_rounded,
                        size: 16, color: AppColors.textSecondary),
                    const SizedBox(width: 6),
                    Text('${schedules.length} buổi học sắp tới',
                        style: AppTextStyles.caption),
                  ],
                ),
              ),

              // ── List ───────────────────────────────────────────────
              Expanded(
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 20),
                  physics: const BouncingScrollPhysics(),
                  itemCount: schedules.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final s = schedules[index];
                    final color = _subjectColor(s.subject);
                    final bg = _subjectBg(s.subject);
                    return AppCard(
                      child: Row(
                        children: [
                          // Subject icon
                          Container(
                            width: 48,
                            height: 48,
                            decoration: BoxDecoration(
                              color: bg,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Center(
                              child: Text(
                                s.subject.substring(0, 1),
                                style: TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                            ),
                          ),
                          const SizedBox(width: 12),
                          // Info
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(s.subject,
                                    style: AppTextStyles.heading3.copyWith(
                                        color: color)),
                                const SizedBox(height: 3),
                                Text(s.date, style: AppTextStyles.caption),
                                const SizedBox(height: 2),
                                Row(
                                  children: [
                                    const Icon(Icons.access_time_rounded,
                                        size: 12,
                                        color: AppColors.textSecondary),
                                    const SizedBox(width: 3),
                                    Text(s.time,
                                        style: AppTextStyles.small),
                                    const SizedBox(width: 10),
                                    const Icon(Icons.meeting_room_outlined,
                                        size: 12,
                                        color: AppColors.textSecondary),
                                    const SizedBox(width: 3),
                                    Text(s.room,
                                        style: AppTextStyles.small),
                                  ],
                                ),
                                const SizedBox(height: 2),
                                Row(
                                  children: [
                                    const Icon(Icons.person_outline_rounded,
                                        size: 12,
                                        color: AppColors.textSecondary),
                                    const SizedBox(width: 3),
                                    Text(s.teacherName,
                                        style: AppTextStyles.small),
                                  ],
                                ),
                              ],
                            ),
                          ),
                          // Order badge
                          Container(
                            width: 28,
                            height: 28,
                            decoration: BoxDecoration(
                              color: bg,
                              shape: BoxShape.circle,
                            ),
                            child: Center(
                              child: Text(
                                '${index + 1}',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}
