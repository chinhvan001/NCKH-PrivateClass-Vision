import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';

class AttentionChartScreen extends StatefulWidget {
  const AttentionChartScreen({super.key});

  @override
  State<AttentionChartScreen> createState() => _AttentionChartScreenState();
}

class _AttentionChartScreenState extends State<AttentionChartScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_ChartData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_ChartData> _loadData() async {
    final students = await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) return _ChartData(points: [], stats: null);

    final student = students.first;
    final supervised =
        await _monitoringService.getSupervisedDataByStudent(student.id);
    final stats = await _monitoringService.getStudentStats(student.id);

    final points = supervised
        .asMap()
        .entries
        .map((e) => FlSpot(
              e.key.toDouble(),
              e.value.attentionScore,
            ))
        .toList();

    return _ChartData(points: points, stats: stats);
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
        title: const Text('Biểu đồ tập trung', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_ChartData>(
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
                    textAlign: TextAlign.center));
          }

          final data = snapshot.data!;
          if (data.points.isEmpty) {
            return const Center(
                child: Text('Chưa có dữ liệu', style: AppTextStyles.caption));
          }

          final stats = data.stats;

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Stats summary ──────────────────────────────────
                if (stats != null)
                  AppCard(
                    child: Row(
                      children: [
                        Expanded(
                          child: _MiniStat(
                            label: 'TB tập trung',
                            value: '${stats.avgAttentionPercent}%',
                            color: AppColors.primary,
                          ),
                        ),
                        Container(
                            width: 1, height: 40, color: AppColors.divider),
                        Expanded(
                          child: _MiniStat(
                            label: 'Tổng buổi',
                            value: '${stats.totalSessions}',
                            color: AppColors.textPrimary,
                          ),
                        ),
                        Container(
                            width: 1, height: 40, color: AppColors.divider),
                        Expanded(
                          child: _MiniStat(
                            label: 'Buổi tập trung',
                            value: '${stats.attentionSessions}',
                            color: AppColors.green,
                          ),
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Line chart ─────────────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Tập trung theo buổi học',
                          style: AppTextStyles.heading3),
                      const SizedBox(height: 4),
                      const Text('Điểm tập trung từ 0–100',
                          style: AppTextStyles.caption),
                      const SizedBox(height: 20),
                      SizedBox(
                        height: 220,
                        child: LineChart(
                          LineChartData(
                            minY: 0,
                            maxY: 100,
                            gridData: FlGridData(
                              show: true,
                              drawVerticalLine: false,
                              horizontalInterval: 25,
                              getDrawingHorizontalLine: (_) => FlLine(
                                color: AppColors.divider,
                                strokeWidth: 1,
                              ),
                            ),
                            borderData: FlBorderData(show: false),
                            titlesData: FlTitlesData(
                              leftTitles: AxisTitles(
                                sideTitles: SideTitles(
                                  showTitles: true,
                                  interval: 25,
                                  reservedSize: 32,
                                  getTitlesWidget: (value, _) => Text(
                                    '${value.round()}',
                                    style: AppTextStyles.small,
                                  ),
                                ),
                              ),
                              bottomTitles: AxisTitles(
                                sideTitles: SideTitles(
                                  showTitles: true,
                                  interval: 1,
                                  getTitlesWidget: (value, _) => Text(
                                    'B${value.round() + 1}',
                                    style: AppTextStyles.small,
                                  ),
                                ),
                              ),
                              topTitles: const AxisTitles(
                                  sideTitles:
                                      SideTitles(showTitles: false)),
                              rightTitles: const AxisTitles(
                                  sideTitles:
                                      SideTitles(showTitles: false)),
                            ),
                            lineBarsData: [
                              LineChartBarData(
                                spots: data.points,
                                isCurved: true,
                                color: AppColors.primary,
                                barWidth: 3,
                                dotData: FlDotData(
                                  show: true,
                                  getDotPainter: (spot, _, __, ___) =>
                                      FlDotCirclePainter(
                                    radius: 4,
                                    color: AppColors.primary,
                                    strokeWidth: 2,
                                    strokeColor: Colors.white,
                                  ),
                                ),
                                belowBarData: BarAreaData(
                                  show: true,
                                  color: AppColors.primary
                                      .withValues(alpha: 0.08),
                                ),
                              ),
                              // Đường trung bình
                              if (stats != null)
                                LineChartBarData(
                                  spots: [
                                    FlSpot(0,
                                        stats.avgAttentionScore),
                                    FlSpot(
                                        (data.points.length - 1)
                                            .toDouble(),
                                        stats.avgAttentionScore),
                                  ],
                                  isCurved: false,
                                  color: AppColors.orange
                                      .withValues(alpha: 0.6),
                                  barWidth: 1.5,
                                  dashArray: [6, 4],
                                  dotData:
                                      const FlDotData(show: false),
                                ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          _LegendLine(
                              color: AppColors.primary,
                              label: 'Tập trung'),
                          const SizedBox(width: 16),
                          _LegendLine(
                              color: AppColors.orange,
                              label: 'Trung bình',
                              dashed: true),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 14),

                // ── Bar chart điểm danh ────────────────────────────
                if (stats != null)
                  AppCard(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Điểm danh', style: AppTextStyles.heading3),
                        const SizedBox(height: 14),
                        SizedBox(
                          height: 140,
                          child: BarChart(
                            BarChartData(
                              maxY: stats.totalSessions.toDouble(),
                              gridData:
                                  const FlGridData(show: false),
                              borderData: FlBorderData(show: false),
                              titlesData: FlTitlesData(
                                bottomTitles: AxisTitles(
                                  sideTitles: SideTitles(
                                    showTitles: true,
                                    getTitlesWidget: (value, _) {
                                      const labels = [
                                        'Có mặt',
                                        'Vắng',
                                        'Tập trung'
                                      ];
                                      if (value.toInt() <
                                          labels.length) {
                                        return Padding(
                                          padding:
                                              const EdgeInsets.only(
                                                  top: 4),
                                          child: Text(
                                              labels[value.toInt()],
                                              style:
                                                  AppTextStyles.small),
                                        );
                                      }
                                      return const SizedBox();
                                    },
                                  ),
                                ),
                                leftTitles: const AxisTitles(
                                    sideTitles: SideTitles(
                                        showTitles: false)),
                                topTitles: const AxisTitles(
                                    sideTitles: SideTitles(
                                        showTitles: false)),
                                rightTitles: const AxisTitles(
                                    sideTitles: SideTitles(
                                        showTitles: false)),
                              ),
                              barGroups: [
                                _barGroup(
                                    0,
                                    stats.presentSessions.toDouble(),
                                    AppColors.green),
                                _barGroup(
                                    1,
                                    stats.absentSessions.toDouble(),
                                    AppColors.red),
                                _barGroup(
                                    2,
                                    stats.attentionSessions.toDouble(),
                                    AppColors.primary),
                              ],
                            ),
                          ),
                        ),
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

  BarChartGroupData _barGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          color: color,
          width: 32,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
        ),
      ],
    );
  }
}

class _ChartData {
  final List<FlSpot> points;
  final StudentStats? stats;
  _ChartData({required this.points, required this.stats});
}

class _MiniStat extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _MiniStat(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value,
            style: TextStyle(
                fontSize: 18, fontWeight: FontWeight.bold, color: color)),
        const SizedBox(height: 2),
        Text(label,
            style: AppTextStyles.small, textAlign: TextAlign.center),
      ],
    );
  }
}

class _LegendLine extends StatelessWidget {
  final Color color;
  final String label;
  final bool dashed;
  const _LegendLine(
      {required this.color, required this.label, this.dashed = false});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 20,
          height: 2,
          color: dashed ? Colors.transparent : color,
          child: dashed
              ? CustomPaint(
                  painter: _DashedLinePainter(color: color),
                )
              : null,
        ),
        const SizedBox(width: 5),
        Text(label, style: AppTextStyles.small),
      ],
    );
  }
}

class _DashedLinePainter extends CustomPainter {
  final Color color;
  const _DashedLinePainter({required this.color});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 1.5;
    double x = 0;
    while (x < size.width) {
      canvas.drawLine(Offset(x, size.height / 2),
          Offset(x + 4, size.height / 2), paint);
      x += 8;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
