import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import 'session_detail_screen.dart';

class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});

  @override
  State<SessionHistoryScreen> createState() => _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  String _activeFilter = 'Tất cả';
  final List<String> _filters = ['Tất cả', 'Có mặt', 'Vắng', 'Đi muộn'];

  final List<Map<String, dynamic>> _sessions = [
    {
      'date': 'Thứ 6, 16/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Toán',
      'room': 'P.201',
      'percent': 85,
      'status': 'present',
    },
    {
      'date': 'Thứ 5, 15/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Toán',
      'room': 'P.201',
      'percent': 85,
      'status': 'present',
    },
    {
      'date': 'Thứ 4, 14/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Tiếng Việt',
      'room': 'P.101',
      'percent': 75,
      'status': 'present',
    },
    {
      'date': 'Thứ 3, 13/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Tiếng Anh',
      'room': 'P.203',
      'percent': 60,
      'status': 'late',
    },
    {
      'date': 'Thứ 2, 12/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Khoa học',
      'room': 'P.205',
      'percent': 80,
      'status': 'absent',
    },
    {
      'date': 'Thứ 6, 10/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Lịch sử',
      'room': 'P.102',
      'percent': 70,
      'status': 'present',
    },
    {
      'date': 'Thứ 5, 09/05/2024',
      'time': '11:00 - 12:30',
      'subject': 'Địa lý',
      'room': 'P.102',
      'percent': 70,
      'status': 'present',
    },
  ];

  List<Map<String, dynamic>> get _filteredSessions {
    if (_activeFilter == 'Tất cả') return _sessions;
    if (_activeFilter == 'Có mặt') {
      return _sessions.where((s) => s['status'] == 'present').toList();
    }
    if (_activeFilter == 'Vắng') {
      return _sessions.where((s) => s['status'] == 'absent').toList();
    }
    if (_activeFilter == 'Đi muộn') {
      return _sessions.where((s) => s['status'] == 'late').toList();
    }
    return _sessions;
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
                icon: const Icon(Icons.arrow_back_ios_new_rounded,
                    color: AppColors.textPrimary, size: 20),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: const Text('Lịch sử các buổi học',
            style: AppTextStyles.heading2),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.divider),
        ),
      ),
      body: Column(
        children: [
          // ── Filter chips ───────────────────────────────────────────────
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 12),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: _filters.map((f) {
                  final selected = f == _activeFilter;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: _FilterChip(
                      label: f,
                      selected: selected,
                      onTap: () => setState(() => _activeFilter = f),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // ── Session count ──────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
            child: Row(
              children: [
                const Icon(Icons.event_note_rounded,
                    size: 16, color: AppColors.textSecondary),
                const SizedBox(width: 6),
                Text(
                  '${_filteredSessions.length} buổi học',
                  style: AppTextStyles.caption,
                ),
              ],
            ),
          ),

          // ── List ───────────────────────────────────────────────────────
          Expanded(
            child: _filteredSessions.isEmpty
                ? const _EmptyState()
                : ListView.separated(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 20),
                    physics: const BouncingScrollPhysics(),
                    itemCount: _filteredSessions.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final s = _filteredSessions[index];
                      return _SessionCard(
                        session: s,
                        onTap: () => Navigator.push(
                          context,
                          _slideRoute(SessionDetailScreen(session: s)),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// ─── Slide route ────────────────────────────────────────────────────────────────
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

// ─── Animated filter chip ───────────────────────────────────────────────────────
class _FilterChip extends StatefulWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  State<_FilterChip> createState() => _FilterChipState();
}

class _FilterChipState extends State<_FilterChip>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 120));
    _scale = Tween(begin: 1.0, end: 0.92)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final selected = widget.selected;
    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 8),
          decoration: BoxDecoration(
            color: selected ? AppColors.primary : Colors.white,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(
              color: selected ? AppColors.primary : AppColors.divider,
              width: 1.5,
            ),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: AppColors.primary.withValues(alpha: 0.22),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ]
                : [],
          ),
          child: AnimatedDefaultTextStyle(
            duration: const Duration(milliseconds: 200),
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: selected ? Colors.white : AppColors.textSecondary,
            ),
            child: Text(widget.label),
          ),
        ),
      ),
    );
  }
}

