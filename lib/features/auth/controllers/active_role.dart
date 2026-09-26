import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

Future<void> signOutAndResetRole(BuildContext context) async {
  final user = FirebaseAuth.instance.currentUser;

  if (user != null) {
    try {
      // 1. Xóa active_role trên Firestore để đăng nhập lần sau bắt buộc chọn lại
      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .update({'active_role': FieldValue.delete()});
    } catch (e) {
      debugPrint("Lỗi xóa active_role: $e");
    }
  }

  // 2. Xóa vai trò đã lưu trong bộ nhớ máy
  final prefs = await SharedPreferences.getInstance();
  await prefs.remove('saved_active_role');

  // 3. Thực hiện Đăng xuất khỏi Firebase Auth
  await FirebaseAuth.instance.signOut();
}