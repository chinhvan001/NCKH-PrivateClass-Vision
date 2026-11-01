import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:flutter_privateclass_vision/core/models/parent_model.dart';
import 'package:flutter_privateclass_vision/core/services/parent_service.dart';

/// Trạng thái phía phụ huynh dùng chung cho mọi màn hình:
/// hồ sơ phụ huynh, danh sách con đã liên kết và con đang được chọn.
///
/// HomeScreen gọi [attach] khi mở và [detach] khi đóng (đăng xuất).
/// Các màn hình khác chỉ cần đọc [ParentSession.instance] và lắng nghe thay đổi.
class ParentSession extends ChangeNotifier {
  ParentSession({ParentService? service}) : _service = service ?? ParentService();

  /// Dùng chung toàn app; test/preview có thể thay bằng bản dùng Firestore giả
  static ParentSession instance = ParentSession();

  final ParentService _service;
  StreamSubscription<List<LinkedChild>>? _sub;
  String? _uid;
  String? _email;
  int _owners = 0;
  int _loadToken = 0;

  bool isLoading = true;
  String? error;
  ParentModel? parent;
  List<LinkedChild> children = const [];
  LinkedChild? selectedChild;

  bool get hasChildren => children.isNotEmpty;

  // Lưu con đang chọn theo từng tài khoản để máy dùng chung vẫn nhớ đúng
  String _prefsKey(String uid) => 'selected_child_id_$uid';

  void attach(String uid, {String? email}) {
    _owners++;
    if (_uid == uid && _sub != null) return;
    _reset();
    _uid = uid;
    _email = email;
    _listen();
  }

  void detach() {
    if (_owners > 0) _owners--;
    // Widget mới có thể attach trước khi widget cũ dispose, nên chỉ huỷ khi hết người dùng
    if (_owners == 0) {
      _reset();
      _uid = null;
      _email = null;
    }
  }

  /// Tải lại từ đầu (nút "Thử lại" khi lỗi mạng hoặc chưa có liên kết)
  void reload() {
    if (_uid == null) return;
    _reset();
    notifyListeners();
    _listen();
  }

  Future<void> selectChild(LinkedChild child) async {
    if (selectedChild?.id == child.id) return;
    selectedChild = child;
    notifyListeners();

    final uid = _uid;
    if (uid == null) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKey(uid), child.id);
  }

  void _listen() {
    _sub = _service.watchChildren(uid: _uid!, email: _email).listen(
      _onChildrenChanged,
      onError: (Object e) {
        debugPrint('ParentSession: lỗi tải danh sách con: $e');
        error = e.toString();
        isLoading = false;
        notifyListeners();
      },
    );
  }

  Future<void> _onChildrenChanged(List<LinkedChild> kids) async {
    final token = ++_loadToken;
    try {
      final newParent = parent ?? await _service.getParent(_uid!);
      final selected = await _pickSelected(kids);
      // Bỏ qua kết quả cũ nếu trong lúc chờ đã có thay đổi mới hoặc đã đăng xuất
      if (token != _loadToken) return;

      parent = newParent;
      children = kids;
      selectedChild = selected;
      error = null;
    } catch (e) {
      if (token != _loadToken) return;
      debugPrint('ParentSession: lỗi tải hồ sơ phụ huynh: $e');
      error = e.toString();
    }
    isLoading = false;
    notifyListeners();
  }

  /// Giữ con đang chọn nếu vẫn còn liên kết, nếu không thì lấy con đã lưu, cuối cùng là con đầu tiên
  Future<LinkedChild?> _pickSelected(List<LinkedChild> kids) async {
    if (kids.isEmpty) return null;

    String? wantedId = selectedChild?.id;
    final uid = _uid;
    if (wantedId == null && uid != null) {
      final prefs = await SharedPreferences.getInstance();
      wantedId = prefs.getString(_prefsKey(uid));
    }

    for (final kid in kids) {
      if (kid.id == wantedId) return kid;
    }
    return kids.first;
  }

  void _reset() {
    _sub?.cancel();
    _sub = null;
    _loadToken++;
    isLoading = true;
    error = null;
    parent = null;
    children = const [];
    selectedChild = null;
  }
}
