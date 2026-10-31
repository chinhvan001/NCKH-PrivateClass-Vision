import { useEffect, useMemo, useState } from "react";

import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";
import CustomScrollbar from "../../common/CustomScrollbar";

const API_URL = "http://127.0.0.1:5000";

const CLASSES_API = `${API_URL}/api/admin/classes`;
const TEACHERS_API = `${API_URL}/api/admin/users`;

const emptyForm = {
  class_name: "",
  teacher_id: "",
  school_year: "2026-2027",
  row_count: 2,
  column_count: 2,
  status: "active",
};

const getErrorMessage = (error) => {
  const message = error?.message || "Có lỗi xảy ra. Vui lòng thử lại.";
  if (message === "Unauthorized.") {
    return "Phiên đăng nhập đã hết hạn.";
  }
  return message;
};

const getTeacherId = (teacher) => teacher?.uid || teacher?.id || "";

const getTeacherNameFromObject = (teacher) =>
  teacher?.full_name ||
  teacher?.display_name ||
  teacher?.name ||
  teacher?.email ||
  "Chưa có giáo viên";

const getClassCapacity = (classItem) => {
  const rows = Number(classItem?.row_count);
  const columns = Number(classItem?.column_count);

  if (
    !Number.isInteger(rows) ||
    rows <= 0 ||
    !Number.isInteger(columns) ||
    columns <= 0
  ) {
    return Number(classItem?.seat_capacity) > 0
      ? Number(classItem.seat_capacity)
      : 0;
  }
  return rows * columns;
};

const getClassSize = (classItem, seats = []) => {
  if (Array.isArray(seats) && seats.length > 0) {
    const occupiedCount = seats.filter(
      (seat) => Boolean(seat?.student_id) || seat?.status === "occupied",
    ).length;
    return occupiedCount;
  }

  const occupiedSeatCount = Number(classItem?.occupied_seat_count);
  if (Number.isFinite(occupiedSeatCount)) {
    return Math.max(0, occupiedSeatCount);
  }

  const studentCount = Number(classItem?.student_count || classItem?.total_students);
  if (Number.isFinite(studentCount)) {
    return Math.max(0, studentCount);
  }

  return 0;
};

const getRowCount = (classItem) => {
  const rows = Number(classItem?.row_count);
  return Number.isInteger(rows) && rows > 0 ? rows : 2;
};

const getColumnCount = (classItem) => {
  const columns = Number(classItem?.column_count);
  return Number.isInteger(columns) && columns > 0 ? columns : 2;
};

const buildSeatGrid = (classItem, seats = [], students = []) => {
  const rows = getRowCount(classItem);
  const columns = getColumnCount(classItem);
  const seatMap = new Map();

  const studentMap = new Map(
    students.map((s) => [s.student_id || s.id, s.full_name]),
  );

  seats.forEach((seat) => {
    const row = Number(seat?.row);
    const column = Number(seat?.column);

    if (
      Number.isInteger(row) &&
      Number.isInteger(column) &&
      row > 0 &&
      column > 0
    ) {
      seatMap.set(`${row}-${column}`, seat);
    }
  });

  const grid = [];

  for (let row = 1; row <= rows; row += 1) {
    for (let column = 1; column <= columns; column += 1) {
      const existingSeat = seatMap.get(`${row}-${column}`);
      const seatNumber = (row - 1) * columns + column;

      const seatId =
        existingSeat?.seat_id && existingSeat.seat_id.trim() !== ""
          ? existingSeat.seat_id
          : `S${String(seatNumber).padStart(2, "0")}`;

      const studentId = existingSeat?.student_id || null;
      const studentName =
        existingSeat?.student_name || studentMap.get(studentId) || "";

      grid.push({
        row,
        column,
        seat_id: seatId,
        student_id: studentId,
        student_name: studentName,
        status: existingSeat?.status || (studentId ? "occupied" : "empty"),
      });
    }
  }

  return grid;
};

