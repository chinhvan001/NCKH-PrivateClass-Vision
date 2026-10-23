import { useEffect, useMemo, useState } from "react";
import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";
import CustomScrollBar from "../../common/CustomScrollbar";

import {
  getCameras,
  createCamera,
  deleteCamera,
} from "../../../services/CameraService";

import AddCameraForm from "./AddCameraForm";

// Trạng thái trong heartbeat của camera AI (edge_nodes/{camera_id})
const EDGE_STATUS = {
  idle: "Sẵn sàng",
  monitoring: "Đang giám sát",
  paused: "Tạm dừng",
  unavailable: "Tạm thời không khả dụng",
  outside_schedule: "Ngoài khung giờ giám sát",
};

const edgeLabel = (edge) => {
  if (!edge) return "Chưa có tín hiệu";
  if (!edge.online) return "Offline";
  return EDGE_STATUS[edge.status] || edge.status;
};

const CameraManagementPanel = () => {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [roomFilter, setRoomFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const [showAddCamera, setShowAddCamera] = useState(false);

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

  useEffect(() => {
    loadCameras();
  }, []);

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

  const onlineCameras = cameras.filter(
    (camera) => camera.status === "online",
  ).length;

  const offlineCameras = cameras.filter(
    (camera) => camera.status !== "online",
  ).length;

  const camerasWithoutEdge = cameras.filter(
    (camera) => !camera.edge,
  ).length;

  const filteredCameras = useMemo(() => {
    const keyword = search.trim().toLowerCase();

    return cameras.filter((camera) => {
      const matchSearch =
        !keyword ||
        (camera.name || "").toLowerCase().includes(keyword) ||
        (camera.camera_id || "").toLowerCase().includes(keyword) ||
        (camera.classroom_name || "").toLowerCase().includes(keyword) ||
        (camera.edge?.class_name || "").toLowerCase().includes(keyword) ||
        (camera.ip_address || "").toLowerCase().includes(keyword);

      const matchRoom = roomFilter === "all" || camera.room_id === roomFilter;

      const matchStatus =
        statusFilter === "all" || camera.status === statusFilter;

      return matchSearch && matchRoom && matchStatus;
    });
  }, [cameras, search, roomFilter, statusFilter]);

  const handleRefresh = () => {
    loadCameras();
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

          setConfirmModal({
            open: false,
            title: "",
            message: "",
            confirmText: "Xác nhận",
            cancelText: "Hủy",
            onConfirm: null,
          });
        } catch (error) {
          console.error("Delete camera error:", error);

          setError(error.message || "Không thể xóa camera.");

          setConfirmModal({
            open: false,
            title: "",
            message: "",
            confirmText: "Xác nhận",
            cancelText: "Hủy",
            onConfirm: null,
          });
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
              <span>Chưa có camera AI</span>

              <strong>{camerasWithoutEdge}</strong>

              <small>Chưa gửi tín hiệu</small>
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
                <th>Camera AI</th>
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
                  <tr key={camera.id}>
                    <td>
                      <div className="camera-cell">
                        <div className="camera-table-icon">
                          <Icon name="camera" size={18} />
                        </div>

                        <div>
                          <strong>{camera.name || "Chưa đặt tên"}</strong>

                          <span>{camera.room_id || "Chưa khai báo phòng"}</span>
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

                        {camera.status === "online"
                          ? "Đang online"
                          : "Đang offline"}
                      </span>
                    </td>

                    <td>
                      <span
                        className={`camera-config-badge ${
                          camera.edge?.online ? "configured" : "not-configured"
                        }`}
                        title={
                          camera.edge?.updated_at
                            ? `Tín hiệu lúc ${new Date(camera.edge.updated_at).toLocaleString("vi-VN")}`
                            : undefined
                        }
                      >
                        <i />

                        {edgeLabel(camera.edge)}
                        {camera.edge?.class_name ? ` · ${camera.edge.class_name}` : ""}
                      </span>
                    </td>

                    <td>
                      <div className="camera-row-actions">
                        {camera.room_id && (
                          <button
                            type="button"
                            className="delete-camera-button"
                            onClick={() => handleDeleteCamera(camera)}
                            disabled={deletingCameraId === camera.camera_id}
                          >
                            {deletingCameraId === camera.camera_id
                              ? "Đang xóa..."
                              : "Xóa"}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          </CustomScrollBar>
        </div>

        <div className="camera-pagination">
          <span>Hiển thị {filteredCameras.length} camera</span>

          <div>
            <button type="button" disabled>
              <Icon name="first" size={15} />
            </button>

            <button type="button" disabled>
              <Icon name="arrowLeft" size={15} />
            </button>

            <button type="button" className="current-page">
              1
            </button>

            <button type="button" disabled>
              <Icon name="arrowRight" size={15} />
            </button>

            <button type="button" disabled>
              <Icon name="last" size={15} />
            </button>
          </div>
        </div>
      </section>

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
            setConfirmModal({
              open: false,
              title: "",
              message: "",
              confirmText: "Xác nhận",
              cancelText: "Hủy",
              onConfirm: null,
            })
          }
        />
      )}
    </div>
  );
};

export default CameraManagementPanel;
