import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:flutter/material.dart';

Future<void> addClass12B2ToFirestore() async {
  final FirebaseFirestore firestore = FirebaseFirestore.instance;

  try {
    // 1. Tạo chính xác 37 student_id khớp với định dạng lúc tạo học sinh (17092005so1 đến 17092005so37)
    List<String> studentIds = List.generate(37, (index) => "28032005so${index + 1}");

    // 2. Thiết lập kích thước phòng học: 8 cột x 5 hàng = 40 ghế tối đa
    int rowCount = 5;
    int columnCount = 8;
    Map<String, dynamic> seatMap = {};

    int studentIndex = 0;
    int seatCounter = 1;

    for (int r = 1; r <= rowCount; r++) {
      for (int c = 1; c <= columnCount; c++) {
        // Nếu đã xếp hết 37 học sinh mà vẫn còn thừa ghế, dừng việc gán học sinh vào ghế tiếp theo
        if (seatCounter > 40) break;

        // Định dạng seat_id dạng S01, S02, ..., S37 (hoặc đến S40)
        String seatId = "S${seatCounter.toString().padLeft(2, '0')}";

        // Lấy student_id, nếu vẫn còn học sinh thì gán vào, hết thì để "null"
        String assignedStudentId = (studentIndex < studentIds.length) 
            ? studentIds[studentIndex] 
            : "null";

        seatMap[seatId] = {
          "column": c,
          "row": r,
          "seat_id": seatId,
          "status": assignedStudentId != "null" ?  "occupied":"empty" , // Nếu trống ghế thì khóa hoặc để empty tùy ý
          "student_id": assignedStudentId,
          "updated_at": Timestamp.now(),
        };

        if (assignedStudentId != "null") {
          studentIndex++;
        }
        seatCounter++;
      }
    }

    // 3. Dữ liệu của lớp học 'lop12b2'
    Map<String, dynamic> classData = {
      "class_name": "12B2",
      "column_count": columnCount,
      "row_count": rowCount,
      "room": "303",
      "school_year": "2026_2027",
      "status": "active",
      "teacher_id": "", // Để trống
      "camera_id": "",  // Để trống
      "seat_map": seatMap,
      "created_at": Timestamp.now(),
      "updated_at": Timestamp.now(),
    };

    // 4. Lưu vào collection 'classes2' với document ID là 'lop12b2'
    await firestore.collection('classes2').doc('lop12b2').set(classData);

    debugPrint("Đã thêm thành công lớp lop12b2 vào collection classes2!");
  } catch (e) {
    debugPrint("Lỗi khi thêm lớp học: $e");
  }
}