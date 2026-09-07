import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/notification_model.dart';
import '../services/notification_service.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  // TODO: thay bằng studentId thật từ auth sau
  static const String _studentId = 'student_minh_anh';

  final _service = NotificationService();
  String _activeTab = 'Tất cả';
  final List<String> _tabs = ['Tất cả', 'Thông báo', 'Nhắc nhở'];

  late Future<List<NotificationModel>> _notifFuture;

  @override
  void initState() {
    super.initState();
    _notifFuture = _service.getNotificationsByStudent(_studentId);
  }

  void _reload() {
    setState(() {
      _notifFuture = _service.getNotificationsByStudent(_studentId);
    });
  }

  List<NotificationModel> _applyTab(List<NotificationModel> all) {
    if (_activeTab == 'Tất cả') return all;
    return all.where((n) => n.tab == _activeTab).toList();
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
        title: const Text('Thông báo', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
            tooltip: 'Tải lại',
          ),
        ],
      ),
      body: FutureBuilder<List<NotificationModel>>(
        future: _notifFuture,
        builder: (context, snapshot) {
          // ── Loading ──────────────────────────────────────────────────
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
              child: CircularProgressIndicator(color: AppColors.primary),
            );
          }

          // ── Error ────────────────────────────────────────────────────
          if (snapshot.hasError) {
            return _ErrorState(
              message: snapshot.error.toString(),
              onRetry: _reload,
            );
          }

          final all = snapshot.data ?? [];
          final filtered = _applyTab(all);

          return Column(
            children: [
              // ── Tab bar ─────────────────────────────────────────────
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
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 16, vertical: 7),
                          decoration: BoxDecoration(
                            color: selected
                                ? AppColors.primary
                                : Colors.white,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: selected
                                  ? AppColors.primary
                                  : AppColors.divider,
                            ),
                          ),
                          child: AnimatedDefaultTextStyle(
                            duration: const Duration(milliseconds: 200),
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w500,
                              color: selected
                                  ? Colors.white
                                  : AppColors.textSecondary,
                            ),
                            child: Text(t),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ),

              // ── Count ────────────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 4),
                child: Row(
                  children: [
                    const Icon(Icons.notifications_none_rounded,
                        size: 16, color: AppColors.textSecondary),
                    const SizedBox(width: 6),
                    Text('${filtered.length} thông báo',
                        style: AppTextStyles.caption),
                  ],
                ),
              ),

              // ── List ────────────────────────────────────────────────
              Expanded(
                child: filtered.isEmpty
                    ? const _EmptyState()
                    : ListView.separated(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 20),
                        physics: const BouncingScrollPhysics(),
                        itemCount: filtered.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(height: 10),
                        itemBuilder: (context, index) {
                          final n = filtered[index];
                          return _NotificationCard(notification: n);
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

// ─── Notification card ─────────────────────────────────────────────────────────
class _NotificationCard extends StatelessWidget {
  final NotificationModel notification;

  const _NotificationCard({required this.notification});

  @override
  Widget build(BuildContext context) {
    final n = notification;
    return AppCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: n.bgColor,
              shape: BoxShape.circle,
            ),
            child: Icon(n.icon, color: n.iconColor, size: 22),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(n.title, style: AppTextStyles.heading3),
                const SizedBox(height: 4),
                Text(n.body, style: AppTextStyles.body2),
                const SizedBox(height: 6),
                Text(n.time, style: AppTextStyles.small),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─── Error state ───────────────────────────────────────────────────────────────
class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
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
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.cloud_off_rounded,
                  size: 44, color: AppColors.red),
            ),
            const SizedBox(height: 14),
            const Text('Không thể tải dữ liệu', style: AppTextStyles.heading3),
            const SizedBox(height: 6),
            Text(
              message.replaceFirst('Exception: ', ''),
              style: AppTextStyles.caption,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: onRetry,
              icon: const Icon(Icons.refresh_rounded, size: 18),
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
}

// ─── Empty state ───────────────────────────────────────────────────────────────
class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: const BoxDecoration(
              color: AppColors.accentLight,
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.notifications_off_rounded,
                size: 44, color: AppColors.primary),
          ),
          const SizedBox(height: 14),
          const Text('Không có thông báo nào', style: AppTextStyles.heading3),
          const SizedBox(height: 6),
          const Text('Thử chọn tab khác', style: AppTextStyles.caption),
        ],
      ),
    );
  }
}
