import 'package:flutter/material.dart';

import '../../../../../core/constants/app_colors.dart';
import '../../../../../core/models/student_model.dart';

/// Lưới sơ đồ chỗ ngồi: bục giảng + các ô ghế.
/// Khi [isEdit] = true: tap ô trống để thêm học sinh, nhấn giữ + kéo để đổi chỗ.
/// Khi [isEdit] = false: chỉ hiển thị, không tương tác.
class SeatingGrid extends StatelessWidget {
  const SeatingGrid({
    super.key,
    required this.rows,
    required this.cols,
    required this.seats,
    required this.homeroomRoster,
    required this.isEdit,
    required this.onTapCell,
    required this.onSwapSeats,
  });

  final int rows;
  final int cols;
  final List<String?> seats;
  final List<StudentModel> homeroomRoster;
  final bool isEdit;
  final void Function(int index) onTapCell;
  final void Function(int fromIndex, int toIndex) onSwapSeats;

  StudentModel? _studentFor(String? id) {
    if (id == null) return null;
    try {
      return homeroomRoster.firstWhere((s) => s.id == id);
    } catch (_) {
      return null;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        _buildPodium(),
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
          itemBuilder: (context, index) => _buildCell(context, index),
        ),
      ],
    );
  }

  Widget _buildPodium() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 8),
      margin: const EdgeInsets.only(bottom: 20),
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
    );
  }

  Widget _buildSeatContent(String? studentId, StudentModel? student) {
    return Container(
      decoration: BoxDecoration(
        color: studentId != null ? const Color(0xFFE9F8EF) : AppColors.appBg,
        border: Border.all(
          color: studentId != null ? const Color(0xFFBFE6CF) : AppColors.hair,
        ),
        borderRadius: BorderRadius.circular(6),
      ),
      child: studentId != null
          ? Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  student?.short ?? '...',
                  style: const TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF137A41),
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            )
          : (isEdit ? const Icon(Icons.add, size: 14, color: AppColors.muted) : null),
    );
  }

  Widget _buildCell(BuildContext context, int index) {
    final studentId = seats[index];
    final student = _studentFor(studentId);
    final cellContent = _buildSeatContent(studentId, student);

    if (!isEdit) return cellContent;

    return DragTarget<int>(
      onAccept: (draggedIndex) => onSwapSeats(draggedIndex, index),
      builder: (context, candidateData, rejectedData) {
        if (candidateData.isNotEmpty) {
          return Container(
            decoration: BoxDecoration(
              color: AppColors.lightBlue,
              border: Border.all(color: AppColors.brand, width: 2),
              borderRadius: BorderRadius.circular(6),
            ),
          );
        }

        if (studentId == null) {
          return InkWell(
            onTap: () => onTapCell(index),
            child: cellContent,
          );
        }

        return LongPressDraggable<int>(
          data: index,
          delay: const Duration(milliseconds: 150),
          feedback: _buildDragFeedback(context, student),
          childWhenDragging: Container(
            decoration: BoxDecoration(
              color: AppColors.appBg,
              border: Border.all(color: AppColors.hair),
              borderRadius: BorderRadius.circular(6),
            ),
          ),
          child: cellContent,
        );
      },
    );
  }

  Widget _buildDragFeedback(BuildContext context, StudentModel? student) {
    final size = MediaQuery.of(context).size.width / cols - 4;
    return Material(
      color: Colors.transparent,
      child: Transform.scale(
        scale: 1.2,
        child: SizedBox(
          width: size,
          height: size,
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: AppColors.brand, width: 2),
              borderRadius: BorderRadius.circular(6),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.2),
                  blurRadius: 10,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            alignment: Alignment.center,
            child: Text(
              student?.short ?? '...',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.bold,
                color: AppColors.brand,
              ),
            ),
          ),
        ),
      ),
    );
  }
}
