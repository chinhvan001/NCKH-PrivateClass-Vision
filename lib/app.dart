import 'package:flutter/material.dart';
import 'package:private_class_vision/auth_wrapper.dart';

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