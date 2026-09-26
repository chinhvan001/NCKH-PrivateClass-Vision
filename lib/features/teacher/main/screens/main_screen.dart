import 'package:flutter/material.dart';

import '../../session_list/screens/session_list_screen.dart'; // Đường dẫn tới file session list
import '../../classes/screens/classes_screen.dart';
import '../../seating_manager/screens/seating_manager_screen.dart';
import '../../account/screens/account_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;

  @override
  Widget build(BuildContext context) {
    final List<Widget> screens = [
      const SessionListScreen(),
      const ClassScreen(),
      const SeatingManagerScreen(),
      AccountScreen(
        onLogout: () {
          debugPrint('Đã bấm đăng xuất!');
        },
      ),
    ];

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          border: Border(
            top: BorderSide(color: Color(0xFFE2E8F0), width: 1.0),
          ),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (index) => setState(() => _currentIndex = index),
          backgroundColor: Colors.white,
          selectedItemColor: const Color(0xFF38BDF8),
          unselectedItemColor: const Color(0xFF64748B),
          selectedFontSize: 12,
          unselectedFontSize: 12,
          selectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            height: 1.4,
          ),
          unselectedLabelStyle: const TextStyle(
            fontWeight: FontWeight.w500,
            height: 1.4,
          ),
          type: BottomNavigationBarType.fixed,
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.calendar_today_outlined, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.calendar_today, size: 22),
              ),
              label: 'Trang chủ',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.class_outlined, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.class_, size: 22),
              ),
              label: 'Lớp học',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.grid_view_rounded, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.grid_view_rounded, size: 22),
              ),
              label: 'Sơ đồ lớp',
            ),
            BottomNavigationBarItem(
              icon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.person_outline_rounded, size: 22),
              ),
              activeIcon: Padding(
                padding: EdgeInsets.symmetric(vertical: 4.0),
                child: Icon(Icons.person_rounded, size: 22),
              ),
              label: 'Tài khoản',
            ),
          ],
        ),
      ),
    );
  }
}