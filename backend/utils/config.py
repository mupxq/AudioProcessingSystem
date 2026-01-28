"""
配置文件
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 模型目录
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# 输出目录
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.wma', '.aac']

# Fun-ASR 模型配置
ASR_MODEL_CONFIG = {
    'model_name': 'paraformer-zh',  # 使用中文模型
    'vad_model': 'fsmn-vad',
    'punc_model': 'ct-punc',
}

# 批处理配置
BATCH_CONFIG = {
    'max_workers': 2,  # 最大并发数，根据CPU/GPU调整
    'chunk_size': 30,  # 音频分块时长（秒）
}

# Flask 配置
FLASK_CONFIG = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True,
    'threaded': True,
}

# 确保输出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)
