import { useEffect, useMemo, useState } from "react";
import Icon from "../../common/Icon";
import ConfirmModal from "../../common/ConfirmModal";
import CustomScrollBar from "../../common/CustomScrollbar";

import {
  getCameras,
  createCamera,
  updateCamera,
  deleteCamera,
} from "../../../services/CameraService";

import AddCameraForm from "./AddCameraForm";
import CameraSnapshotModal from "./CameraSnapshotModal";
import SeatRegionModal from "./SeatRegionModal";

// Trạng thái trong heartbeat của camera AI (edge_nodes/{camera_id})
const EDGE_STATUS = {
  idle: "Sẵn sàng",
  monitoring: "Đang giám sát",
  paused: "Tạm dừng",
  unavailable: "Tạm thời không khả dụng",
  outside_schedule: "Ngoài khung giờ giám sát",
  unconfigured: "Chờ thêm camera trên web",
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

  const [addCameraName, setAddCameraName] = useState(null); // null: form đóng
  const [editCamera, setEditCamera] = useState(null);
  const [seatCamera, setSeatCamera] = useState(null);
  const [snapshotCamera, setSnapshotCamera] = useState(null);
  const [menu, setMenu] = useState(null); // menu chuột phải: { camera, x, y }

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

  // Đóng menu khi bấm ra ngoài, cuộn, Esc. contextmenu bắt ở pha capture: chuột phải sang dòng khác
  // thì đóng menu cũ trước, rồi dòng đó mở menu mới.
  useEffect(() => {
    if (!menu) return undefined;

    const close = (event) => {
      if (event.type !== "keydown" || event.key === "Escape") setMenu(null);
    };
    const events = [["click", false], ["contextmenu", true], ["scroll", true], ["resize", false], ["keydown", false]];

    events.forEach(([name, capture]) => window.addEventListener(name, close, capture));

    return () => events.forEach(([name, capture]) => window.removeEventListener(name, close, capture));
  }, [menu]);

  const rooms = useMemo(() => {
    const roomSet = new Set();

    cameras.forEach((camera) => {
      if (camera.room_name) {
        roomSet.add(camera.room_name);
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
        (camera.room_name || "").toLowerCase().includes(keyword) ||
        (camera.edge?.class_name || "").toLowerCase().includes(keyword) ||
        (camera.ip_address || "").toLowerCase().includes(keyword);

      const matchRoom = roomFilter === "all" || camera.room_name === roomFilter;

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
      message: `Bạn có chắc chắn muốn xóa camera "${camera.name}" khỏi phòng "${camera.room_name}"?`,
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
            onClick={() => setAddCameraName("")}
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
                <th>Lớp theo dõi</th>
                <th>Trạng thái</th>
                <th>Camera AI</th>
                <th>Thao tác</th>
              </tr>
            </thead>

            <tbody>
              {error ? (
                <tr>
                  <td colSpan="8" className="camera-table-empty">
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
                  <td colSpan="8" className="camera-table-empty">
                    Không tìm thấy camera phù hợp.
                  </td>
                </tr>
              ) : (
                filteredCameras.map((camera) => (
                  <tr
                    key={camera.id}
                    onContextMenu={(event) => {
                      event.preventDefault();
                      setMenu({ camera, x: event.clientX, y: event.clientY });
                    }}
                  >
                    <td>
                      <div className="camera-cell">
                        <div className="camera-table-icon">
                          <Icon name="camera" size={18} />
                        </div>

                        <div>
                          <strong>{camera.name || "Chưa đặt tên"}</strong>

                          <span>{camera.declared ? camera.camera_id : "Chưa thêm trên web"}</span>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span className="camera-room">
                        {camera.room_name || "--"}
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
                      <span className="camera-room">
                        {camera.configured ? camera.class_name || camera.class_id : "--"}
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
                        {!camera.declared && (
                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => setAddCameraName(camera.camera_name)}
                          >
                            Thêm
                          </button>
                        )}

                        {camera.declared && (
                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => setEditCamera(camera)}
                          >
                            Sửa
                          </button>
                        )}

                        {camera.snapshot && (
                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => setSnapshotCamera(camera)}
                          >
                            Xem hình
                          </button>
                        )}

                        {camera.camera_name && (
                          <button
                            type="button"
                            className="configure-camera-button"
                            onClick={() => setSeatCamera(camera)}
                          >
                            Xác định chỗ ngồi
                          </button>
                        )}

                        {camera.declared && (
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

      {addCameraName !== null && (
        <AddCameraForm
          edgeNames={cameras.filter((camera) => !camera.declared).map((camera) => camera.camera_name)}
          defaultCameraName={addCameraName}
          onClose={() => setAddCameraName(null)}
          onSubmit={async (cameraData) => {
            await createCamera(cameraData); // lỗi hiện trong form

            setAddCameraName(null);

            await loadCameras();
          }}
        />
      )}

      {editCamera && (
        <AddCameraForm
          camera={editCamera}
          onClose={() => setEditCamera(null)}
          onSubmit={async (cameraData) => {
            await updateCamera(editCamera.camera_id, cameraData); // lỗi hiện trong form

            setEditCamera(null);

            await loadCameras();
          }}
        />
      )}

      {seatCamera && (
        <SeatRegionModal camera={seatCamera} onClose={() => setSeatCamera(null)} />
      )}

      {snapshotCamera && (
        <CameraSnapshotModal camera={snapshotCamera} onClose={() => setSnapshotCamera(null)} />
      )}

      {menu && (
        <div
          className="camera-context-menu"
          role="menu"
          style={{
            left: Math.min(menu.x, window.innerWidth - 220),
            top: Math.min(menu.y, window.innerHeight - 190),
          }}
        >
          {menu.camera.declared ? (
            <button type="button" role="menuitem" onClick={() => setEditCamera(menu.camera)}>
              <Icon name="edit" size={16} />
              <span>Chỉnh sửa thông tin</span>
            </button>
          ) : (
            <button type="button" role="menuitem" onClick={() => setAddCameraName(menu.camera.camera_name)}>
              <Icon name="plus" size={16} />
              <span>Thêm camera</span>
            </button>
          )}

          {menu.camera.snapshot && (
            <button type="button" role="menuitem" onClick={() => setSnapshotCamera(menu.camera)}>
              <Icon name="eye" size={16} />
              <span>Xem hình camera</span>
            </button>
          )}

          {menu.camera.camera_name && (
            <button type="button" role="menuitem" onClick={() => setSeatCamera(menu.camera)}>
              <Icon name="seatGrid" size={16} />
              <span>Xác định chỗ ngồi</span>
            </button>
          )}

          {menu.camera.declared && (
            <button
              type="button"
              role="menuitem"
              className="danger"
              onClick={() => handleDeleteCamera(menu.camera)}
            >
              <Icon name="trash" size={16} />
              <span>Xóa camera</span>
            </button>
          )}
        </div>
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
