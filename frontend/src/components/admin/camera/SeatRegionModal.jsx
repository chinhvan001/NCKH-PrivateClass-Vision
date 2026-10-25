import { useEffect, useRef, useState } from "react";
import { ImagePlus, Trash2, X } from "lucide-react";

import { getAuthHeaders } from "../../../utils/AuthSession";

// Xác định chỗ ngồi: admin kéo chuột vẽ ô chữ nhật cho từng ghế trên ảnh chụp từ camera. Ảnh chỉ hiển thị
// trong trình duyệt (object URL), không gửi lên server; server lưu tọa độ ô vào seat_regions/{camera_id}
// và camera AI dùng chúng từ tiết bắt đầu sau đó. Trong component, ô lưu theo tỉ lệ 0-1 của ảnh.
const MIN_BOX = 0.01; // ô nhỏ hơn 1% ảnh: coi như bấm nhầm

async function api(url, options = {}) {
  const response = await fetch(url, { ...options, headers: await getAuthHeaders() });
  const result = await response.json().catch(() => ({}));
  return { ok: response.ok && result.success !== false, result };
}

// Như backend và camera AI: S01, S02... đánh số theo từng hàng
const seatIds = (rows, columns) =>
  Array.from({ length: rows * columns }, (_, index) => `S${String(index + 1).padStart(2, "0")}`);

const clamp = (value) => Math.min(Math.max(value, 0), 1);

const toBox = (a, b) => [Math.min(a[0], b[0]), Math.min(a[1], b[1]), Math.max(a[0], b[0]), Math.max(a[1], b[1])];

const boxStyle = ([x1, y1, x2, y2]) => ({
  left: `${x1 * 100}%`,
  top: `${y1 * 100}%`,
  width: `${(x2 - x1) * 100}%`,
  height: `${(y2 - y1) * 100}%`,
});

