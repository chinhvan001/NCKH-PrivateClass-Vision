import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/student_model.dart';
import '../services/student_service.dart';
import 'attendance_detail_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';

  final _studentService = StudentService();
  late Future<StudentModel?> _studentFuture;

  @override
  void initState() {
    super.initState();
    _studentFuture = _studentService.getStudentById(_studentId);
  }

  void _reload() {
    setState(() {
      _studentFuture = _studentService.getStudentById(_studentId);
    });
  }

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
          onPressed: () =>
          Navigator.canPop(context) ? Navigator.pop(context) : null,
        ),
        title: const Text('Hồ sơ học sinh', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
            tooltip: 'Tải lại',
          ),
        ],
      ),
      body: FutureBuilder<StudentModel?>(
        future: _studentFuture,
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

          // ── Not found ──────────────────────────────────────────────
          final student = snapshot.data;
          if (student == null) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.person_off_rounded,
                      size: 48, color: AppColors.textHint),
                  const SizedBox(height: 12),
                  const Text('Không tìm thấy hồ sơ',
                      style: AppTextStyles.heading3),
                  const SizedBox(height: 6),
                  const Text('Vui lòng kiểm tra lại',
                      style: AppTextStyles.caption),
                ],
              ),
            );
          }

          // ── Content ────────────────────────────────────────────────
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Student header ───────────────────────────────────
                AppCard(
                  child: Row(
                    children: [
                      Container(
                        width: 64,
                        height: 64,
                        decoration: const BoxDecoration(
                          color: AppColors.accentLight,
                          shape: BoxShape.circle,
                        ),
                        child: Center(
                          child: Text(
                            _initials(student.name),
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: AppColors.primary,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(student.name,
                                style: AppTextStyles.heading2),
                            const SizedBox(height: 4),
                            Text(
                              '${student.className} - ${student.schoolName}',
                              style: AppTextStyles.caption,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Personal info ────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Thông tin chung',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 12),
                      _ProfileRow(
                          label: 'Ngày sinh',
                          value: student.dateOfBirth.isNotEmpty
                              ? student.dateOfBirth
                              : '---'),
                      _ProfileRow(
                          label: 'Giáo viên chủ nhiệm',
                          value: student.teacherName.isNotEmpty
                              ? student.teacherName
                              : '---'),
                      _ProfileRow(
                          label: 'Phụ huynh liên hệ',
                          value: student.parentPhone.isNotEmpty
                              ? student.parentPhone
                              : '---'),
                      _ProfileRow(
                          label: 'Email liên hệ',
                          value: student.parentEmail.isNotEmpty
                              ? student.parentEmail
                              : '---'),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Quick stats ──────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Thống kê nhanh',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _QuickStat(
                            icon: Icons.psychology_rounded,
                            color: AppColors.primary,
                            bgColor: AppColors.accentLight,
                            label: 'Tập trung TB',
                            value: '${student.avgFocusPercent}%',
                          ),
                          const SizedBox(width: 10),
                          _QuickStat(
                            icon: Icons.fact_check_rounded,
                            color: AppColors.green,
                            bgColor: AppColors.greenLight,
                            label: 'Điểm danh',
                            value:
                            '${student.presentSessions}/${student.totalSessions}',
                          ),
                          const SizedBox(width: 10),
                          _QuickStat(
                            icon: Icons.watch_later_rounded,
                            color: AppColors.orange,
                            bgColor: AppColors.orangeLight,
                            label: 'Đi muộn',
                            value: '${student.lateSessions}',
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Report link ──────────────────────────────────────
                AppCard(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const AttendanceDetailScreen()),
                    );
                  },
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: AppColors.accentLight,
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: const Icon(Icons.bar_chart,
                            color: AppColors.primary, size: 22),
                      ),
                      const SizedBox(width: 12),
                      const Expanded(
                        child: Text('Xem báo cáo tổng kết',
                            style: AppTextStyles.heading3),
                      ),
                      const Icon(Icons.chevron_right,
                          color: AppColors.textSecondary),
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

  String _initials(String name) {
    final parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[parts.length - 1][0]}'.toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }
}

// ─── Profile row ───────────────────────────────────────────────────────────────
class _ProfileRow extends StatelessWidget {
  final String label;
  final String value;

  const _ProfileRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 160,
            child: Text(label, style: AppTextStyles.caption),
          ),
          Expanded(
            child: Text(value, style: AppTextStyles.body2),
          ),
        ],
      ),
    );
  }
}

// ─── Quick stat card ───────────────────────────────────────────────────────────
class _QuickStat extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String label;
  final String value;

  const _QuickStat({
    required this.icon,
    required this.color,
    required this.bgColor,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 6),
            Text(
              value,
              style: TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 3),
            Text(label,
                style: AppTextStyles.small,
                textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
