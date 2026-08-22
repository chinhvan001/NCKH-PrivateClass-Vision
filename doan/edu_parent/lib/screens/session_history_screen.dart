import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import 'session_detail_screen.dart';

class SessionHistoryScreen extends StatefulWidget {
  const SessionHistoryScreen({super.key});

  @override
  State<SessionHistoryScreen> createState() => _SessionHistoryScreenState();
}

class _SessionHistoryScreenState extends State<SessionHistoryScreen> {
  String _activeFilter = 'Tất cả';
  final List<String> _filters = ['Tất cả', 'Đã tham gia', 'Vắng', 'Đi muộn'];

  final List<Map<String, dynamic>> _sessions = [
    {
      'date': 'Thứ 6, 16/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Toán',
      'room': 'P.201',
      'percent': 85,
      'status': 'present',
    },
    {
      'date': 'Thứ 5, 15/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Toán',
      'room': 'P.201',
      'percent': 85,
      'status': 'present',
    },
    {
      'date': 'Thứ 4, 14/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Tiếng Việt',
      'room': 'P.101',
      'percent': 75,
      'status': 'present',
    },
    {
      'date': 'Thứ 3, 13/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Tiếng Anh',
      'room': 'P.203',
      'percent': 60,
      'status': 'late',
    },
    {
      'date': 'Thứ 2, 12/05/2024',
      'time': '10:00 - 11:30',
      'subject': 'Khoa học',
      'room': 'P.205',
      'percent': 80,
      'status': 'absent',
    },
    {
      'date': 'Thứ 6, 10/05/2024',
      'time': '08:00 - 09:30',
      'subject': 'Lịch sử',
      'room': 'P.102',
      'percent': 70,
      'status': 'present',
    },
    {
      'date': 'Thứ 5, 10/05/2024',
      'time': '11:00 - 12:30',
      'subject': 'Lịch sử',
      'room': 'P.102',
      'percent': 70,
      'status': 'present',
    },
  ];

  List<Map<String, dynamic>> get _filteredSessions {
    if (_activeFilter == 'Tất cả') return _sessions;
    if (_activeFilter == 'Đã tham gia') {
      return _sessions.where((s) => s['status'] == 'present').toList();
    }
    if (_activeFilter == 'Vắng') {
      return _sessions.where((s) => s['status'] == 'absent').toList();
    }
    if (_activeFilter == 'Đi muộn') {
      return _sessions.where((s) => s['status'] == 'late').toList();
    }
    return _sessions;
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'present': return AppColors.green;
      case 'absent': return AppColors.red;
      case 'late': return AppColors.orange;
      default: return AppColors.textSecondary;
    }
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'present': return 'Có mặt';
      case 'absent': return 'Vắng';
      case 'late': return 'Đi muộn';
      default: return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios, color: AppColors.textPrimary, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Lịch sử các buổi học', style: AppTextStyles.heading2),
      ),
      body: Column(
        children: [
          // Filter chips
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _filters.map((f) {
                  final selected = f == _activeFilter;
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: GestureDetector(
                      onTap: () => setState(() => _activeFilter = f),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 7),
                        decoration: BoxDecoration(
                          color: selected ? AppColors.primary : Colors.white,
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: selected ? AppColors.primary : AppColors.divider,
                          ),
                        ),
                        child: Text(
                          f,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w500,
                            color: selected ? Colors.white : AppColors.textSecondary,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          // Sessions list
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: _filteredSessions.length,
              separatorBuilder: (_, _a) => const SizedBox(height: 10),
              itemBuilder: (context, index) {
                final s = _filteredSessions[index];
                return AppCard(
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => SessionDetailScreen(session: s),
                      ),
                    );
                  },
                  child: Row(
                    children: [
                      // Progress circle
                      SizedBox(
                        width: 52,
                        height: 52,
                        child: Stack(
                          alignment: Alignment.center,
                          children: [
                            CircularProgressIndicator(
                              value: (s['percent'] as int) / 100,
                              strokeWidth: 5,
                              backgroundColor: AppColors.divider,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                _percentColor(s['percent'] as int),
                              ),
                            ),
                            Text(
                              '${s['percent']}%',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(s['date'], style: AppTextStyles.caption),
                            const SizedBox(height: 2),
                            Text(
                              '${s['time']} | ${s['subject']} | ${s['room']}',
                              style: AppTextStyles.body2,
                            ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          StatusChip(
                            label: _statusLabel(s['status']),
                            bgColor: _statusColor(s['status']).withValues(alpha: 0.12),
                            textColor: _statusColor(s['status']),
                          ),
                          const SizedBox(height: 4),
                          const Icon(Icons.chevron_right, color: AppColors.textHint, size: 20),
                        ],
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Color _percentColor(int percent) {
    if (percent >= 80) return AppColors.green;
    if (percent >= 60) return AppColors.orange;
    return AppColors.red;
  }
}
