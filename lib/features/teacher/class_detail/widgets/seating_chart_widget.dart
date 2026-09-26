import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/student_model.dart';
import '../../../../core/services/student_service.dart';

class SeatingChartWidget extends StatelessWidget {
  final String classId;
  final int totalStudents;

  const SeatingChartWidget({
    super.key,
    required this.classId,
    required this.totalStudents,
  });

  final int _rows = 5;
  final int _cols = 8;

  @override
  Widget build(BuildContext context) {
    final StudentService studentService = StudentService();

    return StreamBuilder<List<StudentModel>>(
      stream: studentService.getStudentsStream(classId),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Padding(
            padding: EdgeInsets.symmetric(vertical: 40),
            child: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.hasError) {
          return Center(
            child: Text(
              'Lỗi tải sơ đồ: ${snapshot.error}',
              style: const TextStyle(color: Colors.red),
            ),
          );
        }

        final List<StudentModel> roster = snapshot.data ?? [];

        // Khởi tạo mảng 40 chỗ ngồi và map theo tọa độ row/column thật từ enrollments
        final List<StudentModel?> seats = List.filled(_rows * _cols, null);
        int assignedCount = 0;

        for (final student in roster) {
          final r = student.row ?? 0;
          final c = student.column ?? 0;

          if (r > 0 && c > 0) {
            final index = (r - 1) * _cols + (c - 1);
            if (index >= 0 && index < seats.length) {
              seats[index] = student;
              assignedCount++;
            }
          }
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thẻ tóm tắt chỗ ngồi
            Card(
              elevation: 0,
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.hair),
              ),
              color: Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Sĩ số thực tế',
                          style: TextStyle(fontSize: 12, color: AppColors.muted),
                        ),
                        Text(
                          '${roster.length} học sinh',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: AppColors.navy,
                          ),
                        ),
                      ],
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        const Text(
                          'Đã xếp chỗ',
                          style: TextStyle(fontSize: 12, color: AppColors.muted),
                        ),
                        Text(
                          '$assignedCount/${roster.length}',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            color: AppColors.brand,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),

            // Lưới hiển thị sơ đồ chỗ ngồi
            Card(
              elevation: 0,
              margin: EdgeInsets.zero,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: const BorderSide(color: AppColors.hair),
              ),
              color: Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    // Bục giảng
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: AppColors.navy,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      alignment: Alignment.center,
                      child: const Text(
                        'BỤC GIẢNG',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: Colors.white,
                          letterSpacing: 2.0,
                        ),
                      ),
                    ),

                    // Lưới 5x8
                    GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: _cols,
                        crossAxisSpacing: 4,
                        mainAxisSpacing: 4,
                        childAspectRatio: 1.0,
                      ),
                      itemCount: _rows * _cols,
                      itemBuilder: (context, index) {
                        final student = seats[index];

                        return Container(
                          decoration: BoxDecoration(
                            color: student != null
                                ? const Color(0xFFE9F8EF)
                                : AppColors.appBg,
                            border: Border.all(
                              color: student != null
                                  ? const Color(0xFFBFE6CF)
                                  : AppColors.hair,
                            ),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          alignment: Alignment.center,
                          child: student != null
                              ? Text(
                            student.short,
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Color(0xFF137A41),
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          )
                              : null,
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}