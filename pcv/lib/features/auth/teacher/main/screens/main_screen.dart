import 'package:flutter/material.dart';

// Import từ các tính năng (Features) tương ứng
import '../../dashboard/screens/dashboard_screen.dart';
import '../../classes/screens/classes_screen.dart';
import '../../seating_manager/screens/seating_manager_screen.dart';
import '../../account/screens/account_screen.dart';

// =========================================================
// MÀN HÌNH CHÍNH (CHỨA BOTTOM NAVIGATION BAR)
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
          // Mở trang ClassesScreen đè lên màn hình hiện tại
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

      // Tab 1: Sơ đồ lớp (Seating Manager)
      const SeatingManagerScreen(),

      // Tab 2: Tài khoản
      AccountScreen(
        onLogout: () {
          debugPrint('Đã bấm đăng xuất!');
        },
      ),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: screens),
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
                child: Icon(Icons.grid_view_rounded, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.only(bottom: 4.0, top: 4.0),
                child: Icon(Icons.grid_view_rounded, size: 22),
              ),
              label: 'Sơ đồ lớp',
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
