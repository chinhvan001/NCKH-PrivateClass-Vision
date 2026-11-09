import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/features/auth/controllers/active_role.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/widgets/common_widgets.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_colors.dart';
import 'package:flutter_privateclass_vision/features/parent/utils/app_text_styles.dart';

import 'attendance_detail_screen.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
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
        title: const Text('Hồ sơ', style: AppTextStyles.heading2),
      ),
      body: ListenableBuilder(
        listenable: ParentSession.instance,
        builder: (context, _) => _buildBody(context),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final session = ParentSession.instance;
    final parent = session.parent;
    final children = session.children;
    final selectedId = session.selectedChild?.id;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Hồ sơ phụ huynh (collection parents) ─────────────────────────
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    AvatarWidget(name: parent?.name ?? '', size: 56),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _orDefault(parent?.name),
                            style: AppTextStyles.heading2,
                          ),
                          const SizedBox(height: 2),
                          const Text('Phụ huynh', style: AppTextStyles.caption),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Divider(height: 1, color: AppColors.divider),
                const SizedBox(height: 6),
                _ProfileRow(
                  icon: Icons.person_outline_rounded,
                  label: 'Họ tên',
                  value: _orDefault(parent?.name),
                ),
                _ProfileRow(
                  icon: Icons.phone_outlined,
                  label: 'Số điện thoại',
                  value: _orDefault(parent?.phoneNumber),
                ),
                _ProfileRow(
                  icon: Icons.mail_outline_rounded,
                  label: 'Email',
                  value: _orDefault(parent?.email),
                ),
              ],
            ),
          ),
          const SizedBox(height: 18),

          // ── Danh sách con (students2 có parent_id = uid) ─────────────────
          Row(
            children: [
              const Expanded(
                child: Text('Con của tôi', style: AppTextStyles.heading3),
              ),
              Text('${children.length} học sinh', style: AppTextStyles.caption),
            ],
          ),
          const SizedBox(height: 4),
          const Text(
            'Chọn một học sinh để xem thông tin ở các mục khác.',
            style: AppTextStyles.caption,
          ),
          const SizedBox(height: 10),
          if (children.isEmpty)
            const AppCard(
              child: Center(
                child: Padding(
                  padding: EdgeInsets.symmetric(vertical: 12),
                  child: Text(
                    'Chưa có học sinh nào được liên kết',
                    style: AppTextStyles.caption,
                  ),
                ),
              ),
            )
          else
            ...children.map(
              (child) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _ChildTile(
                  child: child,
                  selected: child.id == selectedId,
                  onTap: () => session.selectChild(child),
                ),
              ),
            ),
          const SizedBox(height: 8),

          // ── Liên kết báo cáo ─────────────────────────────────────────────
          AppCard(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const AttendanceDetailScreen(),
                ),
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
                  child: const Icon(
                    Icons.bar_chart,
                    color: AppColors.primary,
                    size: 22,
                  ),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text(
                    'Xem báo cáo tổng kết',
                    style: AppTextStyles.heading3,
                  ),
                ),
                const Icon(Icons.chevron_right, color: AppColors.textSecondary),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // ── Đăng xuất ────────────────────────────────────────────────────
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () async {
                try {
                  await signOutAndResetRole();
                } catch (e) {
                  debugPrint('Lỗi đăng xuất: $e');
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Đăng xuất thất bại: $e')),
                    );
                  }
                }
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFEF4444),
                foregroundColor: Colors.white,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: const Text(
                'Đăng xuất',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
              ),
            ),
          ),
        ],
      ),
    );
  }

  static String _orDefault(String? v) =>
      (v != null && v.trim().isNotEmpty) ? v.trim() : 'Chưa cập nhật';
}

// ─── Thẻ một học sinh trong danh sách ──────────────────────────────────────
class _ChildTile extends StatelessWidget {
  final LinkedChild child;
  final bool selected;
  final VoidCallback onTap;

  const _ChildTile({
    required this.child,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final statusColor = child.isActive ? AppColors.green : AppColors.textSecondary;
    final statusBg = child.isActive ? AppColors.greenLight : AppColors.backgroundGrey;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: selected ? AppColors.accentLight : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.divider,
            width: 1.5,
          ),
        ),
        child: Row(
          children: [
            AvatarWidget(
              name: child.name,
              size: 46,
              bgColor: selected ? AppColors.primary : AppColors.accentLight,
              textColor: selected ? Colors.white : AppColors.primary,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    child.name,
                    style: AppTextStyles.heading3.copyWith(
                      color: selected ? AppColors.primary : AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(child.classDisplay, style: AppTextStyles.caption),
                  const SizedBox(height: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 3,
                    ),
                    decoration: BoxDecoration(
                      color: statusBg,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      child.statusDisplay,
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: statusColor,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Icon(
              selected ? Icons.check_circle : Icons.radio_button_unchecked,
              color: selected ? AppColors.primary : AppColors.textHint,
              size: 22,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _ProfileRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 16, color: AppColors.textSecondary),
          const SizedBox(width: 8),
          SizedBox(width: 100, child: Text(label, style: AppTextStyles.caption)),
          Expanded(child: Text(value, style: AppTextStyles.body2)),
        ],
      ),
    );
  }
}
