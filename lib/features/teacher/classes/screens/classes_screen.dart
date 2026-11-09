import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/class_model.dart';
import '../../class_detail/screens/class_detail_screen.dart';
import '../widgets/class_card.dart';
import 'teacher_month_classes_service.dart';

class ClassScreen extends StatefulWidget {
  const ClassScreen({super.key});
  
  @override
  State<ClassScreen> createState() => _ClassScreenState();
}

class _ClassScreenState extends State<ClassScreen> {
  Stream<List<QueryDocumentSnapshot<Map<String, dynamic>>>>? _classesStream;

  @override
  void initState() {
    super.initState();
    final teacherId = FirebaseAuth.instance.currentUser?.uid;
    if (teacherId != null) {
      _classesStream =
          TeacherMonthClassesService().classesOfMonthStream(teacherId);
    }
  }

  @override
  Widget build(BuildContext context) {
    final now = DateTime.now();

    return Scaffold(
      backgroundColor: AppColors.appBg,
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.fromLTRB(20, 56, 20, 36),
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [AppColors.navy, AppColors.darkBlue],
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Danh sách lớp đang dạy',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Tháng ${now.month}/${now.year}',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w500,
                    color: Colors.white.withValues(alpha: 0.7),
                  ),
                ),
              ],
            ),
          ),
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
                child: _buildBody(),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    final stream = _classesStream;
    if (stream == null) {
      return const Center(
        child: Text(
          'Vui lòng đăng nhập để xem danh sách lớp.',
          style: TextStyle(color: AppColors.muted),
        ),
      );
    }

    return StreamBuilder<List<QueryDocumentSnapshot<Map<String, dynamic>>>>(
      stream: stream,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }

        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                'Lỗi tải dữ liệu: ${snapshot.error}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.red),
              ),
            ),
          );
        }

        final docs = snapshot.data ?? [];

        if (docs.isEmpty) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'Tháng này bạn chưa có buổi dạy nào.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.muted),
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 20, 16, 24),
          itemCount: docs.length,
          itemBuilder: (context, index) {
            final data = docs[index].data();
            final String docId = docs[index].id;
            final String name = (data['class_name'] ?? 'Lớp học').toString();

            final ClassModel cls = ClassModel(
              id: docId,
              name: name,
              room: (data['room'] ?? 'Chưa cập nhật').toString(),
              schedule: '',
              students: _countStudents(data['seat_map']),
              grade: RegExp(r'^\d+').firstMatch(name)?.group(0) ?? '',
            );

            return ClassCard(
              classInfo: cls,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ClassDetailScreen(classId: docId),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  /// Sĩ số = số ghế có học sinh thật trong `classes2.seat_map`
  /// (bỏ qua ghế khóa và student_id rỗng hoặc chuỗi "null").
  int _countStudents(dynamic seatMap) {
    if (seatMap is! Map) return 0;
    var n = 0;
    for (final v in seatMap.values) {
      if (v is! Map || v['status'] == 'locked') continue;
      final id = v['student_id'];
      if (id is String && id.isNotEmpty && id != 'null') n++;
    }
    return n;
  }
}
