import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Account UI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Roboto',
        scaffoldBackgroundColor: AppColors.appBg,
      ),
      // Bọc giao diện trong một khung có nền tối để làm nổi bật "điện thoại ảo"
      builder: (context, child) {
        return Scaffold(
          backgroundColor: Colors.grey[900], // Nền ngoài cùng màu tối
          body: Center(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(
                24,
              ), // Bo góc cho giống điện thoại
              child: Container(
                width: 392, // Giới hạn chiều rộng
                height: 851, // Giới hạn chiều cao
                decoration: const BoxDecoration(
                  color: Colors.white,
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black54,
                      blurRadius: 20,
                      spreadRadius: 5,
                    ),
                  ],
                ),
                // Hiển thị giao diện chính bên trong khung này
                child: child,
              ),
            ),
          ),
        );
      },
      home: AccountScreen(
        onLogout: () {
          debugPrint('Đã bấm đăng xuất!');
        },
      ),
    );
  }
}

// ==========================================
// 1. CORE: MÀU SẮC & DỮ LIỆU
// ==========================================
class AppColors {
  static const Color navy = Color(0xFF0F172A);
  static const Color darkBlue = Color(0xFF1E3A8A);
  static const Color brand = Color(0xFF2563EB);
  static const Color lightBlue = Color(0xFFDBEAFE);
  static const Color muted = Color(0xFF64748B);
  static const Color hair = Color(0xFFE2E8F0);
  static const Color appBg = Color(0xFFF8FAFC);

  static const Color logoutText = Color(0xFFE5484D);
  static const Color logoutBorder = Color(0xFFF3D0D1);
}

class TeacherModel {
  final String name, role, email, phone, school;
  const TeacherModel({
    required this.name,
    required this.role,
    required this.email,
    required this.phone,
    required this.school,
  });
}

// ==========================================
// 2. MÀN HÌNH CHÍNH (ACCOUNT SCREEN)
// ==========================================
class AccountScreen extends StatelessWidget {
  final VoidCallback onLogout;

  // Dữ liệu giả lập
  final TeacherModel teacher = const TeacherModel(
    name: 'Trần Quang Minh',
    role: 'Giáo viên Toán',
    email: 'tranquangminh@example.com',
    phone: '0901234567',
    school: 'THPT Nguyễn Du',
  );

  const AccountScreen({super.key, required this.onLogout});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildHeaderAndProfile(),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 24),
                  _buildSectionTitle('Thông tin liên hệ'),
                  _buildContactInfo(),

                  const SizedBox(height: 24),
                  _buildSectionTitle('Bảo mật & cài đặt'),
                  _buildSettingsInfo(),

                  const SizedBox(height: 32),
                  // Đã thêm truyền context vào hàm _buildLogoutButton
                  _buildLogoutButton(context),

                  const SizedBox(height: 16),
                  const Center(
                    child: Text(
                      'PrivateClass Vision · Phiên bản 2.4.0',
                      style: TextStyle(fontSize: 12, color: AppColors.muted),
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
  }

  Widget _buildHeaderAndProfile() {
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
          child: ProfileCard(teacher: teacher),
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

  Widget _buildContactInfo() {
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
          InfoRow(
            icon: Icons.mail_outline,
            label: 'Email',
            value: teacher.email,
          ),
          const Divider(height: 1, color: AppColors.hair),
          InfoRow(
            icon: Icons.phone_outlined,
            label: 'Số điện thoại',
            value: teacher.phone,
          ),
          const Divider(height: 1, color: AppColors.hair),
          InfoRow(
            icon: Icons.school_outlined,
            label: 'Trường',
            value: teacher.school,
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
                  'Bạn có chắc chắn muốn đăng xuất khỏi tài khoản giáo viên không?',
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
                    onPressed: () {
                      Navigator.of(context).pop();
                      onLogout();
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

// ==========================================
// 3. REUSABLE WIDGETS (CÁC COMPONENT TÁI SỬ DỤNG)
// ==========================================
class ProfileCard extends StatelessWidget {
  final TeacherModel teacher;

  const ProfileCard({super.key, required this.teacher});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      shadowColor: Colors.black12,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      color: Colors.white,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 20),
        child: Column(
          children: [
            Stack(
              alignment: Alignment.bottomRight,
              children: [
                const CircleAvatar(
                  radius: 42,
                  backgroundColor: AppColors.lightBlue,
                  child: Icon(Icons.person, size: 40, color: AppColors.brand),
                ),
                Container(
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    color: AppColors.brand,
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white, width: 2),
                  ),
                  child: const Icon(Icons.edit, size: 14, color: Colors.white),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              teacher.name,
              style: const TextStyle(
                fontSize: 19,
                fontWeight: FontWeight.w800,
                color: AppColors.navy,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              teacher.role,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: AppColors.brand,
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () {},
              icon: const Icon(Icons.edit, size: 17, color: AppColors.navy),
              label: const Text(
                'Chỉnh sửa hồ sơ',
                style: TextStyle(color: AppColors.navy),
              ),
              style: OutlinedButton.styleFrom(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
                side: const BorderSide(color: AppColors.hair),
                padding: const EdgeInsets.symmetric(
                  horizontal: 24,
                  vertical: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class InfoRow extends StatelessWidget {
  final IconData icon;
  final String label, value;

  const InfoRow({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: AppColors.lightBlue,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: AppColors.brand, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 12, color: AppColors.muted),
                ),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: AppColors.navy,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class ActionRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String? hint;

  const ActionRow({
    super.key,
    required this.icon,
    required this.label,
    this.hint,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () {},
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.lightBlue,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Icon(icon, color: AppColors.brand, size: 20),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.navy,
                ),
              ),
            ),
            if (hint != null) ...[
              Text(
                hint!,
                style: const TextStyle(fontSize: 12, color: AppColors.muted),
              ),
              const SizedBox(width: 8),
            ],
            const Icon(Icons.chevron_right, size: 20, color: Colors.black26),
          ],
        ),
      ),
    );
  }
}
