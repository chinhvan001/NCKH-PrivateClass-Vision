import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  String _activeTab = 'Tất cả';
  final List<String> _tabs = ['Tất cả', 'Thông báo', 'Nhắc nhở'];

  Future<List<ParentNotification>> _future = Future.value(const []);
  String? _loadedKey;

  @override
  void initState() {
    super.initState();
    _session.addListener(_onSessionChanged);
    _load();
  }

  @override
  void dispose() {
    _session.removeListener(_onSessionChanged);
    super.dispose();
  }

  /// Khóa nhận diện "học sinh + các lớp" đang được tải
  String? _keyOf(LinkedChild? child) =>
      child == null ? null : '${child.id}|${child.classes.map((c) => c.id).join(',')}';

  /// Đổi con (hoặc danh sách lớp của con thay đổi) thì tự tải lại
  void _onSessionChanged() {
    if (!mounted) return;
    if (_keyOf(_session.selectedChild) != _loadedKey) {
      setState(_load);
    }
  }

  void _load() {
    final child = _session.selectedChild;
    _loadedKey = _keyOf(child);
    _future = child == null
        ? Future.value(const <ParentNotification>[])
        : _parentService.getNotificationsForStudent(
            studentId: child.id,
            classIds: child.classes.map((c) => c.id).toList(),
          );
  }

  Future<void> _refresh() async {
    setState(_load);
    try {
      await _future;
    } catch (_) {
      // Lỗi đã được hiển thị bởi FutureBuilder
    }
  }

  // ── Định dạng ────────────────────────────────────────────────────────────
  static const _weekdays = [
    'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật',
  ];

  String _two(int v) => v.toString().padLeft(2, '0');

  String _dateText(DateTime d) =>
      '${_weekdays[d.weekday - 1]}, ${_two(d.day)}/${_two(d.month)}/${d.year}';

  String _timeText(DateTime d) => '${_two(d.hour)}:${_two(d.minute)}';

  String _timeRange(ParentNotification n) {
    final s = n.startTime;
    final e = n.endTime;
    if (s != null && e != null) return '${_timeText(s)} - ${_timeText(e)}';
    if (s != null) return _timeText(s);
    if (e != null) return _timeText(e);
    return '';
  }

  String _formatTimeAgo(DateTime timestamp) {
    final diff = DateTime.now().difference(timestamp);
    if (diff.inMinutes < 1) return 'Vừa xong';
    if (diff.inMinutes < 60) return '${diff.inMinutes} phút trước';
    if (diff.inHours < 24) return '${diff.inHours} giờ trước';
    if (diff.inDays == 1) return 'Hôm qua';
    if (diff.inDays < 7) return '${diff.inDays} ngày trước';
    if (diff.inDays < 30) return '${diff.inDays ~/ 7} tuần trước';
    if (diff.inDays < 365) return '${diff.inDays ~/ 30} tháng trước';
    return '${diff.inDays ~/ 365} năm trước';
  }

  String _categoryTab(NotificationType type) =>
      type == NotificationType.absence ? 'Thông báo' : 'Nhắc nhở';

  // ── Giao diện ────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: _session,
      builder: (context, _) {
        final child = _session.selectedChild;
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
              onPressed: () =>
                  Navigator.canPop(context) ? Navigator.pop(context) : null,
            ),
            title: const Text('Thông báo', style: AppTextStyles.heading2),
          ),
          body: Column(
            children: [
              _buildTabs(child),
              Expanded(
                child: child == null
                    ? const Center(child: Text('Chưa có thông tin học sinh'))
                    : RefreshIndicator(
                        onRefresh: _refresh,
                        child: _buildList(),
                      ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTabs(LinkedChild? child) {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (child != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  const Icon(
                    Icons.child_care_rounded,
                    size: 16,
                    color: AppColors.textSecondary,
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      'Thông báo của ${child.name}',
                      style: AppTextStyles.caption,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
            ),
          Row(
            children: _tabs.map((t) {
              final selected = t == _activeTab;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: GestureDetector(
                  onTap: () => setState(() => _activeTab = t),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 7,
                    ),
                    decoration: BoxDecoration(
                      color: selected ? AppColors.primary : Colors.white,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: selected ? AppColors.primary : AppColors.divider,
                      ),
                    ),
                    child: Text(
                      t,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w500,
                        color: selected ? Colors.white : AppColors.textSecondary,
                      ),
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildList() {
    return FutureBuilder<List<ParentNotification>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 80),
              const Icon(
                Icons.cloud_off_rounded,
                size: 44,
                color: AppColors.textSecondary,
              ),
              const SizedBox(height: 12),
              const Text(
                'Không tải được thông báo',
                style: AppTextStyles.heading3,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              Text(
                '${snapshot.error}',
                style: AppTextStyles.caption,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Center(
                child: OutlinedButton(
                  onPressed: _refresh,
                  child: const Text('Thử lại'),
                ),
              ),
            ],
          );
        }

        final all = snapshot.data ?? const <ParentNotification>[];
        final items = all
            .where((n) => _activeTab == 'Tất cả' || _categoryTab(n.type) == _activeTab)
            .toList();

        if (items.isEmpty) {
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            children: const [
              SizedBox(height: 100),
              Center(
                child: Text('Chưa có thông báo nào', style: AppTextStyles.caption),
              ),
            ],
          );
        }

        return ListView.separated(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          itemCount: items.length,
          separatorBuilder: (_, _a) => const SizedBox(height: 12),
          itemBuilder: (context, i) => _buildCard(items[i]),
        );
      },
    );
  }

  Widget _buildCard(ParentNotification n) {
    final isAbsence = n.type == NotificationType.absence;
    final accent = isAbsence ? AppColors.red : AppColors.orange;
    final accentBg = isAbsence ? AppColors.redLight : AppColors.orangeLight;
    final title = isAbsence ? 'Cảnh báo vắng mặt không phép' : 'Nhắc nhở từ giáo viên';
    final icon = isAbsence ? Icons.event_busy_rounded : Icons.edit_note_rounded;

    final lines = <Widget>[
      if (n.startTime != null || n.endTime != null)
        _InfoLine(
          icon: Icons.calendar_today_rounded,
          text: _dateText((n.startTime ?? n.endTime)!),
        ),
      if (_timeRange(n).isNotEmpty || n.period != null)
        _InfoLine(
          icon: Icons.access_time_rounded,
          text: [
            if (n.period != null) 'Tiết ${n.period}',
            if (_timeRange(n).isNotEmpty) _timeRange(n),
          ].join(' · '),
        ),
      _InfoLine(icon: Icons.menu_book_rounded, text: 'Môn ${n.subject}'),
      if (!isAbsence && n.teacherName.isNotEmpty)
        _InfoLine(
          icon: Icons.person_outline_rounded,
          text: 'Giáo viên ${n.teacherName}',
        ),
    ];

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(color: accentBg, shape: BoxShape.circle),
                child: Icon(icon, color: accent, size: 22),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTextStyles.heading3.copyWith(color: accent),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isAbsence
                          ? 'Bé vắng mặt trong buổi học này.'
                          : 'Giáo viên để lại lời nhắn cho buổi học.',
                      style: AppTextStyles.caption,
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: AppColors.backgroundGrey,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                for (var i = 0; i < lines.length; i++) ...[
                  if (i > 0) const SizedBox(height: 6),
                  lines[i],
                ],
              ],
            ),
          ),
          if (!isAbsence) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: accentBg,
                borderRadius: BorderRadius.circular(10),
                border: Border(left: BorderSide(color: accent, width: 3)),
              ),
              child: Text(
                n.note,
                style: AppTextStyles.body2.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: [
              const Icon(
                Icons.schedule_rounded,
                size: 13,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 4),
              Text(_formatTimeAgo(n.timestamp), style: AppTextStyles.small),
            ],
          ),
        ],
      ),
    );
  }
}

class _InfoLine extends StatelessWidget {
  final IconData icon;
  final String text;

  const _InfoLine({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 15, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        Expanded(child: Text(text, style: AppTextStyles.body2)),
      ],
    );
  }
}
