import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

Future<void> add37StudentsToFirestore() async {
  final FirebaseFirestore firestore = FirebaseFirestore.instance;
  
  // Danh sách 37 tên học sinh mới (không trùng với danh sách cũ)
  final List<String> sampleNames = [
    "Nguyễn Đình Chiểu", "Trần Mai Anh", "Lê Gia Hưng", "Phạm Quỳnh Chi",
    "Hoàng Tuấn Kiệt", "Vũ Ngọc Mai", "Đặng Quang Huy", "Bùi Khánh Linh",
    "Đỗ Hải Nam", "Ngô Phương Thảo", "Dương Quốc Bảo", "Lý Thu Hà",
    "Hồ Minh Triết", "Mạc Ngọc Ánh", "Phan Nhật Quang", "Trịnh Mỹ Duyên",
    "Đoàn Gia Huy", "Tạ Thanh Trúc", "Vương Đình Trọng", "Lương Hải Yến",
    "Lâm Thế Vinh", "Thạch Thảo My", "Tạ Hoàng Gia", "Cao Mỹ Lệ",
    "Tống Khánh Duy", "Phùng Ngọc Trâm", "Đinh Thế Hùng", "Mai Thanh Hà",
    "Lều Quốc Tuấn", "Kiều Khánh Vi", "Tạ Minh Triết", "Bùi Phương Linh",
    "Lê Hoàng Nam", "Trần Thảo Nguyên", "Nguyễn Gia Bảo", "Phạm Minh Thư",
    "Vũ Đình Phong"
  ];

  // Ngày hiện tại cho created_at và updated_at
  final Timestamp todayTimestamp = Timestamp.now();
  
  // Ngày sinh mẫu dưới dạng Timestamp
  final Timestamp defaultBirthday = Timestamp.fromDate(DateTime(2005, 5, 15));

  // Sử dụng WriteBatch để ghi dữ liệu tối ưu và an toàn
  WriteBatch batch = firestore.batch();

  // Vòng lặp từ 1 đến 37
  for (int i = 1; i <= 37; i++) {
    // Tạo document ID theo định dạng: 17092005so1, 17092005so2, ... 17092005so37
    String docId = "28032005so$i";
    
    // Tham chiếu đến document cần tạo trong collection 'students2'
    DocumentReference docRef = firestore.collection('students2').doc(docId);

    // Lấy tên theo vòng lặp, nếu vượt quá danh sách thì gán tên kèm số thứ tự phụ
    String studentName = (i <= sampleNames.length) 
        ? sampleNames[i - 1] 
        : "Học Sinh $i";

    // Dữ liệu cho từng học sinh dựa theo cấu trúc mẫu
    Map<String, dynamic> studentData = {
      "full_name": studentName,
      "birthday": defaultBirthday, // Kiểu Timestamp
      "gender": i % 2 == 0 ? "Nam" : "Nữ",
      "is_active": true,
      "parent_id": "null", // Chuỗi "null" theo yêu cầu
      "parent_name": "Chưa cập nhật",
      "parent_phonenumber": "09${(20000000 + i).toString()}", // Số điện thoại giả lập ngẫu nhiên
      "status": "Đang học",
      "created_at": todayTimestamp,
      "updated_at": todayTimestamp,
    };

    // Đưa lệnh set vào batch
    batch.set(docRef, studentData);
  }

  try {
    // Thực thi ghi hàng loạt lên Firestore
    await batch.commit();
    print("Đã thêm thành công 37 học sinh mới vào bảng students2!");
  } catch (e) {
    print("Lỗi khi thêm dữ liệu: $e");
  }
}