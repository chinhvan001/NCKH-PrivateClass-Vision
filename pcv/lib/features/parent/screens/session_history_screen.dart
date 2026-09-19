import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/supervised_student_model.dart';
import '../models/monitoring_session_model.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';
import 'session_detail_screen.dart';

class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});

  @override
  State<SessionHistoryScreen> createState() =>
      _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  String _activeFilter = 'Tất cả';
  final List<String> _filters = [
    'Tất cả',
    'Có mặt',
    'Vắng',
    'Tập trung'
  ];

  late Future<List<_SessionRow>> _sessionsFuture;

  @override
  void initState() {
    super.initState();
    _sessionsFuture = _loadData();
  }

  Future<List<_SessionRow>> _loadData() async {
    final students =
    await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) return [];
    final student = students.first;

    final supervised = await _monitoringService
        .getSupervisedDataByStudent(student.id);
    if (supervised.isEmpty) return [];

    final rows = <_SessionRow>[];
    for (final s in supervised) {
      MonitoringSessionModel? sessionModel;
      if (s.monitoringSessionId.isNotEmpty) {
        try {
          final doc = await FirebaseFirestore.instance
              .collection('monitoring_sessions')
              .doc(s.monitoringSessionId)
              .get();
          if (doc.exists) {
            sessionModel = MonitoringSessionModel.fromFirestore(doc);
          }
        } catch (_) {}
      }
      rows.add(_SessionRow(supervised: s, session: sessionModel));
    }
    return rows;
  }

  void _reload() {
    setState(() {
      _sessionsFuture = _loadData();
    });
  }

  List<_SessionRow> _applyFilter(List<_SessionRow> all) {
    switch (_activeFilter) {
      case 'Có mặt':
        return all.where((r) => r.supervised.isPresent).toList();
      case 'Vắng':
        return all.where((r) => !r.supervised.isPresent).toList();
      case 'Tập trung':
        return all.where((r) => r.supervised.isAttention).toList();
      default:
        return all;
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
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        )
            : null,
        title: const Text('Lịch sử buổi học',
            style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1),
          child: Container(height: 1, color: AppColors.divider),
        ),
      ),
      body: FutureBuilder<List<_SessionRow>>(
        future: _sessionsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(
                    color: AppColors.primary));
          }
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
                          shape: BoxShape.circle),
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
                      icon: const Icon(Icons.refresh_rounded,
                          size: 18),
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

          final all = snapshot.data ?? [];
          final filtered = _applyFilter(all);

          return Column(
            children: [
              // ── Filter chips ────────────────────────────────────
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
                        child: GestureDetector(
                          onTap: () =>
                              setState(() => _activeFilter = f),
                          child: AnimatedContainer(
                            duration:
                            const Duration(milliseconds: 200),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 18, vertical: 8),
                            decoration: BoxDecoration(
                              color: selected
                                  ? AppColors.primary
                                  : Colors.white,
                              borderRadius:
                              BorderRadius.circular(22),
                              border: Border.all(
                                color: selected
                                    ? AppColors.primary
                                    : AppColors.divider,
                                width: 1.5,
                              ),
                            ),
                            child: Text(f,
                                style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w600,
                                    color: selected
                                        ? Colors.white
                                        : AppColors.textSecondary)),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ),
              ),

              // ── Count ─────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                child: Row(
                  children: [
                    const Icon(Icons.event_note_rounded,
                        size: 16,
                        color: AppColors.textSecondary),
                    const SizedBox(width: 6),
                    Text('${filtered.length} buổi học',
                        style: AppTextStyles.caption),
                  ],
                ),
              ),

              // ── List ───────────────────────────────────────────────
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: const BoxDecoration(
                            color: AppColors.accentLight,
                            shape: BoxShape.circle),
                        child: const Icon(
                            Icons.event_busy_rounded,
                            size: 44,
                            color: AppColors.primary),
                      ),
                      const SizedBox(height: 14),
                      const Text('Không có buổi học nào',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 6),
                      const Text('Thử chọn bộ lọc khác',
                          style: AppTextStyles.caption),
                    ],
                  ),
                )
                    : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(
                      16, 8, 16, 20),
                  physics: const BouncingScrollPhysics(),
                  itemCount: filtered.length,
                  separatorBuilder: (_, __) =>
                  const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final row = filtered[index];
                    return _SessionCard(
                      row: row,
                      onTap: () => Navigator.push(
                        context,
                        _slideRoute(SessionDetailScreen(
                          session: {
                            'attentionScore': row
                                .supervised.attentionScore,
                            'attentionPercent': row
                                .supervised.attentionPercent,
                            'isPresent':
                            row.supervised.isPresent,
                            'isAttention':
                            row.supervised.isAttention,
                            'row': row.supervised.row,
                            'column': row.supervised.column,
                            'note': row.supervised.note,
                            'avgAttentionScore': row
                                .session
                                ?.avgAttentionScore ??
                                0.0,
                            'presentStudents': row
                                .session
                                ?.presentStudents ??
                                0,
                            'sessionNote':
                            row.session?.note ?? '',
                          },
                        )),
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

Route<void> _slideRoute(Widget page) {
  return PageRouteBuilder(
    pageBuilder: (_, __, ___) => page,
    transitionsBuilder: (_, anim, __, child) => SlideTransition(
      position: Tween(begin: const Offset(1, 0), end: Offset.zero)
          .animate(CurvedAnimation(
          parent: anim, curve: Curves.easeOutCubic)),
      child: child,
    ),
    transitionDuration: const Duration(milliseconds: 280),
  );
}

class _SessionRow {
  final SupervisedStudentModel supervised;
  final MonitoringSessionModel? session;
  _SessionRow({required this.supervised, required this.session});
}

class _SessionCard extends StatelessWidget {
  final _SessionRow row;
  final VoidCallback onTap;
  const _SessionCard({required this.row, required this.onTap});

  Color _percentColor(double p) {
    if (p >= 70) return AppColors.green;
    if (p >= 40) return AppColors.orange;
    return AppColors.red;
  }

  @override
  Widget build(BuildContext context) {
    final s = row.supervised;
    final session = row.session;
    final pColor = _percentColor(s.attentionScore);

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          boxShadow: const [
            BoxShadow(
                color: Color(0x0F000000),
                blurRadius: 8,
                offset: Offset(0, 2))
          ],
        ),
        child: Row(
          children: [
            // Progress circle
            SizedBox(
              width: 56,
              height: 56,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  CircularProgressIndicator(
                    value: s.attentionScore / 100,
                    strokeWidth: 5,
                    strokeCap: StrokeCap.round,
                    backgroundColor: AppColors.divider,
                    valueColor:
                    AlwaysStoppedAnimation<Color>(pColor),
                  ),
                  Text('${s.attentionPercent}%',
                      style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: pColor)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (session != null)
                    Text(
                      'TB lớp: ${session.avgAttentionPercent}% · ${session.presentStudents} HS có mặt',
                      style: AppTextStyles.caption,
                    ),
                  const SizedBox(height: 3),
                  Text(
                    'Vị trí: Hàng ${s.row} · Cột ${s.column}',
                    style: AppTextStyles.body2.copyWith(
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      _StatusBadge(
                        icon: s.isPresent
                            ? Icons.check_circle_rounded
                            : Icons.cancel_rounded,
                        label: s.isPresent ? 'Có mặt' : 'Vắng',
                        color: s.isPresent
                            ? AppColors.green
                            : AppColors.red,
                      ),
                      const SizedBox(width: 8),
                      _StatusBadge(
                        icon: s.isAttention
                            ? Icons.visibility_rounded
                            : Icons.visibility_off_rounded,
                        label: s.isAttention
                            ? 'Tập trung'
                            : 'Mất tập trung',
                        color: s.isAttention
                            ? AppColors.primary
                            : AppColors.textHint,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded,
                color: AppColors.textHint, size: 20),
          ],
        ),
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  const _StatusBadge(
      {required this.icon,
        required this.label,
        required this.color});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 12, color: color),
        const SizedBox(width: 3),
        Text(label,
            style: TextStyle(fontSize: 11, color: color)),
      ],
    );
  }
}
