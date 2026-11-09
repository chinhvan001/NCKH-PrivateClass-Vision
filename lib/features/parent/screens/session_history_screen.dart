import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

// ─── Màu & hằng số dùng riêng cho lịch tuần ─────────────────────────────────
const Color _kYellow = Color(0xFFFFE08A);
const Color _kYellowBorder = Color(0xFFF2B705);
const Color _kYellowText = Color(0xFF7A5600);

const List<String> _kWeekdayShort = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
const List<String> _kWeekdayLong = [
  'Thứ 2',
  'Thứ 3',
  'Thứ 4',
  'Thứ 5',
  'Thứ 6',
  'Thứ 7',
  'Chủ nhật',
];

String _two(int v) => v.toString().padLeft(2, '0');

/// Thứ 2 của tuần chứa ngày [d]
DateTime _mondayOf(DateTime d) =>
    DateTime(d.year, d.month, d.day - (d.weekday - 1));

String _slotKey(DateTime date, int period) =>
    '${date.year}-${_two(date.month)}-${_two(date.day)}#$period';

String _timeOf(DateTime? d) =>
    d == null ? 'Chưa cập nhật' : '${_two(d.hour)}:${_two(d.minute)}';

String _orNA(String v) => v.trim().isEmpty ? 'Chưa cập nhật' : v.trim();

