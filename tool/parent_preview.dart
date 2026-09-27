// Bản xem thử giao diện phụ huynh với Firestore giả (không cần đăng nhập Google).
// Chạy: flutter run -t tool/parent_preview.dart --dart-define=PREVIEW_UID=p1
//   p1      : phụ huynh có 2 con (1 con liên kết qua parent_id, 1 con qua parent_email)
//   p_empty : phụ huynh chưa liên kết con nào
import 'package:flutter/material.dart';

import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/home_screen.dart';

import '../test/fixtures/parent_fixture.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const uid = String.fromEnvironment('PREVIEW_UID', defaultValue: 'p1');
  const email = uid == 'p1' ? 'mai@gmail.com' : 'x@gmail.com';

  final db = await seedDb();
  ParentSession.instance = ParentSession(service: ParentService(db: db));

  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: HomeScreen(uid: uid, email: email),
  ));
}
