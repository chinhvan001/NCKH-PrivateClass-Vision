import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';

class SessionDetailScreen extends StatelessWidget {
  final Map<String, dynamic> session;

  const SessionDetailScreen({super.key, required this.session});

  Color _percentColor(double p) {
    if (p >= 70) return AppColors.green;
    if (p >= 40) return AppColors.orange;
    return AppColors.red;
  }

  String _percentLabel(double p) {
    if (p >= 70) return 'Tốt';
    if (p >= 40) return 'Khá';
    return 'Cần cải thiện';
  }

  @override
  Widget build(BuildContext context) {
    final double attentionScore =
        (session['attentionScore'] as num?)?.toDouble() ?? 0.0;
    final bool isPresent = session['isPresent'] as bool? ?? false;
    final bool isAttention =
        session['isAttention'] as bool? ?? false;
    final int row = session['row'] as int? ?? 0;
    final int column = session['column'] as int? ?? 0;
    final String note = session['note'] as String? ?? '';
    final double avgScore =
        (session['avgAttentionScore'] as num?)?.toDouble() ?? 0.0;
    final int presentStudents =
        session['presentStudents'] as int? ?? 0;
    final String sessionNote =
        session['sessionNote'] as String? ?? '';

    final color = _percentColor(attentionScore);

    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Chi tiết buổi học',
            style: AppTextStyles.heading2),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        physics: const BouncingScrollPhysics(),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Attention score card ──────────────────────────────
            AppCard(
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: color.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.track_changes_rounded,
                            color: color, size: 20),
                      ),
                      const SizedBox(width: 10),
                      const Text('Mức độ tập trung',
                          style: AppTextStyles.heading3),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Center(
                    child: SizedBox(
                      width: 130,
                      height: 130,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          CircularProgressIndicator(
                            value: attentionScore / 100,
                            strokeWidth: 11,
                            strokeCap: StrokeCap.round,
                            backgroundColor: AppColors.divider,
                            valueColor:
                                AlwaysStoppedAnimation<Color>(color),
                          ),
                          Column(
                            mainAxisAlignment:
                                MainAxisAlignment.center,
                            children: [
                              Text(
                                '${attentionScore.round()}%',
                                style: TextStyle(
                                    fontSize: 28,
                                    fontWeight: FontWeight.bold,
                                    color: color),
                              ),
                              Text(
                                _percentLabel(attentionScore),
                                style: TextStyle(
                                    fontSize: 13,
                                    fontWeight: FontWeight.w500,
                                    color: color),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Progress bar
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment:
                            MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('Điểm tập trung',
                              style: AppTextStyles.caption),
                          Text('${attentionScore.round()}%',
                              style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: color)),
                        ],
                      ),
                      const SizedBox(height: 6),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(6),
                        child: LinearProgressIndicator(
                          value: attentionScore / 100,
                          minHeight: 8,
                          backgroundColor: AppColors.divider,
                          valueColor:
                              AlwaysStoppedAnimation<Color>(color),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // ── Student info ──────────────────────────────────────
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.person_outline_rounded,
                          color: AppColors.primary, size: 20),
                      SizedBox(width: 8),
                      Text('Thông tin học sinh',
                          style: AppTextStyles.heading3),
                    ],
                  ),
                  const SizedBox(height: 14),
                  _InfoRow(
                    icon: isPresent
                        ? Icons.check_circle_rounded
                        : Icons.cancel_rounded,
                    label: 'Điểm danh',
                    value: isPresent ? 'Có mặt' : 'Vắng',
                    valueColor:
                        isPresent ? AppColors.green : AppColors.red,
                  ),
                  const Divider(height: 16, color: AppColors.divider),
                  _InfoRow(
                    icon: isAttention
                        ? Icons.visibility_rounded
                        : Icons.visibility_off_rounded,
                    label: 'Tập trung',
                    value:
                        isAttention ? 'Có tập trung' : 'Mất tập trung',
                    valueColor: isAttention
                        ? AppColors.primary
                        : AppColors.textHint,
                  ),
                  const Divider(height: 16, color: AppColors.divider),
                  _InfoRow(
                    icon: Icons.table_chart_outlined,
                    label: 'Vị trí ngồi',
                    value: 'Hàng $row · Cột $column',
                  ),
                  if (note.isNotEmpty) ...[
                    const Divider(
                        height: 16, color: AppColors.divider),
                    _InfoRow(
                      icon: Icons.sticky_note_2_outlined,
                      label: 'Ghi chú',
                      value: note,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 14),

            // ── Class info ────────────────────────────────────────
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.groups_rounded,
                          color: AppColors.primary, size: 20),
                      SizedBox(width: 8),
                      Text('Thông tin lớp học',
                          style: AppTextStyles.heading3),
                    ],
                  ),
                  const SizedBox(height: 14),
                  _InfoRow(
                    icon: Icons.psychology_rounded,
                    label: 'TB tập trung lớp',
                    value: '${avgScore.round()}%',
                    valueColor: _percentColor(avgScore),
                  ),
                  const Divider(height: 16, color: AppColors.divider),
                  _InfoRow(
                    icon: Icons.how_to_reg_rounded,
                    label: 'Học sinh có mặt',
                    value: '$presentStudents người',
                  ),
                  if (sessionNote.isNotEmpty) ...[
                    const Divider(
                        height: 16, color: AppColors.divider),
                    _InfoRow(
                      icon: Icons.note_outlined,
                      label: 'Ghi chú buổi',
                      value: sessionNote,
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? valueColor;
  const _InfoRow(
      {required this.icon,
      required this.label,
      required this.value,
      this.valueColor});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        SizedBox(
            width: 130,
            child: Text(label, style: AppTextStyles.caption)),
        Expanded(
          child: Text(value,
              style: AppTextStyles.body2.copyWith(
                  color: valueColor,
                  fontWeight: valueColor != null
                      ? FontWeight.w600
                      : FontWeight.normal)),
        ),
      ],
    );
  }
}
