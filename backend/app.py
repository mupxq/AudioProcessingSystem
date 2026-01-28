"""
Fun-ASR 语音识别批量处理系统 - 后端主应用
"""
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.asr_engine import get_asr_engine, get_device_status
from backend.audio_processor import AudioProcessor
from backend.result_exporter import ResultExporter
from backend.utils.config import FLASK_CONFIG, OUTPUT_DIR

# 创建 Flask 应用
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # 允许跨域请求

# 全局变量存储处理状态
processing_state = {
    "is_processing": False,
    "current_index": 0,
    "total": 0,
    "results": [],
    "current_file": "",
    "device": "cpu",  # 当前使用的设备
    "speaker_diarization": False,  # 是否启用说话人分离
}


@app.route('/')
def index():
    """返回前端页面"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/api/scan-folder', methods=['POST'])
def scan_folder():
    """
    扫描文件夹，获取音频文件列表

    请求体:
    {
        "folder_path": "/path/to/audio/folder"
    }

    返回:
    {
        "success": true,
        "files": [...],
        "count": 10
    }
    """
    try:
        data = request.get_json()
        folder_path = data.get('folder_path', '').strip()

        if not folder_path:
            return jsonify({
                "success": False,
                "error": "请提供文件夹路径"
            }), 400

        # 扫描文件夹
        files = AudioProcessor.scan_folder(folder_path)

        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        })

    except FileNotFoundError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 404
    except PermissionError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 403
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"扫描文件夹失败: {str(e)}"
        }), 500


@app.route('/api/start-recognition', methods=['POST'])
def start_recognition():
    """
    开始批量识别

    请求体:
    {
        "files": [
            {"path": "/path/to/audio1.wav", ...},
            {"path": "/path/to/audio2.wav", ...}
        ],
        "device": "cpu",  // 可选，"cpu" 或 "cuda"，默认 "cpu"
        "speaker_diarization": false  // 可选，是否启用说话人分离，默认 false
    }

    返回:
    {
        "success": true,
        "message": "开始批量识别"
    }
    """
    global processing_state

    try:
        data = request.get_json()
        files = data.get('files', [])
        device = data.get('device', 'cpu')  # 默认使用 CPU
        speaker_diarization = data.get('speaker_diarization', False)  # 默认不启用说话人分离

        if not files:
            return jsonify({
                "success": False,
                "error": "没有提供音频文件"
            }), 400

        if processing_state["is_processing"]:
            return jsonify({
                "success": False,
                "error": "已有任务在处理中"
            }), 400

        # 重置处理状态
        processing_state.update({
            "is_processing": True,
            "current_index": 0,
            "total": len(files),
            "results": [],
            "current_file": "",
            "device": device,
            "speaker_diarization": speaker_diarization,
        })

        # 获取音频文件路径列表
        audio_paths = [f["path"] for f in files]

        # 在后台线程中处理
        def process_batch():
            global processing_state
            asr_engine = get_asr_engine(device=device, enable_speaker_diarization=speaker_diarization)

            for i, audio_path in enumerate(audio_paths):
                if not processing_state["is_processing"]:
                    # 被中断
                    break

                processing_state["current_index"] = i
                processing_state["current_file"] = os.path.basename(audio_path)

                # 识别单个文件
                result = asr_engine.transcribe(audio_path)
                processing_state["results"].append(result)

                # 更新文件状态
                for f in files:
                    if f["path"] == audio_path:
                        f["status"] = "completed" if result["success"] else "failed"
                        f["result"] = result
                        break

            # 处理完成
            processing_state["is_processing"] = False
            processing_state["current_index"] = len(audio_paths)

        # 启动后台线程
        import threading
        thread = threading.Thread(target=process_batch)
        thread.daemon = True
        thread.start()

        speaker_info = " + 说话人分离" if speaker_diarization else ""
        return jsonify({
            "success": True,
            "message": f"开始识别 {len(files)} 个音频文件 (使用 {device.upper()}{speaker_info})"
        })

    except Exception as e:
        processing_state["is_processing"] = False
        return jsonify({
            "success": False,
            "error": f"启动识别失败: {str(e)}"
        }), 500


@app.route('/api/progress', methods=['GET'])
def get_progress():
    """
    获取识别进度

    返回:
    {
        "is_processing": true,
        "current_index": 5,
        "total": 10,
        "current_file": "audio5.wav",
        "results": [...]
    }
    """
    return jsonify(processing_state)


@app.route('/api/export-results', methods=['POST'])
def export_results():
    """
    导出识别结果到 Markdown 文件

    请求体:
    {
        "results": [...],
        "output_dir": "/custom/output/path"  // 可选
    }

    返回:
    {
        "success": true,
        "exported_count": 10,
        "summary_path": "/path/to/summary.md"
    }
    """
    try:
        data = request.get_json()
        results = data.get('results', [])
        output_dir = data.get('output_dir', OUTPUT_DIR)

        if not results:
            return jsonify({
                "success": False,
                "error": "没有可导出的结果"
            }), 400

        # 批量导出
        exporter = ResultExporter()
        output_paths = exporter.export_batch(results, output_dir)

        # 创建汇总文件
        summary_path = exporter.create_summary(results, output_dir)

        return jsonify({
            "success": True,
            "exported_count": len(output_paths),
            "summary_path": summary_path,
            "output_dir": output_dir
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"导出失败: {str(e)}"
        }), 500


@app.route('/api/model-status', methods=['GET'])
def model_status():
    """
    检查模型状态

    返回:
    {
        "loaded": true,
        "model_name": "paraformer-zh"
    }
    """
    try:
        asr_engine = get_asr_engine()
        return jsonify({
            "loaded": asr_engine.is_loaded,
            "model_name": "paraformer-zh",
            "device": asr_engine._device
        })
    except Exception as e:
        return jsonify({
            "loaded": False,
            "error": str(e)
        }), 500


@app.route('/api/device-status', methods=['GET'])
def device_status():
    """
    获取设备状态

    返回:
    {
        "cuda_available": false,
        "current_device": "cpu"
    }
    """
    try:
        status = get_device_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            "cuda_available": False,
            "current_device": "cpu",
            "error": str(e)
        }), 500


@app.route('/api/stop-recognition', methods=['POST'])
def stop_recognition():
    """
    停止当前的识别任务

    返回:
    {
        "success": true,
        "message": "识别任务已停止"
    }
    """
    global processing_state

    processing_state["is_processing"] = False

    return jsonify({
        "success": True,
        "message": "识别任务已停止"
    })


def main():
    """启动服务器"""
    print("=" * 50)
    print("Fun-ASR 语音识别批量处理系统")
    print("=" * 50)
    print(f"服务器地址: http://{FLASK_CONFIG['host']}:{FLASK_CONFIG['port']}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 50)

    # 预加载模型
    try:
        print("\n正在预加载模型...")
        get_asr_engine()
        print("模型加载完成！\n")
    except Exception as e:
        print(f"警告: 模型加载失败 - {e}")
        print("请确保已安装 funasr: pip install funasr\n")

    # 启动 Flask 服务器
    app.run(
        host=FLASK_CONFIG['host'],
        port=FLASK_CONFIG['port'],
        debug=FLASK_CONFIG['debug'],
        threaded=FLASK_CONFIG['threaded']
    )


if __name__ == '__main__':
    main()
