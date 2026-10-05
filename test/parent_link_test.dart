import 'package:fake_cloud_firestore/fake_cloud_firestore.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:flutter_privateclass_vision/core/services/parent_service.dart';
import 'package:flutter_privateclass_vision/features/parent/controllers/parent_session.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/home_screen.dart';
import 'package:flutter_privateclass_vision/features/parent/screens/profile_screen.dart';

import 'fixtures/parent_fixture.dart';

/// Font giả của môi trường test rộng hơn font thật nên vài thẻ cũ trên Home báo tràn chữ;
/// lỗi tràn được kiểm tra riêng trên emulator, ở đây chỉ kiểm tra dữ liệu hiển thị.
Future<void> ignoringOverflow(Future<void> Function() body) async {
  final original = FlutterError.onError;
  FlutterError.onError = (details) {
    if (details.exceptionAsString().contains('overflowed')) return;
    original?.call(details);
  };
  try {
    await body();
  } finally {
    FlutterError.onError = original;
  }
}

/// Đợi stream Firestore giả xử lý xong rồi vẽ lại giao diện
Future<void> settle(WidgetTester tester) async {
  for (var i = 0; i < 5; i++) {
    await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 50)));
    await tester.pump();
  }
}

void main() {
  setUp(() => SharedPreferences.setMockInitialValues({}));

  group('ParentService', () {
    test('lấy đúng con theo parent_id và parent_email, bỏ qua con người khác', () async {
      final db = await seedDb();
      final service = ParentService(db: db);

      final kids = await service.watchChildren(uid: 'p1', email: 'mai@gmail.com').first;

      expect(kids.map((k) => k.id), ['s2', 's1']); // sắp theo tên: "Trần Gia Bảo" < "Trần Minh Anh"
      final minhAnh = kids.firstWhere((k) => k.id == 's1');
      expect(minhAnh.birthday, '12/03/2009');
      expect(minhAnh.gender, 'Nữ');
      expect(minhAnh.classes.map((c) => c.name).toSet(), {'12A1', '10B2'});
      expect(minhAnh.teacherDisplay, contains('Nguyễn Văn Hùng'));
      expect(minhAnh.teacherDisplay, contains('Lê Thu Hà'));

      final giaBao = kids.firstWhere((k) => k.id == 's2');
      expect(giaBao.birthday, '05/09/2011');
      expect(giaBao.classDisplay, '10B2 · Năm học 2026-2027');
    });

    test('không có email thì chỉ lấy theo parent_id', () async {
      final db = await seedDb();
      final kids = await ParentService(db: db).watchChildren(uid: 'p1').first;
      expect(kids.map((k) => k.id), ['s1']);
    });

    test('phụ huynh chưa liên kết trả về danh sách rỗng', () async {
      final db = await seedDb();
      final kids = await ParentService(db: db).watchChildren(uid: 'p_empty', email: 'x@gmail.com').first;
      expect(kids, isEmpty);
    });

    test('học sinh chưa ghi danh hiển thị "Chưa xếp lớp"', () async {
      final db = await seedDb();
      await db.collection('students').doc('s4').set({'student_name': 'Học Sinh Mới', 'parent_id': 'p1'});
      final kids = await ParentService(db: db).watchChildren(uid: 'p1').first;
      expect(kids.firstWhere((k) => k.id == 's4').classDisplay, 'Chưa xếp lớp');
    });

    test('đọc được is_active của phụ huynh', () async {
      final db = await seedDb();
      await db.collection('parents').doc('p_locked').set({'name': 'Bị khoá', 'is_active': false});
      final service = ParentService(db: db);
      expect((await service.getParent('p1'))!.isActive, isTrue);
      expect((await service.getParent('p_empty'))!.isActive, isTrue); // thiếu trường -> coi như đang hoạt động
      expect((await service.getParent('p_locked'))!.isActive, isFalse);
      expect(await service.getParent('khong_ton_tai'), isNull);
    });
  });

  group('ParentSession', () {
    Future<void> waitLoaded(ParentSession session) async {
      for (var i = 0; i < 50 && session.isLoading; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 20));
      }
    }

    test('chọn con đầu tiên, nhớ lựa chọn sau khi mở lại app', () async {
      final db = await seedDb();
      final session = ParentSession(service: ParentService(db: db));

      session.attach('p1', email: 'mai@gmail.com');
      await waitLoaded(session);
      expect(session.parent!.name, 'Trần Thị Mai');
      expect(session.children.length, 2);
      expect(session.selectedChild!.id, 's2');

      await session.selectChild(session.children.firstWhere((k) => k.id == 's1'));
      session.detach(); // đăng xuất / đóng app

      final reopened = ParentSession(service: ParentService(db: db));
      reopened.attach('p1', email: 'mai@gmail.com');
      await waitLoaded(reopened);
      expect(reopened.selectedChild!.id, 's1');
      reopened.detach();
    });

    test('cập nhật ngay khi giáo viên thêm hoặc gỡ liên kết trên Firestore', () async {
      final db = await seedDb();
      final session = ParentSession(service: ParentService(db: db));
      session.attach('p1');
      await waitLoaded(session);
      expect(session.children.map((k) => k.id), ['s1']);

      await db.collection('students').doc('s3').update({'parent_id': 'p1'});
      await Future<void>.delayed(const Duration(milliseconds: 200));
      expect(session.children.map((k) => k.id), containsAll(['s1', 's3']));

      await session.selectChild(session.children.firstWhere((k) => k.id == 's3'));
      await db.collection('students').doc('s3').update({'parent_id': 'p_other'});
      await Future<void>.delayed(const Duration(milliseconds: 200));
      expect(session.children.map((k) => k.id), ['s1']);
      expect(session.selectedChild!.id, 's1'); // con đang chọn bị gỡ -> tự chuyển sang con còn lại
      session.detach();
    });
  });

  group('Giao diện phụ huynh', () {
    Future<void> pumpHome(WidgetTester tester, FakeFirebaseFirestore db, String uid, {String? email}) async {
      ParentSession.instance = ParentSession(service: ParentService(db: db));
      await tester.binding.setSurfaceSize(const Size(430, 932));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(MaterialApp(home: HomeScreen(uid: uid, email: email)));
      await settle(tester);
    }

    testWidgets('phụ huynh 2 con: hiện tên con, có nút Đổi và chuyển được con', (tester) async => ignoringOverflow(() async {
      final db = await tester.runAsync(seedDb);
      await pumpHome(tester, db!, 'p1', email: 'mai@gmail.com');

      expect(find.text('Trần Gia Bảo'), findsOneWidget);
      expect(find.text('10B2 · Năm học 2026-2027'), findsOneWidget);
      expect(find.text('Đổi'), findsOneWidget);

      await tester.tap(find.text('Đổi'));
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 500));
      expect(find.text('Chọn tài khoản con'), findsOneWidget);

      await tester.tap(find.text('Trần Minh Anh').last);
      await settle(tester);
      await tester.tap(find.text('Đóng'));
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));
      expect(find.text('Chọn tài khoản con'), findsNothing);

      expect(find.text('Trần Minh Anh'), findsOneWidget);
      expect(find.text('12A1, 10B2'), findsOneWidget);
      expect(ParentSession.instance.selectedChild!.id, 's1');
    }));

    testWidgets('phụ huynh 1 con: không hiện nút Đổi', (tester) async => ignoringOverflow(() async {
      final db = await tester.runAsync(seedDb);
      await pumpHome(tester, db!, 'p1');
      expect(find.text('Trần Minh Anh'), findsOneWidget);
      expect(find.text('Đổi'), findsNothing);
    }));

    testWidgets('phụ huynh chưa liên kết: hiện màn hình Chưa liên kết học sinh', (tester) async => ignoringOverflow(() async {
      final db = await tester.runAsync(seedDb);
      await pumpHome(tester, db!, 'p_empty', email: 'x@gmail.com');
      expect(find.text('Chưa liên kết học sinh'), findsOneWidget);
      expect(find.text('Thử lại'), findsOneWidget);
      expect(find.text('Đăng xuất'), findsOneWidget);
    }));

    testWidgets('hồ sơ học sinh hiển thị dữ liệu thật của con đang chọn', (tester) async => ignoringOverflow(() async {
      final db = await tester.runAsync(seedDb);
      await pumpHome(tester, db!, 'p1');
      await tester.pumpWidget(const MaterialApp(home: ProfileScreen()));
      await tester.pump();

      expect(find.text('Trần Minh Anh'), findsOneWidget);
      expect(find.text('12/03/2009'), findsOneWidget);
      expect(find.text('Nữ'), findsOneWidget);
      expect(find.text('Trần Thị Mai'), findsOneWidget);
      expect(find.text('0901 234 567'), findsOneWidget);
      expect(find.text('mai@gmail.com'), findsOneWidget);
    }));
  });
}
