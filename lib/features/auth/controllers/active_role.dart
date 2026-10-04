import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Đăng xuất dùng chung cho giáo viên và phụ huynh.
/// AuthWrapper tự chuyển về LoginScreen khi trạng thái đăng nhập thay đổi.
Future<void> signOutAndResetRole() async {
  // 1. Xoá vai trò đã chọn (cùng key với LoginScreen và AuthWrapper)
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove('selected_login_role');

  // 2. Đăng xuất Google để lần sau được chọn lại tài khoản
  await GoogleSignIn().signOut();

  // 3. Đăng xuất Firebase Auth
  await FirebaseAuth.instance.signOut();
}
