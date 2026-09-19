import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';
import '../models/supervised_student_model.dart';

class AttentionHeatmapScreen extends StatefulWidget {
  const AttentionHeatmapScreen({super.key});

  @override
  State<AttentionHeatmapScreen> createState() =>
      _AttentionHeatmapScreenState();
}

class _AttentionHeatmapScreenState extends State<AttentionHeatmapScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<List<SupervisedStudentModel>> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<List<SupervisedStudentModel>> _loadData() async {
    final students = await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) return [];
    return _monitoringService
        .getSupervisedDataByStudent(students.first.id);
  }

  void _reload() => setState(() => _dataFuture = _loadData());

  Color _heatColor(double score, bool isPresent) {
    if (!isPresent) return AppColors.divider;
    if (score >= 80) return const Color(0xFF1B5E20); // đậm xanh
    if (score >= 60) return const Color(0xFF388E3C);
    if (score >= 40) return const Color(0xFFFFA000);
    if (score >= 20) return const Color(0xFFE64A19);
    return const Color(0xFFB71C1C); // đỏ đậm
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
                icon: const Icon(Icons.arrow_back_ios,
                    color: AppColors.textPrimary, size: 20),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title: const Text('Bản đồ nhiệt tập trung',
            style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<List<SupervisedStudentModel>>(
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
                    style: AppTextStyles.caption));
          }

          final sessions = snapshot.data ?? [];
          if (sessions.isEmpty) {
            return const Center(
                child:
                    Text('Chưa có dữ liệu', style: AppTextStyles.caption));
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Legend ──────────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Chú thích', style: AppTextStyles.heading3),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          _HeatLegend(
                              color: const Color(0xFF1B5E20),
                              label: '≥80%'),
                          const SizedBox(width: 8),
                          _HeatLegend(
                              color: const Color(0xFF388E3C),
                              label: '60–79%'),
                          const SizedBox(width: 8),
                          _HeatLegend(
                              color: const Color(0xFFFFA000),
                              label: '40–59%'),
                          const SizedBox(width: 8),
                          _HeatLegend(
                              color: const Color(0xFFE64A19),
                              label: '20–39%'),
                          const SizedBox(width: 8),
                          _HeatLegend(
                              color: const Color(0xFFB71C1C),
                              label: '<20%'),
                          const SizedBox(width: 8),
                          _HeatLegend(
                              color: AppColors.divider, label: 'Vắng'),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Heatmap grid ─────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tập trung từng buổi học',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 4),
                      const Text(
                          'Màu càng xanh = tập trung càng cao',
                          style: AppTextStyles.caption),
                      const SizedBox(height: 16),
                      // Chia thành grid 7 cột (như lịch tuần)
                      GridView.builder(
                        shrinkWrap: true,
                        physics: const NeverScrollableScrollPhysics(),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                          crossAxisCount: 7,
                          crossAxisSpacing: 4,
                          mainAxisSpacing: 4,
                          childAspectRatio: 1,
                        ),
                        itemCount: sessions.length,
                        itemBuilder: (context, i) {
                          final s = sessions[i];
                          return Tooltip(
                            message:
                                'Buổi ${i + 1}: ${s.attentionPercent}%',
                            child: Container(
                              decoration: BoxDecoration(
                                color: _heatColor(
                                    s.attentionScore, s.isPresent),
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Center(
                                child: Text(
                                  '${i + 1}',
                                  style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 9,
                                      fontWeight: FontWeight.bold),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Stats từ heatmap ─────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Phân bổ tập trung',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 14),
                      _buildDistributionBar(sessions),
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

  Widget _buildDistributionBar(List<SupervisedStudentModel> sessions) {
    final present = sessions.where((s) => s.isPresent).toList();
    if (present.isEmpty) return const SizedBox();

    final total = present.length;
    final high = present.where((s) => s.attentionScore >= 70).length;
    final mid =
        present.where((s) => s.attentionScore >= 40 && s.attentionScore < 70).length;
    final low = present.where((s) => s.attentionScore < 40).length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _DistRow(
            label: 'Tập trung cao (≥70%)',
            count: high,
            total: total,
            color: AppColors.green),
        const SizedBox(height: 8),
        _DistRow(
            label: 'Trung bình (40–69%)',
            count: mid,
            total: total,
            color: AppColors.orange),
        const SizedBox(height: 8),
        _DistRow(
            label: 'Thấp (<40%)',
            count: low,
            total: total,
            color: AppColors.red),
      ],
    );
  }
}

class _DistRow extends StatelessWidget {
  final String label;
  final int count;
  final int total;
  final Color color;
  const _DistRow(
      {required this.label,
      required this.count,
      required this.total,
      required this.color});

  @override
  Widget build(BuildContext context) {
    final ratio = total > 0 ? count / total : 0.0;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: AppTextStyles.caption),
            Text('$count/$total buổi',
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: color)),
          ],
        ),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: ratio,
            minHeight: 8,
            backgroundColor: AppColors.divider,
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ],
    );
  }
}

class _HeatLegend extends StatelessWidget {
  final Color color;
  final String label;
  const _HeatLegend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration:
              BoxDecoration(color: color, borderRadius: BorderRadius.circular(2)),
        ),
        const SizedBox(width: 3),
        Text(label, style: const TextStyle(fontSize: 9)),
      ],
    );
  }
}
