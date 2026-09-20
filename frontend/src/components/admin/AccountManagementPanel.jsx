import { useMemo, useState } from "react";

import Icon from "../common/Icon";
import EditTeacherForm from "./EditTeacherForm";
import AddTeacherForm from "./AddTeacherForm";
import ConfirmModal from "../common/ConfirmModal";

const AccountManagementPanel = ({
  users = [],
  loading = false,
  onRefresh,
  onUpdateUser,
  onDeleteTeacher,
}) => {
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedTeacher, setSelectedTeacher] = useState(null);
  const [detailTeacher, setDetailTeacher] = useState(null);
  const [showAddTeacher, setShowAddTeacher] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);

  const [confirmModal, setConfirmModal] = useState({
    open: false,
    title: "",
    message: "",
    confirmText: "Xác nhận",
    cancelText: "Hủy",
    onConfirm: null,
  });

  const TEACHERS_PER_PAGE = 10;

  const SUBJECT_OPTIONS = [
    "Toán",
    "Ngữ văn",
    "Tiếng Anh",
    "Vật lý",
    "Hóa học",
    "Sinh học",
    "Lịch sử",
    "Địa lý",
    "Giáo dục kinh tế và pháp luật",
    "Tin học",
    "Công nghệ",
    "Âm nhạc",
    "Mỹ thuật",
    "Thể dục",
  ];

  const teachers = useMemo(() => {
    return users.map((user) => ({
      id: user.id,
      uid: user.uid || null,
      email: user.email || "Chưa có email",
      name: user.name || "Chưa cập nhật",
      phone_number: user.phone_number || "",
      subject: user.subject || "",
      create_date: user.create_date || null,
      is_active: user.is_active !== false,
      auth_provider: user.auth_provider || "google",
      auth_status: user.auth_status || "pending",
    }));
  }, [users]);

  const subjects = SUBJECT_OPTIONS;

  const filteredTeachers = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return teachers.filter((teacher) => {
      const matchSearch =
        !keyword ||
        teacher.name.toLowerCase().includes(keyword) ||
        teacher.email.toLowerCase().includes(keyword) ||
        teacher.phone_number.toLowerCase().includes(keyword);

      const matchSubject =
        subjectFilter === "all" || teacher.subject === subjectFilter;

      const matchStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && teacher.is_active) ||
        (statusFilter === "inactive" && !teacher.is_active);

      return matchSearch && matchSubject && matchStatus;
    });
  }, [teachers, search, subjectFilter, statusFilter]);

  const totalTeachers = teachers.length;

  const activeTeachers = teachers.filter(
    (teacher) => teacher.is_active,
  ).length;

  const inactiveTeachers = totalTeachers - activeTeachers;

  const totalPages = Math.ceil(
    filteredTeachers.length / TEACHERS_PER_PAGE,
  );

  const safeCurrentPage =
    totalPages === 0 ? 1 : Math.min(currentPage, totalPages);

  const startIndex =
    (safeCurrentPage - 1) * TEACHERS_PER_PAGE;

  const currentTeachers = filteredTeachers.slice(
    startIndex,
    startIndex + TEACHERS_PER_PAGE,
  );

  const displayStart =
    filteredTeachers.length === 0 ? 0 : startIndex + 1;

  const displayEnd = Math.min(
    startIndex + TEACHERS_PER_PAGE,
    filteredTeachers.length,
  );

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  const handleViewDetails = (teacher) => {
    setDetailTeacher(teacher);
  };

  const handleSaveTeacher = async (updatedTeacher) => {
    try {
      if (!onUpdateUser) {
        throw new Error(
          "Không tìm thấy chức năng cập nhật tài khoản.",
        );
      }

      await onUpdateUser(updatedTeacher);
      setSelectedTeacher(null);

      if (onRefresh) {
        await onRefresh();
      }
    } catch (error) {
      console.error("Update teacher error:", error);
      throw error;
    }
  };

  const handleDeleteTeacher = (teacher) => {
    setConfirmModal({
      open: true,
      title: "Xóa giáo viên",
      message: `Bạn có chắc muốn xóa giáo viên "${teacher.name}" không?`,
      confirmText: "Xóa",
      cancelText: "Hủy",
      onConfirm: async () => {
        try {
          if (!onDeleteTeacher) {
            throw new Error(
              "Không tìm thấy chức năng xóa giáo viên.",
            );
          }

          await onDeleteTeacher(teacher);

          setConfirmModal({
            open: false,
            title: "",
            message: "",
            confirmText: "Xác nhận",
            cancelText: "Hủy",
            onConfirm: null,
          });

          if (onRefresh) {
            await onRefresh();
          }
        } catch (error) {
          console.error("Delete teacher error:", error);

          setConfirmModal({
            open: false,
            title: "",
            message: "",
            confirmText: "Xác nhận",
            cancelText: "Hủy",
            onConfirm: null,
          });

          window.alert(
            error.message || "Không thể xóa giáo viên.",
          );
        }
      },
    });
  };

  const handleAddTeacher = async (newTeacher) => {
    try {
      const idToken = localStorage.getItem("idToken");

      if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
      }

      const response = await fetch(
        "http://127.0.0.1:5000/api/admin/teachers",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${idToken}`,
          },
          body: JSON.stringify(newTeacher),
        },
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          data.message || "Không thể thêm giáo viên.",
        );
      }

      console.log("Add teacher success:", data);

      setShowAddTeacher(false);

      if (onRefresh) {
        await onRefresh();
      }
    } catch (error) {
      console.error("Add teacher error:", error);
      throw error;
    }
  };

  const resetConfirmModal = () => {
    setConfirmModal({
      open: false,
      title: "",
      message: "",
      confirmText: "Xác nhận",
      cancelText: "Hủy",
      onConfirm: null,
    });
  };

  const formatCreateDate = (createDate) => {
    if (!createDate) {
      return "Chưa có thông tin";
    }

    try {
      let dateValue = createDate;

      if (
        typeof createDate === "object" &&
        createDate !== null &&
        "seconds" in createDate
      ) {
        dateValue = createDate.seconds * 1000;
      }

      const date = new Date(dateValue);

      if (Number.isNaN(date.getTime())) {
        return "Chưa có thông tin";
      }

      return date.toLocaleString("vi-VN");
    } catch {
      return "Chưa có thông tin";
    }
  };

  const getAuthStatusText = (status) => {
    switch (status) {
      case "linked":
        return "Đã liên kết Firebase";
      case "pending":
        return "Chưa liên kết Firebase";
      default:
        return status || "Chưa xác định";
    }
  };

  return (
    <>
      <section className="account-stats-section">
        <h2>Tài khoản giáo viên</h2>

        <div className="account-stats-grid">
          <article className="account-stat-card blue">
            <div className="account-stat-icon">
              <Icon name="user" size={21} />
            </div>

            <div>
              <span>Tổng giáo viên</span>
              <strong>{totalTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          <article className="account-stat-card green">
            <div className="account-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>

            <div>
              <span>Đang hoạt động</span>
              <strong>{activeTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          <article className="account-stat-card red">
            <div className="account-stat-icon">
              <Icon name="xCircle" size={21} />
            </div>

            <div>
              <span>Đã vô hiệu hóa</span>
              <strong>{inactiveTeachers}</strong>
              <small>Tài khoản</small>
            </div>
          </article>

          <article className="account-stat-card purple">
            <div className="account-stat-icon">
              <Icon name="school" size={21} />
            </div>

            <div>
              <span>Bộ môn</span>
              <strong>{subjects.length}</strong>
              <small>Môn học</small>
            </div>
          </article>

          <article className="account-stat-card add-stat-card">
            <div className="account-stat-icon">
              <Icon name="plus" size={22} />
            </div>

            <div>
              <strong>Sắp có thêm</strong>
              <small>Tính năng sắp cập nhật</small>
            </div>
          </article>
        </div>
      </section>

      <section className="account-panel">
        <div className="account-panel-heading">
          <div>
            <h2>Quản lý tài khoản giáo viên</h2>
            <p>Danh sách tài khoản giáo viên trong hệ thống.</p>
          </div>

          <button
            type="button"
            className="add-account-button"
            onClick={() => setShowAddTeacher(true)}
          >
            <Icon name="plus" size={17} />
            <span>Thêm giáo viên</span>
          </button>
        </div>

        <div className="account-filters">
          <div className="account-search">
            <input
              type="text"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Tìm kiếm theo tên..."
            />

            <span className="account-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          <label className="account-select">
            <span>Bộ môn</span>

            <select
              value={subjectFilter}
              onChange={(e) => {
                setSubjectFilter(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tất cả các môn</option>

              {subjects.map((subject) => (
                <option key={subject} value={subject}>
                  {subject}
                </option>
              ))}
            </select>
          </label>

          <label className="account-select">
            <span>Trạng thái</span>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="inactive">Đã vô hiệu hóa</option>
            </select>
          </label>

          <button
            type="button"
            className="refresh-button"
            onClick={handleRefresh}
          >
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        <div className="account-table-wrap">
          <table className="account-table">
            <thead>
              <tr>
                <th>Tên giáo viên</th>
                <th>Gmail</th>
                <th>Số điện thoại</th>
                <th>Bộ môn</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="table-empty">
                    Đang tải danh sách giáo viên...
                  </td>
                </tr>
              ) : filteredTeachers.length === 0 ? (
                <tr>
                  <td colSpan="6" className="table-empty">
                    Không tìm thấy tài khoản giáo viên.
                  </td>
                </tr>
              ) : (
                currentTeachers.map((teacher) => (
                  <tr key={teacher.id}>
                    <td>
                      <div className="account-cell">
                        <div className="table-avatar">
                          <Icon name="user" size={19} />
                        </div>

                        <div>
                          <strong>{teacher.name}</strong>
                          <span>Giáo viên</span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span className="account-email">
                        {teacher.email}
                      </span>
                    </td>

                    <td>
                      <span className="account-phone">
                        {teacher.phone_number || "--"}
                      </span>
                    </td>

                    <td>
                      <div className="account-subject-list">
                        {teacher.subject ? (
                          <span className="account-subject-tag">
                            {teacher.subject}
                          </span>
                        ) : (
                          <span className="account-subject-empty">
                            Chưa cập nhật
                          </span>
                        )}
                      </div>
                    </td>

                    <td>
                      <span
                        className={`status-badge ${
                          teacher.is_active ? "active" : "inactive"
                        }`}
                      >
                        <i />
                        {teacher.is_active
                          ? "Đang hoạt động"
                          : "Đã vô hiệu hóa"}
                      </span>
                    </td>

                    <td>
                      <div className="row-actions">
                        <button
                          type="button"
                          className="edit-button"
                          onClick={() => setSelectedTeacher(teacher)}
                          title="Chỉnh sửa"
                        >
                          <Icon name="edit" size={18} />
                        </button>

                        <button
                          type="button"
                          className="detail-button"
                          onClick={() => handleViewDetails(teacher)}
                          title="Xem chi tiết"
                        >
                          <Icon name="eye" size={18} />
                        </button>

                        <button
                          type="button"
                          className="delete-button"
                          onClick={() => handleDeleteTeacher(teacher)}
                          title="Xóa giáo viên"
                        >
                          <Icon name="trash" size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="account-pagination">
          <span>
            Hiển thị {displayStart}-{displayEnd} trên{" "}
            {filteredTeachers.length} giáo viên
          </span>

          <div>
            <button
              type="button"
              disabled={safeCurrentPage === 1}
              onClick={() => setCurrentPage(1)}
            >
              <Icon name="first" size={15} />
            </button>

            <button
              type="button"
              disabled={safeCurrentPage === 1}
              onClick={() =>
                setCurrentPage((page) => Math.max(1, page - 1))
              }
            >
              <Icon name="arrowLeft" size={15} />
            </button>

            {Array.from(
              { length: totalPages },
              (_, index) => index + 1,
            ).map((page) => (
              <button
                key={page}
                type="button"
                className={
                  safeCurrentPage === page ? "current-page" : ""
                }
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </button>
            ))}

            <button
              type="button"
              disabled={
                totalPages === 0 ||
                safeCurrentPage === totalPages
              }
              onClick={() =>
                setCurrentPage((page) =>
                  Math.min(totalPages, page + 1),
                )
              }
            >
              <Icon name="arrowRight" size={15} />
            </button>

            <button
              type="button"
              disabled={
                totalPages === 0 ||
                safeCurrentPage === totalPages
              }
              onClick={() => setCurrentPage(totalPages)}
            >
              <Icon name="last" size={15} />
            </button>
          </div>
        </div>
      </section>

      {selectedTeacher && (
        <EditTeacherForm
          teacher={selectedTeacher}
          onClose={() => setSelectedTeacher(null)}
          onSave={handleSaveTeacher}
        />
      )}

      {showAddTeacher && (
        <AddTeacherForm
          onClose={() => setShowAddTeacher(false)}
          onSave={handleAddTeacher}
        />
      )}

      {detailTeacher && (
        <div
          className="teacher-detail-overlay"
          onClick={() => setDetailTeacher(null)}
        >
          <div
            className="teacher-detail-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="teacher-detail-header">
              <div>
                <h2>Thông tin giáo viên</h2>
                <p>Chi tiết tài khoản giáo viên.</p>
              </div>

              <button
                type="button"
                className="edit-teacher-close"
                onClick={() => setDetailTeacher(null)}
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="teacher-detail-content">
              <div className="teacher-detail-avatar">
                <Icon name="user" size={28} />
              </div>

              <div className="teacher-detail-info">
                <div className="teacher-detail-item">
                  <span>Họ và tên</span>
                  <strong>{detailTeacher.name}</strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Gmail</span>
                  <strong>{detailTeacher.email}</strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Số điện thoại</span>
                  <strong>
                    {detailTeacher.phone_number || "Chưa cập nhật"}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Bộ môn</span>
                  <strong>
                    {detailTeacher.subject || "Chưa cập nhật"}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Trạng thái</span>
                  <strong>
                    {detailTeacher.is_active
                      ? "Đang hoạt động"
                      : "Đã vô hiệu hóa"}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Trạng thái liên kết</span>
                  <strong>
                    {getAuthStatusText(detailTeacher.auth_status)}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Nhà cung cấp đăng nhập</span>
                  <strong>
                    {detailTeacher.auth_provider || "Chưa có thông tin"}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Firebase UID</span>
                  <strong>
                    {detailTeacher.uid || "Chưa liên kết"}
                  </strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Firestore Document ID</span>
                  <strong>{detailTeacher.id || "Chưa có thông tin"}</strong>
                </div>

                <div className="teacher-detail-item">
                  <span>Ngày tạo tài khoản</span>
                  <strong>
                    {formatCreateDate(detailTeacher.create_date)}
                  </strong>
                </div>
              </div>
            </div>

            <div className="teacher-detail-actions">
              <button
                type="button"
                className="edit-teacher-cancel"
                onClick={() => setDetailTeacher(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmModal.open && (
        <ConfirmModal
          title={confirmModal.title}
          message={confirmModal.message}
          confirmText={confirmModal.confirmText}
          cancelText={confirmModal.cancelText}
          onConfirm={confirmModal.onConfirm}
          onCancel={resetConfirmModal}
        />
      )}
    </>
  );
};

export default AccountManagementPanel;