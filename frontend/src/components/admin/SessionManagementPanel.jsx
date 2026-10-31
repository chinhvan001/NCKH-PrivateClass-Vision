import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import Icon from "../common/Icon";

const SessionManagementPanel = () => {
  const navigate = useNavigate();

  const [selectedDate, setSelectedDate] = useState(new Date(2026, 8, 2));
  const [showCreateModal, setShowCreateModal] = useState(false);

  const [filters, setFilters] = useState({
    search: "",
    class: "all",
    subject: "all",
    teacher: "all",
    status: "all",
  });

  const sessions = [
    {
      id: 1,
      date: "2026-09-02",
      start: "07:00",
      end: "08:00",
      className: "10A1",
      subject: "Toán",
      teacher: "Nguyễn Văn An",
      room: "P101",
      status: "completed",
      focus: 82,
    },
    {
      id: 2,
      date: "2026-09-02",
      start: "07:00",
      end: "08:00",
      className: "10A2",
      subject: "Ngữ Văn",
      teacher: "Trần Thị Bình",
      room: "P102",
      status: "completed",
      focus: 76,
    },
    {
      id: 3,
      date: "2026-09-02",
      start: "07:00",
      end: "08:00",
      className: "10A3",
      subject: "Tiếng Anh",
      teacher: "Lê Minh Anh",
      room: "P103",
      status: "completed",
      focus: 88,
    },
    {
      id: 4,
      date: "2026-09-02",
      start: "08:00",
      end: "09:00",
      className: "10A1",
      subject: "Vật Lý",
      teacher: "Phạm Minh Đức",
      room: "P101",
      status: "live",
      focus: 71,
    },
    {
      id: 5,
      date: "2026-09-02",
      start: "08:00",
      end: "09:00",
      className: "10A2",
      subject: "Toán",
      teacher: "Nguyễn Văn An",
      room: "P102",
      status: "live",
      focus: 84,
    },
    {
      id: 6,
      date: "2026-09-02",
      start: "08:00",
      end: "09:00",
      className: "10A3",
      subject: "Hóa Học",
      teacher: "Hoàng Văn Nam",
      room: "P103",
      status: "scheduled",
      focus: null,
    },
    {
      id: 7,
      date: "2026-09-02",
      start: "09:00",
      end: "10:00",
      className: "10A1",
      subject: "Tiếng Anh",
      teacher: "Lê Minh Anh",
      room: "P101",
      status: "scheduled",
      focus: null,
    },
    {
      id: 8,
      date: "2026-09-02",
      start: "09:00",
      end: "10:00",
      className: "10A2",
      subject: "Sinh Học",
      teacher: "Đỗ Thu Hà",
      room: "P102",
      status: "scheduled",
      focus: null,
    },
    {
      id: 9,
      date: "2026-09-02",
      start: "10:00",
      end: "11:00",
      className: "10A1",
      subject: "Lịch Sử",
      teacher: "Nguyễn Thị Lan",
      room: "P101",
      status: "scheduled",
      focus: null,
    },
    {
      id: 10,
      date: "2026-09-02",
      start: "10:00",
      end: "11:00",
      className: "10A3",
      subject: "Toán",
      teacher: "Nguyễn Văn An",
      room: "P103",
      status: "scheduled",
      focus: null,
    },
  ];

  const classes = ["10A1", "10A2", "10A3"];

  const subjects = [
    "Toán",
    "Ngữ Văn",
    "Tiếng Anh",
    "Vật Lý",
    "Hóa Học",
    "Sinh Học",
    "Lịch Sử",
    "Địa Lý",
    "Giáo dục kinh tế và pháp luật",
    "Tin Học",
    "Công Nghệ",
    "Âm Nhạc",
    "Mỹ Thuật",
    "Thể Dục",
  ];

  const teachers = [
    "Nguyễn Văn An",
    "Trần Thị Bình",
    "Lê Minh Anh",
    "Phạm Minh Đức",
    "Hoàng Văn Nam",
    "Đỗ Thu Hà",
    "Nguyễn Thị Lan",
  ];

  const timeSlots = [
    "07:00",
    "08:00",
    "09:00",
    "10:00",
  ];

  const formatDateKey = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
  };

  const formatDate = (date) => {
    return date.toLocaleDateString("vi-VN", {
      weekday: "long",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case "live":
        return "Đang diễn ra";

      case "completed":
        return "Hoàn thành";

      case "scheduled":
        return "Sắp diễn ra";

      case "cancelled":
        return "Đã hủy";

      default:
        return status;
    }
  };

  const getSessionStatusClass = (status) => {
    switch (status) {
      case "live":
        return "live";

      case "completed":
        return "completed";

      case "scheduled":
        return "scheduled";

      case "cancelled":
        return "cancelled";

      default:
        return "";
    }
  };

  const getFocusClass = (focus) => {
    if (focus >= 80) return "good";
    if (focus >= 60) return "medium";

    return "low";
  };

  const updateFilter = (key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const changeDate = (amount) => {
    const newDate = new Date(selectedDate);

    newDate.setDate(newDate.getDate() + amount);

    setSelectedDate(newDate);
  };

  const goToday = () => {
    setSelectedDate(new Date(2026, 8, 2));
  };

  const selectedDateKey = formatDateKey(selectedDate);

  const dateSessions = useMemo(() => {
    return sessions.filter(
      (session) => session.date === selectedDateKey
    );
  }, [selectedDateKey]);

  const filteredSessions = useMemo(() => {
    return dateSessions.filter((session) => {
      const search = filters.search.trim().toLowerCase();

      const matchesSearch =
        !search ||
        session.className.toLowerCase().includes(search) ||
        session.subject.toLowerCase().includes(search) ||
        session.teacher.toLowerCase().includes(search) ||
        session.room.toLowerCase().includes(search);

      const matchesClass =
        filters.class === "all" ||
        session.className === filters.class;

      const matchesSubject =
        filters.subject === "all" ||
        session.subject === filters.subject;

      const matchesTeacher =
        filters.teacher === "all" ||
        session.teacher === filters.teacher;

      const matchesStatus =
        filters.status === "all" ||
        session.status === filters.status;

      return (
        matchesSearch &&
        matchesClass &&
        matchesSubject &&
        matchesTeacher &&
        matchesStatus
      );
    });
  }, [dateSessions, filters]);

  const totalSessions = dateSessions.length;

  const liveSessions = dateSessions.filter(
    (session) => session.status === "live"
  ).length;

  const scheduledSessions = dateSessions.filter(
    (session) => session.status === "scheduled"
  ).length;

  const completedSessions = dateSessions.filter(
    (session) => session.status === "completed"
  ).length;

  const getSessionForSlot = (className, time) => {
    return filteredSessions.find(
      (session) =>
        session.className === className &&
        session.start === time
    );
  };

  const openSessionDetail = (session) => {
    navigate(`/session-management/${session.id}`, {
      state: {
        session,
      },
    });
  };

  return (
    <div className="session-management">

      <div className="session-page-header">
        <div>
          <h1 className="session-page-title">
            Quản lý phiên lớp học
          </h1>

          <p className="session-page-description">
            Quản lý lịch học và các phiên lớp học trong toàn trường
          </p>
        </div>

        <button
          type="button"
          className="session-create-btn"
          onClick={() => setShowCreateModal(true)}
        >
          <Icon name="plus" size={18} />

          <span>Tạo phiên lớp học</span>
        </button>
      </div>

      <div className="session-statistics">
        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">
              Tổng phiên
            </p>

            <p className="session-stat-value">
              {totalSessions}
            </p>
          </div>

          <div className="session-stat-icon blue">
            <Icon name="activity" size={21} />
          </div>
        </div>

        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">
              Đang diễn ra
            </p>

            <p className="session-stat-value">
              {liveSessions}
            </p>
          </div>

          <div className="session-stat-icon green">
            <span className="session-stat-live-dot" />
          </div>
        </div>

        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">
              Sắp diễn ra
            </p>

            <p className="session-stat-value">
              {scheduledSessions}
            </p>
          </div>

          <div className="session-stat-icon orange">
            <Icon name="bell" size={21} />
          </div>
        </div>

        <div className="session-stat-card">
          <div>
            <p className="session-stat-label">
              Hoàn thành
            </p>

            <p className="session-stat-value">
              {completedSessions}
            </p>
          </div>

          <div className="session-stat-icon purple">
            <Icon name="checkCircle" size={21} />
          </div>
        </div>
      </div>

      <div className="session-calendar-card">
        <div className="session-date-header">
          <div className="session-date-navigation">
            <button
              type="button"
              className="session-date-btn"
              onClick={() => changeDate(-1)}
              aria-label="Ngày trước"
            >
              ‹
            </button>

            <div className="session-current-date">
              {formatDate(selectedDate)}
            </div>

            <button
              type="button"
              className="session-date-btn"
              onClick={() => changeDate(1)}
              aria-label="Ngày sau"
            >
              ›
            </button>

            <button
              type="button"
              className="session-today-btn"
              onClick={goToday}
            >
              Hôm nay
            </button>
          </div>

          <div className="session-status-legend">
            <span className="session-status-legend-item">
              <span className="session-status-dot live" />
              Đang diễn ra
            </span>

            <span className="session-status-legend-item">
              <span className="session-status-dot scheduled" />
              Sắp diễn ra
            </span>

            <span className="session-status-legend-item">
              <span className="session-status-dot completed" />
              Hoàn thành
            </span>
          </div>
        </div>

        <div className="session-filters">
          <div className="session-search">
            <span className="session-search-icon">
              <Icon name="search" size={17} />
            </span>

            <input
              type="text"
              value={filters.search}
              onChange={(e) =>
                updateFilter("search", e.target.value)
              }
              placeholder="Tìm kiếm phiên lớp học..."
              className="session-filter-input"
            />
          </div>

          <select
            value={filters.class}
            onChange={(e) =>
              updateFilter("class", e.target.value)
            }
            className="session-filter-select"
          >
            <option value="all">
              Tất cả lớp
            </option>

            {classes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <select
            value={filters.subject}
            onChange={(e) =>
              updateFilter("subject", e.target.value)
            }
            className="session-filter-select"
          >
            <option value="all">
              Tất cả môn
            </option>

            {subjects.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <select
            value={filters.teacher}
            onChange={(e) =>
              updateFilter("teacher", e.target.value)
            }
            className="session-filter-select"
          >
            <option value="all">
              Tất cả giáo viên
            </option>

            {teachers.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <select
            value={filters.status}
            onChange={(e) =>
              updateFilter("status", e.target.value)
            }
            className="session-filter-select"
          >
            <option value="all">
              Tất cả trạng thái
            </option>

            <option value="live">
              Đang diễn ra
            </option>

            <option value="scheduled">
              Sắp diễn ra
            </option>

            <option value="completed">
              Hoàn thành
            </option>

            <option value="cancelled">
              Đã hủy
            </option>
          </select>
        </div>

        <div className="session-calendar-wrapper">
          <div className="session-calendar">

            <div className="session-time-header">
              <div className="session-time-header-label">
                Lớp
              </div>

              {timeSlots.map((time) => (
                <div
                  key={time}
                  className="session-time-header-cell"
                >
                  {time}
                </div>
              ))}
            </div>

            {classes.map((className) => (
              <div
                key={className}
                className="session-class-row"
              >
                <div className="session-class-name">
                  <strong>{className}</strong>

                  <span>Lớp học</span>
                </div>

                {timeSlots.map((time) => {
                  const session = getSessionForSlot(
                    className,
                    time
                  );

                  return (
                    <div
                      key={`${className}-${time}`}
                      className="session-cell"
                    >
                      {session ? (
                        <button
                          type="button"
                          className={`session-item ${getSessionStatusClass(
                            session.status
                          )}`}
                          onClick={() =>
                            openSessionDetail(session)
                          }
                        >
                          <div className="session-item-header">
                            <div>
                              <p className="session-item-time">
                                {session.start} - {session.end}
                              </p>

                              <p className="session-item-subject">
                                {session.subject}
                              </p>
                            </div>

                            <span
                              className={`session-item-status-dot ${getSessionStatusClass(
                                session.status
                              )}`}
                            />
                          </div>

                          <div className="session-item-info">
                            <p>
                              <span>GV:</span>{" "}
                              {session.teacher}
                            </p>

                            <p>
                              <span>Phòng:</span>{" "}
                              {session.room}
                            </p>
                          </div>

                          <div className="session-item-footer">
                            <span
                              className={`session-item-status ${getSessionStatusClass(
                                session.status
                              )}`}
                            >
                              {getStatusLabel(session.status)}
                            </span>

                            {session.focus !== null && (
                              <span
                                className={`session-item-focus ${getFocusClass(
                                  session.focus
                                )}`}
                              >
                                {session.focus}%
                              </span>
                            )}
                          </div>
                        </button>
                      ) : (
                        <div className="session-empty-cell">
                          <span>—</span>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {showCreateModal && (
        <div
          className="session-modal-overlay"
          onMouseDown={(e) => {
            if (e.target === e.currentTarget) {
              setShowCreateModal(false);
            }
          }}
        >
          <div className="session-modal">

            <div className="session-modal-header">
              <div>
                <h2>Tạo phiên lớp học</h2>

                <p>
                  Tạo phiên lớp học mới trong lịch học
                </p>
              </div>

              <button
                type="button"
                className="session-modal-close"
                onClick={() =>
                  setShowCreateModal(false)
                }
                aria-label="Đóng"
              >
                ×
              </button>
            </div>

            <div className="session-modal-content">

              <div className="session-form-group">
                <label>Ngày học</label>

                <input
                  type="date"
                  defaultValue="2026-09-02"
                  className="session-form-control"
                />
              </div>

              <div className="session-form-grid">
                <div className="session-form-group">
                  <label>Bắt đầu</label>

                  <input
                    type="time"
                    defaultValue="07:00"
                    className="session-form-control"
                  />
                </div>

                <div className="session-form-group">
                  <label>Kết thúc</label>

                  <input
                    type="time"
                    defaultValue="08:00"
                    className="session-form-control"
                  />
                </div>
              </div>

              <div className="session-form-group">
                <label>Lớp học</label>

                <select className="session-form-control">
                  <option value="">
                    Chọn lớp
                  </option>

                  {classes.map((item) => (
                    <option
                      key={item}
                      value={item}
                    >
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="session-form-group">
                <label>Môn học</label>

                <select className="session-form-control">
                  <option value="">
                    Chọn môn
                  </option>

                  {subjects.map((item) => (
                    <option
                      key={item}
                      value={item}
                    >
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="session-form-group">
                <label>Giáo viên</label>

                <select className="session-form-control">
                  <option value="">
                    Chọn giáo viên
                  </option>

                  {teachers.map((item) => (
                    <option
                      key={item}
                      value={item}
                    >
                      {item}
                    </option>
                  ))}
                </select>
              </div>

              <div className="session-form-group">
                <label>Phòng học</label>

                <input
                  type="text"
                  placeholder="Ví dụ: P101"
                  className="session-form-control"
                />
              </div>
            </div>

            <div className="session-modal-footer">
              <button
                type="button"
                className="session-secondary-btn"
                onClick={() =>
                  setShowCreateModal(false)
                }
              >
                Hủy
              </button>

              <button
                type="button"
                className="session-primary-btn"
                onClick={() =>
                  setShowCreateModal(false)
                }
              >
                Tạo phiên lớp học
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionManagementPanel;