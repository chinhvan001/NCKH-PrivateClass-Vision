import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/class_model.dart';
import '../../../../core/models/student_model.dart';
import '../../../../core/services/student_service.dart';
import '../widgets/seating_chart_widget.dart';

class ClassDetailScreen extends StatefulWidget {
  final String classId;

  const ClassDetailScreen({super.key, required this.classId});

  @override
  State<ClassDetailScreen> createState() => _ClassDetailScreenState();
}

class _ClassDetailScreenState extends State<ClassDetailScreen> {
  int _selectedTabIndex = 0; // 0: Lịch dạy, 1: Danh sách lớp, 2: Sơ đồ lớp
  final List<String> _tabs = ['Lịch dạy', 'Danh sách lớp', 'Sơ đồ lớp'];

  final StudentService _studentService = StudentService();

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<DocumentSnapshot>(
      stream: FirebaseFirestore.instance
          .collection('classes')
          .doc(widget.classId)
          .snapshots(),
      builder: (context, classSnapshot) {
        if (classSnapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (classSnapshot.hasError || !classSnapshot.hasData || !classSnapshot.data!.exists) {
          return Scaffold(
            backgroundColor: AppColors.appBg,
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('Không tìm thấy thông tin lớp học.'),
                  const SizedBox(height: 12),
                  ElevatedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('Quay lại'),
                  ),
                ],
              ),
            ),
          );
        }

        final classData = classSnapshot.data!.data() as Map<String, dynamic>;
        final cls = ClassModel(
          id: widget.classId,
          name: classData['class_name'] ?? 'Lớp học',
          room: classData['classroom_id'] ?? classData['classroom_name'] ?? 'Chưa cập nhật',
          schedule: '',
          students: (classData['class_size'] as num?)?.toInt() ?? 0,
          grade: (classData['grade'] ?? '12').toString(),
        );

        return Scaffold(
          backgroundColor: AppColors.appBg,
          body: Column(
            children: [
              _buildScreenHeader(context, cls),
              Expanded(
                child: Transform.translate(
                  offset: const Offset(0, -16),
                  child: Container(
                    width: double.infinity,
                    decoration: const BoxDecoration(
                      color: AppColors.appBg,
                      borderRadius: BorderRadius.only(
                        topLeft: Radius.circular(24),
                        topRight: Radius.circular(24),
                      ),
                    ),
                    child: Column(
                      children: [
                        const SizedBox(height: 16),
                        // 3 Tab điều hướng
                        Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          child: Container(
                            height: 44,
                            padding: const EdgeInsets.all(4),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(color: AppColors.hair),
                            ),
                            child: Row(
                              children: List.generate(_tabs.length, (index) {
                                final isSelected = _selectedTabIndex == index;
                                return Expanded(
                                  child: GestureDetector(
                                    onTap: () => setState(() => _selectedTabIndex = index),
                                    child: AnimatedContainer(
                                      duration: const Duration(milliseconds: 200),
                                      alignment: Alignment.center,
                                      decoration: BoxDecoration(
                                        color: isSelected ? AppColors.navy : Colors.transparent,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: Text(
                                        _tabs[index],
                                        style: TextStyle(
                                          fontSize: 13,
                                          fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                                          color: isSelected ? Colors.white : AppColors.muted,
                                        ),
                                      ),
                                    ),
                                  ),
                                );
                              }),
                            ),
                          ),
                        ),
                        const SizedBox(height: 14),
                        Expanded(
                          child: _buildTabContent(cls),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildTabContent(ClassModel cls) {
    switch (_selectedTabIndex) {
      case 0:
        return _buildSchedulesTab();
      case 1:
        return _buildStudentListTab(cls);
      case 2:
      default:
        return SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          child: SeatingChartWidget(
            classId: cls.id,
            totalStudents: cls.students,
          ),
        );
    }
  }

  // TAB 0: LỊCH HỌC (LẤY TỪ SCHEDULES THEO LỚP)
  Widget _buildSchedulesTab() {
    return StreamBuilder<QuerySnapshot>(
      stream: FirebaseFirestore.instance
          .collection('schedules')
          .where('class_id', isEqualTo: widget.classId)
          .snapshots(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        final docs = snapshot.data?.docs ?? [];
        if (docs.isEmpty) {
          return const Center(
            child: Text(
              'Chưa có lịch học nào được thiết lập.',
              style: TextStyle(fontSize: 14, color: AppColors.muted),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          itemCount: docs.length,
          itemBuilder: (context, index) {
            final data = docs[index].data() as Map<String, dynamic>;
            return Card(
              elevation: 0,
              margin: const EdgeInsets.only(bottom: 12),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.hair),
              ),
              color: Colors.white,
              child: ListTile(
                title: Text(
                  data['subject_name'] ?? data['title'] ?? 'Tiết học',
                  style: const TextStyle(fontWeight: FontWeight.bold, color: AppColors.navy),
                ),
                subtitle: Text(
                  '${data['day_of_week'] ?? ''} · ${data['start_time'] ?? ''} - ${data['end_time'] ?? ''}',
                  style: const TextStyle(fontSize: 13, color: AppColors.muted),
                ),
                trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.black26),
              ),
            );
          },
        );
      },
    );
  }

  // TAB 1: DANH SÁCH HỌC SINH TỪ ENROLLMENTS & STUDENTS
  Widget _buildStudentListTab(ClassModel cls) {
    return StreamBuilder<List<StudentModel>>(
      stream: _studentService.getStudentsStream(cls.id),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(
            child: Text(
              'Lỗi tải danh sách: ${snapshot.error}',
              style: const TextStyle(color: Colors.red),
            ),
          );
        }

        final students = snapshot.data ?? [];

        if (students.isEmpty) {
          return const Center(
            child: Text(
              'Chưa có học sinh nào trong lớp này.',
              style: TextStyle(fontSize: 14, color: AppColors.muted),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          itemCount: students.length,
          itemBuilder: (context, index) {
            final student = students[index];
            final hasSeat = (student.row ?? 0) > 0 && (student.column ?? 0) > 0;

            return Card(
              elevation: 0,
              margin: const EdgeInsets.only(bottom: 8),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14),
                side: const BorderSide(color: AppColors.hair),
              ),
              color: Colors.white,
              child: ListTile(
                leading: CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.lightBlue,
                  child: Text(
                    '${index + 1}',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: AppColors.brand,
                    ),
                  ),
                ),
                title: Text(
                  student.name,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: AppColors.navy,
                  ),
                ),
                subtitle: Text(
                  hasSeat
                      ? 'Vị trí: Hàng ${student.row}, Cột ${student.column}'
                      : 'Chưa xếp chỗ',
                  style: TextStyle(
                    fontSize: 12,
                    color: hasSeat ? AppColors.brand : AppColors.muted,
                    fontWeight: hasSeat ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
                trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.black26),
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildScreenHeader(BuildContext context, ClassModel cls) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 36),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.navy, AppColors.darkBlue],
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          InkWell(
            onTap: () => Navigator.pop(context),
            borderRadius: BorderRadius.circular(20),
            child: Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.arrow_back,
                color: Colors.white,
                size: 22,
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  cls.name,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                    height: 1.2,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  'Phòng ${cls.room} · ${cls.students} học sinh',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withOpacity(0.7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}