import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import 'evidence_screen.dart';

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
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
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
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: const Icon(Icons.calendar_today, color: AppColors.primary, size: 22),
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        session['date'] ?? 'Thứ 5, 16/05/2024',
                        style: AppTextStyles.heading3,
                      ),
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
                  const Text('Mức độ tập trung', style: AppTextStyles.heading3),
                  const SizedBox(height: 16),
                  Center(
                    child: SizedBox(
                      width: 120,
                      height: 120,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          SizedBox(
                            width: 120,
                            height: 120,
                            child: CircularProgressIndicator(
                              value: percent / 100,
                              strokeWidth: 10,
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
                                  fontSize: 26,
                                  fontWeight: FontWeight.bold,
                                  color: _percentColor(percent),
                                ),
                              ),
                              Text(
                                _percentLabel(percent),
                                style: TextStyle(
                                  fontSize: 13,
                                  color: _percentColor(percent),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
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
                  const Text('Thông tin buổi học', style: AppTextStyles.heading3),
                  const SizedBox(height: 12),
                  _InfoRow(label: 'Giáo viên', value: 'Nguyễn Văn A'),
                  _InfoRow(label: 'Lớp / phòng', value: 'Lớp 5A / ${session['room'] ?? 'P.201'}'),
                  _InfoRow(
                    label: 'Ghi chú',
                    value: 'Minh Anh tham gia tích cực trong giờ học',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),
            // Evidence card
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Minh chứng (ảnh/video)', style: AppTextStyles.heading3),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      _EvidenceThumb(color: AppColors.accentLight),
                      const SizedBox(width: 8),
                      _EvidenceThumb(color: const Color(0xFFE8F5E9)),
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const EvidenceScreen()),
                          );
                        },
                        child: Container(
                          width: 70,
                          height: 70,
                          decoration: BoxDecoration(
                            color: AppColors.backgroundGrey,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Center(
                            child: Text(
                              '+3',
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  GestureDetector(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const EvidenceScreen()),
                      );
                    },
                    child: const Text('Xem tất cả minh chứng >', style: AppTextStyles.linkText),
                  ),
                ],
              ),
            ),
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

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;

  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(label, style: AppTextStyles.caption),
          ),
          Expanded(
            child: Text(value, style: AppTextStyles.body2),
          ),
        ],
      ),
    );
  }
}

class _EvidenceThumb extends StatelessWidget {
  final Color color;

  const _EvidenceThumb({required this.color});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 70,
      height: 70,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Icon(Icons.image, color: AppColors.textHint, size: 32),
    );
  }
}
