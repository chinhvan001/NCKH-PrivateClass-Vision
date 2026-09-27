import 'package:flutter/material.dart';
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
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.canPop(context) ? Navigator.pop(context) : null,
        ),
        title: const Text('Hồ sơ học sinh', style: AppTextStyles.heading2),
      ),
      body: ListenableBuilder(
        listenable: ParentSession.instance,
        builder: (context, _) => _buildBody(context),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    final session = ParentSession.instance;
    final child = session.selectedChild;
    final parent = session.parent;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Student header
          AppCard(
            child: Row(
              children: [
                Container(
                  width: 64,
                  height: 64,
                  decoration: BoxDecoration(
                    color: AppColors.accentLight,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.person, color: AppColors.primary, size: 36),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(child?.name ?? '', style: AppTextStyles.heading2),
                      const SizedBox(height: 4),
                      Text(
                        child?.classDisplay ?? '',
                        style: AppTextStyles.caption,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
          // Personal info
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Thông tin chung', style: AppTextStyles.heading3),
                const SizedBox(height: 12),
                _ProfileRow(
                  label: 'Ngày sinh',
                  value: (child?.birthday.isNotEmpty ?? false) ? child!.birthday : 'Chưa cập nhật',
                ),
                _ProfileRow(
                  label: 'Giới tính',
                  value: (child?.gender.isNotEmpty ?? false) ? child!.gender : 'Chưa cập nhật',
                ),
                _ProfileRow(label: 'Giáo viên phụ trách', value: child?.teacherDisplay ?? 'Chưa cập nhật'),
                _ProfileRow(label: 'Phụ huynh', value: parent?.name ?? 'Chưa cập nhật'),
                _ProfileRow(label: 'SĐT liên hệ', value: parent?.phoneNumber ?? 'Chưa cập nhật'),
                _ProfileRow(label: 'Email liên hệ', value: parent?.email ?? 'Chưa cập nhật'),
              ],
            ),
          ),
          const SizedBox(height: 14),
          // Report link
          AppCard(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const AttendanceDetailScreen()),
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
                  child: const Icon(Icons.bar_chart, color: AppColors.primary, size: 22),
                ),
                const SizedBox(width: 12),
                const Expanded(
                  child: Text('Xem báo cáo tổng kết', style: AppTextStyles.heading3),
                ),
                const Icon(Icons.chevron_right, color: AppColors.textSecondary),
              ],
            ),
          ),            
          const SizedBox(height: 20,),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton(
              onPressed: () async {
                try {
                  // AuthWrapper sẽ tự chuyển về LoginScreen khi state đăng xuất thay đổi
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
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProfileRow extends StatelessWidget {
  final String label;
  final String value;

  const _ProfileRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 7),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
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