export default function SeatRegionModal({ camera, onClose }) {
  const cameraId = camera.camera_name;
  const defaultClassId = camera.edge?.class_id || "";
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [saved, setSaved] = useState(null);
  const [boxes, setBoxes] = useState({});
  const [current, setCurrent] = useState("");
  const [image, setImage] = useState(null); // { url, width, height }
  const [draft, setDraft] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const area = useRef(null);
  const start = useRef(null);

  useEffect(() => {
    Promise.all([api("/api/admin/classes"), api(`/api/admin/seat-regions/${encodeURIComponent(cameraId)}`)]).then(
      ([classResponse, regionResponse]) => {
        if (!classResponse.ok || !regionResponse.ok) {
          setError(classResponse.result.message || regionResponse.result.message || "Không tải được dữ liệu.");
          return;
        }
        const regions = regionResponse.result.seat_regions;
        setClasses(classResponse.result.data || []);
        setSaved(regions);
        if (!regions) {
          setClassId(defaultClassId);
          return;
        }
        const { image_width: width, image_height: height } = regions;
        setClassId(regions.class_id);
        setBoxes(
          Object.fromEntries(
            Object.entries(regions.seats).map(([seat, [x1, y1, x2, y2]]) => [
              seat,
              [x1 / width, y1 / height, x2 / width, y2 / height],
            ])
          )
        );
      }
    );
  }, [cameraId, defaultClassId]);

  useEffect(() => () => image && URL.revokeObjectURL(image.url), [image]);

  const selectedClass = classes.find((item) => item.id === classId);
  const seats = selectedClass ? seatIds(Number(selectedClass.row_count) || 0, Number(selectedClass.column_count) || 0) : [];
  const active = seats.includes(current) ? current : seats.find((seat) => !boxes[seat]) || seats[0];
  const drawn = seats.filter((seat) => boxes[seat]).length;
  const ratioChanged =
    image && saved && Math.abs(image.width / image.height - saved.image_width / saved.image_height) > 0.01;

  const changeClass = (value) => {
    setClassId(value);
    setBoxes({});
    setCurrent("");
  };

  const chooseImage = (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const url = URL.createObjectURL(file);
    const probe = new Image();
    probe.onload = () => setImage({ url, width: probe.naturalWidth, height: probe.naturalHeight });
    probe.onerror = () => {
      URL.revokeObjectURL(url);
      setError("Không đọc được ảnh này.");
    };
    probe.src = url;
  };

  const point = (event) => {
    const rect = area.current.getBoundingClientRect();
    return [clamp((event.clientX - rect.left) / rect.width), clamp((event.clientY - rect.top) / rect.height)];
  };

  const beginDraw = (event) => {
    if (!active || event.button !== 0) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    start.current = point(event);
    setDraft(toBox(start.current, start.current));
  };

  const moveDraw = (event) => {
    if (start.current) setDraft(toBox(start.current, point(event)));
  };

  const endDraw = (event) => {
    if (!start.current) return;
    const box = toBox(start.current, point(event));
    start.current = null;
    setDraft(null);
    if (box[2] - box[0] < MIN_BOX || box[3] - box[1] < MIN_BOX) return;
    const next = { ...boxes, [active]: box };
    setBoxes(next);
    setCurrent(seats.find((seat) => !next[seat]) || active); // sang ghế chưa vẽ tiếp theo
  };

  const removeBox = (seat) => {
    const next = { ...boxes };
    delete next[seat];
    setBoxes(next);
  };

  const save = async () => {
    const size = image ||
      (saved && { width: saved.image_width, height: saved.image_height }) || { width: 1, height: 1 };
    const pixels = Object.fromEntries(
      Object.entries(boxes).map(([seat, [x1, y1, x2, y2]]) => [
        seat,
        [x1 * size.width, y1 * size.height, x2 * size.width, y2 * size.height].map((v) => Math.round(v * 10) / 10),
      ])
    );
    setBusy(true);
    setError("");
    const { ok, result } = await api(`/api/admin/seat-regions/${encodeURIComponent(cameraId)}`, {
      method: "PUT",
      body: JSON.stringify({ class_id: classId, image_width: size.width, image_height: size.height, seats: pixels }),
    });
    setBusy(false);
    if (!ok) {
      setError(result.message || "Không lưu được.");
      return;
    }
    setSaved(result.seat_regions);
    setNotice(
      result.seat_regions
        ? `Đã lưu ${Object.keys(pixels).length} ô ghế. Camera AI dùng từ tiết bắt đầu sau.`
        : "Đã xóa các ô ghế: camera AI quay về vị trí ghế trong cấu hình của nó."
    );
  };

  return (
    <div className="session-modal-overlay">
      <div className="session-modal seat-region-modal">
        <div className="session-modal-header">
          <div>
            <h2>Xác định chỗ ngồi · {cameraId}</h2>
            <p>Kéo chuột trên ảnh để vẽ ô cho ghế đang chọn. Ô bao phần vai và thân trên của học sinh khi ngồi.</p>
          </div>
          <button type="button" onClick={onClose} className="session-modal-close" title="Đóng">
            <X size={18} />
          </button>
        </div>

        <div className="session-modal-content">
          {error && <div className="monitor-error">{error}</div>}
          {notice && <div className="seat-region-notice">{notice}</div>}

          <div className="seat-region-toolbar">
            <label>
              Lớp camera đang quay
              <select value={classId} onChange={(event) => changeClass(event.target.value)}>
                <option value="">Chọn lớp</option>
                {classes.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.class_name || item.id}
                  </option>
                ))}
              </select>
            </label>
            <label className="session-secondary-btn seat-region-file">
              <ImagePlus size={16} />
              Chọn ảnh chụp từ camera
              <input type="file" accept="image/*" hidden onChange={chooseImage} />
            </label>
          </div>
          <p className="monitor-muted">
            Chụp một ảnh từ camera khi lớp trống, đúng góc camera AI đang dùng (ví dụ VLC: mở luồng RTSP rồi Video →
            Take Snapshot). Ảnh chỉ hiển thị trên máy này, không tải lên máy chủ; máy chủ chỉ lưu tọa độ các ô.
          </p>

          {image ? (
            <div
              ref={area}
              className="seat-region-area"
              onPointerDown={beginDraw}
              onPointerMove={moveDraw}
              onPointerUp={endDraw}
              onPointerCancel={() => {
                start.current = null;
                setDraft(null);
              }}
            >
              <img src={image.url} alt="Ảnh chụp từ camera" draggable={false} />
              {seats
                .filter((seat) => boxes[seat])
                .map((seat) => (
                  <div key={seat} className={`seat-region-box${seat === active ? " active" : ""}`} style={boxStyle(boxes[seat])}>
                    <span
                      onPointerDown={(event) => {
                        event.stopPropagation();
                        setCurrent(seat);
                      }}
                    >
                      {seat}
                    </span>
                  </div>
                ))}
              {draft && <div className="seat-region-box draft" style={boxStyle(draft)} />}
            </div>
          ) : (
            <div className="seat-region-empty">
              {saved
                ? `Đã xác định ${Object.keys(saved.seats).length} ghế. Chọn ảnh chụp từ camera để xem hoặc sửa.`
                : "Chọn ảnh chụp từ camera để bắt đầu vẽ."}
            </div>
          )}
          {ratioChanged && (
            <div className="monitor-error">Ảnh này khác tỉ lệ khung hình với ảnh lúc vẽ trước, các ô có thể bị lệch.</div>
          )}

          {seats.length > 0 ? (
            <>
              <div className="seat-region-summary">
                <span>
                  Đã vẽ {drawn}/{seats.length} ghế · đang chọn <strong>{active}</strong>
                </span>
                <button type="button" className="session-secondary-btn" disabled={!boxes[active]} onClick={() => removeBox(active)}>
                  Xóa ô {active}
                </button>
                <button type="button" className="session-secondary-btn monitor-danger" disabled={!drawn} onClick={() => setBoxes({})}>
                  <Trash2 size={14} /> Xóa tất cả
                </button>
              </div>
              <div className="seat-region-seats">
                {seats.map((seat) => (
                  <button
                    key={seat}
                    type="button"
                    className={`${boxes[seat] ? "drawn" : ""}${seat === active ? " active" : ""}`}
                    onClick={() => setCurrent(seat)}
                  >
                    {seat}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <p className="monitor-muted">{classId ? "Lớp chưa có sơ đồ chỗ ngồi." : "Chọn lớp mà camera này quay."}</p>
          )}
          <p className="monitor-muted">
            Ghế không có ô sẽ không được theo dõi. Vẽ lại khi camera bị xoay hoặc dời chỗ.
          </p>
        </div>

        <div className="session-modal-footer">
          <button type="button" className="session-secondary-btn" onClick={onClose}>
            Đóng
          </button>
          <button
            type="button"
            className="session-primary-btn"
            disabled={busy || !classId || (drawn > 0 && !image && !saved)}
            onClick={save}
          >
            {busy ? "Đang lưu..." : "Lưu"}
          </button>
        </div>
      </div>
    </div>
  );
}
