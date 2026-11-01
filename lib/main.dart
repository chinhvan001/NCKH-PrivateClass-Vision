import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'app.dart';


void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Chạy thẳng vào app (màn hình chính Giáo viên) không qua Auth:
  // runApp(const PrivateClassVision(home: MainScreen()));

  // Hoặc đổi sang màn hình Phụ huynh:
  // runApp(const PrivateClassVision(home: HomeScreen()));

  // Bật lại luồng Login Auth:
  runApp(const PrivateClassVision());
}
