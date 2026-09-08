import { useNavigate, useParams } from "react-router-dom";

const SessionDetail = ({ sessions = [] }) => {
  const navigate = useNavigate();
  const { id } = useParams();

  const session = sessions.find((item) => String(item.id) === String(id)) || {
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

  const getFocusLabel = (focus) => {
    if (focus === null || focus === undefined) {
      return "Chưa có dữ liệu";
    }

    if (focus >= 80) return "Tốt";
    if (focus >= 60) return "Trung bình";

    return "Thấp";
  };

  const getFocusClass = (focus) => {
    if (focus >= 80) return "good";
    if (focus >= 60) return "medium";

    return "low";
  };

  const formatDate = (date) => {
    return new Date(`${date}T00:00:00`).toLocaleDateString("vi-VN", {
      weekday: "long",
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const getDuration = () => {
    const [startHour, startMinute] = session.start.split(":").map(Number);

    const [endHour, endMinute] = session.end.split(":").map(Number);

    return endHour * 60 + endMinute - (startHour * 60 + startMinute);
  };

  const duration = getDuration();

  const hasFocusData = session.focus !== null && session.focus !== undefined;

  const focusedMinutes = hasFocusData
    ? Math.round((duration * session.focus) / 100)
    : 0;

  const unfocusedMinutes = hasFocusData ? duration - focusedMinutes : 0;

  return (
    <main className="session-detail-page">
      <div className="session-detail-page-header">
        <div>
          <h1 className="session-detail-page-title">Chi tiết phiên lớp học</h1>

          <p className="session-detail-page-description">
            Thông tin và kết quả giám sát của phiên lớp học
          </p>
        </div>
      </div>

      <section className="session-detail-hero">
        <div className="session-detail-hero-top">
          <div>
            <span className="session-detail-number">PHIÊN #{session.id}</span>

            <h2>{session.subject}</h2>

            <p className="session-detail-class">Lớp {session.className}</p>
          </div>

          <span className={`session-detail-status ${session.status}`}>
            <span className="session-detail-status-dot" />

            {getStatusLabel(session.status)}
          </span>
        </div>

        <div className="session-detail-hero-meta">
          <div className="session-detail-hero-meta-item">
            <span className="session-detail-meta-icon">◷</span>

            <div>
              <span>Thời gian</span>

              <strong>
                {session.start} - {session.end}
              </strong>
            </div>
          </div>

          <div className="session-detail-hero-meta-item">
            <span className="session-detail-meta-icon">▣</span>

            <div>
              <span>Ngày học</span>

              <strong>{formatDate(session.date)}</strong>
            </div>
          </div>

          <div className="session-detail-hero-meta-item">
            <span className="session-detail-meta-icon">□</span>

            <div>
              <span>Phòng học</span>

              <strong>{session.room}</strong>
            </div>
          </div>
        </div>
      </section>

      <div className="session-detail-main-grid">
        <section className="session-detail-card">
          <div className="session-detail-card-header">
            <div>
              <span className="session-detail-card-label">THÔNG TIN</span>

              <h3>Thông tin phiên lớp học</h3>
            </div>
          </div>

          <div className="session-detail-info-list">
            <div className="session-detail-info-item">
              <div className="session-detail-info-icon blue">GV</div>

              <div>
                <span>Giáo viên</span>

                <strong>{session.teacher}</strong>
              </div>
            </div>

            <div className="session-detail-info-item">
              <div className="session-detail-info-icon blue">MH</div>

              <div>
                <span>Môn học</span>

                <strong>{session.subject}</strong>
              </div>
            </div>

            <div className="session-detail-info-item">
              <div className="session-detail-info-icon blue">P</div>

              <div>
                <span>Phòng học</span>

                <strong>{session.room}</strong>
              </div>
            </div>

            <div className="session-detail-info-item">
              <div className="session-detail-info-icon blue">⏱</div>

              <div>
                <span>Thời lượng</span>

                <strong>{duration} phút</strong>
              </div>
            </div>
          </div>
        </section>

        <section className="session-detail-card session-focus-card">
          <div className="session-detail-card-header">
            <div>
              <span className="session-detail-card-label">GIÁM SÁT</span>

              <h3>Mức độ tập trung</h3>
            </div>

            {hasFocusData && (
              <span
                className={`session-focus-label ${getFocusClass(
                  session.focus,
                )}`}
              >
                {getFocusLabel(session.focus)}
              </span>
            )}
          </div>

          {hasFocusData ? (
            <>
              <div className="session-focus-score">
                <strong>{session.focus}%</strong>

                <span>Mức tập trung tổng thể</span>
              </div>

              <div className="session-focus-progress">
                <div
                  className={`session-focus-progress-bar ${getFocusClass(
                    session.focus,
                  )}`}
                  style={{
                    width: `${session.focus}%`,
                  }}
                />
              </div>

              <div className="session-focus-scale">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
              </div>
            </>
          ) : (
            <div className="session-detail-no-data">
              <span>—</span>

              <p>Phiên lớp học chưa bắt đầu nên chưa có dữ liệu giám sát.</p>
            </div>
          )}
        </section>
      </div>

      {hasFocusData && (
        <section className="session-evaluation-section">
          <div className="session-detail-section-heading">
            <div>
              <span className="session-detail-card-label">KẾT QUẢ</span>

              <h3>Đánh giá phiên lớp học</h3>
            </div>
          </div>

          <div className="session-metrics-grid">
            <div className="session-metric-card primary">
              <span className="session-metric-icon">%</span>

              <div>
                <strong>{session.focus}%</strong>

                <span>Tập trung tổng thể</span>
              </div>
            </div>

            <div className="session-metric-card">
              <span className="session-metric-icon">✓</span>

              <div>
                <strong>{focusedMinutes} phút</strong>

                <span>Thời gian tập trung</span>
              </div>
            </div>

            <div className="session-metric-card">
              <span className="session-metric-icon">!</span>

              <div>
                <strong>{unfocusedMinutes} phút</strong>

                <span>Thời gian mất tập trung</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {session.status !== "cancelled" && (
        <div className="session-detail-footer">
          <button
            className="session-detail-back-btn"
            onClick={() => navigate("/session-management")}
          >
            <span>←</span>
            Quay lại
          </button>
          <button type="button" className="session-danger-btn">
            Hủy phiên lớp học
          </button>
        </div>
      )}
    </main>
  );
};

export default SessionDetail;
