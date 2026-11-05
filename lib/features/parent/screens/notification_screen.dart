import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

class NotificationScreen extends StatefulWidget {
  const NotificationScreen({super.key});

  @override
  State<NotificationScreen> createState() => _NotificationScreenState();
}

class _NotificationScreenState extends State<NotificationScreen> {
  final ParentService _parentService = ParentService();
  final ParentSession _session = ParentSession.instance;

  String _activeTab = 'Tất cả';
  final List<String> _tabs = ['Tất cả', 'Thông báo', 'Nhắc nhở'];

  Future<List<ParentNotification>>? _notificationFuture;
  String? _lastLoadedStudentId;

  @override
  void initState() {
    super.initState();
    _fetchNotifications();
  }

  void _fetchNotifications() {
    final currentChild = _session.selectedChild;
    if (currentChild != null) {
      _lastLoadedStudentId = currentChild.id;
      final classId =
          currentChild.classes.isNotEmpty ? currentChild.classes.first.id : null;
      setState(() {
        _notificationFuture = _parentService.getNotificationsForStudent(
          studentId: currentChild.id,
          classId: classId,
        );
      });
    } else {
      setState(() {
        _notificationFuture = Future.value([]);
      });
    }
  }

  String _formatTimeAgo(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 60) {
      final mins = difference.inMinutes <= 0 ? 1 : difference.inMinutes;
      return '$mins phút trước';
    } else if (difference.inHours < 24) {
      return '${difference.inHours} giờ trước';
    } else if (difference.inDays == 1) {
      return 'Hôm qua';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} ngày trước';
    } else {
      return '${timestamp.day.toString().padLeft(2, '0')}/${timestamp.month.toString().padLeft(2, '0')}/${timestamp.year}';
    }
  }

  IconData _getIconForType(NotificationType type, bool isPresent) {
    switch (type) {
      case NotificationType.attendance:
        return isPresent ? Icons.check_circle_outline : Icons.event_busy;
      case NotificationType.attentionWarning:
        return Icons.warning_amber_rounded;
      case NotificationType.attentionPraise:
        return Icons.star_border_rounded;
      case NotificationType.note:
        return Icons.edit_note;
    }
  }

  Color _getIconColor(NotificationType type, bool isPresent) {
    switch (type) {
      case NotificationType.attendance:
        return isPresent ? AppColors.green : AppColors.red;
      case NotificationType.attentionWarning:
        return AppColors.orange;
      case NotificationType.attentionPraise:
        return AppColors.primary;
      case NotificationType.note:
        return AppColors.primary;
    }
  }

  Color _getBgColor(NotificationType type, bool isPresent) {
    switch (type) {
      case NotificationType.attendance:
        return isPresent ? AppColors.greenLight : const Color(0xFFFFEBEE);
      case NotificationType.attentionWarning:
        return AppColors.orangeLight;
      case NotificationType.attentionPraise:
        return AppColors.primaryLight;
      case NotificationType.note:
        return AppColors.accentLight;
    }
  }

  String _getCategoryTab(NotificationType type) {
    switch (type) {
      case NotificationType.attentionWarning:
      case NotificationType.note:
        return 'Nhắc nhở';
      case NotificationType.attendance:
      case NotificationType.attentionPraise:
        return 'Thông báo';
    }
  }

  @override
  Widget build(BuildContext context) {
    final currentChild = _session.selectedChild;

    if (currentChild != null && currentChild.id != _lastLoadedStudentId) {
      _fetchNotifications();
    }

    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(
            Icons.arrow_back_ios,
            color: AppColors.textPrimary,
            size: 20,
          ),
          onPressed: () =>
              Navigator.canPop(context) ? Navigator.pop(context) : null,
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
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 7,
                      ),
                      decoration: BoxDecoration(
                        color: selected ? AppColors.primary : Colors.white,
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(
                          color: selected
                              ? AppColors.primary
                              : AppColors.divider,
                        ),
                      ),
                      child: Text(
                        t,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: selected
                              ? Colors.white
                              : AppColors.textSecondary,
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
            child: currentChild == null
                ? const Center(child: Text('Chưa có thông tin học sinh'))
                : RefreshIndicator(
                    onRefresh: () async => _fetchNotifications(),
                    child: FutureBuilder<List<ParentNotification>>(
                      future: _notificationFuture,
                      builder: (context, snapshot) {
                        if (snapshot.connectionState ==
                            ConnectionState.waiting) {
                          return const Center(
                            child: CircularProgressIndicator(),
                          );
                        }

                        if (snapshot.hasError) {
                          return Center(
                            child: Text(
                              'Lỗi tải thông báo: ${snapshot.error}',
                            ),
                          );
                        }

                        final allNotifications = snapshot.data ?? [];

                        final filteredNotifications =
                            allNotifications.where((n) {
                          if (_activeTab == 'Tất cả') return true;
                          return _getCategoryTab(n.type) == _activeTab;
                        }).toList();

                        if (filteredNotifications.isEmpty) {
                          return ListView(
                            physics: const AlwaysScrollableScrollPhysics(),
                            children: const [
                              SizedBox(height: 100),
                              Center(
                                child: Text(
                                  'Chưa có thông báo nào',
                                  style: AppTextStyles.caption,
                                ),
                              ),
                            ],
                          );
                        }

                        return ListView.separated(
                          physics: const AlwaysScrollableScrollPhysics(),
                          padding: const EdgeInsets.all(16),
                          itemCount: filteredNotifications.length,
                          separatorBuilder: (_, _a) =>
                              const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final n = filteredNotifications[index];
                            final icon =
                                _getIconForType(n.type, n.isPresent);
                            final iconColor =
                                _getIconColor(n.type, n.isPresent);
                            final bgColor =
                                _getBgColor(n.type, n.isPresent);

                            return AppCard(
                              child: Row(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Container(
                                    width: 42,
                                    height: 42,
                                    decoration: BoxDecoration(
                                      color: bgColor,
                                      shape: BoxShape.circle,
                                    ),
                                    child: Icon(
                                      icon,
                                      color: iconColor,
                                      size: 22,
                                    ),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          n.title,
                                          style: AppTextStyles.heading3,
                                        ),
                                        const SizedBox(height: 4),
                                        Text(
                                          n.message,
                                          style: AppTextStyles.body2,
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          _formatTimeAgo(n.timestamp),
                                          style: AppTextStyles.small,
                                        ),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}