import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  String _activeTab = 'Tất cả';
  final List<String> _tabs = ['Tất cả', 'Thông báo', 'Nhắc nhở'];

  final List<Map<String, dynamic>> _notifications = [
    {
      'type': 'teacher',
      'title': 'Thông báo mới từ giáo viên',
      'body': 'Hôm nay Minh Anh có điểm kiểm tra môn Tiếng Anh xuất sắc trong buổi học Toán.',
      'time': '10 phút trước',
      'icon': Icons.campaign_outlined,
      'iconColor': AppColors.primary,
      'bgColor': AppColors.accentLight,
      'tab': 'Thông báo',
    },
    {
      'type': 'reminder',
      'title': 'Nhắc nhở',
      'body': 'Hôm nay Minh Anh có tiết kiểm tra môn Tiếng Anh.',
      'time': '2 giờ trước',
      'icon': Icons.alarm,
      'iconColor': AppColors.orange,
      'bgColor': AppColors.orangeLight,
      'tab': 'Nhắc nhở',
    },
    {
      'type': 'report',
      'title': 'Thông báo điểm danh',
      'body': 'Minh Anh vắng mặt buổi học hôm nay.',
      'time': 'Hôm qua',
      'icon': Icons.assignment_outlined,
      'iconColor': AppColors.green,
      'bgColor': AppColors.greenLight,
      'tab': 'Thông báo',
    },
    {
      'type': 'teacher',
      'title': 'Thông báo mới từ giáo viên',
      'body': 'Minh Anh cần cải thiện mức độ tập trung ở tiết học tuần trước.',
      'time': '2 ngày trước',
      'icon': Icons.campaign_outlined,
      'iconColor': AppColors.primary,
      'bgColor': AppColors.accentLight,
      'tab': 'Thông báo',
    },
  ];

  List<Map<String, dynamic>> get _filtered {
    if (_activeTab == 'Tất cả') return _notifications;
    return _notifications.where((n) => n['tab'] == _activeTab).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.canPop(context) ? Navigator.pop(context) : null,
        ),
        title: const Text('Thông báo', style: AppTextStyles.heading2),
      ),
      body: Column(
        children: [
          // Tab bar
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 12),
            child: Row(
              children: _tabs.map((t) {
                final selected = t == _activeTab;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: GestureDetector(
                    onTap: () => setState(() => _activeTab = t),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
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
          ),
          // Notification list
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _filtered.length,
              separatorBuilder: (_, _a) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final n = _filtered[index];
                return AppCard(
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        width: 42,
                        height: 42,
                        decoration: BoxDecoration(
                          color: n['bgColor'] as Color,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          n['icon'] as IconData,
                          color: n['iconColor'] as Color,
                          size: 22,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(n['title'] as String, style: AppTextStyles.heading3),
                            const SizedBox(height: 4),
                            Text(n['body'] as String, style: AppTextStyles.body2),
                            const SizedBox(height: 6),
                            Text(n['time'] as String, style: AppTextStyles.small),
                          ],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
          // See all
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: TextButton(
              onPressed: () {},
              child: const Text('Xem tất cả', style: AppTextStyles.linkText),
            ),
          ),
        ],
      ),
    );
  }
}
