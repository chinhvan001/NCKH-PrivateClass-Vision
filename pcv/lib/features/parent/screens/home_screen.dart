import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/common_widgets.dart';
import '../models/student_model.dart';
import '../models/attendance_summary_model.dart';
import '../services/student_service.dart';
import '../services/session_service.dart';
import '../services/notification_service.dart';
import '../services/subject_focus_service.dart';
import '../services/schedule_service.dart';
import '../services/child_service.dart';
import '../services/attendance_detail_service.dart';
import 'session_history_screen.dart';
import 'notification_screen.dart';
import 'profile_screen.dart';
import 'daily_overview_screen.dart';
import 'switch_account_screen.dart';
import 'upcoming_schedule_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  static const String _studentId = 'student_minh_anh';

  // ── Seed tất cả data mẫu 1 lần ──────────────────────────────────────────
  Future<void> _seedAll() async {
    try {
      await Future.wait([
        StudentService().seedSampleData(),
        SessionService().seedSampleData(_studentId),
        NotificationService().seedSampleData(_studentId),
        SubjectFocusService().seedSampleData(_studentId),
        ScheduleService().seedSampleData(_studentId),
        ChildService().seedSampleData('parent_001'),
        AttendanceDetailService().seedSampleData(_studentId),
      ]);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Seed data thành công!'),
            backgroundColor: AppColors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Lỗi seed: $e'),
            backgroundColor: AppColors.red,
          ),
        );
      }
    }
  }

  final List<Widget> _screens = const [
    _HomeContent(),
    SessionHistoryScreen(),
    NotificationScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      body: AnimatedSwitcher(
        duration: const Duration(milliseconds: 220),
        switchInCurve: Curves.easeOut,
        switchOutCurve: Curves.easeIn,
        child: KeyedSubtree(
          key: ValueKey(_currentIndex),
          child: _screens[_currentIndex],
        ),
      ),
      // TODO: xóa floatingActionButton sau khi seed xong
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _seedAll,
        backgroundColor: AppColors.primary,
        icon: const Icon(Icons.cloud_upload_rounded, color: Colors.white),
        label: const Text('Seed Data',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
      ),
      bottomNavigationBar: AppBottomNavBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
      ),
    );
  }
}

// ─── Home content ──────────────────────────────────────────────────────────────
class _HomeContent extends StatefulWidget {
  const _HomeContent();

  @override
  State<_HomeContent> createState() => _HomeContentState();
}

