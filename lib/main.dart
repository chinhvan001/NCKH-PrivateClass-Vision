import 'package:flutter/material.dart';

// Gọi MainScreen từ thư mục features
import 'features/main/screens/main_screen.dart';

void main() {
  runApp(const MyApp());
}

// =========================================================
// CLASS MYAPP: CHỨA CẤU HÌNH MOBILE VÀ KHỞI CHẠY APP
// =========================================================
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PrivateClass Vision',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Inter',
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      ),

      // Khung giới hạn 392x851 giả lập điện thoại
      builder: (context, child) {
        return Scaffold(
          backgroundColor: Colors.grey[900], // Nền đen bên ngoài
          body: Center(
            child: ClipRRect(
              borderRadius: BorderRadius.circular(24),
              child: Container(
                width: 392,
                height: 851,
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
                child: child, // Giao diện app thực tế sẽ nằm ở đây
              ),
            ),
          ),
        );
      },

      // Gọi màn hình chính chứa thanh điều hướng
      home: const MainScreen(),
    );
  }
}
