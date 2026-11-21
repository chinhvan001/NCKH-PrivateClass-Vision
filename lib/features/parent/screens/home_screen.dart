import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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

  void _goHome() => setState(() => _currentIndex = 0);

  Widget _buildBody() {
    switch (_currentIndex) {
      case 0:
        return const _HomeContent();
      case 1:
        return const SessionHistoryScreen();
      case 2:
        return NotificationScreen(onBack: _goHome);
      case 3:
        return ProfileScreen(onBack: _goHome);
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

// ─── Hàm dùng chung ──────────────────────────────────────────────────────────
String _two(int v) => v.toString().padLeft(2, '0');
String _dm(DateTime d) => '${_two(d.day)}/${_two(d.month)}';

Color _levelColor(int p) {
  if (p >= 80) return AppColors.green;
  if (p >= 60) return AppColors.orange;
  return AppColors.red;
}

String _levelLabel(int p) {
  if (p >= 80) return 'Tốt';
  if (p >= 60) return 'Khá';
  return 'Cần chú ý';
}

/// Trung bình các buổi có mặt và đã có điểm (percent >= 0).
/// Trả về null nếu chưa có dữ liệu.
int? _avgPercent(Iterable<SubjectDailyFocus> records) {
  final values = records
      .where((r) => r.isPresent && r.percent >= 0)
      .map((r) => r.percent)
      .toList();
  if (values.isEmpty) return null;
  return (values.reduce((a, b) => a + b) / values.length).round();
}

DateTime? _parseDmy(String s) {
  final p = s.split('/');
  if (p.length != 3) return null;
  final d = int.tryParse(p[0]);
  final m = int.tryParse(p[1]);
  final y = int.tryParse(p[2]);
  if (d == null || m == null || y == null) return null;
  return DateTime(y, m, d);
}

class _TrendPoint {
  final DateTime? date;
  final String label;
  final int value;

  const _TrendPoint({
    required this.date,
    required this.label,
    required this.value,
  });
}

// ─── TRANG CHỦ: TỔNG QUAN ────────────────────────────────────────────────────
class _HomeContent extends StatefulWidget {
  const _HomeContent();

  @override
  State<_HomeContent> createState() => _HomeContentState();
}

class _HomeContentState extends State<_HomeContent> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  Future<OverviewStats>? _overviewFuture;
  String? _loadedKey;

  String _selectedPeriod = 'Tất cả';
  final List<String> _periods = const ['Tất cả', 'Tuần này', 'Tháng này'];

  /// null = tất cả môn
  String? _selectedSubject;

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
    _loadOverview();
  }

  @override
  void dispose() {
    _session.removeListener(_onSessionChanged);
    super.dispose();
  }

  String? _keyOf(LinkedChild? child) => child == null
      ? null
      : '${child.id}|${child.classes.map((c) => c.id).join(',')}';

  void _onSessionChanged() {
    if (!mounted) return;
    if (_keyOf(_session.selectedChild) != _loadedKey) {
      setState(() {
        _selectedSubject = null;
        _loadOverview();
      });
    }
  }

  void _loadOverview() {
    final child = _session.selectedChild;
    _loadedKey = _keyOf(child);
    _overviewFuture = child == null
        ? Future.value(const OverviewStats())
        : _parentService.getOverviewStats(
            studentId: child.id,
            classIds: child.classes.map((c) => c.id).toList(),
            period: _selectedPeriod,
          );
  }

  Future<void> _refresh() async {
    setState(_loadOverview);
    final f = _overviewFuture;
    if (f == null) return;
    try {
      await f;
    } catch (_) {
      // Lỗi đã hiển thị bởi FutureBuilder
    }
  }

  void _onPeriodChanged(String period) {
    if (_selectedPeriod == period) return;
    setState(() {
      _selectedPeriod = period;
      _loadOverview();
    });
  }

  String _periodRange() {
    final now = DateTime.now();
    final start = _selectedPeriod == 'Tuần này'
        ? DateTime(now.year, now.month, now.day - (now.weekday - 1))
        : DateTime(now.year, now.month, 1);
    return '${_dm(start)} – ${_dm(now)}';
  }

  // ── Giao diện ────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle.light,
      child: RefreshIndicator(
        onRefresh: _refresh,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeader(context),
              _buildBody(),
            ],
          ),
        ),
      ),
    );
  }

  // ── Header: thông tin học sinh + bộ lọc kỳ ───────────────────────────────
  Widget _buildHeader(BuildContext context) {
    final top = MediaQuery.of(context).padding.top;
    final dark = Color.lerp(AppColors.primary, Colors.black, 0.28)!;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.fromLTRB(16, top + 14, 16, 18),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.primary, dark],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: const BorderRadius.vertical(bottom: Radius.circular(28)),
      ),
      child: ListenableBuilder(
        listenable: _session,
        builder: (context, _) {
          final child = _session.selectedChild;
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  AvatarWidget(
                    name: child?.name ?? '',
                    size: 50,
                    bgColor: Colors.white,
                    textColor: AppColors.primary,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          child?.name ?? '',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Row(
                          children: [
                            Icon(
                              Icons.school_rounded,
                              size: 14,
                              color: Colors.white.withValues(alpha: 0.85),
                            ),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                child?.classDisplay ?? '',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: TextStyle(
                                  fontSize: 12.5,
                                  color: Colors.white.withValues(alpha: 0.85),
                                ),
                              ),
                            ),
                          ],
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
                          horizontal: 12,
                          vertical: 7,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.18),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: Colors.white.withValues(alpha: 0.3),
                          ),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Đổi',
                              style: TextStyle(
                                fontSize: 12.5,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                            SizedBox(width: 3),
                            Icon(
                              Icons.swap_horiz_rounded,
                              size: 16,
                              color: Colors.white,
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 18),
              _buildPeriodSelector(),
              const SizedBox(height: 8),
              Center(
                child: Text(
                  _selectedPeriod == 'Tất cả'
                      ? 'Thống kê mọi buổi đã giám sát đến ${_dm(DateTime.now())}'
                      : 'Thống kê từ ${_periodRange()}',
                  style: TextStyle(
                    fontSize: 11.5,
                    color: Colors.white.withValues(alpha: 0.75),
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildPeriodSelector() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.16),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: _periods.map((p) {
          final selected = p == _selectedPeriod;
          return Expanded(
            child: GestureDetector(
              onTap: () => _onPeriodChanged(p),
              behavior: HitTestBehavior.opaque,
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(vertical: 9),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: selected ? Colors.white : Colors.transparent,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Text(
                  p,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: selected ? AppColors.primary : Colors.white,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  // ── Nội dung theo dữ liệu ────────────────────────────────────────────────
  Widget _buildBody() {
    return FutureBuilder<OverviewStats>(
      future: _overviewFuture,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 60),
            child: Center(child: CircularProgressIndicator()),
          );
        }

        if (snap.hasError) {
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                const Icon(
                  Icons.cloud_off_rounded,
                  size: 44,
                  color: AppColors.textSecondary,
                ),
                const SizedBox(height: 10),
                const Text(
                  'Không tải được dữ liệu',
                  style: AppTextStyles.heading3,
                ),
                const SizedBox(height: 4),
                Text(
                  '${snap.error}',
                  style: AppTextStyles.caption,
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                OutlinedButton(onPressed: _refresh, child: const Text('Thử lại')),
              ],
            ),
          );
        }

        final subjects = (snap.data ?? const OverviewStats()).subjects;
        final String? selected =
            subjects.any((s) => s.subject == _selectedSubject)
                ? _selectedSubject
                : null;
        final shown = selected == null
            ? subjects
            : subjects.where((s) => s.subject == selected).toList();

        return Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildKpiGrid(shown),
              const SizedBox(height: 16),
              if (subjects.isNotEmpty) ...[
                _buildSubjectChips(subjects, selected),
                const SizedBox(height: 14),
              ],
              _buildTrendCard(shown, selected),
              const SizedBox(height: 18),
              Row(
                children: [
                  const Expanded(
                    child: Text('Môn học', style: AppTextStyles.heading3),
                  ),
                  Text('${shown.length} môn', style: AppTextStyles.caption),
                ],
              ),
              const SizedBox(height: 10),
              if (shown.isEmpty)
                AppCard(
                  child: Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      child: Text(
                        'Chưa có dữ liệu buổi học trong kỳ này',
                        style: AppTextStyles.caption,
                      ),
                    ),
                  ),
                )
              else
                ...shown.map(
                  (item) {
                    final color =
                        _palette[subjects.indexOf(item) % _palette.length];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _buildSubjectCard(item, color),
                    );
                  },
                ),
            ],
          ),
        );
      },
    );
  }

  // ── 4 thẻ KPI ────────────────────────────────────────────────────────────
  Widget _buildKpiGrid(List<SubjectFocus> shown) {
    final records = shown.expand((s) => s.dailyRecords).toList();
    final avg = _avgPercent(records);
    final attended = shown.fold<int>(0, (a, s) => a + s.attendedSessions);
    final absent = shown.fold<int>(0, (a, s) => a + s.absentSessions);
    final total = attended + absent;
    final rate = total > 0 ? (attended * 100 / total).round() : null;

    SubjectFocus? best;
    int bestAvg = -1;
    for (final s in shown) {
      final a = _avgPercent(s.dailyRecords);
      if (a != null && a > bestAvg) {
        best = s;
        bestAvg = a;
      }
    }

    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                icon: Icons.track_changes_rounded,
                color: avg != null ? _levelColor(avg) : AppColors.textSecondary,
                label: 'Tập trung trung bình',
                value: avg != null ? '$avg%' : '--',
                sub: avg != null ? _levelLabel(avg) : 'Chưa có dữ liệu',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _KpiCard(
                icon: Icons.emoji_events_rounded,
                color: AppColors.primary,
                label: 'Môn tập trung nhất',
                value: best != null ? best.subject : '--',
                sub: best != null ? '$bestAvg%' : 'Chưa có dữ liệu',
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _KpiCard(
                icon: Icons.check_circle_rounded,
                color: AppColors.green,
                label: 'Số buổi có mặt',
                value: '$attended',
                sub: 'trên $total buổi',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _KpiCard(
                icon: Icons.cancel_rounded,
                color: AppColors.red,
                label: 'Số buổi vắng',
                value: '$absent',
                sub: rate != null ? 'Chuyên cần $rate%' : 'Chưa có dữ liệu',
              ),
            ),
          ],
        ),
      ],
    );
  }

  // ── Chip lọc môn ─────────────────────────────────────────────────────────
  Widget _buildSubjectChips(List<SubjectFocus> subjects, String? selected) {
    final names = <String>['Tất cả môn', ...subjects.map((s) => s.subject)];
    return SizedBox(
      height: 36,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: names.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final isAll = i == 0;
          final name = names[i];
          final active = isAll ? selected == null : selected == name;
          return GestureDetector(
            onTap: () => setState(() => _selectedSubject = isAll ? null : name),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              padding: const EdgeInsets.symmetric(horizontal: 16),
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: active ? AppColors.primary : Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: active ? AppColors.primary : AppColors.divider,
                ),
              ),
              child: Text(
                name,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: active ? Colors.white : AppColors.textSecondary,
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  // ── Biểu đồ xu hướng ─────────────────────────────────────────────────────
  Widget _buildTrendCard(List<SubjectFocus> shown, String? selected) {
    final Map<String, List<int>> byDate = {};
    for (final s in shown) {
      for (final r in s.dailyRecords) {
        if (r.isPresent && r.percent >= 0) {
          byDate.putIfAbsent(r.date, () => []).add(r.percent);
        }
      }
    }

    final points = byDate.entries.map((e) {
      final d = _parseDmy(e.key);
      final v = (e.value.reduce((a, b) => a + b) / e.value.length).round();
      return _TrendPoint(
        date: d,
        label: d != null ? _dm(d) : e.key,
        value: v,
      );
    }).toList();

    points.sort((a, b) {
      final x = a.date;
      final y = b.date;
      if (x == null || y == null) return 0;
      return x.compareTo(y);
    });
    final visible =
        points.length > 14 ? points.sublist(points.length - 14) : points;

    return AppCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: AppColors.accentLight,
                  borderRadius: BorderRadius.circular(9),
                ),
                child: const Icon(
                  Icons.show_chart_rounded,
                  size: 18,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'Xu hướng tập trung',
                  style: AppTextStyles.heading3,
                ),
              ),
              Text(selected ?? 'Tất cả môn', style: AppTextStyles.caption),
            ],
          ),
          const SizedBox(height: 16),
          if (visible.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 28),
              child: Center(
                child: Text(
                  'Chưa có dữ liệu tập trung trong kỳ này',
                  style: AppTextStyles.caption,
                ),
              ),
            )
          else
            _TrendChart(points: visible),
        ],
      ),
    );
  }

  // ── Thẻ từng môn ─────────────────────────────────────────────────────────
  Widget _buildSubjectCard(SubjectFocus item, Color color) {
    final avg = _avgPercent(item.dailyRecords);
    final rate = item.totalSessions > 0
        ? (item.attendedSessions * 100 / item.totalSessions).round()
        : 0;
    final levelColor = avg != null ? _levelColor(avg) : AppColors.textSecondary;

    return AppCard(
      padding: const EdgeInsets.all(16),
      onTap: () => _showSubjectDailyDetail(item, color),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 42,
                height: 42,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: color.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  item.subject.isNotEmpty ? item.subject[0].toUpperCase() : '?',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    color: color,
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      item.subject,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTextStyles.heading3,
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(
                          Icons.person_outline_rounded,
                          size: 14,
                          color: AppColors.textSecondary,
                        ),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            item.teacherName,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: AppTextStyles.caption,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: levelColor.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  avg != null ? '$avg% · ${_levelLabel(avg)}' : 'Chưa có điểm',
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w700,
                    color: levelColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: (avg ?? 0) / 100.0,
              minHeight: 8,
              backgroundColor: AppColors.backgroundGrey,
              valueColor: AlwaysStoppedAnimation<Color>(levelColor),
            ),
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
            decoration: BoxDecoration(
              color: AppColors.backgroundGrey,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Expanded(
                  child: _MiniStat(
                    label: 'Có mặt',
                    value: '${item.attendedSessions}',
                    color: AppColors.green,
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    label: 'Vắng',
                    value: '${item.absentSessions}',
                    color: AppColors.red,
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    label: 'Chuyên cần',
                    value: '$rate%',
                    color: AppColors.primary,
                  ),
                ),
                const Icon(
                  Icons.chevron_right_rounded,
                  color: AppColors.textSecondary,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ── Chi tiết tập trung từng ngày của một môn ─────────────────────────────
  void _showSubjectDailyDetail(SubjectFocus item, Color color) {
    final avg = _avgPercent(item.dailyRecords);
    final records = [...item.dailyRecords];
    records.sort((a, b) {
      final x = _parseDmy(a.date);
      final y = _parseDmy(b.date);
      if (x == null || y == null) return 0;
      final c = y.compareTo(x);
      return c != 0 ? c : b.period.compareTo(a.period);
    });

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          minChildSize: 0.35,
          maxChildSize: 0.9,
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
                          avg != null ? 'TB: $avg%' : 'Chưa có điểm',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: color,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  const Divider(height: 1),
                  const SizedBox(height: 12),
                  Expanded(
                    child: records.isEmpty
                        ? const Center(
                            child: Text(
                              'Chưa có dữ liệu từng ngày cho môn này',
                              style: AppTextStyles.caption,
                            ),
                          )
                        : ListView.separated(
                            controller: scrollController,
                            itemCount: records.length,
                            separatorBuilder: (context, index) =>
                                const SizedBox(height: 10),
                            itemBuilder: (context, idx) {
                              final r = records[idx];
                              final has = r.percent >= 0;
                              final c = has
                                  ? _levelColor(r.percent)
                                  : AppColors.textSecondary;
                              return Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: AppColors.backgroundGrey,
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(
                                          Icons.calendar_today_rounded,
                                          size: 14,
                                          color: color,
                                        ),
                                        const SizedBox(width: 6),
                                        Expanded(
                                          child: Text(
                                            '${r.date} · Tiết ${r.period}',
                                            style: AppTextStyles.body2.copyWith(
                                              fontWeight: FontWeight.w600,
                                            ),
                                          ),
                                        ),
                                        Text(
                                          has ? '${r.percent}%' : '--',
                                          style: TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                            color: c,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 8),
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(6),
                                      child: LinearProgressIndicator(
                                        value: (r.percent < 0 ? 0 : r.percent) / 100.0,
                                        minHeight: 7,
                                        backgroundColor: Colors.white,
                                        valueColor:
                                            AlwaysStoppedAnimation<Color>(c),
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
}

// ─── Thẻ KPI ─────────────────────────────────────────────────────────────────
class _KpiCard extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final String value;
  final String sub;

  const _KpiCard({
    required this.icon,
    required this.color,
    required this.label,
    required this.value,
    required this.sub,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0F000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.13),
              borderRadius: BorderRadius.circular(11),
            ),
            child: Icon(icon, size: 20, color: color),
          ),
          const SizedBox(height: 12),
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTextStyles.caption,
          ),
          const SizedBox(height: 3),
          Text(
            sub,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Biểu đồ cột xu hướng tập trung ──────────────────────────────────────────
class _TrendChart extends StatelessWidget {
  final List<_TrendPoint> points;

  const _TrendChart({required this.points});

  static const double _barArea = 96;

  Widget _bar(_TrendPoint p) {
    final color = _levelColor(p.value);
    final h = (_barArea * p.value / 100).clamp(6.0, _barArea).toDouble();
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Text(
          '${p.value}',
          style: TextStyle(
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            color: color,
          ),
        ),
        const SizedBox(height: 4),
        Container(
          width: 18,
          height: h,
          decoration: BoxDecoration(
            color: color,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          p.label,
          style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final few = points.length <= 8;
    final bars = points
        .map<Widget>(
          (p) => few
              ? Expanded(child: _bar(p))
              : SizedBox(width: 44, child: _bar(p)),
        )
        .toList();

    return SizedBox(
      height: _barArea + 54,
      child: few
          ? Row(crossAxisAlignment: CrossAxisAlignment.end, children: bars)
          : SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: bars,
              ),
            ),
    );
  }
}

// ─── Chỉ số nhỏ trong thẻ môn ────────────────────────────────────────────────
class _MiniStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;

  const _MiniStat({
    required this.label,
    required this.value,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w800,
            color: color,
          ),
        ),
        const SizedBox(height: 2),
        Text(label, style: AppTextStyles.caption),
      ],
    );
  }
}

// ─── Hiệu ứng nhấn nút ───────────────────────────────────────────────────────
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
