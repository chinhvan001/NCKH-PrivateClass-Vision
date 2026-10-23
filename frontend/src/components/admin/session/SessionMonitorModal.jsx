import { useEffect, useState } from "react";
import { AlertTriangle, Ban, Camera, Pause, Play, RefreshCw, Square, X } from "lucide-react";

import { getAuthHeaders } from "../../../utils/AuthSession";

// Edge node camera-ai ghi session_results 10 giây/lần (camera-ai/docs/web_admin_integration.md).
const POLL_MS = 10000;

const SESSION_STATUS = {
  scheduled: { label: "Đã lên lịch", tone: "gray" },
  running: { label: "Đang giám sát", tone: "green" },
  paused: { label: "Tạm dừng", tone: "orange" },
  completed: { label: "Đã kết thúc", tone: "blue" },
  cancelled: { label: "Đã hủy", tone: "red" },
};

const ACTIONS = {
  scheduled: [
    { next: "cancelled", label: "Hủy tiết", Icon: Ban, confirm: "Hủy tiết học này?" },
    { next: "running", label: "Bắt đầu giám sát", Icon: Play, primary: true },
  ],
  running: [
    { next: "paused", label: "Tạm dừng", Icon: Pause },
    { next: "completed", label: "Kết thúc", Icon: Square, primary: true, confirm: "Kết thúc tiết? Camera AI sẽ chốt kết quả." },
  ],
  paused: [
    { next: "completed", label: "Kết thúc", Icon: Square, confirm: "Kết thúc tiết? Camera AI sẽ chốt kết quả." },
    { next: "running", label: "Tiếp tục", Icon: Play, primary: true },
  ],
};

const SEAT_STATUS = {
  focused: { label: "Tập trung", tone: "green" },
  drowsy: { label: "Buồn ngủ", tone: "red" },
  distracted: { label: "Mất tập trung", tone: "orange" },
  away: { label: "Không có mặt", tone: "gray" },
};

const EDGE_STATUS = {
  idle: "Sẵn sàng",
  monitoring: "Đang giám sát",
  paused: "Tạm dừng",
  unavailable: "Tạm thời không khả dụng",
  outside_schedule: "Ngoài khung giờ giám sát",
};

const ALERT_TYPES = {
  head_drop: "Cúi đầu kéo dài",
  back_turn: "Quay lưng lại",
  side_conversation: "Nói chuyện riêng",
};

const ALERT_STATUS = { acknowledged: "Đã xử lý", dismissed: "Đã bỏ qua" };

const MONITORING_STATUS = {
  running: "đang cập nhật",
  completed: "đã chốt",
  incomplete: "chưa đầy đủ (tiết bị gián đoạn)",
};

async function api(url, options = {}) {
  const response = await fetch(url, { ...options, headers: await getAuthHeaders() });
  const result = await response.json().catch(() => ({}));
  return { ok: response.ok && result.success !== false, result };
}

const formatTime = (iso) => (iso ? new Date(iso).toLocaleTimeString("vi-VN") : "--");

export function SessionStatusBadge({ status }) {
  const info = SESSION_STATUS[status] || SESSION_STATUS.scheduled;
  return <span className={`monitor-badge ${info.tone}`}>{info.label}</span>;
}

