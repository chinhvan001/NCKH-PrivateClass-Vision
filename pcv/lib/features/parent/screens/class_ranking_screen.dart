import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';
import '../utils/app_colors.dart';
import '../utils/app_text_styles.dart';
import '../widgets/common_widgets.dart';
import '../models/supervised_student_model.dart';
import '../services/student_service.dart';
import '../services/monitoring_session_service.dart';

class ClassRankingScreen extends StatefulWidget {
  const ClassRankingScreen({super.key});

  @override
  State<ClassRankingScreen> createState() => _ClassRankingScreenState();
}

class _ClassRankingScreenState extends State<ClassRankingScreen> {
  static const String _parentId = 'MfKMuHu5NreYs1A9IO4YJ5AuZao2';

  final _studentService = StudentService();
  final _monitoringService = MonitoringSessionService();

  late Future<_RankingData> _dataFuture;

  @override
  void initState() {
    super.initState();
    _dataFuture = _loadData();
  }

  Future<_RankingData> _loadData() async {
    final students = await _studentService.getStudentsByParent(_parentId);
    if (students.isEmpty) return _RankingData(rankings: [], myRank: 0, myScore: 0);

    final student = students.first;
    final mySupervised =
        await _monitoringService.getSupervisedDataByStudent(student.id);
    if (mySupervised.isEmpty) {
      return _RankingData(rankings: [], myRank: 0, myScore: 0);
    }

    // Lấy buổi học gần nhất
    final latestSession = mySupervised.last;
    if (latestSession.monitoringSessionId.isEmpty) {
      return _RankingData(rankings: [], myRank: 0, myScore: 0);
    }

    // Lấy tất cả học sinh trong cùng buổi
    final snapshot = await FirebaseFirestore.instance
        .collection('supervised_students')
        .where('monitoring_session_id',
            isEqualTo: latestSession.monitoringSessionId)
        .get();

    final allStudents = snapshot.docs
        .map(SupervisedStudentModel.fromFirestore)
        .where((s) => s.isPresent)
        .toList();

    // Sắp xếp theo attention_score giảm dần
    allStudents.sort((a, b) => b.attentionScore.compareTo(a.attentionScore));

    final rankings = allStudents
        .asMap()
        .entries
        .map((e) => _RankEntry(
              rank: e.key + 1,
              studentId: e.value.studentId,
              attentionScore: e.value.attentionScore,
              isMe: e.value.studentId == student.id,
            ))
        .toList();

    final myRankEntry = rankings.where((r) => r.isMe).firstOrNull;

    return _RankingData(
      rankings: rankings,
      myRank: myRankEntry?.rank ?? 0,
      myScore: myRankEntry?.attentionScore ?? 0,
    );
  }