class _HomeContentState extends State<_HomeContent> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';

  final _studentService = StudentService();
  final _sessionService = SessionService();

  late Future<_HomeData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_HomeData> _loadData() async {
    final results = await Future.wait([
      _studentService.getStudentById(_studentId),
      _sessionService.getAttendanceSummary(_studentId),
    ]);
    return _HomeData(
      student: results[0] as StudentModel?,
      summary: results[1] as AttendanceSummaryModel,
    );
  }

  void _reload() => setState(() => _dataFuture = _loadData());

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<_HomeData>(
      future: _dataFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(
            child: CircularProgressIndicator(color: AppColors.primary),
          );
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
                    snapshot.error.toString().replaceFirst('Exception: ', ''),
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
        final student = data.student;
        final summary = data.summary;

        return SafeArea(
          child: SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Header bar ──────────────────────────────────────────────
                Container(
                  color: Colors.white,
                  padding: const EdgeInsets.fromLTRB(16, 14, 8, 14),
                  child: Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: const [
                            Text('Lớp học của con',
                                style: AppTextStyles.heading2),
                          ],
                        ),
                      ),
                      _IconBadgeButton(
                        icon: Icons.notifications_none_rounded,
                        activeIcon: Icons.notifications_rounded,
                        count: 3,
                        onTap: () {},
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 12),

                // ── Student card ─────────────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: AppCard(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Student info + switch account
                        Row(
                          children: [
                            AvatarWidget(
                                name: student?.name ?? '?', size: 46),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    student?.name ?? '---',
                                    style: AppTextStyles.heading3,
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    student != null
                                        ? '${student.className} · ${student.schoolName}'
                                        : '---',
                                    style: AppTextStyles.caption,
                                  ),
                                ],
                              ),
                            ),
                            _TapScaleWidget(
                              onTap: () {
                                showModalBottomSheet(
                                  context: context,
                                  isScrollControlled: true,
                                  backgroundColor: Colors.transparent,
                                  builder: (_) => const SwitchAccountScreen(),
                                );
                              },
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 10, vertical: 6),
                                decoration: BoxDecoration(
                                  color: AppColors.accentLight,
                                  borderRadius: BorderRadius.circular(20),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: const [
                                    Text('Đổi',
                                        style: TextStyle(
                                          fontSize: 12,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.primary,
                                        )),
                                    SizedBox(width: 2),
                                    Icon(Icons.swap_horiz_rounded,
                                        color: AppColors.primary, size: 16),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 12),

                        // Info banner
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 12, vertical: 9),
                          decoration: BoxDecoration(
                            color: AppColors.accentLight,
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.trending_up_rounded,
                                  color: AppColors.primary, size: 18),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  student != null
                                      ? 'Mức độ tập trung trung bình: ${student.avgFocusPercent}%'
                                      : 'Đang tải...',
                                  style: AppTextStyles.caption
                                      .copyWith(color: AppColors.primary),
                                ),
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),
                        const Divider(height: 1, color: AppColors.divider),
                        const SizedBox(height: 16),

                        // ── Stats row ────────────────────────────────────────
                        IntrinsicHeight(
                          child: Row(
                            children: [
                              _StatBlock(
                                icon: Icons.access_time_rounded,
                                iconColor: AppColors.primary,
                                value: student?.nextSessionTime ?? '--:--',
                                label: 'Lịch buổi tới',
                              ),
                              const _VertDivider(),
                              _StatBlock(
                                icon: Icons.psychology_rounded,
                                iconColor: AppColors.primary,
                                value: '${summary.avgFocusPercent}%',
                                label: 'Tập trung TB',
                                valueColor: AppColors.primary,
                              ),
                              const _VertDivider(),
                              _StatBlock(
                                icon: Icons.fact_check_rounded,
                                iconColor: AppColors.green,
                                value: summary.attendanceLabel,
                                label: 'Điểm danh',
                                valueColor: AppColors.green,
                              ),
                            ],
                          ),
                        ),

                        const SizedBox(height: 16),

                        // ── Progress circles ─────────────────────────────────
                        Row(
                          children: [
                            Expanded(
                              child: _FocusCard(
                                icon: Icons.psychology_rounded,
                                iconColor: AppColors.primary,
                                bgColor: AppColors.accentLight,
                                label: 'Tập trung',
                                percent: summary.avgFocusPercent,
                                color: AppColors.primary,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: _FocusCard(
                                icon: Icons.how_to_reg_rounded,
                                iconColor: AppColors.green,
                                bgColor: AppColors.greenLight,
                                label: 'Điểm danh',
                                percent:
                                    (summary.attendanceRate * 100).round(),
                                color: AppColors.green,
                                centerText: summary.attendanceLabel,
                              ),
                            ),
                          ],
                        ),

                        const SizedBox(height: 14),

                        // ── Attendance badges ────────────────────────────────
                        Row(
                          children: [
                            _AttendanceBadge(
                              icon: Icons.check_circle_rounded,
                              color: AppColors.green,
                              bgColor: AppColors.greenLight,
                              label: 'Có phép',
                              value: '${summary.excusedSessions} buổi',
                            ),
                            const SizedBox(width: 8),
                            _AttendanceBadge(
                              icon: Icons.cancel_rounded,
                              color: AppColors.red,
                              bgColor: AppColors.redLight,
                              label: 'Không phép',
                              value: '${summary.absentSessions} buổi',
                            ),
                            const SizedBox(width: 8),
                            _AttendanceBadge(
                              icon: Icons.watch_later_rounded,
                              color: AppColors.orange,
                              bgColor: AppColors.orangeLight,
                              label: 'Đi muộn',
                              value: '${summary.lateSessions} buổi',
                            ),
                          ],
                        ),

                        const SizedBox(height: 14),

                        // ── View history button ──────────────────────────────
                        _AnimatedButton(
                          label: 'Xem lịch sử các buổi học',
                          icon: Icons.history_rounded,
                          onTap: () => Navigator.push(
                            context,
                            _slideRoute(const SessionHistoryScreen()),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 12),

                // ── Daily overview card ──────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: _TapScaleWidget(
                    onTap: () => Navigator.push(
                      context,
                      _slideRoute(const DailyOverviewScreen()),
                    ),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AppColors.primary, AppColors.primaryLight],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: [
                          BoxShadow(
                            color: AppColors.primary.withValues(alpha: 0.28),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.18),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.bar_chart_rounded,
                                color: Colors.white, size: 26),
                          ),
                          const SizedBox(width: 14),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Tổng quan trong ngày',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.white,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'Tập trung & điểm danh chi tiết',
                                  style: TextStyle(
                                      fontSize: 12, color: Colors.white70),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: Colors.white.withValues(alpha: 0.18),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.arrow_forward_rounded,
                                color: Colors.white, size: 18),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 20),

                // ── Lịch học sắp tới card ────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: _TapScaleWidget(
                    onTap: () => Navigator.push(
                      context,
                      _slideRoute(const UpcomingScheduleScreen()),
                    ),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(14),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0x0F000000),
                            blurRadius: 8,
                            offset: Offset(0, 2),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.greenLight,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: const Icon(Icons.calendar_month_rounded,
                                color: AppColors.green, size: 26),
                          ),
                          const SizedBox(width: 14),
                          const Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  'Lịch học sắp tới',
                                  style: TextStyle(
                                    fontSize: 15,
                                    fontWeight: FontWeight.bold,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                SizedBox(height: 3),
                                Text(
                                  'Xem các buổi học sắp diễn ra',
                                  style: TextStyle(
                                      fontSize: 12,
                                      color: AppColors.textSecondary),
                                ),
                              ],
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.all(6),
                            decoration: BoxDecoration(
                              color: AppColors.greenLight,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.arrow_forward_rounded,
                                color: AppColors.green, size: 18),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }
}

