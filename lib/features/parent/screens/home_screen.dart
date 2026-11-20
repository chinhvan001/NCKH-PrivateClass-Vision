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
  final List<String> _periods = ['Tuần này', 'Tháng này'];

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
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Môn ${item.subject}',
                              style: AppTextStyles.heading2,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'GV: ${item.teacherName} · $_selectedPeriod',
                              style: AppTextStyles.caption,
                            ),
                          ],
                        ),
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
                              'Chưa có dữ liệu tập trung từng ngày cho môn này',
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

                  // ── Student card (Đã tinh gọn, căn giữa Mức độ tập trung) ─
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: AppCard(
                      padding: const EdgeInsets.all(16),
                      child: Column(
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

                          const SizedBox(height: 16),
                          const Divider(height: 1, color: AppColors.divider),
                          const SizedBox(height: 18),

                          // ── KHỐI MỨC ĐỘ TẬP TRUNG CĂN GIỮA ────────────────
                          Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              SizedBox(
                                width: 92,
                                height: 92,
                                child: Stack(
                                  alignment: Alignment.center,
                                  children: [
                                    SizedBox(
                                      width: 92,
                                      height: 92,
                                      child: CircularProgressIndicator(
                                        value: stats.attentionPercent / 100,
                                        strokeWidth: 8,
                                        strokeCap: StrokeCap.round,
                                        backgroundColor: AppColors.accentLight,
                                        valueColor:
                                            const AlwaysStoppedAnimation<Color>(
                                          AppColors.primary,
                                        ),
                                      ),
                                    ),
                                    Column(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Text(
                                          '${stats.attentionPercent}%',
                                          style: const TextStyle(
                                            fontSize: 22,
                                            fontWeight: FontWeight.bold,
                                            color: AppColors.primary,
                                          ),
                                        ),
                                        const Text(
                                          'Tập trung',
                                          style: TextStyle(
                                            fontSize: 11,
                                            color: AppColors.textSecondary,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 10),
                              const Text(
                                'Mức độ tập trung trung bình',
                                style: TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.textPrimary,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(height: 16),

                          // ── Chỉ giữ 2 thẻ gọn: Đã tham gia & Vắng ─────────
                          Row(
                            children: [
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 10,
                                    horizontal: 12,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppColors.greenLight,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      const Icon(
                                        Icons.check_circle_rounded,
                                        color: AppColors.green,
                                        size: 18,
                                      ),
                                      const SizedBox(width: 6),
                                      Text(
                                        'Có mặt: ${stats.attended} buổi',
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.green,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 10,
                                    horizontal: 12,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppColors.redLight,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      const Icon(
                                        Icons.cancel_rounded,
                                        color: AppColors.red,
                                        size: 18,
                                      ),
                                      const SizedBox(width: 6),
                                      Text(
                                        'Vắng: ${stats.unexcusedAbsence} buổi',
                                        style: const TextStyle(
                                          fontSize: 13,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.red,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),

                  const SizedBox(height: 14),

                  // ── KHỐI MỨC ĐỘ TẬP TRUNG THEO MÔN (TUẦN / THÁNG) ─────────
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: FutureBuilder<OverviewStats>(
                      future: _overviewFuture,
                      builder: (context, ovSnapshot) {
                        final ovStats =
                            ovSnapshot.data ?? const OverviewStats();

                        return AppCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                mainAxisAlignment:
                                    MainAxisAlignment.spaceBetween,
                                children: [
                                  const Expanded(
                                    child: Text(
                                      'Mức độ tập trung theo môn',
                                      style: AppTextStyles.heading3,
                                    ),
                                  ),
                                  GestureDetector(
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        _slideRoute(
                                          _SubjectDetailListScreen(
                                            subjects: ovStats.subjects,
                                            periodLabel: _selectedPeriod,
                                            onSelectSubject: (item, color) =>
                                                _showSubjectDailyDetail(
                                              item,
                                              color,
                                            ),
                                          ),
                                        ),
                                      );
                                    },
                                    child: const Text(
                                      'Chi tiết >',
                                      style: AppTextStyles.linkText,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 12),

                              // Thanh chọn Tuần này / Tháng này
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
                                          horizontal: 16,
                                          vertical: 6,
                                        ),
                                        decoration: BoxDecoration(
                                          color: selected
                                              ? AppColors.primary
                                              : Colors.transparent,
                                          borderRadius:
                                              BorderRadius.circular(7),
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

                              if (ovSnapshot.connectionState ==
                                  ConnectionState.waiting)
                                const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 24),
                                  child: Center(
                                    child: CircularProgressIndicator(),
                                  ),
                                )
                              else if (ovStats.subjects.isEmpty)
                                const Padding(
                                  padding: EdgeInsets.symmetric(vertical: 16),
                                  child: Center(
                                    child: Text(
                                      'Chưa có dữ liệu môn học trong khoảng thời gian này',
                                      style: AppTextStyles.caption,
                                    ),
                                  ),
                                )
                              else
                                Column(
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
                                            vertical: 5,
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
                                ),
                            ],
                          ),
                        );
                      },
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

// ─── MÀN HÌNH CHI TIẾT TỪNG MÔN HỌC (BẤM "CHI TIẾT >") ──────────────────────
class _SubjectDetailListScreen extends StatelessWidget {
  final List<SubjectFocus> subjects;
  final String periodLabel;
  final void Function(SubjectFocus item, Color color) onSelectSubject;

  const _SubjectDetailListScreen({
    required this.subjects,
    required this.periodLabel,
    required this.onSelectSubject,
  });

  static const List<Color> _palette = [
    AppColors.primary,
    AppColors.green,
    AppColors.orange,
    AppColors.red,
    AppColors.accent,
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios,
            color: AppColors.textPrimary,
            size: 20,
          ),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          'Chi tiết môn học ($periodLabel)',
          style: AppTextStyles.heading2,
        ),
      ),
      body: subjects.isEmpty
          ? const Center(
              child: Text(
                'Chưa có dữ liệu môn học trong khoảng thời gian này',
                style: AppTextStyles.caption,
              ),
            )
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: subjects.length,
              separatorBuilder: (_, __) => const SizedBox(height: 12),
              itemBuilder: (context, index) {
                final item = subjects[index];
                final color = _palette[index % _palette.length];

                return InkWell(
                  onTap: () => onSelectSubject(item, color),
                  borderRadius: BorderRadius.circular(14),
                  child: AppCard(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Hàng 1: Tên môn + Badge % tập trung
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 10,
                                  height: 10,
                                  decoration: BoxDecoration(
                                    color: color,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  item.subject,
                                  style: AppTextStyles.heading3,
                                ),
                              ],
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 4,
                              ),
                              decoration: BoxDecoration(
                                color: color.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(20),
                              ),
                              child: Text(
                                'Tập trung: ${item.percent}%',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: color,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 6),

                        // Hàng 2: Giảng viên phụ trách
                        Row(
                          children: [
                            const Icon(
                              Icons.person_outline_rounded,
                              size: 16,
                              color: AppColors.textSecondary,
                            ),
                            const SizedBox(width: 6),
                            Text(
                              'GV phụ trách: ${item.teacherName}',
                              style: AppTextStyles.body2.copyWith(
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        // Thanh tiến độ tập trung
                        ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: LinearProgressIndicator(
                            value: item.percent / 100.0,
                            minHeight: 7,
                            backgroundColor: AppColors.backgroundGrey,
                            valueColor: AlwaysStoppedAnimation<Color>(color),
                          ),
                        ),
                        const SizedBox(height: 12),
                        const Divider(height: 1, color: AppColors.divider),
                        const SizedBox(height: 10),

                        // Hàng 3: Số tiết, có mặt, số tiết vắng
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            _MiniMetric(
                              label: 'Tổng số tiết',
                              value: '${item.totalSessions} tiết',
                              valueColor: AppColors.textPrimary,
                            ),
                            _MiniMetric(
                              label: 'Có mặt',
                              value: '${item.attendedSessions} tiết',
                              valueColor: AppColors.green,
                            ),
                            _MiniMetric(
                              label: 'Số tiết vắng',
                              value: '${item.absentSessions} tiết',
                              valueColor: AppColors.red,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}

class _MiniMetric extends StatelessWidget {
  final String label;
  final String value;
  final Color valueColor;

  const _MiniMetric({
    required this.label,
    required this.value,
    required this.valueColor,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: AppTextStyles.caption),
        const SizedBox(height: 2),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: valueColor,
          ),
        ),
      ],
    );
  }
}

// ─── Helpers ───────────────────────────────────────────────────────────────────
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