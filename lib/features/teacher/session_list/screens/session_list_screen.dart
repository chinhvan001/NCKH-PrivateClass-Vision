import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/core/models/session_model.dart';

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

  final Map<int, String> _weekdayLabels = {
    1: 'Thứ Hai',
    2: 'Thứ Ba',
    3: 'Thứ Tư',
    4: 'Thứ Năm',
    5: 'Thứ Sáu',
    6: 'Thứ Bảy',
    7: 'Chủ Nhật',
  };

  String _formatDate(DateTime date) {
    final d = date.day.toString().padLeft(2, '0');
    final m = date.month.toString().padLeft(2, '0');
    final y = date.year.toString();
    return '$d/$m/$y';
  }

  String _formatTime(DateTime date) {
    final h = date.hour.toString().padLeft(2, '0');
    final m = date.minute.toString().padLeft(2, '0');
    return '$h:$m';
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

  Stream<List<ScheduleItem>> _fetchSchedulesStream() {
    final currentUser = FirebaseAuth.instance.currentUser;
    final currentUserId = currentUser?.uid ?? 'TCtETv0Db6Nu5fjfVdzGfA0eZJ92';

    return FirebaseFirestore.instance
        .collection('monitoring_sessions')
        .where('teacher_id', isEqualTo: currentUserId)
        .snapshots()
        .asyncMap((snapshot) async {
      List<ScheduleItem> items = [];

      for (var doc in snapshot.docs) {
        final data = doc.data();
        final classId = data['class_id'] ?? '';
        final classroomId = data['classroom_id'] ?? '';

        String className = 'Lớp chưa xác định';
        if (classId.isNotEmpty) {
          final classDoc = await FirebaseFirestore.instance
              .collection('classes')
              .doc(classId)
              .get();
          if (classDoc.exists && classDoc.data() != null) {
            className = classDoc.data()!['class_name'] ?? 'Lớp $classId';
          }
        }

        String roomName = classroomId;
        if (classroomId.isNotEmpty) {
          final roomDoc = await FirebaseFirestore.instance
              .collection('classrooms')
              .doc(classroomId)
              .get();
          if (roomDoc.exists && roomDoc.data() != null) {
            roomName = roomDoc.data()!['classroom_name'] ?? classroomId;
          }
        }

        items.add(
          ScheduleItem.fromFirestore(
            doc,
            className: className,
            roomName: roomName,
          ),
        );
      }

      items.sort((a, b) => a.startTime.compareTo(b.startTime));
      return items;
    });
  }

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<List<ScheduleItem>>(
      stream: _fetchSchedulesStream(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final allSchedules = snapshot.data ?? [];
        final visibleDates = _getVisibleDates();

        final filteredSchedules = allSchedules.where((item) {
          return visibleDates.any((d) =>
              d.year == item.startTime.year &&
              d.month == item.startTime.month &&
              d.day == item.startTime.day);
        }).toList();

        final totalSessions = filteredSchedules.length;

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

                          final dayItems = filteredSchedules.where((h) {
                            return h.startTime.year == date.year &&
                                h.startTime.month == date.month &&
                                h.startTime.day == date.day;
                          }).toList();

                          if (_viewMode == ViewPeriodMode.week && dayItems.isEmpty) {
                            return const SizedBox.shrink();
                          }

                          return Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const SizedBox(height: 12),
                              Container(
                                width: double.infinity,
                                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
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
                              ...dayItems.map(
                                (item) => SessionListCard(
                                  item: HistItem(
                                    id: item.id,
                                    classId: item.classId,
                                    className: item.className,
                                    room: item.roomName,
                                    date: _formatDate(item.startTime),
                                    start: _formatTime(item.startTime),
                                    end: _formatTime(item.endTime),
                                    size: 40,
                                    status: item.status,
                                  ),
                                  onTap: () {
                                    Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder: (context) => SessionDetailScreen(
                                          classId: item.classId,
                                          className: item.className,
                                          room: item.roomName,
                                          start: _formatTime(item.startTime),
                                          end: _formatTime(item.endTime),
                                          date: _formatDate(item.startTime),
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
      },
    );
  }

  Widget _buildHeader(int count) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          const Text(
            'Danh sách phiên',
            style: TextStyle(
              fontSize: 20, // Giảm nhẹ font size tiêu đề để tranh chấp không gian ở màn hình nhỏ
              fontWeight: FontWeight.w800,
              color: AppColors.navy,
            ),
          ),
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
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          InkWell(
            onTap: () => setState(() => _offset--),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                children: const [
                  Icon(Icons.chevron_left, size: 20, color: AppColors.navy),
                  Text(
                    'Lùi',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.navy,
                    ),
                  ),
                ],
              ),
            ),
          ),
          // Bọc Expanded vào đây để Text tự căn giữa và co dãn linh hoạt, tránh tràn màn hình
          Expanded(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 12, // Giảm nhẹ font từ 13 xuống 12 để vừa màn hình nhỏ
                fontWeight: FontWeight.bold,
                color: AppColors.navy,
              ),
              maxLines: 1,
              overflow: TextOverflow.ellipsis, // Nếu màn hình quá bé sẽ hiển thị dấu ... thay vì bị nổ giao diện
            ),
          ),
          InkWell(
            onTap: () => setState(() => _offset++),
            borderRadius: BorderRadius.circular(8),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                children: const [
                  Text(
                    'Tiếp',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: AppColors.navy,
                    ),
                  ),
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