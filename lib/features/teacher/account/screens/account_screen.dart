import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:google_sign_in/google_sign_in.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/teacher_model.dart';
import '../../../../global_widgets/action_row.dart';
import '../../../../global_widgets/info_row.dart';
import '../widgets/profile_card.dart';

class AccountScreen extends StatelessWidget {
  final VoidCallback onLogout;

  const AccountScreen({super.key, required this.onLogout});

  @override
  Widget build(BuildContext context) {
    final currentUser = FirebaseAuth.instance.currentUser;

    if (currentUser == null) {
      return const Scaffold(
        body: Center(child: Text('Người dùng chưa đăng nhập')),
      );
    }

    return StreamBuilder<DocumentSnapshot<Map<String, dynamic>>>(
      stream: FirebaseFirestore.instance
          .collection('teachers')
          .doc(currentUser.uid)
          .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasError) {
          return Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: Text('Lỗi tải dữ liệu: ${snapshot.error}')),
          );
        }

        if (!snapshot.hasData || !snapshot.data!.exists) {
          return const Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: Text('Không tìm thấy thông tin tài khoản')),
          );
        }

        // Chuyển đổi dữ liệu Firestore sang UserModel
        final userModel = TeacherModel.fromFirestore(snapshot.data!);

        return Scaffold(
          backgroundColor: AppColors.appBg,
          body: SingleChildScrollView(
            child: Column(
              children: [
                _buildHeaderAndProfile(userModel),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const SizedBox(height: 24),
                      _buildSectionTitle('Thông tin liên hệ'),
                      _buildContactInfo(userModel),

                      const SizedBox(height: 24),
                      _buildSectionTitle('Bảo mật & cài đặt'),
                      _buildSettingsInfo(),

                      const SizedBox(height: 32),
                      _buildLogoutButton(context),

                      const SizedBox(height: 16),
                      const Center(
                        child: Text(
                          'PrivateClass Vision · Phiên bản 2.4.0',
                          style: TextStyle(
                            fontSize: 12,
                            color: AppColors.muted,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                    ],
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeaderAndProfile(TeacherModel user) {
    return Stack(
      clipBehavior: Clip.none,
      alignment: Alignment.topCenter,
      children: [
        Container(
          width: double.infinity,
          height: 180,
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [AppColors.navy, AppColors.darkBlue],
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
          child: const SafeArea(
            child: Padding(
              padding: EdgeInsets.only(top: 16.0),
              child: Text(
                'Tài khoản',
                textAlign: TextAlign.center,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                ),
              ),
            ),
          ),
        ),
        Padding(
          padding: const EdgeInsets.only(top: 130, left: 16, right: 16),
          child: ProfileCard(user: user),
        ),
      ],
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: AppColors.navy,
        ),
      ),
    );
  }

  Widget _buildContactInfo(TeacherModel user) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: Column(
        children: [
          InfoRow(icon: Icons.mail_outline, label: 'Email', value: user.email),
          const Divider(height: 1, color: AppColors.hair),
          InfoRow(
            icon: Icons.phone_outlined,
            label: 'Số điện thoại',
            value: user.phoneNumber,
          ),
          const Divider(height: 1, color: AppColors.hair),
          InfoRow(
            icon: Icons.school_outlined,
            label: 'Trường',
            value: 'THPT Phan Châu Trinh',
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsInfo() {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: const Column(
        children: [
          ActionRow(icon: Icons.vpn_key_outlined, label: 'Đổi mật khẩu'),
          Divider(height: 1, color: AppColors.hair),
          ActionRow(
            icon: Icons.security_outlined,
            label: 'Cài đặt bảo mật',
            hint: 'Xác thực 2 lớp',
          ),
          Divider(height: 1, color: AppColors.hair),
          ActionRow(
            icon: Icons.notifications_none_outlined,
            label: 'Thông báo',
          ),
        ],
      ),
    );
  }

  Widget _buildLogoutButton(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: () => _showLogoutDialog(context),
      icon: const Icon(Icons.logout, size: 19, color: AppColors.logoutText),
      label: const Text(
        'Đăng xuất',
        style: TextStyle(
          fontSize: 15,
          fontWeight: FontWeight.w600,
          color: AppColors.logoutText,
        ),
      ),
      style: OutlinedButton.styleFrom(
        backgroundColor: Colors.white,
        side: const BorderSide(color: AppColors.logoutBorder),
        padding: const EdgeInsets.symmetric(vertical: 14),
        minimumSize: const Size(double.infinity, 50),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(24.0),
          ),
          backgroundColor: Colors.white,
          elevation: 0,
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 24.0,
              vertical: 32.0,
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.logout,
                      color: Color(0xFFEF4444),
                      size: 28,
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Đăng xuất',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Bạn có chắc chắn muốn đăng xuất khỏi tài khoản không?',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 14,
                    color: Color(0xFF64748B),
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () async {
                      Navigator.of(context).pop();
                      try {
                        await GoogleSignIn().signOut();
                        await FirebaseAuth.instance.signOut();
                      } catch (e) {
                        debugPrint('Lỗi đăng xuất: $e');
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
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: OutlinedButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                    },
                    style: OutlinedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF0F172A),
                      side: const BorderSide(color: Color(0xFFE2E8F0)),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      'Huỷ',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