export default function SessionMonitorModal({ session, className, teacherName, onClose, onStatusChange }) {
  const [live, setLive] = useState(null);
  const [plan, setPlan] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(0);
  const status = live?.session?.status || session.status;

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const { ok, result } = await api(`/api/admin/schedules/${session.id}/monitoring`);
      if (cancelled) return;
      if (ok) {
        setLive(result.data);
        setError("");
      } else {
        setError(result.message || "Không tải được dữ liệu giám sát.");
      }
    };
    load();
    const timer = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [session.id, version]);

  // Sơ đồ ghế được chốt lúc bắt đầu: chỉ tải lại khi trạng thái tiết đổi.
  useEffect(() => {
    let cancelled = false;
    api(`/api/admin/schedules/${session.id}/seats`).then(({ ok, result }) => {
      if (!cancelled && ok) setPlan(result.data);
    });
    return () => {
      cancelled = true;
    };
  }, [session.id, status]);

  const changeStatus = async (next, force = false) => {
    setBusy(true);
    const { ok, result } = await api(`/api/admin/schedules/${session.id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: next, force }),
    });
    setBusy(false);
    if (!ok && result.code === "edge_offline" && !force) {
      if (window.confirm(`${result.message} Vẫn bắt đầu? Camera AI sẽ nhận tiết ngay khi hoạt động trở lại.`)) {
        await changeStatus(next, true);
      }
      return;
    }
    if (!ok) {
      setError(result.message || "Không đổi được trạng thái tiết học.");
      return;
    }
    setVersion((value) => value + 1);
    onStatusChange();
  };

  const handleAlert = async (alertId, alertStatus) => {
    const { ok, result } = await api(`/api/admin/schedules/${session.id}/alerts/${alertId}`, {
      method: "PUT",
      body: JSON.stringify({ status: alertStatus }),
    });
    if (ok) {
      setVersion((value) => value + 1);
    } else {
      setError(result.message || "Không cập nhật được cảnh báo.");
    }
  };

  const edge = live?.edge;
  const result = live?.result;
  const seatResults = result?.result_map || {};
  const names = Object.fromEntries((plan?.seats || []).map((seat) => [seat.seat_id, seat.student_name]));

  return (
    <div className="session-modal-overlay" onClick={onClose}>
      <div className="session-modal session-monitor" onClick={(event) => event.stopPropagation()}>
        <div className="session-modal-header">
          <div>
            <h2>
              {session.subject || "Tiết học"} · {className}
            </h2>
            <p>
              {session.session_date} · {session.start_time} - {session.end_time} · GV: {teacherName}
            </p>
          </div>
          <div className="monitor-header-actions">
            <SessionStatusBadge status={status} />
            <button type="button" onClick={onClose} className="session-modal-close" title="Đóng">
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="session-modal-content">
          {error && <div className="monitor-error">{error}</div>}

          <div className="monitor-edge">
            <Camera size={16} />
            {edge ? (
              <span>
                Camera AI {edge.camera_id}:{" "}
                <strong className={edge.online ? "monitor-text-ok" : "monitor-text-bad"}>
                  {edge.online ? EDGE_STATUS[edge.status] || edge.status : "Offline"}
                </strong>
                {edge.online && edge.status === "monitoring" && ` · ${edge.fps} khung hình/giây`} · cập nhật{" "}
                {formatTime(edge.updated_at)}
              </span>
            ) : (
              <span>Lớp chưa có camera AI gửi tín hiệu.</span>
            )}
          </div>

          {plan && plan.column_count > 0 ? (
            <div
              className="monitor-seat-grid"
              style={{ gridTemplateColumns: `repeat(${plan.column_count}, minmax(0, 1fr))` }}
            >
              {plan.seats.map((seat) => {
                const seatResult = seatResults[seat.seat_id];
                const seatStatus = SEAT_STATUS[seatResult?.status];
                return (
                  <div key={seat.seat_id} className={`monitor-seat ${seatStatus ? seatStatus.tone : "empty"}`}>
                    <div className="monitor-seat-head">
                      <strong>{seat.seat_id}</strong>
                      {seatResult?.concentration != null && <span>{seatResult.concentration}%</span>}
                    </div>
                    <div className="monitor-seat-name">{seat.student_name || "Chưa xếp chỗ"}</div>
                    <div className="monitor-seat-status">{seatStatus ? seatStatus.label : "Chưa có dữ liệu"}</div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="monitor-muted">Lớp chưa có sơ đồ chỗ ngồi.</p>
          )}
          {result && (
            <p className="monitor-muted">
              Kết quả lúc {formatTime(result.captured_at)}, {MONITORING_STATUS[result.monitoring_status] || ""}. Điểm là
              mức tập trung trong 60 giây gần nhất.
            </p>
          )}

          <h3 className="monitor-section-title">
            <AlertTriangle size={16} /> Cảnh báo gần đây
          </h3>
          {live?.alerts?.length ? (
            <ul className="monitor-alerts">
              {live.alerts.map((alert) => (
                <li key={alert.id}>
                  <div>
                    <strong>{ALERT_TYPES[alert.type] || alert.type}</strong>
                    <span>
                      Ghế {alert.seat_id}
                      {names[alert.seat_id] ? ` · ${names[alert.seat_id]}` : ""} · phút{" "}
                      {Math.floor(alert.start_sec / 60) + 1} · {Math.round(alert.duration_sec)} giây
                    </span>
                  </div>
                  {ALERT_STATUS[alert.status] ? (
                    <span className="monitor-muted">{ALERT_STATUS[alert.status]}</span>
                  ) : (
                    <div className="monitor-alert-actions">
                      <button type="button" className="session-secondary-btn" onClick={() => handleAlert(alert.id, "dismissed")}>
                        Bỏ qua
                      </button>
                      <button type="button" className="session-primary-btn" onClick={() => handleAlert(alert.id, "acknowledged")}>
                        Đã xử lý
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p className="monitor-muted">Chưa có cảnh báo.</p>
          )}
        </div>

        <div className="session-modal-footer">
          <button type="button" className="session-secondary-btn" onClick={() => setVersion((value) => value + 1)}>
            <RefreshCw size={14} /> Làm mới
          </button>
          {(ACTIONS[status] || []).map(({ next, label, Icon, primary, confirm }) => (
            <button
              key={next}
              type="button"
              disabled={busy}
              className={primary ? "session-primary-btn" : "session-secondary-btn"}
              onClick={() => (!confirm || window.confirm(confirm)) && changeStatus(next)}
            >
              <Icon size={14} /> {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
