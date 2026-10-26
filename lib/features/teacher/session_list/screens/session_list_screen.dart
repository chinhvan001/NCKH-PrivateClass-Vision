import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../widgets/session_list_card.dart';
import '../../session_detail/screens/session_detail_screen.dart';
import '../controllers/session_list_controller.dart';

enum ViewPeriodMode { day, week }

class SessionListScreen extends StatefulWidget {
  const SessionListScreen({super.key});

  @override
  State<SessionListScreen> createState() => _SessionListScreenState();
}

class _SessionListScreenState extends State<SessionListScreen> {
  ViewPeriodMode _viewMode = ViewPeriodMode.week;
  int _offset = 0;

  final SessionListController _controller = SessionListController();

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
    _controller.addListener(_onControllerUpdate);
    _fetchData();
  }

  @override
  void dispose() {
    _controller.removeListener(_onControllerUpdate);
    _controller.dispose();
    super.dispose();
  }

  void _onControllerUpdate() {
    if (mounted) setState(() {});
  }

  Future<void> _fetchData() async {
    await _controller.loadSessionsForRange(null, null);
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
      total += _controller.sessions.where((h) => h.date == dateStr).length;
    }
    return total;
  }

  @override
  Widget build(BuildContext context) {
    final visibleDates = _getVisibleDates();
    final totalSessions = _getTotalCount(visibleDates);

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: Column(
          children: [
            Container(
              color: Colors.white,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(),
                  _buildSegmentedFilter(),
                  const Divider(height: 1, color: Color(0xFFE2E8F0)),
                  _buildFilterNavigator(),
                ],
              ),
            ),
            Expanded(
              child: _controller.isLoading
                  ? const Center(
                      child: CircularProgressIndicator(color: AppColors.navy),
                    )
                  : (totalSessions == 0
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 24),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(
                                  Icons.calendar_month_outlined,
                                  size: 72,
                                  color: Colors.blueGrey.shade200,
                                ),
                                const SizedBox(height: 20),
                                Text(
                                  _viewMode == ViewPeriodMode.week
                                      ? 'Không có phiên nào trong tuần này.'
                                      : 'Không có phiên nào trong ngày này.',
                                  textAlign: TextAlign.center,
                                  style: const TextStyle(
                                    fontSize: 18,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF1E293B),
                                  ),
                                ),
                                const SizedBox(height: 8),
                                Text(
                                  'Dữ liệu các buổi học sẽ hiển thị tại đây khi có lịch diễn ra.',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 14,
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                          itemCount: visibleDates.length,
                          itemBuilder: (context, index) {
                            final date = visibleDates[index];
                            final dateStr = _formatDate(date);
                            final dayLabel = _weekdayLabels[date.weekday] ?? '';
                            final dayItems = _controller.sessions
                                .where((h) => h.date == dateStr)
                                .toList();

                            if (_viewMode == ViewPeriodMode.week && dayItems.isEmpty) {
                              return const SizedBox.shrink();
                            }

                            return Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 14),
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 18,
                                    vertical: 12,
                                  ),
                                  decoration: BoxDecoration(
                                    color: AppColors.navy,
                                    borderRadius: BorderRadius.circular(16),
                                  ),
                                  child: Row(
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '$dayLabel, $dateStr',
                                          style: const TextStyle(
                                            fontSize: 16,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                          ),
                                          textAlign: TextAlign.center,
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 10,
                                          vertical: 3,
                                        ),
                                        decoration: BoxDecoration(
                                          color: Colors.white24,
                                          borderRadius: BorderRadius.circular(12),
                                        ),
                                        child: Text(
                                          '${dayItems.length}',
                                          style: const TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.bold,
                                            color: Colors.white,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(height: 10),
                                ...dayItems.map(
                                  (item) => SessionListCard(
                                    item: item,
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) =>
                                              SessionDetailScreen(
                                                sessionId: item.id,
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
                        )),
            ),
          ],
        ),
      ),
    );
  }

  // Tiêu đề to bản, đặt riêng ở trên cùng
  Widget _buildHeader() {
    return const Padding(
      padding: EdgeInsets.fromLTRB(20, 16, 20, 12),
      child: Text(
        'Danh sách phiên',
        style: TextStyle(
          fontSize: 26,
          fontWeight: FontWeight.w800,
          color: AppColors.navy,
          letterSpacing: -0.5,
        ),
      ),
    );
  }

  // Thanh chuyển đổi Ngày / Tuần tách riêng 1 hàng to bản, dễ chạm
  Widget _buildSegmentedFilter() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
      child: Container(
        height: 44,
        decoration: BoxDecoration(
          color: const Color(0xFFF1F5F9),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Row(
          children: [
            Expanded(child: _buildModeTab('Theo Ngày', ViewPeriodMode.day)),
            Expanded(child: _buildModeTab('Theo Tuần', ViewPeriodMode.week)),
          ],
        ),
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
          _fetchData();
        }
      },
      child: Container(
        alignment: Alignment.center,
        margin: const EdgeInsets.all(3),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.navy : Colors.transparent,
          borderRadius: BorderRadius.circular(10),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.08),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ]
              : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 16, // Chữ to rõ rệt
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
            color: isSelected ? Colors.white : const Color(0xFF64748B),
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
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          InkWell(
            onTap: () {
              setState(() => _offset--);
              _fetchData();
            },
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              child: Row(
                children: const [
                  Icon(Icons.chevron_left, size: 24, color: AppColors.navy),
                  SizedBox(width: 2),
                  Text(
                    'Lùi',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.navy,
                    ),
                  ),
                ],
              ),
            ),
          ),
          Expanded(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 15,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1E293B),
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          InkWell(
            onTap: () {
              setState(() => _offset++);
              _fetchData();
            },
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              child: Row(
                children: const [
                  Text(
                    'Tiếp',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.navy,
                    ),
                  ),
                  SizedBox(width: 2),
                  Icon(Icons.chevron_right, size: 24, color: AppColors.navy),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}