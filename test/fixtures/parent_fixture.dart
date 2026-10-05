import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:fake_cloud_firestore/fake_cloud_firestore.dart';

/// Dữ liệu mẫu theo sơ đồ CSDL khách gửi (databasepcv.drawio)
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

  await db.collection('classes').doc('c1').set({
    'class_name': '12A1',
    'school_year': '2026-2027',
    'teacher_id': 't1',
  });
  await db.collection('classes').doc('c2').set({
    'class_name': '10B2',
    'school_year': '2026-2027',
    'teacher_id': 't2',
  });

  // Con 1: liên kết qua parent_id, học 2 lớp
  await db.collection('students').doc('s1').set({
    'student_name': 'Trần Minh Anh',
    'birthday': Timestamp.fromDate(DateTime(2009, 3, 12)),
    'gender': 'Nữ',
    'parent_id': 'p1',
    'parent_email': 'mai@gmail.com',
  });
  // Con 2: mới chỉ điền parent_email (phụ huynh chưa đăng nhập lần nào)
  await db.collection('students').doc('s2').set({
    'student_name': 'Trần Gia Bảo',
    'birthday': '05/09/2011',
    'gender': 'Nam',
    'parent_email': 'mai@gmail.com',
  });
  // Học sinh của phụ huynh khác: không được xuất hiện
  await db.collection('students').doc('s3').set({
    'student_name': 'Phạm Văn Khác',
    'parent_id': 'p_other',
  });

  await db.collection('enrollments').add({'student_id': 's1', 'class_id': 'c1'});
  await db.collection('enrollments').add({'student_id': 's1', 'class_id': 'c2'});
  await db.collection('enrollments').add({'student_id': 's2', 'class_id': 'c2'});
  await db.collection('enrollments').add({'student_id': 's3', 'class_id': 'c1'});

  return db;
}
