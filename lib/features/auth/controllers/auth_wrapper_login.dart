import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:flutter_privateclass_vision/features/auth/screens/login_screen.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/home_screen.dart';
import 'package:flutter_privateclass_vision/features/teacher/main/screens/main_screen.dart';

class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  String? _selectedRole;
  bool _isDialogShowing = false;
  bool _isLoadingLocalRole = true;

  @override
  void initState() {
    super.initState();
    _loadSavedRole();
  }

  Future<void> _loadSavedRole() async {
    final prefs = await SharedPreferences.getInstance();
    if (mounted) {
      setState(() {
        _selectedRole = prefs.getString('saved_active_role');
        _isLoadingLocalRole = false;
      });
    }
  }

  Future<void> _saveRole(String role) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('saved_active_role', role);
    if (mounted) {
      setState(() {
        _selectedRole = role;
      });
    }
  }

  Future<void> _clearSavedRole() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('saved_active_role');
    if (mounted) {
      setState(() {
        _selectedRole = null;
      });
    }
  }

  void _handleInvalidAccount(BuildContext context, String errorMessage) {
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await _clearSavedRole();
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

  void _showRoleSelectionDialog(
      BuildContext context, String uid, List<String> roles) {
    if (_isDialogShowing) return;
    _isDialogShowing = true;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (dialogContext) {
          return PopScope(
            canPop: false, // Ngăn bấm back để thoát dialog
            child: AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              title: const Text(
                'Chọn vai trò đăng nhập',
                textAlign: TextAlign.center,
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                children: roles.map((role) {
                  final isTeacher = role == 'teacher';
                  final roleTitle = isTeacher ? 'Giáo viên' : 'Phụ huynh';
                  final roleIcon =
                  isTeacher ? Icons.school : Icons.family_restroom;

                  return Card(
                    elevation: 2,
                    margin: const EdgeInsets.symmetric(vertical: 6),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: ListTile(
                      leading: Icon(roleIcon, color: const Color(0xFF2563EB)),
                      title: Text(
                        roleTitle,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                      onTap: () async {
                        // 1. Cập nhật Firestore trước và CHỜ hoàn tất (await)
                        try {
                          await FirebaseFirestore.instance
                              .collection('users')
                              .doc(uid)
                              .update({'active_role': role});
                        } catch (e) {
                          debugPrint("Lỗi cập nhật role: $e");
                        }

                        // 2. Lưu bộ nhớ máy
                        await _saveRole(role);

                        // 3. Đóng Dialog sau khi dữ liệu đã đồng bộ thành công
                        if (dialogContext.mounted) {
                          Navigator.of(dialogContext).pop();
                        }
                        _isDialogShowing = false;
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
          );
        },
      ).then((_) {
        _isDialogShowing = false;
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoadingLocalRole) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, authSnapshot) {
        if (authSnapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final user = authSnapshot.data;

        if (user == null) {
          if (_selectedRole != null) {
            _selectedRole = null;
            _clearSavedRole();
          }
          return const LoginScreen();
        }

        return StreamBuilder<DocumentSnapshot>(
          stream: FirebaseFirestore.instance
              .collection('users')
              .doc(user.uid)
              .snapshots(),
          builder: (context, docSnapshot) {
            if (docSnapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }

            if (docSnapshot.hasError) {
              _handleInvalidAccount(
                context,
                'Lỗi kết nối dữ liệu: ${docSnapshot.error}',
              );
              return const LoginScreen();
            }

            final doc = docSnapshot.data;

            if (doc == null || !doc.exists || doc.data() == null) {
              _handleInvalidAccount(
                context,
                'Tài khoản chưa được khởi tạo dữ liệu trên hệ thống.',
              );
              return const LoginScreen();
            }

            final data = doc.data() as Map<String, dynamic>;

            // Lấy danh sách roles
            List<String> roles = [];
            if (data['role'] is List) {
              roles = List<String>.from(
                (data['role'] as List).map((e) => e.toString().trim()),
              );
            } else if (data['role'] is String) {
              roles = [(data['role'] as String).trim()];
            }

            if (roles.isEmpty) {
              _handleInvalidAccount(
                context,
                'Tài khoản của bạn chưa được cấp quyền truy cập.',
              );
              return const LoginScreen();
            }

            // Trường hợp 1 vai trò
            if (roles.length == 1) {
              final singleRole = roles.first;
              if (singleRole == 'teacher') return const MainScreen();
              if (singleRole == 'parent') return const HomeScreen();
            }

            // Trường hợp từ 2 vai trò trở lên
            if (roles.length > 1) {
              final activeRole = data['active_role'] as String?;

              // Ưu tiên theo thứ tự: _selectedRole -> activeRole từ Firestore
              final currentRole = _selectedRole ?? activeRole;

              // Chưa chọn vai trò hợp lệ -> Hiển thị Dialog
              if (currentRole == null || !roles.contains(currentRole)) {
                _showRoleSelectionDialog(context, user.uid, roles);
                return const Scaffold(
                  body: Center(child: CircularProgressIndicator()),
                );
              }

              // Đã chọn vai trò -> Vào đúng màn hình
              if (currentRole == 'teacher') return const MainScreen();
              if (currentRole == 'parent') return const HomeScreen();
            }

            _handleInvalidAccount(
              context,
              'Cấu hình vai trò tài khoản không hợp lệ.',
            );
            return const LoginScreen();
          },
        );
      },
    );
  }
}