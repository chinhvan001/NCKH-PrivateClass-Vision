import { useState } from "react";
import Icon from "../../common/Icon";
import { testCameraConnection } from "../../../services/cameraService";

const AddCameraForm = ({
    onClose,
    onSubmit,
}) => {
    const [checkingConnection, setCheckingConnection] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState("idle");
    const [connectionMessage, setConnectionMessage] = useState("");

    const getFormData = (form) => {
        const formData = new FormData(form);

        return {
            room_id: formData.get("room_id").trim(),
            camera_name: formData.get("camera_name").trim(),
            ip_address: formData.get("ip_address").trim(),
            rtsp_port: formData.get("rtsp_port").trim(),
            rtsp_url: formData.get("rtsp_url").trim(),
        };
    };

    const handleTestConnection = async (event) => {
        event.preventDefault();

        const cameraData = getFormData(event.currentTarget.form);

        if (!cameraData.rtsp_url) {
            setConnectionStatus("error");
            setConnectionMessage("Vui lòng nhập RTSP URL.");
            return;
        }

        try {
            setCheckingConnection(true);
            setConnectionStatus("idle");
            setConnectionMessage("");

            const result = await testCameraConnection(
                cameraData.rtsp_url
            );

            if (result.connected) {
                setConnectionStatus("success");
                setConnectionMessage(
                    "Kết nối camera thành công."
                );
            } else {
                setConnectionStatus("error");
                setConnectionMessage(
                    "Không thể kết nối tới camera."
                );
            }
        } catch (error) {
            console.error(
                "Test camera connection error:",
                error
            );

            setConnectionStatus("error");
            setConnectionMessage(
                error.message ||
                "Không thể kiểm tra kết nối camera."
            );
        } finally {
            setCheckingConnection(false);
        }
    };

    const handleSubmit = (event) => {
        event.preventDefault();

        if (connectionStatus !== "success") {
            setConnectionStatus("error");
            setConnectionMessage(
                "Vui lòng kiểm tra kết nối camera trước khi thêm."
            );
            return;
        }

        const cameraData = getFormData(event.currentTarget);

        onSubmit(cameraData);
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
                            Thêm camera
                        </h2>

                        <p>
                            Nhập thông tin camera để kết nối với phòng học.
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
                            <label htmlFor="room_id">
                                Mã phòng
                                <span>*</span>
                            </label>

                            <input
                                id="room_id"
                                name="room_id"
                                type="text"
                                placeholder="Ví dụ: p201a"
                                required
                            />

                            <small>
                                Mã document của phòng trong classrooms.
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
                                placeholder="Ví dụ: Camera 201"
                                required
                            />
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
                                placeholder="Ví dụ: 554"
                                required
                            />
                        </div>

                        <div className="camera-form-field camera-form-field-full">
                            <label htmlFor="rtsp_url">
                                RTSP URL
                                <span>*</span>
                            </label>

                            <input
                                id="rtsp_url"
                                name="rtsp_url"
                                type="text"
                                placeholder="Ví dụ: rtsp://192.168.1.103:554/stream"
                                required
                            />

                            <small>
                                Địa chỉ luồng RTSP dùng để kết nối camera.
                            </small>
                        </div>
                    </div>

                    <div className="camera-form-note">
                        <Icon
                            name="alertCircle"
                            size={17}
                        />

                        <p>
                            Camera cần được kiểm tra kết nối trước khi hoàn tất cấu hình.
                        </p>
                    </div>

                    {connectionStatus === "success" && (
                        <div className="camera-connection-status camera-connection-success">
                            <Icon
                                name="check"
                                size={17}
                            />

                            <span>
                                {connectionMessage}
                            </span>
                        </div>
                    )}

                    {connectionStatus === "error" && (
                        <div className="camera-connection-status camera-connection-error">
                            <Icon
                                name="alertCircle"
                                size={17}
                            />

                            <span>
                                {connectionMessage}
                            </span>
                        </div>
                    )}

                    <div className="camera-modal-actions">
                        <button
                            type="button"
                            className="camera-cancel-button"
                            onClick={onClose}
                        >
                            Hủy
                        </button>

                        <button
                            type="button"
                            className="camera-test-button"
                            onClick={handleTestConnection}
                            disabled={checkingConnection}
                        >
                            <Icon
                                name="refresh"
                                size={16}
                            />

                            <span>
                                {checkingConnection
                                    ? "Đang kiểm tra..."
                                    : "Kiểm tra kết nối"}
                            </span>
                        </button>

                        <button
                            type="submit"
                            className="camera-save-button"
                            disabled={
                                connectionStatus !== "success"
                            }
                        >
                            <Icon
                                name="plus"
                                size={16}
                            />

                            <span>
                                Thêm camera
                            </span>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default AddCameraForm;