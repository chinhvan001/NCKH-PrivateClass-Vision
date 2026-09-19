import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/supervised_student_model.dart';
import '../models/monitoring_session_model.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';

class ClassComparisonScreen extends StatefulWidget {
  const ClassComparisonScreen({super.key});

  @override
  State<ClassComparisonScreen> createState() => _ClassComparisonScreenState();
}

class _ClassComparisonScreenState extends State<ClassComparisonScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_ComparisonData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_ComparisonData> _loadData() async {
    final students = await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) {
      return _ComparisonData(sessions: []);
    }
    final student = students.first;
    final supervised =
        await _monitoringService.getSupervisedDataByStudent(student.id);
    if (supervised.isEmpty) return _ComparisonData(sessions: []);

    final rows = <_ComparisonRow>[];
    for (final s in supervised) {
      if (s.monitoringSessionId.isEmpty) continue;
      try {
        final doc = await FirebaseFirestore.instance
            .collection('monitoring_sessions')
            .doc(s.monitoringSessionId)
            .get();
        if (doc.exists) {
          final session = MonitoringSessionModel.fromFirestore(doc);
          rows.add(_ComparisonRow(
            sessionIndex: rows.length + 1,
            myScore: s.attentionScore,
            classAvgScore: session.avgAttentionScore,
            isPresent: s.isPresent,
          ));
        }
      } catch (_) {}
    }
    return _ComparisonData(sessions: rows);
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
        title: const Text('So sánh với lớp', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_ComparisonData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: AppColors.primary));
          }
          if (snapshot.hasError) {
            return Center(
              child: Text(
                snapshot.error.toString().replaceFirst('Exception: ', ''),
                style: AppTextStyles.caption,
                textAlign: TextAlign.center,
              ),
            );
          }

          final data = snapshot.data!;
          if (data.sessions.isEmpty) {
            return const Center(
              child: Text('Chưa có dữ liệu buổi học',
                  style: AppTextStyles.caption),
            );
          }

          // Tính trung bình tổng
          final myAvg = data.sessions
                  .map((s) => s.myScore)
                  .reduce((a, b) => a + b) /
              data.sessions.length;
          final classAvg = data.sessions
                  .map((s) => s.classAvgScore)
                  .reduce((a, b) => a + b) /
              data.sessions.length;
          final diff = myAvg - classAvg;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Summary card ────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tổng quan so sánh',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: _CompareBox(
                              label: 'TB của con',
                              value: '${myAvg.round()}%',
                              color: AppColors.primary,
                              bgColor: AppColors.accentLight,
                              icon: Icons.person_rounded,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _CompareBox(
                              label: 'TB lớp',
                              value: '${classAvg.round()}%',
                              color: AppColors.textSecondary,
                              bgColor: AppColors.backgroundGrey,
                              icon: Icons.groups_rounded,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: _CompareBox(
                              label: 'Chênh lệch',
                              value:
                                  '${diff >= 0 ? '+' : ''}${diff.round()}%',
                              color: diff >= 0 ? AppColors.green : AppColors.red,
                              bgColor: diff >= 0
                                  ? AppColors.greenLight
                                  : AppColors.redLight,
                              icon: diff >= 0
                                  ? Icons.trending_up_rounded
                                  : Icons.trending_down_rounded,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: diff >= 0
                              ? AppColors.greenLight
                              : AppColors.redLight,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              diff >= 0
                                  ? Icons.emoji_events_rounded
                                  : Icons.info_outline_rounded,
                              color: diff >= 0
                                  ? AppColors.green
                                  : AppColors.red,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                diff >= 0
                                    ? 'Con đang tập trung tốt hơn trung bình lớp ${diff.abs().round()}%'
                                    : 'Con đang thấp hơn trung bình lớp ${diff.abs().round()}%, cần cải thiện',
                                style: AppTextStyles.caption.copyWith(
                                    color: diff >= 0
                                        ? AppColors.green
                                        : AppColors.red),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Per session comparison ──────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Chi tiết từng buổi',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 6),
                      Row(
                        children: [
                          _LegendDot(
                              color: AppColors.primary, label: 'Con'),
                          const SizedBox(width: 16),
                          _LegendDot(
                              color: AppColors.textSecondary,
                              label: 'TB lớp'),
                        ],
                      ),
                      const SizedBox(height: 14),
                      ...data.sessions.map((row) => Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: Column(
                              crossAxisAlignment:
                                  CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text('Buổi ${row.sessionIndex}',
                                        style: AppTextStyles.caption),
                                    const Spacer(),
                                    if (!row.isPresent)
                                      Container(
                                        padding:
                                            const EdgeInsets.symmetric(
                                                horizontal: 8,
                                                vertical: 2),
                                        decoration: BoxDecoration(
                                          color: AppColors.redLight,
                                          borderRadius:
                                              BorderRadius.circular(10),
                                        ),
                                        child: const Text('Vắng',
                                            style: TextStyle(
                                                fontSize: 10,
                                                color: AppColors.red)),
                                      ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                // Con
                                Row(
                                  children: [
                                    SizedBox(
                                      width: 50,
                                      child: Text('Con',
                                          style: AppTextStyles.small),
                                    ),
                                    Expanded(
                                      child: ClipRRect(
                                        borderRadius:
                                            BorderRadius.circular(4),
                                        child: LinearProgressIndicator(
                                          value: row.myScore / 100,
                                          minHeight: 8,
                                          backgroundColor:
                                              AppColors.divider,
                                          valueColor:
                                              const AlwaysStoppedAnimation(
                                                  AppColors.primary),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text('${row.myScore.round()}%',
                                        style: const TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w600,
                                            color: AppColors.primary)),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                // Lớp
                                Row(
                                  children: [
                                    SizedBox(
                                      width: 50,
                                      child: Text('Lớp',
                                          style: AppTextStyles.small),
                                    ),
                                    Expanded(
                                      child: ClipRRect(
                                        borderRadius:
                                            BorderRadius.circular(4),
                                        child: LinearProgressIndicator(
                                          value:
                                              row.classAvgScore / 100,
                                          minHeight: 8,
                                          backgroundColor:
                                              AppColors.divider,
                                          valueColor:
                                              const AlwaysStoppedAnimation(
                                                  AppColors.textSecondary),
                                        ),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                        '${row.classAvgScore.round()}%',
                                        style: const TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w600,
                                            color:
                                                AppColors.textSecondary)),
                                  ],
                                ),
                              ],
                            ),
                          )),
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
}

class _ComparisonData {
  final List<_ComparisonRow> sessions;
  _ComparisonData({required this.sessions});
}

class _ComparisonRow {
  final int sessionIndex;
  final double myScore;
  final double classAvgScore;
  final bool isPresent;
  _ComparisonRow({
    required this.sessionIndex,
    required this.myScore,
    required this.classAvgScore,
    required this.isPresent,
  });
}

class _CompareBox extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  final Color bgColor;
  final IconData icon;
  const _CompareBox(
      {required this.label,
      required this.value,
      required this.color,
      required this.bgColor,
      required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
          color: bgColor, borderRadius: BorderRadius.circular(10)),
      child: Column(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(height: 4),
          Text(value,
              style: TextStyle(
                  fontSize: 16, fontWeight: FontWeight.bold, color: color)),
          const SizedBox(height: 2),
          Text(label, style: AppTextStyles.small, textAlign: TextAlign.center),
        ],
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
            width: 10,
            height: 10,
            decoration:
                BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 5),
        Text(label, style: AppTextStyles.small),
      ],
    );
  }
}