  void _reload() => setState(() => _dataFuture = _loadData());

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.backgroundGrey,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: Navigator.canPop(context)
            ? IconButton(
                icon: const Icon(Icons.arrow_back_ios,
                    color: AppColors.textPrimary, size: 20),
                onPressed: () => Navigator.pop(context),
              )
            : null,
        title:
            const Text('Xếp hạng trong lớp', style: AppTextStyles.heading2),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded,
                color: AppColors.textSecondary, size: 22),
            onPressed: _reload,
          ),
        ],
      ),
      body: FutureBuilder<_RankingData>(
        future: _dataFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(
                child: CircularProgressIndicator(color: AppColors.primary));
          }
          if (snapshot.hasError) {
            return Center(
                child: Text(
                    snapshot.error.toString().replaceFirst('Exception: ', ''),
                    style: AppTextStyles.caption,
                    textAlign: TextAlign.center));
          }

          final data = snapshot.data!;
          if (data.rankings.isEmpty) {
            return Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: const BoxDecoration(
                        color: AppColors.accentLight, shape: BoxShape.circle),
                    child: const Icon(Icons.leaderboard_rounded,
                        size: 44, color: AppColors.primary),
                  ),
                  const SizedBox(height: 14),
                  const Text('Chưa có dữ liệu', style: AppTextStyles.heading3),
                ],
              ),
            );
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            physics: const BouncingScrollPhysics(),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── My rank card ───────────────────────────────────
                if (data.myRank > 0)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.primary, AppColors.primaryLight],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      borderRadius: BorderRadius.circular(14),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.primary.withValues(alpha: 0.28),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 60,
                          height: 60,
                          decoration: BoxDecoration(
                            color: Colors.white.withValues(alpha: 0.2),
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Text(
                              '#${data.myRank}',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Xếp hạng của con',
                                  style: TextStyle(
                                      color: Colors.white70, fontSize: 12)),
                              const SizedBox(height: 4),
                              Text(
                                'Hạng ${data.myRank}/${data.rankings.length}',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text(
                                'Điểm tập trung: ${data.myScore.round()}%',
                                style: const TextStyle(
                                    color: Colors.white70, fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        Icon(
                          data.myRank <= 3
                              ? Icons.emoji_events_rounded
                              : Icons.person_rounded,
                          color: data.myRank == 1
                              ? const Color(0xFFFFD700)
                              : data.myRank == 2
                                  ? const Color(0xFFC0C0C0)
                                  : data.myRank == 3
                                      ? const Color(0xFFCD7F32)
                                      : Colors.white70,
                          size: 32,
                        ),
                      ],
                    ),
                  ),
                const SizedBox(height: 14),

                // ── Full ranking list ──────────────────────────────
                AppCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text('Bảng xếp hạng',
                              style: AppTextStyles.heading3),
                          const Spacer(),
                          Text('Buổi gần nhất',
                              style: AppTextStyles.caption),
                        ],
                      ),
                      const SizedBox(height: 14),
                      ...data.rankings.map((r) => _RankRow(entry: r)),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _RankRow extends StatelessWidget {
  final _RankEntry entry;
  const _RankRow({required this.entry});

  Color _rankColor(int rank) {
    if (rank == 1) return const Color(0xFFFFD700);
    if (rank == 2) return const Color(0xFFC0C0C0);
    if (rank == 3) return const Color(0xFFCD7F32);
    return AppColors.textSecondary;
  }

  @override
  Widget build(BuildContext context) {
    final pColor = entry.attentionScore >= 70
        ? AppColors.green
        : entry.attentionScore >= 40
            ? AppColors.orange
            : AppColors.red;

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: entry.isMe ? AppColors.accentLight : AppColors.backgroundGrey,
        borderRadius: BorderRadius.circular(10),
        border: entry.isMe
            ? Border.all(color: AppColors.primary, width: 1.5)
            : null,
      ),
      child: Row(
        children: [
          // Rank badge
          SizedBox(
            width: 28,
            child: entry.rank <= 3
                ? Icon(Icons.emoji_events_rounded,
                    color: _rankColor(entry.rank), size: 20)
                : Text(
                    '${entry.rank}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: _rankColor(entry.rank),
                    ),
                    textAlign: TextAlign.center,
                  ),
          ),
          const SizedBox(width: 8),
          // Student label
          Expanded(
            child: Text(
              entry.isMe ? 'Con bạn' : 'HS ${entry.rank}',
              style: AppTextStyles.body2.copyWith(
                fontWeight: entry.isMe ? FontWeight.bold : FontWeight.normal,
                color: entry.isMe ? AppColors.primary : AppColors.textPrimary,
              ),
            ),
          ),
          // Score bar
          SizedBox(
            width: 100,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: entry.attentionScore / 100,
                minHeight: 7,
                backgroundColor: AppColors.divider,
                valueColor: AlwaysStoppedAnimation<Color>(pColor),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            '${entry.attentionScore.round()}%',
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: pColor,
            ),
          ),
        ],
      ),
    );
  }
}

class _RankingData {
  final List<_RankEntry> rankings;
  final int myRank;
  final double myScore;
  _RankingData(
      {required this.rankings, required this.myRank, required this.myScore});
}

class _RankEntry {
  final int rank;
  final String studentId;
  final double attentionScore;
  final bool isMe;
  _RankEntry({
    required this.rank,
    required this.studentId,
    required this.attentionScore,
    required this.isMe,
  });
}
