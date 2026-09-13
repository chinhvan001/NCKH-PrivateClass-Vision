const API_BASE_URL = "http://127.0.0.1:5000";

export const getCameras = async () => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras`,
        {
            method: "GET",
            headers: {
                Authorization: `Bearer ${idToken}`,
            },
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể lấy danh sách camera."
        );
    }

    return data.cameras || [];
};

export const testCameraConnection = async (rtspUrl) => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/test-connection`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${idToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                rtsp_url: rtspUrl,
            }),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể kiểm tra kết nối camera."
        );
    }

    return data;
};

export const createCamera = async (cameraData) => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${idToken}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(cameraData),
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể thêm camera."
        );
    }

    return data;
};

export const configureCamera = async (cameraId) => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${cameraId}/configure`,
        {
            method: "PUT",
            headers: {
                Authorization: `Bearer ${idToken}`,
            },
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể cấu hình camera."
        );
    }

    return data;
};

export const deleteCamera = async (cameraId) => {
    const idToken = localStorage.getItem("idToken");

    if (!idToken) {
        throw new Error("Không tìm thấy ID Token.");
    }

    const response = await fetch(
        `${API_BASE_URL}/api/admin/cameras/${cameraId}`,
        {
            method: "DELETE",
            headers: {
                Authorization: `Bearer ${idToken}`,
            },
        }
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
        throw new Error(
            data.message ||
            "Không thể xóa camera."
        );
    }

    return data;
};