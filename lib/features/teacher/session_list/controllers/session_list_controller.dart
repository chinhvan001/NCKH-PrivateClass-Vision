// File: lib/features/teacher/session_list/controllers/session_list_controller.dart
import 'package:flutter/foundation.dart';
import 'package:firebase_auth/firebase_auth.dart';

import '../../../../core/models/session_model.dart';
import '../../../../core/services/session_service.dart';

class SessionListController extends ChangeNotifier {
  final SessionService _sessionService = SessionService();

  List<SessionModel> _sessions = [];
  bool _isLoading = false;
  String? _errorMessage;
  DateTime _selectedDate = DateTime.now();

  List<SessionModel> get sessions => _sessions;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  DateTime get selectedDate => _selectedDate;

  SessionListController() {
    loadSessionsForDate(_selectedDate);
  }

  void setSelectedDate(DateTime date) {
    _selectedDate = date;
    loadSessionsForDate(date);
  }

  Future<void> loadSessionsForDate(DateTime date) async {
    final DateTime startDate = DateTime(
      date.year,
      date.month,
      date.day,
      0,
      0,
      0,
    );
    final DateTime endDate = DateTime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
    );
    await loadSessionsForRange(startDate, endDate);
  }

  Future<void> loadSessionsForRange(DateTime? start, DateTime? end) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final User? user = FirebaseAuth.instance.currentUser;
      // Tạm thời để trống teacherId nếu chưa login để test dữ liệu mẫu
      final String teacherId = user?.uid ?? '';

      _sessions = await _sessionService.getSessionsByTimeRange(
        teacherId,
        start,
        end,
      );

      // ignore: avoid_print
      print('Đã tải ${_sessions.length} sessions');
    } catch (e) {
      _errorMessage = 'Không thể tải danh sách buổi dạy: $e';
      // ignore: avoid_print
      print('Lỗi loadSessionsForRange: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Stream<List<SessionModel>> getSessionsStreamForDate(DateTime date) {
    final User? user = FirebaseAuth.instance.currentUser;
    final String teacherId = user?.uid ?? '';

    final DateTime startDate = DateTime(
      date.year,
      date.month,
      date.day,
      0,
      0,
      0,
    );
    final DateTime endDate = DateTime(
      date.year,
      date.month,
      date.day,
      23,
      59,
      59,
    );

    return _sessionService.getSessionsStreamByTimeRange(
      teacherId,
      startDate,
      endDate,
    );
  }
}
