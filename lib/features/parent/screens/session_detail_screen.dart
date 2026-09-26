import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class SessionDetailScreen extends StatelessWidget {
  final Map<String, dynamic> session;

  const SessionDetailScreen({super.key, required this.session});

  @override
  Widget build(BuildContext context) {
    final int percent = session['percent'] ?? 85;
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
        title: const Text('Chi tiết buổi học', style: AppTextStyles.heading2),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Date / subject header
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x0F000000),
                    blurRadius: 6,
                    offset: Offset(0, 2),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.calendar_today_rounded,
                        color: AppColors.primary, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session['date'] ?? 'Thứ 5, 16/05/2024',
                        style: AppTextStyles.heading3,
                      ),
                      const SizedBox(height: 2),
                      Text(
                        '${session['time'] ?? '08:00 - 09:30'} | ${session['subject'] ?? 'Toán'} | ${session['room'] ?? 'P.201'}',
                        style: AppTextStyles.caption,
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Focus level card
            AppCard(
              child: Column(
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: _percentColor(percent).withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.track_changes_rounded,
                            color: _percentColor(percent), size: 20),
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
                          SizedBox(
                            width: 130,
                            height: 130,
                            child: CircularProgressIndicator(
                              value: percent / 100,
                              strokeWidth: 11,
                              strokeCap: StrokeCap.round,
                              backgroundColor: AppColors.divider,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                _percentColor(percent),
                              ),
                            ),
                          ),
                          Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                '$percent%',
                                style: TextStyle(
                                  fontSize: 28,
                                  fontWeight: FontWeight.bold,
                                  color: _percentColor(percent),
                                ),
                              ),
                              Text(
                                _percentLabel(percent),
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w500,
                                  color: _percentColor(percent),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  // Progress bar summary row
                  _FocusBarRow(
                    label: 'Tập trung cao',
                    value: percent,
                    color: _percentColor(percent),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Session info card
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.info_outline_rounded,
                          color: AppColors.primary, size: 20),
                      SizedBox(width: 8),
                      Text('Thông tin buổi học', style: AppTextStyles.heading3),
                    ],
                  ),
                  const SizedBox(height: 14),
                  _InfoRow(
                    icon: Icons.person_outline_rounded,
                    label: 'Giáo viên',
                    value: 'Nguyễn Văn A',
                  ),
                  const Divider(height: 16, color: AppColors.divider),
                  _InfoRow(
                    icon: Icons.meeting_room_outlined,
                    label: 'Lớp / phòng',
                    value:
                        'Lớp 5A / ${session['room'] ?? 'P.201'}',
                  ),
                  const Divider(height: 16, color: AppColors.divider),
                  _InfoRow(
                    icon: Icons.sticky_note_2_outlined,
                    label: 'Ghi chú',
                    value: 'Minh Anh tham gia tích cực trong giờ học',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Color _percentColor(int p) {
    if (p >= 80) return AppColors.green;
    if (p >= 60) return AppColors.orange;
    return AppColors.red;
  }

  String _percentLabel(int p) {
    if (p >= 80) return 'Tốt';
    if (p >= 60) return 'Khá';
    return 'Cần cải thiện';
  }
}

// ─── Info row with leading icon ───────────────────────────────────────────────
class _InfoRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _InfoRow(
      {required this.icon, required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 16, color: AppColors.textSecondary),
        const SizedBox(width: 8),
        SizedBox(
          width: 90,
          child: Text(label, style: AppTextStyles.caption),
        ),
        Expanded(
          child: Text(value, style: AppTextStyles.body2),
        ),
      ],
    );
  }
}

// ─── Horizontal focus bar ─────────────────────────────────────────────────────
class _FocusBarRow extends StatelessWidget {
  final String label;
  final int value;
  final Color color;

  const _FocusBarRow(
      {required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: AppTextStyles.caption),
            Text('$value%',
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
            value: value / 100,
            minHeight: 8,
            backgroundColor: AppColors.divider,
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ],
    );
  }
}

