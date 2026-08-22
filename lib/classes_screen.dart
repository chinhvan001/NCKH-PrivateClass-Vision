import 'package:flutter/material.dart';
import 'class_detail_screen.dart';
import 'account_screen.dart'; // Import để dùng chung AppColors

// --- MOCK DATA ---
class ClassModel {
  final String id, name, grade, room, schedule;
  final int students;

  const ClassModel({
    required this.id,
    required this.name,
    required this.grade,
    required this.room,
    required this.schedule,
    required this.students,
  });
}

const List<ClassModel> mockClasses = [
  ClassModel(
    id: '12A1',
    name: 'Toán Đại số 12',
    grade: 'Khối 12',
    room: 'A203',
    schedule: 'T2, T4 · 08:00',
    students: 42,
  ),
  ClassModel(
    id: '12A2',
    name: 'Toán Hình học 12',
    grade: 'Khối 12',
    room: 'A204',
    schedule: 'T3, T5 · 10:00',
    students: 38,
  ),
  ClassModel(
    id: '11B1',
    name: 'Toán Đại số 11',
    grade: 'Khối 11',
    room: 'B102',
    schedule: 'T2, T6 · 14:00',
    students: 45,
  ),
  ClassModel(
    id: '10C1',
    name: 'Toán Cơ bản 10',
    grade: 'Khối 10',
    room: 'C301',
    schedule: 'T4, T7 · 08:00',
    students: 40,
  ),
];

const List<String> filters = ['Tất cả', 'Khối 12', 'Khối 11', 'Khối 10'];

// ==========================================
// MÀN HÌNH CLASSES (LỚP HỌC)
// ==========================================
class ClassesScreen extends StatefulWidget {
  final Function(String id)? onOpenClass;

  const ClassesScreen({super.key, this.onOpenClass});

  @override
  State<ClassesScreen> createState() => _ClassesScreenState();
}

class _ClassesScreenState extends State<ClassesScreen> {
  String _query = '';
  String _filter = 'Tất cả';

  // Lọc danh sách (Tương đương useMemo trong React)
  List<ClassModel> get _filteredList {
    return mockClasses.where((c) {
      final q = _query.trim().toLowerCase();
      final matchQ =
          q.isEmpty ||
          c.name.toLowerCase().contains(q) ||
          c.id.toLowerCase().contains(q);
      final matchF = _filter == 'Tất cả' || (c.grade.contains(_filter));
      return matchQ && matchF;
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          // App bar + Search
          _buildHeader(),

          // Filter chips
          _buildFilterChips(),

          // Danh sách Class Cards
          Expanded(child: _buildClassList()),
        ],
      ),
    );
  }

  // --- CÁC HÀM BUILD GIAO DIỆN CON ---

  Widget _buildHeader() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 56, 16, 12), // pt-14, pb-3, px-4
      child: Column(
        children: [
          // Row 1: Back + Title + Badge
          Row(
            children: [
              InkWell(
                onTap: () {
                  Navigator.pop(context);
                }, // Xử lý nút back nếu cần
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  width: 36,
                  height: 36,
                  decoration: const BoxDecoration(shape: BoxShape.circle),
                  child: const Icon(
                    Icons.arrow_back,
                    color: AppColors.navy,
                    size: 22,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'Lớp học',
                style: TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppColors.navy,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: AppColors.lightBlue,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  '${mockClasses.length} lớp',
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: AppColors.brand,
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Row 2: Search + Filter button
          Row(
            children: [
              Expanded(
                child: Container(
                  height: 44,
                  decoration: BoxDecoration(
                    color: AppColors.appBg,
                    border: Border.all(color: AppColors.hair),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 14),
                  child: Row(
                    children: [
                      const Icon(
                        Icons.search,
                        color: AppColors.muted,
                        size: 20,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: TextField(
                          onChanged: (value) => setState(() => _query = value),
                          style: const TextStyle(
                            fontSize: 14,
                            color: AppColors.navy,
                          ),
                          decoration: const InputDecoration(
                            hintText: 'Tìm lớp học...',
                            hintStyle: TextStyle(color: Colors.black38),
                            border: InputBorder.none,
                            isDense: true,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    return Container(
      width: double.infinity,
      color: Colors.white,
      padding: const EdgeInsets.only(bottom: 12),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(
          children: filters.map((f) {
            final isSelected = _filter == f;
            return Padding(
              padding: const EdgeInsets.only(right: 8),
              child: InkWell(
                onTap: () => setState(() => _filter = f),
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: isSelected ? AppColors.navy : AppColors.appBg,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    f,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: isSelected ? Colors.white : AppColors.muted,
                    ),
                  ),
                ),
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildClassList() {
    final list = _filteredList;

    if (list.isEmpty) {
      return const Padding(
        padding: EdgeInsets.only(top: 64),
        child: Text(
          'Không tìm thấy lớp học phù hợp.',
          style: TextStyle(fontSize: 14, color: AppColors.muted),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: list.length,
      itemBuilder: (context, index) {
        final c = list[index];

        // Thêm tiêu đề ở đầu danh sách
        if (index == 0) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Padding(
                padding: EdgeInsets.only(left: 4, bottom: 8),
                child: Text(
                  'Danh sách lớp đang dạy',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: AppColors.navy,
                  ),
                ),
              ),
              _buildClassCard(c),
            ],
          );
        }

        return _buildClassCard(c);
      },
    );
  }

  Widget _buildClassCard(ClassModel c) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.hair),
        ),
        color: Colors.white,
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ClassDetailScreen(classId: c.id),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                // Info Row
                Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [AppColors.brand, Color(0xFF1D4ED8)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        c.id,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            c.name,
                            style: const TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.w800,
                              color: AppColors.navy,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Row(
                            children: [
                              const Icon(
                                Icons.home_outlined,
                                size: 15,
                                color: AppColors.brand,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Phòng ${c.room}',
                                style: const TextStyle(
                                  fontSize: 13,
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.brand,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const Icon(Icons.chevron_right, color: Colors.black26),
                  ],
                ),

                const SizedBox(height: 12),
                const Divider(height: 1, color: AppColors.hair),
                const SizedBox(height: 12),

                // Meta info Row
                Row(
                  children: [
                    const Icon(
                      Icons.calendar_today_outlined,
                      size: 16,
                      color: AppColors.brand,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      c.schedule,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
                    ),

                    const SizedBox(width: 16),

                    const Icon(
                      Icons.people_alt_outlined,
                      size: 16,
                      color: AppColors.brand,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '${c.students} học sinh',
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.muted,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