/// Lịch học theo tuần của con đang chọn (dữ liệu thật từ collection sessions)
class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});

  @override
  State<SessionHistoryScreen> createState() => _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  static const double _periodColWidth = 30;
  static const double _cellHeight = 54;

  final ParentService _service = ParentService();
  final ParentSession _session = ParentSession.instance;

  DateTime _weekStart = _mondayOf(DateTime.now());
  Map<String, StudentSession> _index = const {};
  bool _loading = true;
  String? _error;
  String? _loadedKey;
  int _token = 0;
  Timer? _ticker;

  @override
  void initState() {
    super.initState();
    _session.addListener(_onSessionChanged);
    _fetch();
    // Mỗi phút cập nhật lại để ô đổi màu khi tiết học trôi qua
    _ticker = Timer.periodic(const Duration(minutes: 1), (_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _ticker?.cancel();
    _session.removeListener(_onSessionChanged);
    super.dispose();
  }

  String? _keyOf(LinkedChild? child) => child == null
      ? null
      : '${child.id}|${child.classes.map((c) => c.id).join(',')}';

  /// Đổi con (hoặc danh sách lớp của con thay đổi) thì tải lại lịch
  void _onSessionChanged() {
    if (!mounted) return;
    if (_keyOf(_session.selectedChild) != _loadedKey) _fetch();
  }

  Future<void> _fetch({bool silent = false}) async {
    final child = _session.selectedChild;
    _loadedKey = _keyOf(child);
    final token = ++_token;

    if (child == null) {
      await Future<void>.value();
      if (!mounted || token != _token) return;
      setState(() {
        _index = const {};
        _loading = false;
        _error = null;
      });
      return;
    }

    if (!silent && (!_loading || _error != null)) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }

    try {
      final list = await _service.getSessionsForStudent(
        studentId: child.id,
        classes: child.classes,
      );
      if (!mounted || token != _token) return;
      setState(() {
        _index = {for (final s in list) _slotKey(s.date, s.period): s};
        _loading = false;
        _error = null;
      });
    } catch (e) {
      if (!mounted || token != _token) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  // ── Điều hướng tuần ──────────────────────────────────────────────────────
  void _shiftWeek(int weeks) {
    setState(() {
      _weekStart = DateTime(
        _weekStart.year,
        _weekStart.month,
        _weekStart.day + 7 * weeks,
      );
    });
  }

  void _goToday() => setState(() => _weekStart = _mondayOf(DateTime.now()));

  bool get _isCurrentWeek => _weekStart == _mondayOf(DateTime.now());

  void _showDetail(StudentSession s) {
    showDialog<void>(
      context: context,
      builder: (_) => _SessionDetailDialog(session: s),
    );
  }

  // ── Giao diện ────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Navigator.canPop(context)
            ? IconButton(
                icon: const Icon(
                  Icons.arrow_back_ios_new_rounded,
                  color: AppColors.textPrimary,
                  size: 20,
                ),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: const Text(
          'Lịch sử các buổi học',
          style: AppTextStyles.heading2,
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.divider),
        ),
      ),
      body: ListenableBuilder(
        listenable: _session,
        builder: (context, _) {
          final child = _session.selectedChild;
          if (child == null) {
            return const Center(child: Text('Chưa có thông tin học sinh'));
          }
          return Column(
            children: [
              _buildWeekBar(child),
              if (_loading)
                const LinearProgressIndicator(minHeight: 2)
              else
                const SizedBox(height: 2),
              Expanded(
                child: _error != null
                    ? _buildError()
                    : RefreshIndicator(
                        onRefresh: () => _fetch(silent: true),
                        child: _buildGrid(),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildWeekBar(LinkedChild child) {
    final end = DateTime(_weekStart.year, _weekStart.month, _weekStart.day + 6);
    final range =
        '${_two(_weekStart.day)}/${_two(_weekStart.month)} - ${_two(end.day)}/${_two(end.month)}/${end.year}';
    final monthLabel = _weekStart.month == end.month
        ? 'Tháng ${end.month}/${end.year}'
        : 'Tháng ${_weekStart.month}/${_weekStart.year} - ${end.month}/${end.year}';

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(8, 6, 8, 10),
      child: Column(
        children: [
          Text(
            'Lịch học của ${child.name}',
            style: AppTextStyles.caption,
            overflow: TextOverflow.ellipsis,
          ),
          Row(
            children: [
              IconButton(
                tooltip: 'Tuần trước',
                onPressed: () => _shiftWeek(-1),
                icon: const Icon(Icons.chevron_left_rounded, size: 28),
                color: AppColors.textPrimary,
              ),
              Expanded(
                child: Column(
                  children: [
                    Text(range, style: AppTextStyles.heading3),
                    const SizedBox(height: 2),
                    Text(
                      _isCurrentWeek ? '$monthLabel · Tuần này' : monthLabel,
                      style: AppTextStyles.caption,
                    ),
                  ],
                ),
              ),
              IconButton(
                tooltip: 'Tuần sau',
                onPressed: () => _shiftWeek(1),
                icon: const Icon(Icons.chevron_right_rounded, size: 28),
                color: AppColors.textPrimary,
              ),
            ],
          ),
          if (!_isCurrentWeek)
            TextButton.icon(
              onPressed: _goToday,
              icon: const Icon(Icons.today_rounded, size: 16),
              label: const Text('Về tuần này'),
            ),
          const SizedBox(height: 4),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _LegendDot(
                color: AppColors.accentLight,
                border: AppColors.primary,
                label: 'Có mặt',
              ),
              const SizedBox(width: 14),
              _LegendDot(color: _kYellow, border: _kYellowBorder, label: 'Vắng'),
              const SizedBox(width: 14),
              _LegendDot(
                color: Colors.white,
                border: AppColors.divider,
                label: 'Chưa diễn ra',
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 60),
        const Icon(
          Icons.cloud_off_rounded,
          size: 44,
          color: AppColors.textSecondary,
        ),
        const SizedBox(height: 12),
        const Text(
          'Không tải được lịch học',
          style: AppTextStyles.heading3,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 6),
        Text(
          '$_error',
          style: AppTextStyles.caption,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        Center(
          child: OutlinedButton(
            onPressed: () => _fetch(),
            child: const Text('Thử lại'),
          ),
        ),
      ],
    );
  }

  Widget _buildGrid() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final days = List<DateTime>.generate(
      7,
      (i) => DateTime(_weekStart.year, _weekStart.month, _weekStart.day + i),
    );

    return LayoutBuilder(
      builder: (context, constraints) {
        const outerPad = 8.0;
        const cardPad = 6.0;
        final colW =
            (constraints.maxWidth - outerPad * 2 - cardPad * 2 - _periodColWidth) /
                7;

        return SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(outerPad, 12, outerPad, 20),
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(cardPad),
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
                child: Column(
                  children: [
                    _buildDayHeader(days, today, colW),
                    const SizedBox(height: 6),
                    _sectionLabel('Sáng'),
                    for (var p = 1; p <= 5; p++)
                      _buildPeriodRow(p, days, colW, now),
                    _sectionLabel('Chiều'),
                    for (var p = 6; p <= 10; p++)
                      _buildPeriodRow(p, days, colW, now),
                  ],
                ),
              ),
              if (!_loading && _index.isEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 16),
                  child: Text(
                    'Chưa có buổi học nào được ghi nhận',
                    style: AppTextStyles.caption,
                  ),
                ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildDayHeader(List<DateTime> days, DateTime today, double colW) {
    return Row(
      children: [
        const SizedBox(width: _periodColWidth),
        for (var i = 0; i < 7; i++)
          SizedBox(
            width: colW,
            child: _DayHeaderCell(
              label: _kWeekdayShort[i],
              day: days[i].day,
              isToday: days[i] == today,
            ),
          ),
      ],
    );
  }

  Widget _sectionLabel(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(
            text,
            style: AppTextStyles.small.copyWith(
              fontWeight: FontWeight.w700,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(width: 8),
          const Expanded(child: Divider(height: 1, color: AppColors.divider)),
        ],
      ),
    );
  }

  Widget _buildPeriodRow(
    int period,
    List<DateTime> days,
    double colW,
    DateTime now,
  ) {
    return Row(
      children: [
        SizedBox(
          width: _periodColWidth,
          height: _cellHeight,
          child: Center(
            child: Text(
              '$period',
              style: AppTextStyles.caption.copyWith(fontWeight: FontWeight.w700),
            ),
          ),
        ),
        for (final d in days)
          SizedBox(
            width: colW,
            height: _cellHeight,
            child: Padding(
              padding: const EdgeInsets.all(2),
              child: _buildCell(_index[_slotKey(d, period)], now),
            ),
          ),
      ],
    );
  }

  Widget _buildCell(StudentSession? s, DateTime now) {
    // Ô không có tiết học
    if (s == null) {
      return Container(
        decoration: BoxDecoration(
          color: AppColors.backgroundGrey,
          borderRadius: BorderRadius.circular(8),
        ),
      );
    }

    final state = s.stateAt(now);
    final Color bg;
    final Color border;
    final Color fg;
    if (state == SessionState.upcoming) {
      // Chưa diễn ra: màu trắng
      bg = Colors.white;
      border = AppColors.divider;
      fg = AppColors.textPrimary;
    } else if (state == SessionState.ongoing) {
      // Đang diễn ra: trắng, viền xanh
      bg = Colors.white;
      border = AppColors.primary;
      fg = AppColors.primary;
    } else if (s.isAbsentAt(now)) {
      // Vắng: màu vàng
      bg = _kYellow;
      border = _kYellowBorder;
      fg = _kYellowText;
    } else {
      bg = AppColors.accentLight;
      border = AppColors.primary.withValues(alpha: 0.35);
      fg = AppColors.primary;
    }

    return Material(
      color: bg,
      borderRadius: BorderRadius.circular(8),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _showDetail(s),
        child: Container(
          alignment: Alignment.center,
          padding: const EdgeInsets.symmetric(horizontal: 1),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: border,
              width: state == SessionState.ongoing ? 1.5 : 1,
            ),
          ),
          child: Text(
            s.subject,
            textAlign: TextAlign.center,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 10,
              height: 1.15,
              fontWeight: FontWeight.w600,
              color: fg,
            ),
          ),
        ),
      ),
    );
  }
}

// ─── Tiêu đề cột ngày ───────────────────────────────────────────────────────
class _DayHeaderCell extends StatelessWidget {
  final String label;
  final int day;
  final bool isToday;

  const _DayHeaderCell({
    required this.label,
    required this.day,
    required this.isToday,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: isToday ? AppColors.primary : AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 3),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
          decoration: BoxDecoration(
            color: isToday ? AppColors.primary : Colors.transparent,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Text(
            _two(day),
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: isToday ? Colors.white : AppColors.textPrimary,
            ),
          ),
        ),
      ],
    );
  }
}

// ─── Chú thích màu ──────────────────────────────────────────────────────────
class _LegendDot extends StatelessWidget {
  final Color color;
  final Color border;
  final String label;

  const _LegendDot({
    required this.color,
    required this.border,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(3),
            border: Border.all(color: border),
          ),
        ),
        const SizedBox(width: 4),
        Text(label, style: AppTextStyles.small),
      ],
    );
  }
}

