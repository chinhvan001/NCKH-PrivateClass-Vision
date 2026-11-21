import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:fake_cloud_firestore/fake_cloud_firestore.dart';

/// Dữ liệu mẫu theo schema web admin + app: students2, classes2 (học sinh nằm trong seat_map của lớp)
Future<FakeFirebaseFirestore> seedDb() async {
  final db = FakeFirebaseFirestore();

  await db.collection('parents').doc('p1').set({
    'name': 'Trần Thị Mai',
    'email': 'mai@gmail.com',
    'phone_number': '0901 234 567',
    'is_active': true,
  });
  await db.collection('parents').doc('p_empty').set({'name': 'Phụ huynh chưa có con'});

  await db.collection('teachers').doc('t1').set({'name': 'Nguyễn Văn Hùng'});
  await db.collection('teachers').doc('t2').set({'name': 'Lê Thu Hà'});

  await db.collection('classes2').doc('c1').set({
    'class_name': '12A1',
    'school_year': '2026-2027',
    'teacher_id': 't1',
    'seat_map': {
      'S01': {'seat_id': 'S01', 'row': 1, 'column': 1, 'student_id': 's1'},
      'S02': {'seat_id': 'S02', 'row': 1, 'column': 2, 'student_id': 's3'},
    },
  });
  await db.collection('classes2').doc('c2').set({
    'class_name': '10B2',
    'school_year': '2026-2027',
    'teacher_id': 't2',
    'seat_map': {
      'S01': {'seat_id': 'S01', 'row': 1, 'column': 1, 'student_id': 's1'},
      'S02': {'seat_id': 'S02', 'row': 1, 'column': 2, 'student_id': 's2'},
    },
  });

  // Con 1: liên kết qua parent_id, học 2 lớp
  await db.collection('students2').doc('s1').set({
    'full_name': 'Trần Minh Anh',
    'birthday': Timestamp.fromDate(DateTime(2009, 3, 12)),
    'gender': 'Nữ',
    'parent_id': 'p1',
    'parent_email': 'mai@gmail.com',
  });
  // Con 2: mới chỉ điền parent_email (phụ huynh chưa đăng nhập lần nào)
  await db.collection('students2').doc('s2').set({
    'full_name': 'Trần Gia Bảo',
    'birthday': '05/09/2011',
    'gender': 'Nam',
    'parent_email': 'mai@gmail.com',
  });
  // Học sinh của phụ huynh khác: không được xuất hiện
  await db.collection('students2').doc('s3').set({
    'full_name': 'Phạm Văn Khác',
    'parent_id': 'p_other',
  });

  return db;
}
