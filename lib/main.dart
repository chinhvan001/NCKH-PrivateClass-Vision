import 'package:flutter/material.dart';

import 'account_screen.dart';
import 'dashboard_screen.dart';
import 'classes_screen.dart';
import 'seating_manager_screen.dart';

void main() {
  runApp(const MyApp());
}

// 1. CLASS MYAPP: CHỨA CẤU HÌNH MOBILE (392x851)
class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        fontFamily: 'Inter',
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
      ),

      // Khung giới hạn 392x851 giả lập điện thoại
      builder: (context, child) {
        return Scaffold(
          backgroundColor: Colors.grey[900],
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
                child: child,
              ),
            ),
          ),
        );
      },

      home: const MainScreen(),
    );
  }
}

// =========================================================
// 2. CLASS MAINSCREEN: CHỨA BOTTOM NAVIGATION BAR
// =========================================================
class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  // Đặt mặc định là 0 để khi mở app sẽ vào luôn Trang chủ
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    // ĐƯA DANH SÁCH SCREENS VÀO TRONG HÀM BUILD ĐỂ DÙNG ĐƯỢC "CONTEXT"
    final List<Widget> screens = [
      // Tab 0: Trang chủ
      DashboardScreen(
        onOpenClasses: () {
          // CHỨC NĂNG MỚI: Mở trang ClassesScreen đè lên màn hình hiện tại
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ClassesScreen(
                onOpenClass: (id) {
                  debugPrint('Mở chi tiết lớp: $id');
                },
              ),
            ),
          );
        },
        onOpenAccount: () {
          // Chuyển sang Tab Tài khoản (index 2)
          setState(() {
            _currentIndex = 2;
          });
        },
      ),

      // Tab 1: Sơ đồ lớp (Đã tích hợp màn hình Seating Manager)
      const SeatingManagerScreen(),

      // Tab 2: Tài khoản
      AccountScreen(
        onLogout: () {
          debugPrint('Đã bấm đăng xuất!');
        },
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens, // Gọi danh sách screens ở đây
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(top: BorderSide(color: Color(0xFFE2E8F0), width: 1.0)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) {
            setState(() {
              _currentIndex = index;
            });
          },
          backgroundColor: Colors.white,
          selectedItemColor: const Color(0xFF38BDF8),
          unselectedItemColor: const Color(0xFF64748B),
          selectedFontSize: 13,
          unselectedFontSize: 13,
          selectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            height: 1.5,
          ),
          unselectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w500,
            height: 1.5,
          ),
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.home_outlined, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.home_outlined, size: 22),
              ),
              label: 'Trang chủ',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(
                  Icons.grid_view_rounded,
                  size: 22,
                ), // Đã đổi icon thành dạng lưới
              ),
              activeIcon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.grid_view_rounded, size: 22),
              ),
              label: 'Sơ đồ lớp', // Đã sửa text
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.verified_user_outlined, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.verified_user_outlined, size: 22),
              ),
              label: 'Tài khoản',
            ),
          ],
        ),
      ),
    );
  }
}
