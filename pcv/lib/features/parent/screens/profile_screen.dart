import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/student_model.dart';
import '../models/parent_model.dart';
import '../services/student_service.dart';
import '../services/parent_service.dart';
import '../services/monitoring_session_service.dart';
import 'attendance_detail_screen.dart';
import 'seat_map_screen.dart';
import 'class_comparison_screen.dart';
import 'class_ranking_screen.dart';
import 'attention_chart_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _parentService = ParentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_ProfileData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_ProfileData> _loadData() async {
    final results = await Future.wait([
      _parentService.getParentById(_parentId),
      _studentService.getStudentsByParent(_parentId),
    ]);
    final parent = results[0] as ParentModel?;
    final students = results[1] as List<StudentModel>;
    StudentStats? stats;
    if (students.isNotEmpty) {
      stats = await _monitoringService.getStudentStats(students.first.id);
    }
    return _ProfileData(
        parent: parent, students: students, stats: stats);
  }

  void _reload() => setState(() => _dataFuture = _loadData());

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
        title:
            const Text('Hồ sơ học sinh', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_ProfileData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child:
                    CircularProgressIndicator(color: AppColors.primary));
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.cloud_off_rounded,
                        size: 48, color: AppColors.red),
                    const SizedBox(height: 12),
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

          final data = snapshot.data!;
          final student = data.students.isNotEmpty
              ? data.students.first
              : null;
          final parent = data.parent;
          final stats = data.stats;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Student header ─────────────────────────────────
                if (student != null)
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
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(student.name,
                                style: AppTextStyles.heading2),
                            const SizedBox(height: 4),
                            Text(
                              student.genderLabel,
                              style: AppTextStyles.caption,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Student info ───────────────────────────────────
                if (student != null)
                  AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Thông tin học sinh',
                            style: AppTextStyles.heading3),
                        const SizedBox(height: 12),
                        _ProfileRow(
                            label: 'Ngày sinh',
                            value: student.birthday.isNotEmpty
                                ? student.birthday
                                : '---'),
                        _ProfileRow(
                            label: 'Giới tính',
                            value: student.genderLabel),
                        _ProfileRow(
                            label: 'Email PH',
                            value: student.parentEmail.isNotEmpty
                                ? student.parentEmail
                                : '---'),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Parent info ────────────────────────────────────
                if (parent != null)
                  AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Thông tin phụ huynh',
                            style: AppTextStyles.heading3),
                        const SizedBox(height: 12),
                        _ProfileRow(
                            label: 'Họ tên',
                            value: parent.name.isNotEmpty
                                ? parent.name
                                : '---'),
                        _ProfileRow(
                            label: 'Email',
                            value: parent.email.isNotEmpty
                                ? parent.email
                                : '---'),
                        _ProfileRow(
                            label: 'Điện thoại',
                            value: parent.phoneNumber.isNotEmpty
                                ? parent.phoneNumber
                                : '---'),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Quick stats ────────────────────────────────────
                if (stats != null && stats.totalSessions > 0)
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
                              value:
                                  '${stats.avgAttentionPercent}%',
                            ),
                            const SizedBox(width: 10),
                            _QuickStat(
                              icon: Icons.fact_check_rounded,
                              color: AppColors.green,
                              bgColor: AppColors.greenLight,
                              label: 'Điểm danh',
                              value: stats.attendanceLabel,
                            ),
                            const SizedBox(width: 10),
                            _QuickStat(
                              icon: Icons.event_note_rounded,
                              color: AppColors.textSecondary,
                              bgColor: AppColors.backgroundGrey,
                              label: 'Tổng buổi',
                              value: '${stats.totalSessions}',
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Report link ────────────────────────────────────
                AppCard(
                  onTap: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) =>
                            const AttendanceDetailScreen()),
                  ),
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
                        child: Text('Xem chi tiết điểm danh',
                            style: AppTextStyles.heading3),
                      ),
                      const Icon(Icons.chevron_right,
                          color: AppColors.textSecondary),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Advanced features ──────────────────────────────
                const Text('Phân tích nâng cao',
                    style: AppTextStyles.heading3),
                const SizedBox(height: 10),
                _ProfileMenuCard(
                  icon: Icons.show_chart_rounded,
                  iconColor: AppColors.primary,
                  bgColor: AppColors.accentLight,
                  title: 'Biểu đồ tập trung',
                  subtitle: 'Xu hướng tập trung theo thời gian',
                  onTap: () => Navigator.push(context,
                      MaterialPageRoute(
                          builder: (_) => const AttentionChartScreen())),
                ),
                const SizedBox(height: 8),
                _ProfileMenuCard(
                  icon: Icons.chair_rounded,
                  iconColor: AppColors.orange,
                  bgColor: AppColors.orangeLight,
                  title: 'Sơ đồ chỗ ngồi',
                  subtitle: 'Vị trí ngồi của con trong lớp',
                  onTap: () => Navigator.push(context,
                      MaterialPageRoute(
                          builder: (_) => const SeatMapScreen())),
                ),
                const SizedBox(height: 8),
                _ProfileMenuCard(
                  icon: Icons.compare_arrows_rounded,
                  iconColor: AppColors.green,
                  bgColor: AppColors.greenLight,
                  title: 'So sánh với lớp',
                  subtitle: 'Con so với trung bình lớp học',
                  onTap: () => Navigator.push(context,
                      MaterialPageRoute(
                          builder: (_) => const ClassComparisonScreen())),
                ),
                const SizedBox(height: 8),
                _ProfileMenuCard(
                  icon: Icons.leaderboard_rounded,
                  iconColor: AppColors.accent,
                  bgColor: AppColors.accentLight,
                  title: 'Xếp hạng trong lớp',
                  subtitle: 'Thứ hạng tập trung của con',
                  onTap: () => Navigator.push(context,
                      MaterialPageRoute(
                          builder: (_) => const ClassRankingScreen())),
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
      return '${parts[0][0]}${parts[parts.length - 1][0]}'
          .toUpperCase();
    }
    return name.isNotEmpty ? name[0].toUpperCase() : '?';
  }
}

class _ProfileData {
  final ParentModel? parent;
  final List<StudentModel> students;
  final StudentStats? stats;
  _ProfileData(
      {required this.parent,
      required this.students,
      required this.stats});
}

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
              width: 140,
              child: Text(label, style: AppTextStyles.caption)),
          Expanded(child: Text(value, style: AppTextStyles.body2)),
        ],
      ),
    );
  }
}

class _QuickStat extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String label;
  final String value;
  const _QuickStat(
      {required this.icon,
      required this.color,
      required this.bgColor,
      required this.label,
      required this.value});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding:
            const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
            color: bgColor, borderRadius: BorderRadius.circular(10)),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 6),
            Text(value,
                style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: color)),
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

// ─── Profile menu card ─────────────────────────────────────────────────────────
class _ProfileMenuCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final Color bgColor;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ProfileMenuCard({
    required this.icon,
    required this.iconColor,
    required this.bgColor,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: const [
            BoxShadow(
                color: Color(0x0F000000),
                blurRadius: 6,
                offset: Offset(0, 2))
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                  color: bgColor, borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: iconColor, size: 22),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: AppTextStyles.heading3),
                  const SizedBox(height: 2),
                  Text(subtitle, style: AppTextStyles.caption),
                ],
              ),
            ),
            const Icon(Icons.chevron_right,
                color: AppColors.textSecondary, size: 20),
          ],
        ),
      ),
    );
  }
}
