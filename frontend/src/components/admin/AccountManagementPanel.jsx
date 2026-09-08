import { useMemo, useState } from "react";

import Icon from "../common/Icon";

import EditTeacherForm from "./EditTeacherForm";

const AccountManagementPanel = ({
  users = [],
  loading = false,
  onRefresh,
  onUpdateUser,
}) => {
  const [search, setSearch] = useState("");
  const [subjectFilter, setSubjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedTeacher, setSelectedTeacher] = useState(null);

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

  /*
   * Chuẩn hóa dữ liệu giáo viên.
   *
   * Backend sử dụng:
   * - uid
   * - phone_number
   * - is_active
   *
   * Giữ nguyên các tên field này trong toàn bộ component
   * để đồng bộ với backend và EditTeacherForm.
   */
  const teachers = useMemo(() => {
    return users.map((user) => {
      let subjects = [];

      if (Array.isArray(user.subject)) {
        subjects = user.subject;
      } else if (user.subject) {
        subjects = [user.subject];
      }

      return {
        uid: user.uid || user.id,
        email: user.email || "Chưa có email",
        name: user.name || "Chưa cập nhật",
        phone_number: user.phone_number || "",
        subject: subjects,
        is_active: user.is_active !== false,
      };
    });
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
        subjectFilter === "all" ||
        teacher.subject.includes(subjectFilter);

      const matchStatus =
        statusFilter === "all" ||
        (statusFilter === "active" && teacher.is_active) ||
        (statusFilter === "inactive" && !teacher.is_active);

      return matchSearch && matchSubject && matchStatus;
    });
  }, [teachers, search, subjectFilter, statusFilter]);

  const totalTeachers = teachers.length;

  const activeTeachers = teachers.filter(
    (teacher) => teacher.is_active
  ).length;

  const inactiveTeachers = totalTeachers - activeTeachers;

  const handleRefresh = () => {
    if (onRefresh) {
      onRefresh();
    }
  };

  /*
   * EditTeacherForm trả về:
   * {
   *   uid,
   *   name,
   *   phone_number,
   *   subject,
   *   is_active
   * }
   *
   * Việc gọi API được xử lý ở AccountManagement.jsx
   * thông qua onUpdateUser để đảm bảo Authorization token
   * được gửi đúng cách.
   */
  const handleSaveTeacher = async (updatedTeacher) => {
    try {
      if (!onUpdateUser) {
        throw new Error(
          "Không tìm thấy chức năng cập nhật tài khoản."
        );
      }

      await onUpdateUser(updatedTeacher);

      setSelectedTeacher(null);
    } catch (error) {
      console.error("Update teacher error:", error);
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
              onChange={(e) => setSearch(e.target.value)}
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
              onChange={(e) => setSubjectFilter(e.target.value)}
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
              onChange={(e) => setStatusFilter(e.target.value)}
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
                  <td
                    colSpan="6"
                    className="table-empty"
                  >
                    Đang tải danh sách giáo viên...
                  </td>
                </tr>
              ) : filteredTeachers.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="table-empty"
                  >
                    Không tìm thấy tài khoản giáo viên.
                  </td>
                </tr>
              ) : (
                filteredTeachers.map((teacher) => (
                  <tr
                    key={teacher.uid || teacher.email}
                  >
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
                        {teacher.subject.length > 0 ? (
                          teacher.subject.map(
                            (subject, index) => (
                              <span
                                key={`${subject}-${index}`}
                                className="account-subject-tag"
                              >
                                {subject}
                              </span>
                            )
                          )
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
                          teacher.is_active
                            ? "active"
                            : "inactive"
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
                          aria-label={`Chỉnh sửa ${teacher.email}`}
                          onClick={() =>
                            setSelectedTeacher(teacher)
                          }
                        >
                          <Icon name="edit" size={17} />
                        </button>

                        <button
                          type="button"
                          aria-label={`Thao tác với ${teacher.email}`}
                        >
                          <Icon name="more" size={18} />
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
            Hiển thị {filteredTeachers.length} giáo viên
          </span>

          <div>
            <button
              type="button"
              disabled
            >
              <Icon name="first" size={15} />
            </button>

            <button
              type="button"
              disabled
            >
              <Icon name="arrowLeft" size={15} />
            </button>

            <button
              type="button"
              className="current-page"
            >
              1
            </button>

            <button type="button">
              <Icon name="arrowRight" size={15} />
            </button>

            <button type="button">
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
    </>
  );
};

export default AccountManagementPanel;