import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../widgets/session_list_card.dart';
import '../../session_detail/screens/session_detail_screen.dart';

enum ViewPeriodMode { day, week }

class SessionListScreen extends StatefulWidget {
  const SessionListScreen({super.key});

  @override
  State<SessionListScreen> createState() => _SessionListScreenState();
}

class _SessionListScreenState extends State<SessionListScreen> {
  ViewPeriodMode _viewMode = ViewPeriodMode.week;
  int _offset = 0;
  late List<HistItem> _mockHistory;

  final Map<int, String> _weekdayLabels = {
    1: 'Thứ Hai',
    2: 'Thứ Ba',
    3: 'Thứ Tư',
    4: 'Thứ Năm',
    5: 'Thứ Sáu',
    6: 'Thứ Bảy',
    7: 'Chủ Nhật',
  };

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();

    // Dữ liệu mock quanh tuần hiện tại để dễ test
    _mockHistory = [
      HistItem(
        id: 's1',
        classId: '12A1',
        className: 'Lớp 12A1',
        room: 'A203',
        date: _formatDate(now.subtract(Duration(days: now.weekday - 2))), // Thứ Ba
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
        date: _formatDate(now.subtract(Duration(days: now.weekday - 3))), // Thứ Tư
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
        date: _formatDate(now.subtract(Duration(days: now.weekday - 3))), // Thứ Tư
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
        date: _formatDate(now.subtract(Duration(days: now.weekday - 4))), // Thứ Năm
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
        date: _formatDate(now.subtract(Duration(days: now.weekday - 5))), // Thứ Sáu
        start: '08:15',
        end: '09:45',
        size: 42,
        status: 'Sắp diễn ra',
      ),
    ];
  }

  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }

  DateTime _getTargetDate() {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    if (_viewMode == ViewPeriodMode.day) {
      return today.add(Duration(days: _offset));
    } else {
      final monday = today.subtract(Duration(days: today.weekday - 1));
      return monday.add(Duration(days: _offset * 7));
    }
  }

  List<DateTime> _getVisibleDates() {
    final target = _getTargetDate();
    if (_viewMode == ViewPeriodMode.day) {
      return [target];
    } else {
      return List.generate(7, (i) => target.add(Duration(days: i)));
    }
  }

  int _getTotalCount(List<DateTime> dates) {
    int total = 0;
    for (final d in dates) {
      final dateStr = _formatDate(d);
      total += _mockHistory.where((h) => h.date == dateStr).length;
    }
    return total;
  }

  @override
  Widget build(BuildContext context) {
    final visibleDates = _getVisibleDates();
    final totalSessions = _getTotalCount(visibleDates);

    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          Container(
            color: Colors.white,
            child: Column(
              children: [
                _buildHeader(totalSessions),
                Container(height: 1, color: AppColors.hair),
                _buildFilterNavigator(),
              ],
            ),
          ),
          Expanded(
            child: totalSessions == 0
                ? Center(
              child: Text(
                _viewMode == ViewPeriodMode.week
                    ? 'Không có phiên nào trong tuần này.'
                    : 'Không có phiên nào trong ngày này.',
                style: const TextStyle(fontSize: 14, color: AppColors.muted),
              ),
            )
                : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              itemCount: visibleDates.length,
              itemBuilder: (context, index) {
                final date = visibleDates[index];
                final dateStr = _formatDate(date);
                final dayLabel = _weekdayLabels[date.weekday] ?? '';
                final dayItems =
                _mockHistory.where((h) => h.date == dateStr).toList();

                // Chế độ tuần: ngày nào không có phiên thì ẩn đi
                if (_viewMode == ViewPeriodMode.week && dayItems.isEmpty) {
                  return const SizedBox.shrink();
                }

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 12),
                    // Thanh tiêu đề gom nhóm theo ngày (phong cách thanh bo tròn)
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 16,
                        vertical: 8,
                      ),
                      decoration: BoxDecoration(
                        color: AppColors.navy,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              '$dayLabel, $dateStr',
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          Text(
                            '${dayItems.length}',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: Colors.white,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Icon(
                            Icons.keyboard_arrow_up,
                            size: 18,
                            color: Colors.white,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Render các SessionListCard của ngày đó
                    ...dayItems.map(
                          (item) => SessionListCard(
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
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(int count) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 56, 20, 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text(
            'Danh sách phiên',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w800,
              color: AppColors.navy,
            ),
          ),
          // Toggle chọn Theo Ngày | Theo Tuần
          Container(
            padding: const EdgeInsets.all(3),
            decoration: BoxDecoration(
              color: AppColors.appBg,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: AppColors.hair),
            ),
            child: Row(
              children: [
                _buildModeTab('Theo Ngày', ViewPeriodMode.day),
                _buildModeTab('Theo Tuần', ViewPeriodMode.week),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildModeTab(String label, ViewPeriodMode mode) {
    final isSelected = _viewMode == mode;
    return GestureDetector(
      onTap: () {
        if (_viewMode != mode) {
          setState(() {
            _viewMode = mode;
            _offset = 0;
          });
        }
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.navy : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? Colors.white : AppColors.muted,
          ),
        ),
      ),
    );
  }

  Widget _buildFilterNavigator() {
    final target = _getTargetDate();
    String label = '';

    if (_viewMode == ViewPeriodMode.day) {
      if (_offset == 0) {
        label = 'Hôm nay, ${_formatDate(target)}';
      } else if (_offset == 1) {
        label = 'Ngày mai, ${_formatDate(target)}';
      } else if (_offset == -1) {
        label = 'Hôm qua, ${_formatDate(target)}';
      } else {
        label = '${_weekdayLabels[target.weekday]}, ${_formatDate(target)}';
      }
    } else {
      final sunday = target.add(const Duration(days: 6));
      if (_offset == 0) {
        label = 'Tuần này (${_formatDate(target)} - ${_formatDate(sunday)})';
      } else if (_offset == -1) {
        label = 'Tuần trước (${_formatDate(target)} - ${_formatDate(sunday)})';
      } else if (_offset == 1) {
        label = 'Tuần sau (${_formatDate(target)} - ${_formatDate(sunday)})';
      } else {
        label = '${_formatDate(target)} - ${_formatDate(sunday)}';
      }
    }

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          InkWell(
            onTap: () => setState(() => _offset--),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                children: const [
                  Icon(Icons.chevron_left, size: 20, color: AppColors.navy),
                  SizedBox(width: 2),
                  Text(
                    'Lùi',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.navy,
                    ),
                  ),
                ],
              ),
            ),
          ),
          Text(
            label,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: AppColors.navy,
            ),
          ),
          InkWell(
            onTap: () => setState(() => _offset++),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              child: Row(
                children: const [
                  Text(
                    'Tiếp',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: AppColors.navy,
                    ),
                  ),
                  SizedBox(width: 2),
                  Icon(Icons.chevron_right, size: 20, color: AppColors.navy),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}