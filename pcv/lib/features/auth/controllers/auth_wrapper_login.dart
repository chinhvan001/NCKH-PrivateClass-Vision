import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/auth/screens/login_screen.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/home_screen.dart';
import 'package:flutter_privateclass_vision/features/teacher/main/screens/main_screen.dart';

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  void _denyAccessAndSignOut(BuildContext context, String message) {
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      await FirebaseAuth.instance.signOut();
      if (context.mounted) {
        ScaffoldMessenger.of(context)
          ..hideCurrentSnackBar()
          ..showSnackBar(
            SnackBar(
              content: Text(message),
              backgroundColor: Colors.red,
              duration: const Duration(seconds: 4),
              behavior: SnackBarBehavior.floating,
            ),
          );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final user = snapshot.data;
        if (user == null) return const LoginScreen();

        if (user.email == null || user.email!.isEmpty) {
          _denyAccessAndSignOut(context, 'Tài khoản không có Email hợp lệ!');
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

            final doc = docSnapshot.data;
            if (doc != null && doc.exists) {
              final data = doc.data() as Map<String, dynamic>?;
              final role = data?['role'];

              if (role == 'teacher') return const MainScreen();
              if (role == 'parent') return const HomeScreen();

              _denyAccessAndSignOut(
                context,
                'Email (${user.email}) chưa được phân quyền trong hệ thống.',
              );
              return const LoginScreen();
            }

            _denyAccessAndSignOut(
              context,
              'Email (${user.email}) không tồn tại trong hệ thống Firestore.',
            );
            return const LoginScreen();
          },
        );
      },
    );
  }
}