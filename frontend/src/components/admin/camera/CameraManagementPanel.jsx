import { useEffect, useMemo, useState } from "react";
import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";
import CustomScrollBar from "../../common/CustomScrollBar";

import {
  getCameras,
  createCamera,
  configureCamera,
  deleteCamera,
} from "../../../services/cameraService";

import AddCameraForm from "./AddCameraForm";

const CameraManagementPanel = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [roomFilter, setRoomFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [showAddCamera, setShowAddCamera] = useState(false);

  // State quản lý Modal xem trực tiếp camera
  const [viewingCamera, setViewingCamera] = useState(null);

  const [configuringCameraId, setConfiguringCameraId] = useState(null);
  const [deletingCameraId, setDeletingCameraId] = useState(null);
  const [confirmModal, setConfirmModal] = useState({
    open: false,
    title: "",
    message: "",
    confirmText: "Xác nhận",
    cancelText: "Hủy",
    onConfirm: null,
  });

  const loadCameras = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getCameras();
      setCameras(data);
    } catch (error) {
      console.error("Get cameras error:", error);
      setError(error.message || "Không thể tải danh sách camera.");
    } finally {
      setLoading(false);
    }
  };

  // Gọi API tải danh sách camera khi vừa vào trang
  useEffect(() => {
    loadCameras();
  }, []);

  // Hàm tối ưu: Tự động trích xuất tên stream path động từ rtsp_url trong database
  const getStreamPath = (camera) => {
    if (camera && camera.rtsp_url) {
      const parts = camera.rtsp_url.split("/");
      const lastPart = parts[parts.length - 1];
      if (lastPart) return lastPart;
    }
    return `camera-${camera?.camera_id || 'p201a'}`;
  };

  // Tự động kích hoạt hệ thống tự động hóa (LDPlayer + MediaMTX + FFmpeg) với stream_path động
  useEffect(() => {
    if (cameras.length === 0) return;

    const triggerAutoFlow = async () => {
      try {
        // Lấy chính xác tên stream path của camera đầu tiên hoặc camera online
        const targetCamera = cameras.find(c => c.status === "online") || cameras[0];
        const targetStreamPath = getStreamPath(targetCamera);
        
        console.log(`Đang gửi yêu cầu khởi chạy luồng động cho: ${targetStreamPath}`);

        const response = await fetch('/api/start-auto-flow', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            stream_path: targetStreamPath,
            index: 0
          })
        });

        const data = await response.json();
        if (data.success) {
          console.log("Tự động mở hệ thống thành công:", data.message);
        } else {
          console.error("Lỗi tự động mở từ server:", data.message);
        }
      } catch (error) {
        console.error("Không thể kết nối đến API tự động khởi chạy:", error);
      }
    };

    triggerAutoFlow();
  }, [cameras]);

  const rooms = useMemo(() => {
    const roomSet = new Set();
    cameras.forEach((camera) => {
      if (camera.room_id) {
        roomSet.add(camera.room_id);
      }
    });
    return Array.from(roomSet);
  }, [cameras]);

  const totalCameras = cameras.length;
  const onlineCameras = cameras.filter((camera) => camera.status === "online").length;
  const offlineCameras = cameras.filter((camera) => camera.status !== "online").length;
  const unconfiguredCameras = cameras.filter((camera) => !camera.is_configured).length;

  const filteredCameras = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return cameras.filter((camera) => {
      const matchSearch =
        !keyword ||
        (camera.name || "").toLowerCase().includes(keyword) ||
        (camera.camera_id || "").toLowerCase().includes(keyword) ||
        (camera.classroom_name || "").toLowerCase().includes(keyword) ||
        (camera.ip_address || "").toLowerCase().includes(keyword);

      const matchRoom = roomFilter === "all" || camera.room_id === roomFilter;
      const matchStatus = statusFilter === "all" || camera.status === statusFilter;

      return matchSearch && matchRoom && matchStatus;
    });
  }, [cameras, search, roomFilter, statusFilter]);

  const handleRefresh = () => {
    loadCameras();
  };

  const handleConfigureCamera = async (camera) => {
    try {
      setConfiguringCameraId(camera.camera_id);
      setError("");
      await configureCamera(camera.camera_id);
      await loadCameras();
    } catch (error) {
      console.error("Configure camera error:", error);
      setError(error.message || "Không thể cấu hình camera.");
    } finally {
      setConfiguringCameraId(null);
    }
  };

  const handleDeleteCamera = (camera) => {
    setConfirmModal({
      open: true,
      title: "Xóa camera",
      message: `Bạn có chắc chắn muốn xóa camera "${camera.name}" khỏi phòng "${camera.classroom_name || camera.room_id}"?`,
      confirmText: "Xóa",
      cancelText: "Hủy",
      onConfirm: async () => {
        try {
          setDeletingCameraId(camera.camera_id);
          setError("");
          await deleteCamera(camera.camera_id);
          await loadCameras();
          setConfirmModal({ open: false, title: "", message: "", onConfirm: null });
        } catch (error) {
          console.error("Delete camera error:", error);
          setError(error.message || "Không thể xóa camera.");
          setConfirmModal({ open: false, title: "", message: "", onConfirm: null });
        } finally {
          setDeletingCameraId(null);
        }
      },
    });
  };

  return (
    <div className="camera-management-page">
      <section className="camera-page-heading">
        <div>
          <h1>Quản lý camera</h1>
          <p>Quản lý và theo dõi các camera trong hệ thống.</p>
        </div>
      </section>

      <section className="camera-stats-section">
        <h2>Tổng quan camera</h2>

        <div className="camera-stats-grid">
          <article className="camera-stat-card blue">
            <div className="camera-stat-icon">
              <Icon name="camera" size={21} />
            </div>
            <div>
              <span>Tổng camera</span>
              <strong>{totalCameras}</strong>
              <small>Thiết bị</small>
            </div>
          </article>

          <article className="camera-stat-card green">
            <div className="camera-stat-icon">
              <Icon name="checkCircle" size={21} />
            </div>
            <div>
              <span>Đang online</span>
              <strong>{onlineCameras}</strong>
              <small>Đang kết nối</small>
            </div>
          </article>

          <article className="camera-stat-card red">
            <div className="camera-stat-icon">
              <Icon name="xCircle" size={21} />
            </div>
            <div>
              <span>Đang offline</span>
              <strong>{offlineCameras}</strong>
              <small>Mất kết nối</small>
            </div>
          </article>

          <article className="camera-stat-card orange">
            <div className="camera-stat-icon">
              <Icon name="alertCircle" size={21} />
            </div>
            <div>
              <span>Chưa cấu hình</span>
              <strong>{unconfiguredCameras}</strong>
              <small>Cần cấu hình</small>
            </div>
          </article>
        </div>
      </section>

      <section className="camera-panel">
        <div className="camera-panel-heading">
          <div>
            <h2>Quản lý camera</h2>
            <p>Danh sách camera được kết nối với phòng học.</p>
          </div>

          <button
            type="button"
            className="camera-add-button"
            onClick={() => setShowAddCamera(true)}
          >
            <Icon name="plus" size={17} />
            <span>Thêm camera</span>
          </button>
        </div>

        <div className="camera-filters">
          <div className="camera-search">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Tìm kiếm camera..."
            />
            <span className="camera-search-icon">
              <Icon name="search" size={19} />
            </span>
          </div>

          <label className="camera-select">
            <span>Phòng</span>
            <select
              value={roomFilter}
              onChange={(e) => setRoomFilter(e.target.value)}
            >
              <option value="all">Tất cả phòng</option>
              {rooms.map((room) => (
                <option key={room} value={room}>
                  {room}
                </option>
              ))}
            </select>
          </label>

          <label className="camera-select">
            <span>Trạng thái</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="online">Đang online</option>
              <option value="offline">Đang offline</option>
            </select>
          </label>

          <button
            type="button"
            className="camera-refresh-button"
            onClick={handleRefresh}
          >
            <Icon name="refresh" size={17} />
            <span>Làm mới</span>
          </button>
        </div>

        <div className="camera-table-wrap">
          <CustomScrollBar style={{ width: "100%", height: "500px" }}>
            <table className="camera-table">
              <thead>
                <tr>
                  <th>Camera</th>
                  <th>Phòng</th>
                  <th>Địa chỉ IP</th>
                  <th>RTSP Port</th>
                  <th>Trạng thái</th>
                  <th>Cấu hình</th>
                  <th>Thao tác</th>
                </tr>
              </thead>

              <tbody>
                {error ? (
                  <tr>
                    <td colSpan="7" className="camera-table-empty">
                      <div className="camera-error-state">
                        <Icon name="alertCircle" size={22} />
                        <p>{error}</p>
                        <button type="button" onClick={handleRefresh}>
                          Thử lại
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : filteredCameras.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="camera-table-empty">
                      Không tìm thấy camera phù hợp.
                    </td>
                  </tr>
                ) : (
                  filteredCameras.map((camera) => (
                    <tr key={camera.camera_id || camera.id}>
                      <td>
                        <div className="camera-cell">
                          <div className="camera-table-icon">
                            <Icon name="camera" size={18} />
                          </div>
                          <div>
                            <strong>{camera.name || "Chưa đặt tên"}</strong>
                            <span>{camera.camera_id || "--"}</span>
                          </div>
                        </div>
                      </td>

                      <td>
                        <span className="camera-room">
                          {camera.classroom_name || camera.room_id || "--"}
                        </span>
                      </td>

                      <td>
                        <span className="camera-ip">
                          {camera.ip_address || "--"}
                        </span>
                      </td>

                      <td>
                        <span className="camera-port">
                          {camera.rtsp_port || "--"}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`camera-status-badge ${
                            camera.status === "online" ? "online" : "offline"
                          }`}
                        >
                          <i />
                          {camera.status === "online" ? "Đang online" : "Đang offline"}
                        </span>
                      </td>

                      <td>
                        <span
                          className={`camera-config-badge ${
                            camera.is_configured ? "configured" : "not-configured"
                          }`}
                        >
                          <i />
                          {camera.is_configured ? "Đã cấu hình" : "Chưa cấu hình"}
                        </span>
                      </td>

                      <td>
                        <div className="camera-row-actions">
                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => setViewingCamera(camera)}
                            disabled={camera.status !== "online"}
                            style={{
                              backgroundColor: camera.status === "online" ? "#2864ea" : "#f3f5f8",
                              color: camera.status === "online" ? "#ffffff" : "#aeb8c7",
                              borderColor: camera.status === "online" ? "#2864ea" : "#dfe5ee",
                            }}
                          >
                            Xem trực tiếp
                          </button>

                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => handleConfigureCamera(camera)}
                            disabled={
                              camera.is_configured ||
                              configuringCameraId === camera.camera_id ||
                              deletingCameraId === camera.camera_id
                            }
                          >
                            {configuringCameraId === camera.camera_id
                              ? "Đang cấu hình..."
                              : "Cấu hình"}
                          </button>

                          <button
                            type="button"
                            className="delete-camera-button"
                            onClick={() => handleDeleteCamera(camera)}
                            disabled={
                              deletingCameraId === camera.camera_id ||
                              configuringCameraId === camera.camera_id
                            }
                          >
                            {deletingCameraId === camera.camera_id ? "Đang xóa..." : "Xóa"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </CustomScrollBar>
        </div>
      </section>

      {/* Modal Xem trực tiếp động từ Database */}
      {viewingCamera && (
        <div className="camera-modal-overlay">
          <div className="camera-modal" style={{ width: "min(850px, 100%)" }}>
            <div className="camera-modal-header">
              <div>
                <h2>Luồng trực tiếp: {viewingCamera.name || viewingCamera.camera_id}</h2>
                <p>Phòng: {viewingCamera.classroom_name || viewingCamera.room_id || "N/A"}</p>
              </div>

              <button
                type="button"
                className="camera-modal-close"
                onClick={() => setViewingCamera(null)}
              >
                ✕
              </button>
            </div>

            <div style={{ padding: "0 24px 20px" }}>
              <div
                style={{
                  backgroundColor: "#000000",
                  borderRadius: "10px",
                  overflow: "hidden",
                  aspectRatio: "16/9",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  boxShadow: "inset 0 0 10px rgba(0,0,0,0.5)"
                }}
              >
                <iframe
                  src={`http://localhost:8889/${getStreamPath(viewingCamera)}`}
                  title="Camera Live Stream WebRTC"
                  style={{
                    width: "100%",
                    height: "100%",
                    border: "none"
                  }}
                  allow="autoplay; fullscreen; encrypted-media"
                />
              </div>

              <div style={{ marginTop: "12px", fontSize: "11px", color: "#61728c" }}>
                <strong>RTSP URL từ Database:</strong> <code>{viewingCamera.rtsp_url}</code>
              </div>
            </div>

            <div className="camera-modal-actions" style={{ padding: "0 24px 20px", margin: 0, border: "none" }}>
              <button
                type="button"
                className="camera-cancel-button"
                onClick={() => setViewingCamera(null)}
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {showAddCamera && (
        <AddCameraForm
          onClose={() => setShowAddCamera(false)}
          onSubmit={async (cameraData) => {
            try {
              setError("");
              await createCamera(cameraData);
              setShowAddCamera(false);
              await loadCameras();
            } catch (error) {
              console.error("Create camera error:", error);
              setError(error.message || "Không thể thêm camera.");
            }
          }}
        />
      )}

      {confirmModal.open && (
        <ConfirmModal
          title={confirmModal.title}
          message={confirmModal.message}
          confirmText={confirmModal.confirmText}
          cancelText={confirmModal.cancelText}
          loading={deletingCameraId !== null}
          onConfirm={confirmModal.onConfirm}
          onCancel={() =>
            setConfirmModal({ open: false, title: "", message: "", onConfirm: null })
          }
        />
      )}
    </div>
  );
};

export default CameraManagementPanel;