import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../widgets/session_list_card.dart';
import '../../session_detail/screens/session_detail_screen.dart';

// ==========================================
// MÀN HÌNH DANH SÁCH PHIÊN
// ==========================================
class SessionListScreen extends StatefulWidget {
  const SessionListScreen({super.key});

  @override
  State<SessionListScreen> createState() => _SessionListScreenState();
}

class _SessionListScreenState extends State<SessionListScreen> {
  late DateTime _selectedDate;
  late List<HistItem> _mockHistory;

  @override
  void initState() {
    super.initState();
    _selectedDate = DateTime.now(); // Khởi tạo là ngày hôm nay

    // Tự động sinh dữ liệu giả xung quanh ngày hiện tại để dễ test
    _mockHistory = [
      HistItem(
        id: 's1',
        classId: '12A1',
        className: 'Lớp 12A1',
        room: 'A203',
        date: _formatDate(DateTime.now()),
        start: '08:00',
        end: '09:30',
        size: 42,
        status: 'Đã kết thúc',
      ),
      HistItem(
        id: 's2',
        classId: '12A2',
        className: 'Lớp 12A2',
        room: 'A204',
        date: _formatDate(DateTime.now()),
        start: '10:00',
        end: '11:30',
        size: 40,
        status: 'Đang diễn ra',
      ),
      HistItem(
        id: 's3',
        classId: '11B1',
        className: 'Lớp 11B1',
        room: 'B102',
        date: _formatDate(DateTime.now()),
        start: '14:00',
        end: '15:30',
        size: 42,
        status: 'Sắp diễn ra',
      ),
      HistItem(
        id: 's4',
        classId: '10C1',
        className: 'Lớp 10C1',
        room: 'C105',
        date: _formatDate(DateTime.now().subtract(const Duration(days: 1))),
        start: '07:30',
        end: '09:00',
        size: 36,
        status: 'Đã kết thúc',
      ),
      HistItem(
        id: 's5',
        classId: '12A1',
        className: 'Lớp 12A1',
        room: 'A203',
        date: _formatDate(DateTime.now().add(const Duration(days: 1))),
        start: '08:15',
        end: '09:45',
        size: 42,
        status: 'Sắp diễn ra',
      ),
    ];
  }

  // --- HÀM TIỆN ÍCH XỬ LÝ NGÀY THÁNG ---
  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }

  String _getDisplayDate() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final target = DateTime(
      _selectedDate.year,
      _selectedDate.month,
      _selectedDate.day,
    );
    final diff = target.difference(today).inDays;

    final dateStr = _formatDate(_selectedDate);
    if (diff == 0) return 'Hôm nay, $dateStr';
    if (diff == 1) return 'Ngày mai, $dateStr';
    if (diff == -1) return 'Hôm qua, $dateStr';
    return dateStr;
  }

  // Lọc dữ liệu theo đúng ngày đang được chọn
  List<HistItem> get _filteredList {
    final targetDateStr = _formatDate(_selectedDate);
    return _mockHistory.where((h) => h.date == targetDateStr).toList();
  }

  // Hàm chuyển ngày
  void _prevDay() => setState(
    () => _selectedDate = _selectedDate.subtract(const Duration(days: 1)),
  );
  void _nextDay() => setState(
    () => _selectedDate = _selectedDate.add(const Duration(days: 1)),
  );

  @override
  Widget build(BuildContext context) {
    final list = _filteredList;

    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          // Header nền trắng + Bộ điều hướng ngày
          Container(
            color: Colors.white,
            child: Column(
              children: [
                _buildHeader(list.length),
                Container(height: 1, color: AppColors.hair),
                _buildDateNavigator(), // Thay thế _buildFilters bằng Navigator
              ],
            ),
          ),

          // Danh sách các phiên
          Expanded(
            child: list.isEmpty
                ? const Center(
                    child: Text(
                      'Không có phiên nào trong ngày này.',
                      style: TextStyle(fontSize: 14, color: AppColors.muted),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: list.length,
                    itemBuilder: (context, index) {
                      final item = list[index];
                      return SessionListCard(
                        item: item,
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => SessionDetailScreen(
                                classId: item.classId,
                                className: item.className,
                                room: item.room,
                                start: item.start,
                                end: item.end,
                                date: item.date,
                                status: item.status,
                              ),
                            ),
                          );
                        },
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }

  // --- CÁC HÀM BUILD GIAO DIỆN CON ---

  Widget _buildHeader(int count) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 16),
      child: Row(
        children: [
          InkWell(
            onTap: () => Navigator.pop(context),
            borderRadius: BorderRadius.circular(20),
            child: Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: AppColors.appBg,
                shape: BoxShape.circle,
                border: Border.all(color: AppColors.hair),
              ),
              child: const Icon(
                Icons.arrow_back,
                color: AppColors.navy,
                size: 20,
              ),
            ),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Text(
              'Danh sách phiên',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: AppColors.navy,
              ),
            ),
          ),
          Text(
            '$count phiên',
            style: const TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w600,
              color: AppColors.muted,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateNavigator() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Nút Lùi
          InkWell(
            onTap: _prevDay,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.hair),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.chevron_left, color: AppColors.navy),
            ),
          ),
          // Hiển thị ngày
          Text(
            _getDisplayDate(),
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: AppColors.navy,
            ),
          ),
          // Nút Tiến
          InkWell(
            onTap: _nextDay,
            borderRadius: BorderRadius.circular(12),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.hair),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.chevron_right, color: AppColors.navy),
            ),
          ),
        ],
      ),
    );
  }
}
