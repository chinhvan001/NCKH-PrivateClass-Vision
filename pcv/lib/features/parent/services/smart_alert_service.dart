import '../models/supervised_student_model.dart';
import 'monitoring_session_service.dart';
import 'student_service.dart';

/// Dịch vụ phát hiện xu hướng tập trung thông minh.
/// Phân tích dữ liệu từ supervised_students để cảnh báo phụ huynh.
class SmartAlertService {
  final StudentService _studentService = StudentService();
  final MonitoringSessionService _monitoringService =
      MonitoringSessionService();

  /// Lấy tất cả cảnh báo cho parent
  Future<List<SmartAlert>> getAlerts(String parentId) async {
    final alerts = <SmartAlert>[];

    final students = await _studentService.getStudentsByParent(parentId);
    if (students.isEmpty) return alerts;

    final student = students.first;
    final supervised =
        await _monitoringService.getSupervisedDataByStudent(student.id);

    if (supervised.isEmpty) return alerts;

    // ── 1. Xu hướng giảm liên tiếp ──────────────────────────────────
    final trend = _detectDecreasingTrend(supervised);
    if (trend != null) alerts.add(trend);

    // ── 2. Vắng nhiều ────────────────────────────────────────────────
    final absentAlert = _detectHighAbsence(supervised);
    if (absentAlert != null) alerts.add(absentAlert);

    // ── 3. Điểm thấp liên tục ────────────────────────────────────────
    final lowScoreAlert = _detectLowScore(supervised);
    if (lowScoreAlert != null) alerts.add(lowScoreAlert);

    // ── 4. Cải thiện tốt ─────────────────────────────────────────────
    final improvementAlert = _detectImprovement(supervised);
    if (improvementAlert != null) alerts.add(improvementAlert);

    // ── 5. Tập trung xuất sắc ─────────────────────────────────────────
    final excellentAlert = _detectExcellent(supervised);
    if (excellentAlert != null) alerts.add(excellentAlert);

    return alerts;
  }

  /// Phát hiện 3 buổi liên tiếp giảm điểm
  SmartAlert? _detectDecreasingTrend(List<SupervisedStudentModel> list) {
    if (list.length < 3) return null;
    final last3 = list.sublist(list.length - 3);
    final isDecreasing = last3[0].attentionScore > last3[1].attentionScore &&
        last3[1].attentionScore > last3[2].attentionScore;
    if (!isDecreasing) return null;
    return SmartAlert(
      type: AlertType.warning,
      title: 'Xu hướng giảm tập trung',
      message:
          'Con có xu hướng giảm tập trung trong 3 buổi gần nhất: '
          '${last3[0].attentionPercent}% → ${last3[1].attentionPercent}% → ${last3[2].attentionPercent}%. '
          'Hãy hỏi thăm con.',
      icon: '📉',
    );
  }

  /// Phát hiện vắng nhiều (> 30% số buổi)
  SmartAlert? _detectHighAbsence(List<SupervisedStudentModel> list) {
    if (list.isEmpty) return null;
    final absentCount = list.where((s) => !s.isPresent).length;
    final ratio = absentCount / list.length;
    if (ratio <= 0.3) return null;
    return SmartAlert(
      type: AlertType.danger,
      title: 'Vắng mặt nhiều',
      message:
          'Con đã vắng $absentCount/${list.length} buổi học '
          '(${(ratio * 100).round()}%). Cần chú ý theo dõi.',
      icon: '🚨',
    );
  }

  /// Phát hiện điểm thấp liên tục (< 40% trong 3 buổi)
  SmartAlert? _detectLowScore(List<SupervisedStudentModel> list) {
    if (list.length < 3) return null;
    final last3 = list.sublist(list.length - 3);
    final allLow = last3.every((s) => s.isPresent && s.attentionScore < 40);
    if (!allLow) return null;
    final avg =
        last3.map((s) => s.attentionScore).reduce((a, b) => a + b) / 3;
    return SmartAlert(
      type: AlertType.warning,
      title: 'Điểm tập trung thấp',
      message:
          'Con có điểm tập trung thấp trong 3 buổi gần nhất '
          '(trung bình ${avg.round()}%). Cần trao đổi với giáo viên.',
      icon: '⚠️',
    );
  }

  /// Phát hiện cải thiện (3 buổi liên tiếp tăng)
  SmartAlert? _detectImprovement(List<SupervisedStudentModel> list) {
    if (list.length < 3) return null;
    final last3 = list.sublist(list.length - 3);
    final isIncreasing = last3[0].attentionScore < last3[1].attentionScore &&
        last3[1].attentionScore < last3[2].attentionScore;
    if (!isIncreasing) return null;
    return SmartAlert(
      type: AlertType.success,
      title: 'Con đang cải thiện!',
      message:
          'Con đang tiến bộ tốt trong 3 buổi gần nhất: '
          '${last3[0].attentionPercent}% → ${last3[1].attentionPercent}% → ${last3[2].attentionPercent}%. '
          'Hãy khen ngợi con!',
      icon: '🎉',
    );
  }

  /// Phát hiện tập trung xuất sắc (TB >= 85%)
  SmartAlert? _detectExcellent(List<SupervisedStudentModel> list) {
    if (list.isEmpty) return null;
    final present = list.where((s) => s.isPresent).toList();
    if (present.isEmpty) return null;
    final avg =
        present.map((s) => s.attentionScore).reduce((a, b) => a + b) /
            present.length;
    if (avg < 85) return null;
    return SmartAlert(
      type: AlertType.success,
      title: 'Tập trung xuất sắc!',
      message:
          'Con có điểm tập trung trung bình ${avg.round()}% — xuất sắc! '
          'Tiếp tục duy trì phong độ.',
      icon: '🏆',
    );
  }
}

enum AlertType { success, warning, danger, info }

class SmartAlert {
  final AlertType type;
  final String title;
  final String message;
  final String icon;

  SmartAlert({
    required this.type,
    required this.title,
    required this.message,
    required this.icon,
  });
}
