import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:flutter_privateclass_vision/features/auth/screens/login_screen.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/home_screen.dart';
import 'package:flutter_privateclass_vision/features/teacher/main/screens/main_screen.dart';

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  // Hàm xử lý đăng xuất và hiển thị thông báo lỗi khi không tìm thấy tài khoản
  void _handleInvalidAccount(BuildContext context, String errorMessage) {
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('selected_login_role');
      await FirebaseAuth.instance.signOut();

      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(errorMessage),
            backgroundColor: Colors.red,
            behavior: SnackBarBehavior.floating,
            duration: const Duration(seconds: 4),
          ),
        );
      }
    });
  }

  // Hàm kiểm tra sự tồn tại của document trong Firestore
  Future<bool> _checkUserInCollection(String uid, String role) async {
    final collectionName = role == 'teacher' ? 'teachers' : 'parents';
    final doc = await FirebaseFirestore.instance
        .collection(collectionName)
        .doc(uid)
        .get();
    return doc.exists;
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, authSnapshot) {
        if (authSnapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final user = authSnapshot.data;

        // Nếu chưa đăng nhập thì hiển thị Trang chủ/Trang đăng nhập
        if (user == null) {
          return const LoginScreen();
        }

        // Đã đăng nhập Google -> Lấy vai trò đã chọn từ SharedPreferences
        return FutureBuilder<SharedPreferences>(
          future: SharedPreferences.getInstance(),
          builder: (context, prefsSnapshot) {
            if (!prefsSnapshot.hasData) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }

            final selectedRole =
                prefsSnapshot.data!.getString('selected_login_role') ?? 'teacher';

            // Kiểm tra tài khoản có tồn tại trong collection tương ứng không
            return FutureBuilder<bool>(
              future: _checkUserInCollection(user.uid, selectedRole),
              builder: (context, checkSnapshot) {
                if (checkSnapshot.connectionState == ConnectionState.waiting) {
                  return const Scaffold(
                    body: Center(child: CircularProgressIndicator()),
                  );
                }

                if (checkSnapshot.hasError) {
                  _handleInvalidAccount(
                    context,
                    'Lỗi kết nối dữ liệu: ${checkSnapshot.error}',
                  );
                  return const LoginScreen();
                }

                final bool exists = checkSnapshot.data ?? false;

                // Không tìm thấy tài khoản trong collection tương ứng
                if (!exists) {
                  final roleName = selectedRole == 'teacher' ? 'Giáo viên' : 'Phụ huynh';
                  _handleInvalidAccount(
                    context,
                    'Tài khoản không tồn tại trong danh sách $roleName. Vui lòng thử lại!',
                  );
                  return const LoginScreen();
                }

                // Nếu có tài khoản -> Chuyển sang màn hình tương ứng
                if (selectedRole == 'teacher') {
                  return const MainScreen();
                } else {
                  return const HomeScreen();
                }
              },
            );
          },
        );
      },
    );
  }
}