import 'package:flutter/material.dart';

import 'dart:math';

import 'account_screen.dart';
import 'classes_screen.dart'; // Import để dùng ClassModel và mockClasses

// --- MOCK DATA: DANH SÁCH HỌC SINH ---
// Danh sách 42 tên học sinh mẫu dựa trên hình ảnh
const List<String> studentNames = [
  'An',
  'Bảo',
  'Cường',
  'Dũng',
  'Hà',
  'Huy',
  'Khang',
  'Linh',
  'Minh',
  'Nam',
  'Ngọc',
  'Oanh',
  'Phúc',
  'Quân',
  'Sơn',
  'Trang',
  'Tú',
  'Uyên',
  'Vy',
  'Yến',
  'Bình',
  'Châu',
  'Đạt',
  'Hương',
  'Kiên',
  'Lan',
  'Mai',
  'Nhung',
  'Phong',
  'Quỳnh',
  'Sang',
  'Thảo',
  'Trí',
  'Vân',
  'Việt',
  'Xuân',
  'Ánh',
  'Diệp',
  'Hòa',
  'Long',
  'Tâm',
  'Yên',
];

// Hàm tạo danh sách học sinh ngẫu nhiên cho từng lớp (để tránh 4 lớp giống hệt nhau)
// Hàm tạo danh sách học sinh ngẫu nhiên cho từng lớp
List<String> getStudentsForClass(String classId) {
  List<String> shuffled = List.of(studentNames);

  var random = Random(classId.hashCode);
  shuffled.shuffle(random);

  final classInfo = mockClasses.firstWhere(
    (c) => c.id == classId,
    orElse: () => mockClasses.first,
  );

  // Không giới hạn số lượng nữa, nếu lớp 45 học sinh, lấy đủ 45.
  // (Lưu ý: Mảng studentNames mẫu của chúng ta đang chỉ có 42 cái tên.
  // Để lớp 45 không bị lỗi, mình sẽ nhân đôi danh sách tên mẫu để đảm bảo luôn đủ người rút).
  if (shuffled.length < classInfo.students) {
    shuffled.addAll(List.of(studentNames));
    shuffled.shuffle(random); // Xáo trộn lại
  }

  return shuffled.take(classInfo.students).toList();
}

// ==========================================
// MÀN HÌNH CLASS DETAIL (CHI TIẾT LỚP HỌC)
// ==========================================
class ClassDetailScreen extends StatelessWidget {
  final String? classId;

  const ClassDetailScreen({super.key, this.classId});

  @override
  Widget build(BuildContext context) {
    // Tìm lớp học dựa trên classId được truyền vào, nếu null thì lấy lớp đầu tiên
    final ClassModel cls = mockClasses.firstWhere(
      (c) => c.id == classId,
      orElse: () => mockClasses.first,
    );

    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          // Header màu Navy
          _buildScreenHeader(context, cls),

          // Nội dung chính
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
                child: SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
                  child: Column(
                    children: [
                      // Card Thông tin cơ bản
                      _buildBasicInfoCard(cls),

                      const SizedBox(height: 20),

                      // Khối Sơ đồ lớp học
                      SeatingChartWidget(
                        classId: cls.id,
                        totalStudents: cls.students,
                      ),
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

  Widget _buildScreenHeader(BuildContext context, ClassModel cls) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 40),
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
                  'Phòng ${cls.room}',
                  style: TextStyle(
                    fontSize: 14,
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

  Widget _buildBasicInfoCard(ClassModel cls) {
    return Card(
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
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              width: 56,
              height: 56,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.brand, Color(0xFF1D4ED8)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(
                cls.id,
                style: const TextStyle(
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    cls.name,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: AppColors.navy,
                      height: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 16,
                    runSpacing: 4,
                    children: [
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.home_outlined,
                            size: 15,
                            color: AppColors.brand,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            'Phòng ${cls.room}',
                            style: const TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: AppColors.brand,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.calendar_today_outlined,
                            size: 15,
                            color: AppColors.muted,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            cls.schedule,
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.people_alt_outlined,
                            size: 15,
                            color: AppColors.muted,
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '${cls.students} học sinh',
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.muted,
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ==========================================
// REUSABLE WIDGET: SEATING CHART (SƠ ĐỒ LỚP HỌC)
// ==========================================
class SeatingChartWidget extends StatelessWidget {
  final String classId;
  final int totalStudents;

  const SeatingChartWidget({
    super.key,
    required this.classId,
    required this.totalStudents,
  });

  @override
  Widget build(BuildContext context) {
    final List<String> students = getStudentsForClass(classId);
    const int columns = 7;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Tiêu đề Sơ đồ lớp
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Sơ đồ lớp',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w800,
                color: AppColors.navy,
              ),
            ),
            // Thay "6 x 7 vị trí" bằng số lượng thực tế
            Text(
              '${students.length} vị trí',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w500,
                color: AppColors.muted.withOpacity(0.7),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // Khung trắng chứa sơ đồ
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.hair),
          ),
          child: Column(
            children: [
              // Nút BỤC GIẢNG
              Container(
                width: 200,
                padding: const EdgeInsets.symmetric(vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.navy,
                  borderRadius: BorderRadius.circular(8),
                ),
                alignment: Alignment.center,
                child: const Text(
                  'BỤC GIẢNG',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: Colors.white,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Lưới chỗ ngồi (Grid) - Tự động giãn hàng tùy số lượng học sinh
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: columns,
                  crossAxisSpacing: 8,
                  mainAxisSpacing: 12,
                  childAspectRatio: 1.0,
                ),
                itemCount: students.length,
                itemBuilder: (context, index) {
                  return Container(
                    decoration: BoxDecoration(
                      color: AppColors.lightBlue.withOpacity(0.4),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      students[index],
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                        color: AppColors.darkBlue,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }
}
