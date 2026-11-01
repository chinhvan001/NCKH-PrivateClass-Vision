from flask import Blueprint, jsonify, request
from services.stream_service import StreamAutomationService

ld_blueprint = Blueprint('ldplayer', __name__)

@ld_blueprint.route('/api/start-auto-flow', methods=['POST'])
def start_auto_flow():
    try:
        # Lấy dữ liệu an toàn, nếu không có JSON thì trả về dict rỗng
        data = request.get_json(silent=True) or {}
        stream_path = data.get('stream_path', 'camera-p201a')
        emulator_index = data.get('index', 0)

        # Gọi service tự động mở LDPlayer, MediaMTX và luồng
        result = StreamAutomationService.launch_all_system(index=emulator_index, stream_path=stream_path)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500