const ClassManagementPanel = () => {
  const [classes, setClasses] = useState([]);
  const [teachers, setTeachers] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [optionsError, setOptionsError] = useState("");

  const [search, setSearch] = useState("");
  const [gradeFilter, setGradeFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);

  const [showClassForm, setShowClassForm] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [formData, setFormData] = useState(emptyForm);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState("");

  const [confirmDeleteClass, setConfirmDeleteClass] = useState(null);

  // Pop-up chi tiết & sơ đồ lớp
  const [selectedClass, setSelectedClass] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");
  const [selectedStudentId, setSelectedStudentId] = useState(null);
  const [studentSearch, setStudentSearch] = useState(""); // Thanh tìm kiếm học sinh trong modal chi tiết

  const getToken = () => localStorage.getItem("idToken");

  const request = async (url, options = {}) => {
    const idToken = getToken();

    if (!idToken) {
      throw new Error("Unauthorized.");
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        Authorization: `Bearer ${idToken}`,
        ...(options.headers || {}),
      },
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Không thể kết nối máy chủ.");
    }

    return data;
  };

  const loadClasses = async () => {
    try {
      setLoading(true);
      setError("");
      const data = await request(CLASSES_API);
      setClasses(Array.isArray(data.data) ? data.data : []);
    } catch (loadError) {
      console.error("Load classes error:", loadError);
      setError(getErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  };

  const loadTeachers = async () => {
    try {
      setOptionsError("");
      const data = await request(TEACHERS_API);
      const list = Array.isArray(data.users)
        ? data.users
        : Array.isArray(data.teachers)
        ? data.teachers
        : [];
      setTeachers(list.filter((teacher) => teacher.is_active !== false));
    } catch (loadError) {
      console.error("Load teachers error:", loadError);
      setOptionsError(getErrorMessage(loadError));
    }
  };

  useEffect(() => {
    loadClasses();
    loadTeachers();
  }, []);

  const getTeacherName = (teacherId, classItem = null) => {
    if (classItem?.teacher_name) {
      return classItem.teacher_name;
    }
    const teacher = teachers.find((item) => getTeacherId(item) === teacherId);
    return getTeacherNameFromObject(teacher);
  };

  const filteredClasses = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return classes.filter((classItem) => {
      const teacher = teachers.find(
        (item) => getTeacherId(item) === classItem.teacher_id,
      );
      const teacherName =
        classItem.teacher_name || getTeacherNameFromObject(teacher);

      const className = String(classItem.class_name || "");

      const matchesSearch =
        !keyword ||
        [
          className,
          classItem.teacher_id,
          teacherName,
          teacher?.email,
          classItem.school_year,
        ].some((value) =>
          String(value || "")
            .toLowerCase()
            .includes(keyword),
        );

      let matchesGrade = true;
      if (gradeFilter !== "all") {
        matchesGrade = className.startsWith(gradeFilter);
      }

      const matchesStatus =
        statusFilter === "all" || classItem.status === statusFilter;

      return matchesSearch && matchesGrade && matchesStatus;
    });
  }, [classes, search, gradeFilter, statusFilter, teachers]);

  const classesPerPage = 10;
  const totalPages = Math.ceil(filteredClasses.length / classesPerPage);
  const safePage = totalPages ? Math.min(currentPage, totalPages) : 1;
  const currentClasses = filteredClasses.slice(
    (safePage - 1) * classesPerPage,
    safePage * classesPerPage,
  );

  const resetForm = () => {
    setFormData({ ...emptyForm });
    setFormError("");
  };

  const openAddClass = () => {
    setEditingClass(null);
    resetForm();
    setShowClassForm(true);
  };

  const openEditClass = (classItem) => {
    setEditingClass(classItem);
    setFormData({
      class_name: classItem.class_name || "",
      teacher_id: classItem.teacher_id || "",
      school_year: classItem.school_year || "",
      row_count: Number(classItem.row_count) > 0 ? Number(classItem.row_count) : 2,
      column_count: Number(classItem.column_count) > 0 ? Number(classItem.column_count) : 2,
      status: classItem.status || "active",
    });
    setFormError("");
    setShowClassForm(true);
  };

  const submitClass = async () => {
    const rowCount = Number(formData.row_count);
    const columnCount = Number(formData.column_count);

    if (
      !formData.class_name.trim() ||
      !formData.teacher_id ||
      !formData.school_year.trim()
    ) {
      setFormError("Vui lòng nhập đầy đủ thông tin lớp học.");
      return;
    }

    if (
      !Number.isInteger(rowCount) ||
      rowCount <= 0 ||
      !Number.isInteger(columnCount) ||
      columnCount <= 0
    ) {
      setFormError("Số hàng và số cột phải là số nguyên dương.");
      return;
    }

    try {
      setFormLoading(true);
      setFormError("");

      const url = editingClass
        ? `${CLASSES_API}/${editingClass.id}`
        : CLASSES_API;

      const data = await request(url, {
        method: editingClass ? "PUT" : "POST",
        body: JSON.stringify({
          class_name: formData.class_name.trim(),
          teacher_id: formData.teacher_id,
          school_year: formData.school_year.trim(),
          row_count: rowCount,
          column_count: columnCount,
          ...(editingClass ? { status: formData.status } : {}),
        }),
      });

      setClasses((current) =>
        editingClass
          ? current.map((item) =>
              item.id === editingClass.id ? data.data : item,
            )
          : [...current, data.data],
      );

      setShowClassForm(false);
      setEditingClass(null);
      resetForm();
    } catch (submitError) {
      console.error("Save class error:", submitError);
      setFormError(getErrorMessage(submitError));
    } finally {
      setFormLoading(false);
    }
  };

  const deleteClass = async () => {
    if (!confirmDeleteClass) return;
    try {
      await request(`${CLASSES_API}/${confirmDeleteClass.id}`, {
        method: "DELETE",
      });

      setClasses((current) =>
        current.filter((item) => item.id !== confirmDeleteClass.id),
      );

      if (selectedClass?.id === confirmDeleteClass.id) {
        closeDetail();
      }
    } catch (deleteError) {
      setError(getErrorMessage(deleteError));
    } finally {
      setConfirmDeleteClass(null);
    }
  };

  const loadClassDetailAndSeatMap = async (classItem) => {
    try {
      setSelectedClass(classItem);
      setDetail(null);
      setDetailError("");
      setDetailLoading(true);
      setSelectedStudentId(null);
      setStudentSearch("");

      const [classData, studentsData, seatsData] = await Promise.all([
        request(`${CLASSES_API}/${classItem.id}`),
        request(`${CLASSES_API}/${classItem.id}/students`),
        request(`${CLASSES_API}/${classItem.id}/seats`),
      ]);

      const currentClass = classData.data || classItem;
      const students = Array.isArray(studentsData.data)
        ? studentsData.data
        : [];
      const seats = Array.isArray(seatsData.data) ? seatsData.data : [];

      const grid = buildSeatGrid(currentClass, seats, students);
      const capacity = getClassCapacity(currentClass);
      const occupiedSeatCount = grid.filter((seat) =>
        Boolean(seat.student_name && seat.student_name.trim() !== "")
      ).length;
      const emptySeatCount = Math.max(0, capacity - occupiedSeatCount);

      const sortedStudents = [...students].sort((a, b) => {
        const getFirstName = (name) => {
          const parts = (name || "").trim().split(" ");
          return parts[parts.length - 1];
        };
        const firstNameA = getFirstName(a.full_name);
        const firstNameB = getFirstName(b.full_name);

        const compareFirstName = firstNameA.localeCompare(firstNameB, "vi", { sensitivity: "base" });
        if (compareFirstName !== 0) return compareFirstName;

        return (a.full_name || "").localeCompare(b.full_name || "", "vi", { sensitivity: "base" });
      });

      setSelectedClass(currentClass);
      setDetail({
        classInfo: currentClass,
        students: sortedStudents,
        seats,
        grid,
        capacity,
        occupiedSeatCount,
        emptySeatCount,
      });
    } catch (loadError) {
      console.error("Load detail error:", loadError);
      setDetailError(getErrorMessage(loadError));
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedClass(null);
    setDetail(null);
    setDetailError("");
    setSelectedStudentId(null);
    setStudentSearch("");
  };

  const detailClass = detail?.classInfo || selectedClass;
  const detailRows = getRowCount(detailClass);
  const detailColumns = getColumnCount(detailClass);

  // Lọc danh sách học sinh theo từ khóa search trong modal chi tiết
  const filteredDetailStudents = useMemo(() => {
    if (!detail?.students) return [];
    const keyword = studentSearch.trim().toLowerCase();
    if (!keyword) return detail.students;
    return detail.students.filter((student) =>
      [student.full_name, student.parent_phone, student.gender].some((val) =>
        String(val || "").toLowerCase().includes(keyword)
      )
    );
  }, [detail?.students, studentSearch]);

  return (
    <div className="class-management-container">
      {/* KHỐI THỐNG KÊ */}
      <section className="class-stats-section">
        <div className="class-stats-grid">
          <article className="class-stat-card">
            <div className="class-stat-icon">
              <Icon name="school" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Tổng số lớp</span>
              <strong>{loading ? "—" : classes.length}</strong>
              <small>Lớp học</small>
            </div>
          </article>

          <article className="class-stat-card green">
            <div className="class-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Đang hoạt động</span>
              <strong>
                {loading
                  ? "—"
                  : classes.filter((item) => item.status === "active").length}
              </strong>
              <small>Lớp học</small>
            </div>
          </article>

          <article className="class-stat-card orange">
            <div className="class-stat-icon">
              <Icon name="book" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Tổng sĩ số</span>
              <strong>
                {loading
                  ? "—"
                  : classes.reduce(
                      (total, item) => total + getClassSize(item),
                      0,
                    )}
              </strong>
              <small>Học sinh đã xếp chỗ</small>
            </div>
          </article>

          <article className="class-stat-card healthy">
            <div className="class-stat-icon">
              <Icon name="users" size={21} />
            </div>
            <div className="class-stat-info">
              <span>Đang hiển thị</span>
              <strong>{loading ? "—" : filteredClasses.length}</strong>
              <small>Kết quả lọc</small>
            </div>
          </article>
        </div>
      </section>

      {/* DANH SÁCH VÀ BỘ LỌC */}
      <section className="class-panel">
        <div className="class-panel-heading">
          <div>
            <h2>Danh sách lớp học</h2>
            <p>Quản lý danh sách lớp, giáo viên chủ nhiệm và sơ đồ chỗ ngồi.</p>
          </div>

          <button
            type="button"
            className="add-account-button"
            onClick={openAddClass}
          >
            <Icon name="plus" size={17} />
            <span>Thêm lớp học</span>
          </button>
        </div>

        {/* BỘ LỌC ĐẸP TRỰC QUAN */}
        <div className="class-filters" style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          <div className="class-search" style={{ flex: 1, minWidth: "240px" }}>
            <input
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Tìm theo tên lớp, giáo viên, năm học..."
            />
            <span className="class-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          <select
            className="class-status-filter"
            value={gradeFilter}
            onChange={(e) => {
              setGradeFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="all">Tất cả Khối</option>
            <option disabled value="">---</option>
            <option value="10">Khối 10</option>
            <option value="11">Khối 11</option>
            <option value="12">Khối 12</option>
          </select>

          <select
            className="class-status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="all">Tất cả trạng thái</option>
            <option disabled value="">---</option>
            <option value="active">Đang hoạt động</option>
            <option value="inactive">Ngừng hoạt động</option>
          </select>

          <button
            type="button"
            className="refresh-button"
            onClick={loadClasses}
            title="Làm mới dữ liệu"
          >
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        {error && <div className="class-error">{error}</div>}

        {/* BẢNG DỮ LIỆU */}
        <div className="class-table-wrap">
          <table className="class-table">
            <thead>
              <tr>
                <th style={{ width: "60px", textAlign: "center" }}>STT</th>
                <th style={{ width: "130px" }}>Tên lớp</th>
                <th style={{ width: "110px", paddingLeft: "10px" }}>Sĩ số</th>
                <th style={{ textAlign: "left", paddingLeft: "20px" }}>Giáo viên chủ nhiệm</th>
                <th style={{ width: "130px", textAlign: "left" }}>Năm học</th>
                <th style={{ width: "150px" }}>Trạng thái</th>
                <th style={{ width: "130px", textAlign: "center" }}>THAO TÁC</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="table-empty">
                    Đang tải danh sách lớp học...
                  </td>
                </tr>
              ) : currentClasses.length === 0 ? (
                <tr>
                  <td colSpan="7" className="table-empty">
                    Không có lớp học phù hợp.
                  </td>
                </tr>
              ) : (
                currentClasses.map((classItem, index) => {
                  const stt = (safePage - 1) * classesPerPage + index + 1;
                  return (
                    <tr key={classItem.id}>
                      <td style={{ textAlign: "center", fontWeight: "500", color: "#64748b" }}>
                        {stt}
                      </td>
                      <td>
                        <div
                          className="class-cell"
                          style={{ cursor: "pointer" }}
                          onClick={() => loadClassDetailAndSeatMap(classItem)}
                          title="Nhấp để xem chi tiết & sơ đồ lớp"
                        >
                          <div className="table-avatar">
                            <Icon name="school" size={18} />
                          </div>
                          <strong style={{ color: "#2563eb", textDecoration: "underline" }}>
                            {classItem.class_name}
                          </strong>
                        </div>
                      </td>
                      <td style={{ paddingLeft: "10px" }}>
                        <strong>{getClassSize(classItem)}</strong> học sinh
                      </td>
                      <td style={{ textAlign: "left", paddingLeft: "20px" }}>
                        {getTeacherName(classItem.teacher_id, classItem)}
                      </td>
                      <td style={{ textAlign: "left" }}>{classItem.school_year}</td>
                      <td>
                        <span
                          className={`class-status ${
                            classItem.status === "active" ? "active" : "inactive"
                          }`}
                        >
                          {classItem.status === "active"
                            ? "Đang hoạt động"
                            : "Ngừng hoạt động"}
                        </span>
                      </td>
                      <td>
                        <div className="row-actions" style={{ justifyContent: "center", display: "flex", gap: "6px" }}>
                          <button
                            type="button"
                            title="Xem chi tiết & sơ đồ lớp"
                            onClick={() => loadClassDetailAndSeatMap(classItem)}
                            style={{
                              padding: "6px",
                              borderRadius: "6px",
                              border: "1px solid #cbd5e1",
                              backgroundColor: "#fff",
                              color: "#2563eb",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              transition: "all 0.2s ease"
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#eff6ff"; e.currentTarget.style.borderColor = "#2563eb"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#fff"; e.currentTarget.style.borderColor = "#cbd5e1"; }}
                          >
                            <Icon name="eye" size={15} />
                          </button>

                          <button
                            type="button"
                            title="Chỉnh sửa"
                            onClick={() => openEditClass(classItem)}
                            style={{
                              padding: "6px",
                              borderRadius: "6px",
                              border: "1px solid #cbd5e1",
                              backgroundColor: "#fff",
                              color: "#475569",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              transition: "all 0.2s ease"
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#f1f5f9"; e.currentTarget.style.borderColor = "#475569"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#fff"; e.currentTarget.style.borderColor = "#cbd5e1"; }}
                          >
                            <Icon name="edit" size={15} />
                          </button>

                          <button
                            type="button"
                            title="Vô hiệu hóa"
                            onClick={() => setConfirmDeleteClass(classItem)}
                            style={{
                              padding: "6px",
                              borderRadius: "6px",
                              border: "1px solid #fecaca",
                              backgroundColor: "#fff",
                              color: "#dc2626",
                              cursor: "pointer",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              transition: "all 0.2s ease"
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "#fef2f2"; e.currentTarget.style.borderColor = "#dc2626"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "#fff"; e.currentTarget.style.borderColor = "#fecaca"; }}
                          >
                            <Icon name="trash" size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* PHÂN TRANG */}
        <div className="class-pagination">
          <span>
            {filteredClasses.length
              ? `${(safePage - 1) * classesPerPage + 1}-${Math.min(
                  safePage * classesPerPage,
                  filteredClasses.length,
                )}`
              : "0"}{" "}
            trên {filteredClasses.length} lớp
          </span>

          <div>
            <button
              type="button"
              disabled={safePage === 1}
              onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
            >
              <Icon name="arrowLeft" size={15} />
            </button>

            <button
              type="button"
              disabled={safePage === totalPages || totalPages === 0}
              onClick={() =>
                setCurrentPage((page) => Math.min(totalPages, page + 1))
              }
            >
              <Icon name="arrowRight" size={15} />
            </button>
          </div>
        </div>
      </section>

      {/* MODAL CẤU HÌNH / CHỈNH SỬA LỚP HỌC */}
      {showClassForm && (
        <div
          className="class-modal-overlay"
          onClick={() => !formLoading && setShowClassForm(false)}
        >
          <div className="class-modal" onClick={(e) => e.stopPropagation()}>
            <div className="class-modal-header">
              <div>
                <h2>{editingClass ? "Chỉnh sửa lớp học" : "Thêm lớp học"}</h2>
              </div>
              <button
                type="button"
                className="edit-teacher-close"
                onClick={() => setShowClassForm(false)}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="class-modal-content">
              <label>
                <span>Tên lớp</span>
                <input
                  value={formData.class_name}
                  placeholder="Ví dụ: 10A1"
                  onChange={(e) =>
                    setFormData({ ...formData, class_name: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Giáo viên chủ nhiệm</span>
                <select
                  value={formData.teacher_id}
                  onChange={(e) =>
                    setFormData({ ...formData, teacher_id: e.target.value })
                  }
                  disabled={formLoading}
                >
                  <option value="">Chọn giáo viên</option>
                  {teachers.map((teacher) => (
                    <option
                      key={getTeacherId(teacher)}
                      value={getTeacherId(teacher)}
                    >
                      {getTeacherNameFromObject(teacher)}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                <span>Năm học</span>
                <input
                  value={formData.school_year}
                  placeholder="2026-2027"
                  onChange={(e) =>
                    setFormData({ ...formData, school_year: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Số hàng (vị trí ngồi)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={formData.row_count}
                  onChange={(e) =>
                    setFormData({ ...formData, row_count: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <label>
                <span>Số cột (vị trí ngồi)</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={formData.column_count}
                  onChange={(e) =>
                    setFormData({ ...formData, column_count: e.target.value })
                  }
                  disabled={formLoading}
                />
              </label>

              <div
                style={{
                  padding: "12px 14px",
                  background: "#f8fafc",
                  borderRadius: "10px",
                  color: "#475569",
                  fontSize: "14px",
                }}
              >
                Sức chứa tối đa:{" "}
                <strong>
                  {Number(formData.row_count) > 0 &&
                  Number(formData.column_count) > 0
                    ? Number(formData.row_count) * Number(formData.column_count)
                    : 0}{" "}
                  chỗ
                </strong>
              </div>

              {editingClass && (
                <label>
                  <span>Trạng thái</span>
                  <select
                    value={formData.status}
                    onChange={(e) =>
                      setFormData({ ...formData, status: e.target.value })
                    }
                    disabled={formLoading}
                  >
                    <option value="active">Đang hoạt động</option>
                    <option value="inactive">Ngừng hoạt động</option>
                  </select>
                </label>
              )}

              {optionsError && (
                <div className="class-form-error">{optionsError}</div>
              )}
              {formError && <div className="class-form-error">{formError}</div>}
            </div>

            <div className="class-modal-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={() => setShowClassForm(false)}
                disabled={formLoading}
              >
                Hủy
              </button>
              <button
                type="button"
                className="add-account-button"
                onClick={submitClass}
                disabled={formLoading}
              >
                {formLoading ? "Đang lưu..." : "Lưu lớp"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* POP-UP CHI TIẾT & SƠ ĐỒ CHỖ NGỒI */}
      {selectedClass && (
        <div className="class-modal-overlay" onClick={closeDetail}>
          <div
            className="class-modal class-detail-wide"
            style={{ maxWidth: "1280px", width: "95vw" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="class-modal-header">
              <div>
                <h2>Thống kê & Sơ đồ lớp — {detailClass?.class_name}</h2>
                <p>Chi tiết thông tin lớp học, vị trí chỗ ngồi và danh sách học sinh.</p>
              </div>
              <button
                type="button"
                className="edit-teacher-close"
                onClick={closeDetail}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            {detailLoading ? (
              <div className="class-detail-state" style={{ padding: "40px", textAlign: "center" }}>
                Đang tải dữ liệu lớp học và sơ đồ chỗ ngồi...
              </div>
            ) : detailError ? (
              <div className="class-matrix-error" style={{ margin: "20px" }}>
                {detailError}
              </div>
            ) : (
              <div className="class-modal-content" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                
                {/* THỐNG KÊ NHANH */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                    gap: "12px",
                    background: "#f8fafc",
                    padding: "16px",
                    borderRadius: "12px",
                    border: "1px solid #e2e8f0"
                  }}
                >
                  <div>
                    <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>Giáo viên chủ nhiệm</span>
                    <strong style={{ fontSize: "15px", color: "#0f172a" }}>
                      {getTeacherName(detailClass?.teacher_id, detailClass)}
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>Năm học</span>
                    <strong style={{ fontSize: "15px", color: "#0f172a" }}>{detailClass?.school_year || "—"}</strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>Số hàng - Số cột</span>
                    <strong style={{ fontSize: "15px", color: "#0f172a" }}>
                      {detailRows} hàng - {detailColumns} cột
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>Sức chứa / Đã xếp chỗ</span>
                    <strong style={{ fontSize: "15px", color: "#2563eb" }}>
                      {detail?.occupiedSeatCount || 0} / {detail?.capacity || 0} chỗ
                    </strong>
                  </div>
                  <div>
                    <span style={{ fontSize: "12px", color: "#64748b", display: "block" }}>Ghế trống</span>
                    <strong style={{ fontSize: "15px", color: "#16a34a" }}>
                      {detail?.emptySeatCount || 0} chỗ
                    </strong>
                  </div>
                </div>

                {/* KHỐI SƠ ĐỒ VÀ DANH SÁCH */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "20px",
                    alignItems: "start",
                  }}
                >
                  {/* SƠ ĐỒ CHỖ NGỒI */}
                  <div
                    style={{
                      border: "1px solid #e2e8f0",
                      borderRadius: "12px",
                      padding: "16px",
                      background: "#ffffff",
                    }}
                  >
                    <div style={{ marginBottom: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>Sơ đồ chỗ ngồi trong lớp</h3>
                      <span style={{ fontSize: "12px", color: "#64748b" }}>Bảng đen phía trên</span>
                    </div>

                    <div
                      style={{
                        background: "#334155",
                        color: "#ffffff",
                        textAlign: "center",
                        padding: "6px",
                        borderRadius: "6px",
                        marginBottom: "16px",
                        fontSize: "12px",
                        fontWeight: "bold",
                        letterSpacing: "1px"
                      }}
                    >
                      BẢNG ĐEN / MÀN HÌNH BÀI GIẢNG
                    </div>

                    <CustomScrollbar height="380px">
                      <div
                        className="class-seat-grid"
                        style={{
                          display: "grid",
                          gridTemplateColumns: `repeat(${detailColumns}, minmax(0, 1fr))`,
                          gap: "8px",
                          padding: "4px"
                        }}
                      >
                        {detail?.grid?.map((seat, index) => {
                          const isOccupied = Boolean(seat.student_name && seat.student_name.trim() !== "");
                          const isSelected = selectedStudentId && (seat.student_id === selectedStudentId || seat.student_name === detail?.students?.find(s => (s.student_id || s.id) === selectedStudentId)?.full_name);

                          return (
                            <div
                              key={index}
                              onClick={() => {
                                if (seat.student_id) {
                                  setSelectedStudentId(seat.student_id);
                                } else if (isOccupied) {
                                  const foundStudent = detail?.students?.find(s => s.full_name === seat.student_name);
                                  if (foundStudent) setSelectedStudentId(foundStudent.student_id || foundStudent.id);
                                }
                              }}
                              style={{
                                border: isSelected ? "2px solid #2563eb" : "1px solid #e2e8f0",
                                background: isSelected ? "#eff6ff" : isOccupied ? "#f8fafc" : "#ffffff",
                                borderRadius: "8px",
                                padding: "8px 4px",
                                textAlign: "center",
                                cursor: isOccupied ? "pointer" : "default",
                                transition: "all 0.2s ease",
                                boxShadow: isSelected ? "0 0 8px rgba(37, 99, 235, 0.3)" : "none"
                              }}
                            >
                              <div style={{ fontSize: "11px", fontWeight: "bold", color: "#64748b" }}>
                                {seat?.seat_id ? seat.seat_id.replace(/^S/i, '') : index + 1}
                              </div>

                              <div
                                style={{
                                  fontSize: "12px",
                                  fontWeight: isOccupied ? "600" : "normal",
                                  color: isOccupied ? "#1e293b" : "#cbd5e1",
                                  marginTop: "4px",
                                  overflow: "hidden",
                                  textOverflow: "ellipsis",
                                  whiteSpace: "nowrap"
                                }}
                                title={seat.student_name || "Ghế trống"}
                              >
                                {isOccupied ? seat.student_name : "Trống"}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CustomScrollbar>
                  </div>

                  {/* DANH SÁCH HỌC SINH */}
                  <div
                    style={{
                      border: "1px solid #e2e8f0",
                      borderRadius: "12px",
                      padding: "16px",
                      background: "#ffffff",
                    }}
                  >
                    <div style={{ marginBottom: "12px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <h3 style={{ margin: 0, fontSize: "16px", color: "#0f172a" }}>
                        Danh sách học sinh ({filteredDetailStudents.length}/{detail?.students?.length || 0})
                      </h3>
                      {selectedStudentId && (
                        <button
                          type="button"
                          onClick={() => setSelectedStudentId(null)}
                          style={{
                            fontSize: "12px",
                            color: "#2563eb",
                            background: "none",
                            border: "none",
                            cursor: "pointer"
                          }}
                        >
                          Bỏ chọn
                        </button>
                      )}
                    </div>

                    {/* Thanh tìm kiếm học sinh trong modal chi tiết */}
                    <div style={{ marginBottom: "12px", position: "relative" }}>
                      <input
                        type="text"
                        value={studentSearch}
                        onChange={(e) => setStudentSearch(e.target.value)}
                        placeholder="Tìm kiếm học sinh theo tên, SĐT..."
                        style={{
                          width: "100%",
                          height: "36px",
                          padding: "0 36px 0 12px",
                          borderRadius: "8px",
                          border: "1px solid #cbd5e1",
                          fontSize: "13px",
                          outline: "none",
                          boxSizing: "border-box"
                        }}
                      />
                      <span style={{ position: "absolute", right: "10px", top: "50%", transform: "translateY(-50%)", color: "#94a3b8", pointerEvents: "none" }}>
                        <Icon name="search" size={15} />
                      </span>
                    </div>

                    {filteredDetailStudents.length === 0 ? (
                      <p className="class-no-data" style={{ padding: "20px 0", textAlign: "center", color: "#94a3b8" }}>
                        Không tìm thấy học sinh phù hợp.
                      </p>
                    ) : (
                      <CustomScrollbar height="360px">
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                          <thead>
                            <tr style={{ background: "#f8fafc", textAlign: "left", color: "#475569", borderBottom: "1px solid #e2e8f0" }}>
                              <th style={{ padding: "8px" }}>STT</th>
                              <th style={{ padding: "8px" }}>Họ và tên</th>
                              <th style={{ padding: "8px" }}>Giới tính</th>
                              <th style={{ padding: "8px" }}>Ngày sinh</th>
                              <th style={{ padding: "8px" }}>SĐT PH</th>
                            </tr>
                          </thead>
                          <tbody>
                            {filteredDetailStudents.map((student, idx) => {
                              const studentKey = student.student_id || student.id || idx;
                              const isSelected = selectedStudentId === studentKey;

                              let formattedBirthday = "—";
                              if (student.birthday) {
                                const date = new Date(student.birthday);
                                if (!isNaN(date.getTime())) {
                                  formattedBirthday = date.toLocaleDateString("vi-VN");
                                } else {
                                  formattedBirthday = student.birthday;
                                }
                              }

                              return (
                                <tr
                                  key={studentKey}
                                  onClick={() => setSelectedStudentId(isSelected ? null : studentKey)}
                                  style={{
                                    borderBottom: "1px solid #f1f5f9",
                                    cursor: "pointer",
                                    background: isSelected ? "#eff6ff" : "transparent",
                                    transition: "background 0.15s ease"
                                  }}
                                >
                                  <td style={{ padding: "10px 8px", color: "#64748b" }}>{idx + 1}</td>
                                  <td style={{ padding: "10px 8px", fontWeight: "600", color: isSelected ? "#2563eb" : "#1e293b" }}>
                                    {student.full_name}
                                  </td>
                                  <td style={{ padding: "10px 8px", color: "#64748b" }}>{student.gender || "—"}</td>
                                  <td style={{ padding: "10px 8px", color: "#64748b" }}>{formattedBirthday}</td>
                                  <td style={{ padding: "10px 8px", color: "#64748b" }}>{student.parent_phone || "—"}</td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </CustomScrollbar>
                    )}
                  </div>
                </div>

              </div>
            )}

            <div className="class-modal-actions" style={{ marginTop: "16px" }}>
              <button
                type="button"
                className="secondary-button"
                onClick={closeDetail}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* POP-UP XÁC NHẬN VÔ HIỆU HÓA */}
      {confirmDeleteClass && (
        <ConfirmModal
          title="Vô hiệu hóa lớp học"
          message={`Bạn có chắc chắn muốn vô hiệu hóa lớp "${confirmDeleteClass.class_name}"? Lớp học sẽ chuyển sang trạng thái Ngừng hoạt động.`}
          onConfirm={deleteClass}
          onCancel={() => setConfirmDeleteClass(null)}
        />
      )}
    </div>
  );
};

export default ClassManagementPanel;