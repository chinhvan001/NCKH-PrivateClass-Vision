import { useEffect, useState } from "react";
import Icon from "../../common/Icon";
import { getCameraSnapshot } from "../../../services/CameraService";

// Xem ảnh camera để test (chỉ có khi backend bật CAMERA_SNAPSHOT=1): mỗi lần chụp lấy 1 khung hình mới qua
// API. Ảnh chỉ nằm trong bộ nhớ trình duyệt (object URL, thu hồi khi chụp lại hoặc đóng), không lưu ở đâu.
const CameraSnapshotModal = ({ camera, onClose }) => {
  const [url, setUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [shot, setShot] = useState(0); // tăng để chụp lại

  useEffect(() => {
    let open = true;

    getCameraSnapshot(camera.camera_id)
      .then((next) => (open ? setUrl(next) : URL.revokeObjectURL(next)))
      .catch((snapshotError) => open && setError(snapshotError.message))
      .finally(() => open && setLoading(false));

    return () => {
      open = false;
    };
  }, [camera.camera_id, shot]);

  useEffect(() => () => url && URL.revokeObjectURL(url), [url]);

  const retake = () => {
    setLoading(true);
    setError("");
    setShot((value) => value + 1);
  };

  return (
    <div className="camera-modal-overlay">
      <div
        className="camera-modal camera-snapshot-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="camera-snapshot-title"
      >
        <div className="camera-modal-header">
          <div>
            <h2 id="camera-snapshot-title">Hình ảnh camera</h2>

            <p>
              {camera.name} · {camera.room_name}. Chỉ để kiểm tra: ảnh không được lưu.
            </p>
          </div>

          <button type="button" className="camera-modal-close" onClick={onClose} aria-label="Đóng">
            <Icon name="close" size={19} />
          </button>
        </div>

        <div className="camera-snapshot-body">
          {error ? (
            <p className="camera-form-error">{error}</p>
          ) : (
            url && <img src={url} alt={`Hình từ ${camera.camera_name}`} />
          )}

          {loading && <p className="camera-snapshot-loading">Đang lấy hình từ camera...</p>}

          <div className="camera-modal-actions">
            <button type="button" className="camera-cancel-button" onClick={onClose}>
              Đóng
            </button>

            <button type="button" className="camera-save-button" onClick={retake} disabled={loading}>
              <Icon name="refresh" size={16} />

              <span>{loading ? "Đang chụp..." : "Chụp lại"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraSnapshotModal;