// ─── Session card with tap animation ───────────────────────────────────────────
class _SessionCard extends StatefulWidget {
  final Map<String, dynamic> session;
  final VoidCallback onTap;

  const _SessionCard({required this.session, required this.onTap});

  @override
  State<_SessionCard> createState() => _SessionCardState();
}

class _SessionCardState extends State<_SessionCard>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 130));
    _scale = Tween(begin: 1.0, end: 0.97)
        .animate(CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'present': return AppColors.green;
      case 'absent': return AppColors.red;
      case 'late': return AppColors.orange;
      default: return AppColors.textSecondary;
    }
  }

  String _statusLabel(String s) {
    switch (s) {
      case 'present': return 'Có mặt';
      case 'absent': return 'Vắng';
      case 'late': return 'Đi muộn';
      default: return '';
    }
  }

  IconData _statusIcon(String s) {
    switch (s) {
      case 'present': return Icons.check_circle_rounded;
      case 'absent': return Icons.cancel_rounded;
      case 'late': return Icons.watch_later_rounded;
      default: return Icons.help_outline;
    }
  }

  Color _percentColor(int p) {
    if (p >= 80) return AppColors.green;
    if (p >= 60) return AppColors.orange;
    return AppColors.red;
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.session;
    final status = s['status'] as String;
    final percent = s['percent'] as int;
    final sColor = _statusColor(status);
    final pColor = _percentColor(percent);

    return GestureDetector(
      onTapDown: (_) => _ctrl.forward(),
      onTapUp: (_) {
        _ctrl.reverse();
        widget.onTap();
      },
      onTapCancel: () => _ctrl.reverse(),
      child: ScaleTransition(
        scale: _scale,
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
              // ── Progress circle ──────────────────────────────────────
              SizedBox(
                width: 56,
                height: 56,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    CircularProgressIndicator(
                      value: percent / 100,
                      strokeWidth: 5,
                      strokeCap: StrokeCap.round,
                      backgroundColor: AppColors.divider,
                      valueColor:
                          AlwaysStoppedAnimation<Color>(pColor),
                    ),
                    Text(
                      '$percent%',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                        color: pColor,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),

              // ── Info ─────────────────────────────────────────────────
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(s['date'] as String,
                        style: AppTextStyles.caption),
                    const SizedBox(height: 3),
                    Text(
                      '${s['time']} · ${s['subject']}',
                      style: AppTextStyles.body2.copyWith(
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Row(
                      children: [
                        const Icon(Icons.meeting_room_outlined,
                            size: 12,
                            color: AppColors.textSecondary),
                        const SizedBox(width: 3),
                        Text(s['room'] as String,
                            style: AppTextStyles.small),
                      ],
                    ),
                  ],
                ),
              ),

              // ── Status badge ─────────────────────────────────────────
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: sColor.withValues(alpha: 0.10),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(_statusIcon(status),
                            color: sColor, size: 13),
                        const SizedBox(width: 4),
                        Text(
                          _statusLabel(status),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: sColor,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Icon(Icons.chevron_right_rounded,
                      color: AppColors.textHint, size: 20),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Empty state ───────────────────────────────────────────────────────────────
class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.accentLight,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.event_busy_rounded,
                size: 44, color: AppColors.primary),
          ),
          const SizedBox(height: 14),
          const Text('Không có buổi học nào',
              style: AppTextStyles.heading3),
          const SizedBox(height: 6),
          const Text('Thử chọn bộ lọc khác',
              style: AppTextStyles.caption),
        ],
      ),
    );
  }
}
