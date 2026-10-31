import { useEffect, useState } from "react";
import Icon from "../../common/Icon";
import { getAuthHeaders } from "../../../utils/AuthSession";

// Đường dẫn luồng chính theo hãng (camera-ai/docs/edge_node.md). Hãng khác: xem tài liệu camera
// hoặc ONVIF Device Manager.
const STREAM_PATHS = {
    hikvision: "/Streaming/Channels/101",
    dahua: "/cam/realmonitor?channel=1&subtype=0",
    tapo: "/stream1",
    other: "",
};

async function getList(url, key) {
    const response = await fetch(url, { headers: await getAuthHeaders() });
    const result = await response.json().catch(() => ({}));
    return response.ok ? result[key] || [] : [];
}

// camera: sửa camera đã thêm (tên camera và phòng giữ nguyên; đường dẫn, tài khoản để trống thì giữ như
// cũ); không có: thêm camera mới
const AddCameraForm = ({
    camera = null,
    edgeNames = [],
    defaultCameraName = "",
    onClose,
    onSubmit,
}) => {
    const [rooms, setRooms] = useState([]);
    const [classes, setClasses] = useState([]);
    const [classId, setClassId] = useState(camera?.class_id || "");
    const [error, setError] = useState("");
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        getList("/api/admin/classrooms", "classrooms").then(setRooms);
        getList("/api/admin/classes", "data").then(setClasses);
    }, []);

    const handleSubmit = async (event) => {
        event.preventDefault();

        const formData = new FormData(event.currentTarget);
        const text = (name) => String(formData.get(name) || "").trim();

        setSaving(true);
        setError("");

        try {
            await onSubmit({
                room_name: text("room_name"),
                camera_name: text("camera_name"),
                class_id: text("class_id"),
                ip_address: text("ip_address"),
                rtsp_port: text("rtsp_port"),
                stream_path: text("stream_path"),
                username: text("username"),
                password: String(formData.get("password") || ""), // giữ nguyên mật khẩu, không cắt khoảng trắng
            });
        } catch (submitError) {
            setError(submitError.message || (camera ? "Không thể lưu camera." : "Không thể thêm camera."));
            setSaving(false);
        }
    };

    return (
        <div className="camera-modal-overlay">
            <div
                className="camera-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="add-camera-title"
            >
                <div className="camera-modal-header">
                    <div>
                        <h2 id="add-camera-title">
                            {camera ? "Chỉnh sửa camera" : "Thêm camera"}
                        </h2>

                        <p>
                            {camera
                                ? `${camera.name} · ${camera.room_name}`
                                : "Camera AI nhận lớp và luồng camera từ đây, không cần cấu hình trên máy."}
                        </p>
                    </div>

                    <button
                        type="button"
                        className="camera-modal-close"
                        onClick={onClose}
                        aria-label="Đóng"
                    >
                        <Icon
                            name="close"
                            size={19}
                        />
                    </button>
                </div>

                <form
                    className="camera-form"
                    onSubmit={handleSubmit}
                >
                    <div className="camera-form-grid">
                        <div className="camera-form-field">
                            <label htmlFor="room_name">
                                Phòng học
                                <span>*</span>
                            </label>

                            <input
                                id="room_name"
                                name="room_name"
                                type="text"
                                list="camera-room-options"
                                defaultValue={camera?.room_name}
                                readOnly={Boolean(camera)}
                                placeholder="Ví dụ: P201"
                                required
                            />

                            <datalist id="camera-room-options">
                                {rooms
                                    .filter((room) => !room.camera_name)
                                    .map((room) => (
                                        <option key={room.id} value={room.classroom_name} />
                                    ))}
                            </datalist>

                            <small>
                                {camera
                                    ? "Muốn đổi phòng hoặc tên camera thì xóa camera rồi thêm lại."
                                    : "Chọn phòng có sẵn hoặc nhập tên phòng mới."}
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="camera_name">
                                Tên camera
                                <span>*</span>
                            </label>

                            <input
                                id="camera_name"
                                name="camera_name"
                                type="text"
                                list="camera-edge-options"
                                defaultValue={camera?.camera_name ?? defaultCameraName}
                                readOnly={Boolean(camera)}
                                placeholder="Ví dụ: Camera 201"
                                required
                            />

                            <datalist id="camera-edge-options">
                                {edgeNames.map((name) => (
                                    <option key={name} value={name} />
                                ))}
                            </datalist>

                            <small>
                                Trùng camera_id trong cấu hình của camera AI.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="class_id">
                                Lớp theo dõi
                                <span>*</span>
                            </label>

                            <select
                                id="class_id"
                                name="class_id"
                                value={classId}
                                onChange={(event) => setClassId(event.target.value)}
                                required
                            >
                                <option value="" disabled>
                                    Chọn lớp
                                </option>

                                {classes.map((item) => (
                                    <option key={item.id} value={item.id}>
                                        {item.class_name || item.id}
                                    </option>
                                ))}
                            </select>

                            <small>
                                Camera AI giám sát các tiết của lớp này.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="camera_brand">
                                Hãng camera
                            </label>

                            <select
                                id="camera_brand"
                                defaultValue={camera ? "" : "hikvision"}
                                onChange={(event) => {
                                    event.currentTarget.form.elements.stream_path.value =
                                        STREAM_PATHS[event.currentTarget.value] || "";
                                }}
                            >
                                {camera && <option value="">Giữ đường dẫn hiện tại</option>}
                                <option value="hikvision">Hikvision, HiLook</option>
                                <option value="dahua">Dahua, KBVision, Imou</option>
                                <option value="tapo">TP-Link Tapo</option>
                                <option value="other">Hãng khác</option>
                            </select>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="ip_address">
                                Địa chỉ IP
                                <span>*</span>
                            </label>

                            <input
                                id="ip_address"
                                name="ip_address"
                                type="text"
                                defaultValue={camera?.ip_address}
                                placeholder="Ví dụ: 192.168.1.103"
                                required
                            />
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="rtsp_port">
                                RTSP Port
                                <span>*</span>
                            </label>

                            <input
                                id="rtsp_port"
                                name="rtsp_port"
                                type="text"
                                inputMode="numeric"
                                defaultValue={camera?.rtsp_port || "554"}
                                required
                            />
                        </div>

                        <div className="camera-form-field camera-form-field-full">
                            <label htmlFor="stream_path">
                                Đường dẫn luồng
                            </label>

                            <input
                                id="stream_path"
                                name="stream_path"
                                type="text"
                                defaultValue={camera ? "" : STREAM_PATHS.hikvision}
                                placeholder={camera ? "Để trống: giữ đường dẫn hiện tại" : undefined}
                            />

                            <small>
                                Tự điền theo hãng. Hãng khác: xem tài liệu camera hoặc ONVIF Device Manager.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="username">
                                Tài khoản camera
                            </label>

                            <input
                                id="username"
                                name="username"
                                type="text"
                                autoComplete="off"
                                placeholder={camera ? "Để trống: giữ như cũ" : "Ví dụ: admin"}
                            />

                            <small>
                                Tapo: tài khoản camera tạo trong app Tapo.
                            </small>
                        </div>

                        <div className="camera-form-field">
                            <label htmlFor="password">
                                Mật khẩu camera
                            </label>

                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete="new-password"
                                placeholder={camera ? "Để trống: giữ như cũ" : undefined}
                            />
                        </div>
                    </div>

                    <div className="camera-form-note">
                        <Icon
                            name="alertCircle"
                            size={17}
                        />

                        <p>
                            {camera
                                ? "Web không hiển thị lại tài khoản và mật khẩu. Để trống cả hai thì giữ như cũ, nhập một trong hai thì thay cả hai."
                                : "Chỉ camera AI đọc được tài khoản và mật khẩu: web không hiển thị lại, giáo viên và phụ huynh không đọc được. Muốn đổi thì nhấn chuột phải vào camera, chọn Chỉnh sửa thông tin."}
                        </p>
                    </div>

                    {error && <p className="camera-form-error">{error}</p>}

                    <div className="camera-modal-actions">
                        <button
                            type="button"
                            className="camera-cancel-button"
                            onClick={onClose}
                        >
                            Hủy
                        </button>

                        <button
                            type="submit"
                            className="camera-save-button"
                            disabled={saving}
                        >
                            <Icon
                                name={camera ? "checkCircle" : "plus"}
                                size={16}
                            />

                            <span>
                                {saving ? "Đang lưu..." : camera ? "Lưu thay đổi" : "Thêm camera"}
                            </span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddCameraForm;
