import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/bottom_nav_bar.dart';
import '../widgets/common_widgets.dart';
import 'session_history_screen.dart';
import 'notification_screen.dart';
import 'profile_screen.dart';
import 'daily_overview_screen.dart';
import 'switch_account_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = const [
    _HomeContent(),
    SessionHistoryScreen(),
    NotificationScreen(),
    ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      body: _screens[_currentIndex],
      bottomNavigationBar: AppBottomNavBar(
        currentIndex: _currentIndex,
        onTap: (i) => setState(() => _currentIndex = i),
      ),
    );
  }
}

class _HomeContent extends StatelessWidget {
  const _HomeContent();

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Lớp học của con', style: AppTextStyles.heading2),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.notifications_outlined, size: 26),
                    onPressed: () {},
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            // Student card
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: AppCard(
                child: Column(
                  children: [
                    // Student info row
                    Row(
                      children: [
                        const AvatarWidget(name: 'Minh Anh', size: 44),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Minh Anh', style: AppTextStyles.heading3),
                              SizedBox(height: 2),
                              Text(
                                'Lớp 5A - Trường Tiểu học ABC',
                                style: AppTextStyles.caption,
                              ),
                            ],
                          ),
                        ),
                        GestureDetector(
                          onTap: () {
                            showModalBottomSheet(
                              context: context,
                              shape: const RoundedRectangleBorder(
                                borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                              ),
                              builder: (_) => const SwitchAccountScreen(),
                            );
                          },
                          child: const Icon(Icons.expand_more, color: AppColors.textSecondary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.accentLight,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.info_outline, color: AppColors.primary, size: 16),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Hôm nay, Minh Anh có mức độ tập trung tốt hơn 15% so với trung bình buổi trước.',
                              style: AppTextStyles.caption.copyWith(color: AppColors.primary),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),
                    const Divider(height: 1),
                    const SizedBox(height: 12),
                    // Stats row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _StatItem(label: 'Cặp lịch lọc', value: '15:30'),
                        _StatItem(label: 'Tập trung (TB)', value: '78%', isPercent: true, color: AppColors.primary),
                        _StatItem(label: 'Điểm danh', value: '9/10', color: AppColors.green),
                      ],
                    ),
                    const SizedBox(height: 14),
                    // Progress circles
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        CircularProgressWidget(
                          percent: 78,
                          centerText: '78%',
                          label: 'Tập trung',
                          color: AppColors.primary,
                          size: 75,
                        ),
                        CircularProgressWidget(
                          percent: 90,
                          centerText: '9/10',
                          label: 'Điểm danh',
                          color: AppColors.green,
                          size: 75,
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // Attendance summary
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceAround,
                      children: [
                        _AttendanceStat(
                          icon: Icons.check_circle_outline,
                          color: AppColors.green,
                          label: 'Vắng có phép',
                          value: '0 buổi',
                        ),
                        _AttendanceStat(
                          icon: Icons.cancel_outlined,
                          color: AppColors.orange,
                          label: 'Vắng không phép',
                          value: '0 buổi',
                        ),
                        _AttendanceStat(
                          icon: Icons.star_outline,
                          color: AppColors.yellow,
                          label: 'Đi muộn',
                          value: '1 buổi',
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    // View history button
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const SessionHistoryScreen()),
                          );
                        },
                        icon: const Icon(Icons.list_alt, size: 18),
                        label: const Text('Xem lịch sử các buổi học'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.primary,
                          side: const BorderSide(color: AppColors.primary),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Daily overview shortcut
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: AppCard(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const DailyOverviewScreen()),
                  );
                },
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: AppColors.accentLight,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.bar_chart, color: AppColors.primary, size: 24),
                    ),
                    const SizedBox(width: 12),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Tổng quan trong ngày', style: AppTextStyles.heading3),
                          SizedBox(height: 2),
                          Text('Xem chi tiết mức độ tập trung & điểm danh', style: AppTextStyles.caption),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: AppColors.textSecondary),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _StatItem extends StatelessWidget {
  final String label;
  final String value;
  final bool isPercent;
  final Color? color;

  const _StatItem({
    required this.label,
    required this.value,
    this.isPercent = false,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color ?? AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 2),
        Text(label, style: AppTextStyles.small),
      ],
    );
  }
}

class _AttendanceStat extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final String value;

  const _AttendanceStat({
    required this.icon,
    required this.color,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 22),
        const SizedBox(height: 4),
        Text(label, style: AppTextStyles.small),
        Text(
          value,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }
}