// ─── Card chi tiết một tiết học ─────────────────────────────────────────────
class _SessionDetailDialog extends StatelessWidget {
  final StudentSession session;

  const _SessionDetailDialog({required this.session});

  @override
  Widget build(BuildContext context) {
    final s = session;
    final now = DateTime.now();
    final state = s.stateAt(now);
    final absent = s.isAbsentAt(now);

    final String statusLabel;
    final Color statusColor;
    final Color statusBg;
    if (state == SessionState.upcoming) {
      statusLabel = 'Chưa diễn ra';
      statusColor = AppColors.textSecondary;
      statusBg = AppColors.backgroundGrey;
    } else if (state == SessionState.ongoing) {
      statusLabel = 'Đang diễn ra';
      statusColor = AppColors.primary;
      statusBg = AppColors.accentLight;
    } else if (absent) {
      statusLabel = 'Vắng mặt';
      statusColor = _kYellowText;
      statusBg = _kYellow;
    } else {
      statusLabel = 'Có mặt';
      statusColor = AppColors.green;
      statusBg = AppColors.greenLight;
    }

    final dateText =
        '${_kWeekdayLong[s.date.weekday - 1]}, ${_two(s.date.day)}/${_two(s.date.month)}/${s.date.year}';

    return Dialog(
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.accentLight,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.menu_book_rounded,
                    color: AppColors.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(s.subject, style: AppTextStyles.heading2),
                      const SizedBox(height: 2),
                      Text(dateText, style: AppTextStyles.caption),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                  color: AppColors.textSecondary,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: statusBg,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                statusLabel,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color: statusColor,
                ),
              ),
            ),
            const SizedBox(height: 14),
            const Divider(height: 1, color: AppColors.divider),
            const SizedBox(height: 14),
            _InfoRow(
              icon: Icons.menu_book_outlined,
              label: 'Môn học',
              value: _orNA(s.subject),
            ),
            _InfoRow(
              icon: Icons.format_list_numbered_rounded,
              label: 'Tiết',
              value: 'Tiết ${s.period} (${s.period <= 5 ? 'Sáng' : 'Chiều'})',
            ),
            _InfoRow(
              icon: Icons.play_circle_outline_rounded,
              label: 'Bắt đầu',
              value: _timeOf(s.startTime),
            ),
            _InfoRow(
              icon: Icons.stop_circle_outlined,
              label: 'Kết thúc',
              value: _timeOf(s.endTime),
            ),
            _InfoRow(
              icon: Icons.groups_outlined,
              label: 'Lớp',
              value: _orNA(s.className),
            ),
            _InfoRow(
              icon: Icons.meeting_room_outlined,
              label: 'Phòng',
              value: _orNA(s.room),
            ),
            _InfoRow(
              icon: Icons.person_outline_rounded,
              label: 'Giáo viên',
              value: _orNA(s.teacherName),
            ),
            const SizedBox(height: 4),
            const Divider(height: 1, color: AppColors.divider),
            const SizedBox(height: 14),
            _buildFocus(absent),
            const SizedBox(height: 18),
            SizedBox(
              width: double.infinity,
              height: 46,
              child: ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Đóng', style: AppTextStyles.buttonText),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFocus(bool absent) {
    final score = session.attentionScore;

    if (session.isPresent && score != null) {
      final int p = score.round().clamp(0, 100).toInt();
      final Color color = p >= 80
          ? AppColors.green
          : (p >= 60 ? AppColors.orange : AppColors.red);
      final String label = p >= 80
          ? 'Tốt'
          : (p >= 60 ? 'Khá' : 'Cần cải thiện');

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.track_changes_rounded, size: 18, color: color),
              const SizedBox(width: 8),
              const Expanded(
                child: Text('Chỉ số tập trung', style: AppTextStyles.heading3),
              ),
              Text(
                '$p%',
                style: TextStyle(
                  fontSize: 22,
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
              value: p / 100,
              minHeight: 8,
              backgroundColor: AppColors.divider,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      );
    }

    return Row(
      children: [
        const Icon(
          Icons.track_changes_rounded,
          size: 18,
          color: AppColors.textSecondary,
        ),
        const SizedBox(width: 8),
        const Text('Chỉ số tập trung', style: AppTextStyles.heading3),
        const Spacer(),
        Text(
          absent ? 'Vắng mặt, không có dữ liệu' : 'Chưa có dữ liệu',
          style: AppTextStyles.caption,
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: AppColors.textSecondary),
          const SizedBox(width: 8),
          SizedBox(width: 78, child: Text(label, style: AppTextStyles.caption)),
          Expanded(child: Text(value, style: AppTextStyles.body2)),
        ],
      ),
    );
  }
}