// ─── Data holder ───────────────────────────────────────────────────────────────
class _HomeData {
  final StudentModel? student;
  final AttendanceSummaryModel summary;
  _HomeData({required this.student, required this.summary});
}

// ─── Slide page route helper ───────────────────────────────────────────────────
Route<void> _slideRoute(Widget page) {
  return PageRouteBuilder(
    pageBuilder: (_, __, ___) => page,
    transitionsBuilder: (_, anim, __, child) => SlideTransition(
      position: Tween(
        begin: const Offset(1, 0),
        end: Offset.zero,
      ).animate(CurvedAnimation(parent: anim, curve: Curves.easeOutCubic)),
      child: child,
    ),
    transitionDuration: const Duration(milliseconds: 280),
  );
}

// ─── Tap-scale wrapper ─────────────────────────────────────────────────────────
class _TapScaleWidget extends StatefulWidget {
  final Widget child;
  final VoidCallback onTap;

  const _TapScaleWidget({required this.child, required this.onTap});

  @override
  State<_TapScaleWidget> createState() => _TapScaleWidgetState();
}

class _TapScaleWidgetState extends State<_TapScaleWidget>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 140));
    _scale = Tween(begin: 1.0, end: 0.95)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(scale: _scale, child: widget.child),
    );
  }
}

// ─── Animated primary button ───────────────────────────────────────────────────
class _AnimatedButton extends StatefulWidget {
  final String label;
  final IconData icon;
  final VoidCallback onTap;

