import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/student_model.dart';
import '../controllers/class_detail_controller.dart';

class SeatingChartWidget extends StatelessWidget {
  final ClassDetailController controller;

  const SeatingChartWidget({super.key, required this.controller});

  @override
  Widget build(BuildContext context) {
    final int rows = controller.classroomRows;
    final int cols = controller.classroomColumns;
    final List<StudentModel> roster = controller.students;

    final List<StudentModel?> seats = List.filled(rows * cols, null);
    int assignedCount = 0;

    for (final student in roster) {
      final r = student.row ?? 0;
      final c = student.column ?? 0;

      if (r > 0 && c > 0 && r <= rows && c <= cols) {
        final index = (r - 1) * cols + (c - 1);
        if (index >= 0 && index < seats.length) {
          seats[index] = student;
          assignedCount++;
        }
      }
    }

    return SingleChildScrollView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.only(bottom: 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.hair),
            ),
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
                        fontSize: 16,
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
                      '$assignedCount/${rows * cols} chỗ',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w800,
                        color: AppColors.brand,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.hair),
            ),
            child: Column(
              children: [
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  margin: const EdgeInsets.only(bottom: 14),
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
                GridView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: cols,
                    crossAxisSpacing: 4,
                    mainAxisSpacing: 4,
                    childAspectRatio: 1.0,
                  ),
                  itemCount: rows * cols,
                  itemBuilder: (context, index) {
                    final student = seats[index];
                    final bool hasStudent = student != null;

                    return Container(
                      decoration: BoxDecoration(
                        color: hasStudent
                            ? const Color(0xFFE9F8EF)
                            : AppColors.appBg,
                        border: Border.all(
                          color: hasStudent
                              ? const Color(0xFFBFE6CF)
                              : AppColors.hair,
                        ),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      alignment: Alignment.center,
                      child: hasStudent
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
        ],
      ),
    );
  }
}
