import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_privateclass_vision/features/teacher/classes/screens/classroom_service.dart'
    show ClassroomService;

import '../../../../core/constants/app_colors.dart';
import '../../../../core/models/class_model.dart';
import '../../class_detail/screens/class_detail_screen.dart';
import 'teacher_month_classes_service.dart';

class ClassScreen extends StatefulWidget {
  const ClassScreen({super.key});

  @override
  State<ClassScreen> createState() => _ClassScreenState();
}

class _ClassScreenState extends State<ClassScreen> {
  final ClassroomService _classroomService = ClassroomService();

  // Stream được tạo MỘT LẦN (không tạo lại mỗi lần build).
  // null khi chưa đăng nhập.
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
                    color: Colors.white.withOpacity(0.7),
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
            final String roomId = (data['classroom_id'] ?? '').toString();

            return FutureBuilder<String>(
              future: _classroomService.getClassroomName(roomId),
              builder: (context, roomSnapshot) {
                final String displayRoom = roomSnapshot.data ?? roomId;

                final ClassModel cls = ClassModel(
                  id: docId,
                  name: data['class_name'] ?? 'Lớp học',
                  room: displayRoom,
                  schedule: '',
                  students: (data['class_size'] as num?)?.toInt() ?? 0,
                  grade: (data['grade'] ?? '12').toString(),
                );

                return _buildClassCard(context, cls, docId);
              },
            );
          },
        );
      },
    );
  }

  Widget _buildClassCard(BuildContext context, ClassModel cls, String docId) {
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
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ClassDetailScreen(classId: docId),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
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
                    cls.name.isNotEmpty
                        ? cls.name.replaceAll('Lớp ', '')
                        : '12',
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      color: Colors.white,
                    ),
                    textAlign: TextAlign.center,
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
                          fontSize: 18,
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
                                Icons.people_outline,
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
                const Icon(
                  Icons.chevron_right,
                  color: Colors.black26,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}