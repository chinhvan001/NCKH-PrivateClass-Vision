import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/bottom_nav_bar.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

import 'session_history_screen.dart';
import 'notification_screen.dart';
import 'profile_screen.dart';
import 'daily_overview_screen.dart';
import 'switch_account_screen.dart';
import 'no_child_screen.dart';

class HomeScreen extends StatefulWidget {
  final String uid;
  final String? email;

  const HomeScreen({super.key, required this.uid, this.email});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final ParentSession _session = ParentSession.instance;

  @override
  void initState() {
    super.initState();
    _session.attach(widget.uid, email: widget.email);
  }

  @override
  void dispose() {
    _session.detach();
    super.dispose();
  }

  Widget _buildBody() {
    switch (_currentIndex) {
      case 0:
        return const _HomeContent();
      case 1:
        return const SessionHistoryScreen();
      case 2:
        return const NotificationScreen();
      case 3:
        return const ProfileScreen();
      default:
        return const _HomeContent();
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _session,
      builder: (context, _) {
        if (_session.isLoading) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (!_session.hasChildren) {
          return NoChildScreen(
            errorMessage: _session.error,
            onRetry: _session.reload,
          );
        }

        return Scaffold(
          backgroundColor: AppColors.backgroundGrey,
          body: _buildBody(),
          bottomNavigationBar: AppBottomNavBar(
            currentIndex: _currentIndex,
            onTap: (i) => setState(() => _currentIndex = i),
          ),
        );
      },
    );
  }
}

// ─── Home content (Tích hợp trực tiếp Mức độ tập trung theo môn) ─────────────
class _HomeContent extends StatefulWidget {
  const _HomeContent();

  @override
  State<_HomeContent> createState() => _HomeContentState();
}