  const _AnimatedButton({
    required this.label,
    required this.icon,
    required this.onTap,
  });

  @override
  State<_AnimatedButton> createState() => _AnimatedButtonState();
}

class _AnimatedButtonState extends State<_AnimatedButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;
  late final Animation<Color?> _color;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 150));
    _scale = Tween(begin: 1.0, end: 0.96)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
    _color = ColorTween(
      begin: Colors.transparent,
      end: AppColors.primary.withValues(alpha: 0.08),
    ).animate(_ctrl);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: AnimatedBuilder(
          animation: _color,
          builder: (_, child) => Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: _color.value,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.primary, width: 1.5),
            ),
            child: child,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(widget.icon, color: AppColors.primary, size: 18),
              const SizedBox(width: 8),
              Text(
                widget.label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.primary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Icon badge button ─────────────────────────────────────────────────────────
class _IconBadgeButton extends StatefulWidget {
  final IconData icon;
  final IconData activeIcon;
  final int count;
  final VoidCallback onTap;

  const _IconBadgeButton({
    required this.icon,
    required this.activeIcon,
    required this.count,
    required this.onTap,
  });

  @override
  State<_IconBadgeButton> createState() => _IconBadgeButtonState();
}

class _IconBadgeButtonState extends State<_IconBadgeButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 130));
    _scale = Tween(begin: 1.0, end: 0.82)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: Stack(
          clipBehavior: Clip.none,
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: const BoxDecoration(
                color: AppColors.backgroundGrey,
                shape: BoxShape.circle,
              ),
              child: Icon(widget.icon,
                  color: AppColors.textPrimary, size: 24),
            ),
            if (widget.count > 0)
              Positioned(
                right: 0,
                top: 0,
                child: Container(
                  width: 17,
                  height: 17,
                  decoration: const BoxDecoration(
                    color: AppColors.red,
                    shape: BoxShape.circle,
                  ),
                  child: Center(
                    child: Text(
                      '${widget.count}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 9,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ─── Stat block ────────────────────────────────────────────────────────────────
class _StatBlock extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final String value;
  final String label;
  final Color? valueColor;

  const _StatBlock({
    required this.icon,
    required this.iconColor,
    required this.value,
    required this.label,
    this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: iconColor, size: 20),
          const SizedBox(height: 4),
          Text(
            value,
            style: TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.bold,
              color: valueColor ?? AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(label, style: AppTextStyles.small),
        ],
      ),
    );
  }
}

class _VertDivider extends StatelessWidget {
  const _VertDivider();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 44,
      color: AppColors.divider,
    );
  }
}

// ─── Focus mini-card ───────────────────────────────────────────────────────────
class _FocusCard extends StatelessWidget {
  final IconData icon;
  final Color iconColor;
  final Color bgColor;
  final String label;
  final int percent;
  final Color color;
  final String? centerText;

  const _FocusCard({
    required this.icon,
    required this.iconColor,
    required this.bgColor,
    required this.label,
    required this.percent,
    required this.color,
    this.centerText,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 48,
            height: 48,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: percent / 100,
                  strokeWidth: 5,
                  strokeCap: StrokeCap.round,
                  backgroundColor: Colors.white.withValues(alpha: 0.6),
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                ),
                Text(
                  centerText ?? '$percent%',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: iconColor, size: 18),
              const SizedBox(height: 3),
              Text(label,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: iconColor,
                  )),
            ],
          ),
        ],
      ),
    );
  }
}

// ─── Attendance badge ──────────────────────────────────────────────────────────
class _AttendanceBadge extends StatelessWidget {
  final IconData icon;
  final Color color;
  final Color bgColor;
  final String label;
  final String value;

  const _AttendanceBadge({
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
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        decoration: BoxDecoration(
          color: bgColor,
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 20),
            const SizedBox(height: 4),
            Text(
              value,
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: color,
              ),
            ),
            const SizedBox(height: 2),
            Text(label,
                style: AppTextStyles.small,
                textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}
