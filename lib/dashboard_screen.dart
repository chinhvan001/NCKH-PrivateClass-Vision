import 'package:flutter/material.dart';

import 'account_screen.dart'; // Import để dùng chung AppColors và TeacherModel

// --- MOCK DATA ---
const Map<String, String>? currentSession = {
  'cls': 'Lớp 12A1',
  'room': 'A203',
  'start': '08:00',
  'end': '09:30',
};

const Map<String, String> nextSession = {
  'cls': 'Lớp 12A2',
  'room': 'A204',
  'time': '10:00',
};

// ==========================================
// MÀN HÌNH DASHBOARD
// ==========================================
class DashboardScreen extends StatelessWidget {
  final VoidCallback onOpenClasses;
  final VoidCallback onOpenAccount;

  // Dữ liệu giáo viên
  final TeacherModel teacher = const TeacherModel(
    name: 'Trần Quang Minh',
    role: 'Giáo viên Toán',
    email: 'tranquangminh@example.com',
    phone: '0901234567',
    school: 'THPT Nguyễn Du',
  );

  const DashboardScreen({
    super.key,
    required this.onOpenClasses,
    required this.onOpenAccount,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          // Phần Header
          _buildHeader(),

          // Phần Body chứa danh sách Card
          Expanded(
            child: Transform.translate(
              offset: const Offset(0, -16),
              child: Container(
                decoration: const BoxDecoration(
                  color: AppColors.appBg,
                  borderRadius: BorderRadius.only(
                    topLeft: Radius.circular(24),
                    topRight: Radius.circular(24),
                  ),
                ),
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
                  child: Column(
                    children: [
                      // 3 Thẻ chức năng còn lại
                      ShortcutCard(
                        icon: Icons.people_alt_outlined,
                        title: 'Danh sách lớp đang dạy',
                        desc: 'Các lớp bạn đang phụ trách',
                        onTap: onOpenClasses,
                      ),
                      const SizedBox(height: 12),
                      ShortcutCard(
                        icon: Icons.videocam_outlined,
                        title: 'Các phiên hôm nay',
                        desc: 'Danh sách phiên học trong ngày',
                        onTap: () {},
                      ),
                      const SizedBox(height: 12),
                      ShortcutCard(
                        icon: Icons.schedule,
                        title: 'Lịch sử phiên giám sát',
                        desc: 'Xem lại các phiên đã diễn ra',
                        onTap: () {},
                      ),

                      const SizedBox(height: 24),

                      // Ngoại lệ 1: Phiên hiện tại
                      _buildCurrentSessionCard(),

                      const SizedBox(height: 12),

                      // Ngoại lệ 2: Phiên kế tiếp
                      _buildNextSessionCard(),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // --- CÁC HÀM BUILD GIAO DIỆN CON ---

  Widget _buildHeader() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 56, 20, 48),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.navy, AppColors.darkBlue],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Lời chào
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Chào buổi sáng,',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: Colors.white.withOpacity(0.6),
                ),
              ),
              const SizedBox(height: 4),
              Text(
                teacher.name,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                  height: 1.2,
                ),
              ),
            ],
          ),

          // Nút Thông báo & Avatar
          Row(
            children: [
              // Nút chuông thông báo
              InkWell(
                onTap: () {},
                borderRadius: BorderRadius.circular(22),
                child: Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      const Icon(Icons.notifications_none, color: Colors.white),
                      Positioned(
                        top: 10,
                        right: 12,
                        child: Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: const Color(0xFFFF6B6B),
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: AppColors.navy,
                              width: 1.5,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),

              // Nút Avatar
              GestureDetector(
                onTap: onOpenAccount,
                child: const CircleAvatar(
                  radius: 22,
                  backgroundColor: AppColors.lightBlue,
                  child: Icon(Icons.person, color: AppColors.brand),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCurrentSessionCard() {
    if (currentSession != null) {
      return Card(
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: Color(0x4020A75A)),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () {},
          child: Column(
            children: [
              // Header Card
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 10,
                ),
                decoration: const BoxDecoration(
                  color: Color(0xFFE9F8EF),
                  border: Border(bottom: BorderSide(color: AppColors.hair)),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: Color(0xFF20A75A),
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Text(
                      'Phiên hiện tại',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF137A41),
                      ),
                    ),
                  ],
                ),
              ),
              // Body Card
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    _buildGradientSquare(
                      currentSession!['cls']!.replaceAll('Lớp ', ''),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${currentSession!['cls']} · Phòng ${currentSession!['room']}',
                            style: const TextStyle(
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                              color: AppColors.navy,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '${currentSession!['start']} – ${currentSession!['end']}',
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF137A41),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: Colors.black26),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    } else {
      return Card(
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        color: Colors.white,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.appBg,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Icon(
                  Icons.videocam_outlined,
                  size: 18,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(width: 12),
              const Text(
                'Không có phiên đang diễn ra',
                style: TextStyle(fontSize: 14, color: AppColors.muted),
              ),
            ],
          ),
        ),
      );
    }
  }

  Widget _buildNextSessionCard() {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () {},
        child: Column(
          children: [
            // Header Card
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.lightBlue.withOpacity(0.5),
                border: const Border(bottom: BorderSide(color: AppColors.hair)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.schedule, size: 16, color: AppColors.brand),
                  SizedBox(width: 8),
                  Text(
                    'Phiên kế tiếp',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: AppColors.navy,
                    ),
                  ),
                ],
              ),
            ),
            // Body Card
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  _buildGradientSquare(
                    nextSession['cls']!.replaceAll('Lớp ', ''),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${nextSession['cls']} · Phòng ${nextSession['room']}',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppColors.navy,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Bắt đầu lúc ${nextSession['time']}',
                          style: const TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            color: AppColors.brand,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right, color: Colors.black26),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildGradientSquare(String text) {
    return Container(
      width: 48,
      height: 48,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppColors.brand, Color(0xFF1D4ED8)], // brand to brand-600
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w800,
          color: Colors.white,
        ),
      ),
    );
  }
}

// ==========================================
// REUSABLE WIDGET: SHORTCUT CARD
// ==========================================
class ShortcutCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String desc;
  final VoidCallback onTap;

  const ShortcutCard({
    super.key,
    required this.icon,
    required this.title,
    required this.desc,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.hair),
      ),
      color: Colors.white,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.brand, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppColors.navy,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      desc,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: Colors.black26),
            ],
          ),
        ),
      ),
    );
  }
}
