import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/auth/controllers/auth_wrapper_login.dart';


class PrivateClassVision extends StatelessWidget {
  const PrivateClassVision({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Private Class Vision',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)),
        useMaterial3: true,
      ),
      // home: const AuthWrapper(),
      home: const AuthWrapper(),
    );
  }
}