class _HomeContentState extends State<_HomeContent> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  Future<HomeStats>? _statsFuture;
  Future<OverviewStats>? _overviewFuture;
  String? _loadedKey;

  String _selectedPeriod = 'Tuần này';
  final List<String> _periods = ['Hôm nay', 'Tuần này', 'Tháng này'];

  static const List<Color> _palette = [
    AppColors.primary,
    AppColors.green,
    AppColors.orange,
    AppColors.red,
    AppColors.accent,
  ];

  @override
  void initState() {
    super.initState();
    _session.addListener(_onSessionChanged);
    _loadAllData();
  }

  @override
  void dispose() {
    _session.removeListener(_onSessionChanged);
    super.dispose();
  }

  String? _keyOf(LinkedChild? child) =>
      child == null ? null : '${child.id}|${child.classes.map((c) => c.id).join(',')}';

  void _onSessionChanged() {
    if (!mounted) return;
    if (_keyOf(_session.selectedChild) != _loadedKey) {
      _loadAllData();
    }
  }

  void _loadAllData() {
    final child = _session.selectedChild;
    _loadedKey = _keyOf(child);
    if (child != null) {
      final classIds = child.classes.map((c) => c.id).toList();
      setState(() {
        _statsFuture = _parentService.getHomeStats(
          studentId: child.id,
          classIds: classIds,
        );
        _overviewFuture = _parentService.getOverviewStats(
          studentId: child.id,
          classIds: classIds,
          period: _selectedPeriod,
        );
      });
    } else {
      setState(() {
        _statsFuture = Future.value(const HomeStats());
        _overviewFuture = Future.value(const OverviewStats());
      });
    }
  }

  void _onPeriodChanged(String period) {
    if (_selectedPeriod == period) return;
    setState(() {
      _selectedPeriod = period;
    });
    final child = _session.selectedChild;
    if (child != null) {
      setState(() {
        _overviewFuture = _parentService.getOverviewStats(
          studentId: child.id,
          classIds: child.classes.map((c) => c.id).toList(),
          period: _selectedPeriod,
        );
      });
    }
  }

  /// Mở bảng chi tiết độ tập trung từng ngày của môn học được chọn
  void _showSubjectDailyDetail(SubjectFocus item, Color color) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.55,
          minChildSize: 0.35,
          maxChildSize: 0.85,
          expand: false,
          builder: (_, scrollController) {
            return Padding(
              padding: const EdgeInsets.fromLTRB(20, 12, 20, 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Center(
                    child: Container(
                      width: 40,
                      height: 4,
                      decoration: BoxDecoration(
                        color: AppColors.divider,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Môn ${item.subject}',
                            style: AppTextStyles.heading2,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Chi tiết tập trung từng ngày ($_selectedPeriod)',
                            style: AppTextStyles.caption,
                          ),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          'TB: ${item.percent}%',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  Expanded(
                    child: item.dailyRecords.isEmpty
                        ? const Center(
                            child: Text(
                              'Chưa có dữ liệu từng ngày cho môn này',
                              style: AppTextStyles.caption,
                            ),
                          )
                        : ListView.separated(
                            controller: scrollController,
                            itemCount: item.dailyRecords.length,
                            separatorBuilder: (_, __) =>
                                const SizedBox(height: 10),
                            itemBuilder: (context, idx) {
                              final record = item.dailyRecords[idx];
                              return Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppColors.backgroundGrey,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      mainAxisAlignment:
                                          MainAxisAlignment.spaceBetween,
                                      children: [
                                        Row(
                                          children: [
                                            Icon(
                                              Icons.calendar_today_rounded,
                                              size: 14,
                                              color: color,
                                            ),
                                            const SizedBox(width: 6),
                                            Text(
                                              '${record.date} · Tiết ${record.period}',
                                              style: AppTextStyles.body2.copyWith(
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ],
                                        ),
                                        Text(
                                          '${record.percent}%',
                                          style: TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                            color: color,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(6),
                                      child: LinearProgressIndicator(
                                        value: record.percent / 100.0,
                                        minHeight: 7,
                                        backgroundColor: Colors.white,
                                        valueColor:
                                            AlwaysStoppedAnimation<Color>(color),
                                      ),
                                    ),
                                  ],
                                ),
                              );
                            },
                          ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<HomeStats>(
      future: _statsFuture,
      builder: (context, snapshot) {
        final stats = snapshot.data ?? const HomeStats();

        return SafeArea(
          child: RefreshIndicator(
            onRefresh: () async => _loadAllData(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // ── Header bar ─────────────────────────────────────────────
                  Container(
                    color: Colors.white,
                    padding: const EdgeInsets.fromLTRB(16, 14, 8, 14),
                    child: Row(
                      children: [
                        const Expanded(
                          child: Text('Lớp học của con', style: AppTextStyles.heading2),
                        ),
                        _IconBadgeButton(
                          icon: Icons.notifications_none_rounded,
                          activeIcon: Icons.notifications_rounded,
                          count: stats.notificationCount,
                          onTap: () {
                            final state = context.findAncestorStateOfType<_HomeScreenState>();
                            if (state != null) {
                              state.setState(() => state._currentIndex = 2);
                            }
                          },
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),

                  // ── Student card ───────────────────────────────────────────
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: AppCard(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          ListenableBuilder(
                            listenable: _session,
                            builder: (context, _) {
                              final child = _session.selectedChild;
                              return Row(
                                children: [
                                  AvatarWidget(name: child?.name ?? '', size: 46),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          child?.name ?? '',
                                          style: AppTextStyles.heading3,
                                        ),
                                        const SizedBox(height: 2),
                                        Text(
                                          child?.classDisplay ?? '',
                                          style: AppTextStyles.caption,
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (_session.children.length > 1)
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
                                          horizontal: 10,
                                          vertical: 6,
                                        ),
                                        decoration: BoxDecoration(
                                          color: AppColors.accentLight,
                                          borderRadius: BorderRadius.circular(20),
                                        ),
                                        child: const Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              'Đổi',
                                              style: TextStyle(
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600,
                                                color: AppColors.primary,
                                              ),
                                            ),
                                            SizedBox(width: 2),
                                            Icon(
                                              Icons.swap_horiz_rounded,
                                              color: AppColors.primary,
                                              size: 16,
                                            ),
                                          ],
                                        ),
                                      ),
                                    ),
                                ],
                              );
                            },
                          ),

                          const SizedBox(height: 12),

                          // Banner trạng thái học tập
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 9,
                            ),
                            decoration: BoxDecoration(
                              color: AppColors.accentLight,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              children: [
                                const Icon(
                                  Icons.trending_up_rounded,
                                  color: AppColors.primary,
                                  size: 18,
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: ListenableBuilder(
                                    listenable: _session,
                                    builder: (context, _) {
                                      final child = _session.selectedChild;
                                      final displayName = child != null && child.name.trim().isNotEmpty
                                          ? child.name.trim().split(' ').last
                                          : 'con';
                                      return Text(
                                        stats.attended > 0
                                            ? 'Điểm danh đạt ${stats.attendancePercent}% số buổi trong kỳ.'
                                            : 'Bé $displayName có ${stats.unexcusedAbsence} buổi vắng cần lưu ý.',
                                        style: AppTextStyles.caption.copyWith(
                                          color: AppColors.primary,
                                        ),
                                      );
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),
                          const Divider(height: 1, color: AppColors.divider),
                          const SizedBox(height: 16),

                          // ── Stats row ──────────────────────────────────────
                          IntrinsicHeight(
                            child: Row(
                              children: [
                                _StatBlock(
                                  icon: Icons.access_time_rounded,
                                  iconColor: AppColors.primary,
                                  value: stats.nextSessionTime,
                                  label: 'Lịch buổi tới',
                                ),
                                const _VertDivider(),
                                _StatBlock(
                                  icon: Icons.psychology_rounded,
                                  iconColor: AppColors.primary,
                                  value: '${stats.attentionPercent}%',
                                  label: 'Tập trung TB',
                                  valueColor: AppColors.primary,
                                ),
                                const _VertDivider(),
                                _StatBlock(
                                  icon: Icons.fact_check_rounded,
                                  iconColor: AppColors.green,
                                  value: stats.attendanceDisplay,
                                  label: 'Điểm danh',
                                  valueColor: AppColors.green,
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),

                          // ── Progress circles ───────────────────────────────
                          Row(
                            children: [
                              Expanded(
                                child: _FocusCard(
                                  icon: Icons.psychology_rounded,
                                  iconColor: AppColors.primary,
                                  bgColor: AppColors.accentLight,
                                  label: 'Tập trung',
                                  percent: stats.attentionPercent,
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
                                  percent: stats.attendancePercent,
                                  color: AppColors.green,
                                  centerText: stats.attendanceDisplay,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 14),

                          // ── Attendance badges ──────────────────────────────
                          Row(
                            children: [
                              _AttendanceBadge(
                                icon: Icons.check_circle_rounded,
                                color: AppColors.green,
                                bgColor: AppColors.greenLight,
                                label: 'Có phép',
                                value: '${stats.excusedAbsence} buổi',
                              ),
                              const SizedBox(width: 8),
                              _AttendanceBadge(
                                icon: Icons.cancel_rounded,
                                color: AppColors.red,
                                bgColor: AppColors.redLight,
                                label: 'Không phép',
                                value: '${stats.unexcusedAbsence} buổi',
                              ),
                              const SizedBox(width: 8),
                              _AttendanceBadge(
                                icon: Icons.watch_later_rounded,
                                color: AppColors.orange,
                                bgColor: AppColors.orangeLight,
                                label: 'Đi muộn',
                                value: '${stats.lateCount} buổi',
                              ),
                            ],
                          ),

                          const SizedBox(height: 14),

                          // ── View history button ─────────────────────────────
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

                  const SizedBox(height: 14),

                  // ── KHỐI MỨC ĐỘ TẬP TRUNG THEO MÔN (CHẠM XEM TỪNG NGÀY) ──
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: AppCard(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Expanded(
                                child: Text(
                                  'Mức độ tập trung theo môn',
                                  style: AppTextStyles.heading3,
                                ),
                              ),
                              GestureDetector(
                                onTap: () => Navigator.push(
                                  context,
                                  _slideRoute(const DailyOverviewScreen()),
                                ),
                                child: const Text(
                                  'Chi tiết >',
                                  style: AppTextStyles.linkText,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),

                          // Thanh chọn Hôm nay / Tuần này / Tháng này
                          Container(
                            padding: const EdgeInsets.all(3),
                            decoration: BoxDecoration(
                              color: AppColors.backgroundGrey,
                              borderRadius: BorderRadius.circular(9),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: _periods.map((p) {
                                final selected = p == _selectedPeriod;
                                return GestureDetector(
                                  onTap: () => _onPeriodChanged(p),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 14,
                                      vertical: 6,
                                    ),
                                    decoration: BoxDecoration(
                                      color: selected
                                          ? AppColors.primary
                                          : Colors.transparent,
                                      borderRadius: BorderRadius.circular(7),
                                    ),
                                    child: Text(
                                      p,
                                      style: TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: selected
                                            ? Colors.white
                                            : AppColors.textSecondary,
                                      ),
                                    ),
                                  ),
                                );
                              }).toList(),
                            ),
                          ),
                          const SizedBox(height: 14),

                          FutureBuilder<OverviewStats>(
                            future: _overviewFuture,
                            builder: (context, ovSnapshot) {
                              if (ovSnapshot.connectionState ==
                                  ConnectionState.waiting) {
                                return const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 20),
                                  child: Center(
                                    child: CircularProgressIndicator(),
                                  ),
                                );
                              }

                              final ovStats =
                                  ovSnapshot.data ?? const OverviewStats();

                              if (ovStats.subjects.isEmpty) {
                                return const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 16),
                                  child: Center(
                                    child: Text(
                                      'Chưa có dữ liệu tập trung trong khoảng thời gian này',
                                      style: AppTextStyles.caption,
                                    ),
                                  ),
                                );
                              }

                              return Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Chạm vào môn học để xem độ tập trung từng ngày',
                                    style: AppTextStyles.caption,
                                  ),
                                  const SizedBox(height: 10),
                                  ...ovStats.subjects
                                      .asMap()
                                      .entries
                                      .map((entry) {
                                    final index = entry.key;
                                    final item = entry.value;
                                    final color =
                                        _palette[index % _palette.length];
                                    return InkWell(
                                      onTap: () => _showSubjectDailyDetail(
                                        item,
                                        color,
                                      ),
                                      borderRadius: BorderRadius.circular(8),
                                      child: Padding(
                                        padding: const EdgeInsets.symmetric(
                                          vertical: 4,
                                        ),
                                        child: Row(
                                          children: [
                                            Expanded(
                                              child: SubjectProgressBar(
                                                subject: item.subject,
                                                percent: item.percent,
                                                color: color,
                                              ),
                                            ),
                                            const SizedBox(width: 6),
                                            const Icon(
                                              Icons.chevron_right_rounded,
                                              size: 20,
                                              color: AppColors.textSecondary,
                                            ),
                                          ],
                                        ),
                                      ),
                                    );
                                  }),
                                ],
                              );
                            },
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
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
      vsync: this,
      duration: const Duration(milliseconds: 140),
    );
    _scale = Tween(
      begin: 1.0,
      end: 0.95,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
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
      vsync: this,
      duration: const Duration(milliseconds: 150),
    );
    _scale = Tween(
      begin: 1.0,
      end: 0.96,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
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
      vsync: this,
      duration: const Duration(milliseconds: 130),
    );
    _scale = Tween(
      begin: 1.0,
      end: 0.82,
    ).animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
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
              child: Icon(widget.icon, color: AppColors.textPrimary, size: 24),
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
    return Container(width: 1, height: 44, color: AppColors.divider);
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
              Text(
                label,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: iconColor,
                ),
              ),
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
            Text(
              label,
              style: AppTextStyles.small,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}