"""
ASR 引擎模块
封装 Fun-ASR 模型进行语音识别
"""
import os
import time
from typing import Optional, Dict, Any
from threading import Lock

try:
    from funasr import AutoModel
except ImportError:
    AutoModel = None
    print("警告: funasr 未安装，请运行: pip install funasr")


class ASREngine:
    """Fun-ASR 语音识别引擎"""

    _instance = None
    _lock = Lock()
    _model = None
    _device = "cpu"  # 默认使用 CPU

    def __new__(cls, device="cpu", enable_speaker_diarization=False):
        """
        单例模式，确保模型只加载一次

        Args:
            device: 设备类型，"cpu" 或 "cuda"
            enable_speaker_diarization: 是否启用说话人分离
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._device = device
                    cls._instance._enable_speaker_diarization = enable_speaker_diarization
        return cls._instance

    def __init__(self, device="cpu", enable_speaker_diarization=False):
        """
        初始化 ASR 引擎

        Args:
            device: 设备类型，"cpu" 或 "cuda"
            enable_speaker_diarization: 是否启用说话人分离
        """
        self._enable_speaker_diarization = enable_speaker_diarization
        # 如果设备改变了或模型未加载，重新加载模型
        if not hasattr(self, '_initialized') or self._device != device or getattr(self, '_speaker_enabled', False) != enable_speaker_diarization:
            self._device = device
            self._load_model()
            self._initialized = True
            self._speaker_enabled = enable_speaker_diarization

    @property
    def _current_device(self):
        """获取当前使用的设备"""
        return getattr(self, '__device', 'cpu')

    @_current_device.setter
    def _current_device(self, value):
        """设置当前使用的设备"""
        self.__device = value

    def _load_model(self):
        """加载 Fun-ASR 模型"""
        if AutoModel is None:
            raise RuntimeError("funasr 库未安装，请先安装: pip install funasr")

        speaker_info = " + 说话人分离" if self._enable_speaker_diarization else ""
        print(f"正在加载 Fun-ASR 模型 (设备: {self._device}{speaker_info})...")
        start_time = time.time()

        try:
            # 检测 CUDA 是否可用
            if self._device == "cuda":
                try:
                    import torch
                    if not torch.cuda.is_available():
                        print("警告: CUDA 不可用，切换到 CPU 模式")
                        self._device = "cpu"
                except ImportError:
                    print("警告: PyTorch 未安装 CUDA 支持，切换到 CPU 模式")
                    self._device = "cpu"

            # 加载模型（首次运行会自动下载）
            model_kwargs = {
                "model": "paraformer-zh",  # 中文语音识别
                "vad_model": "fsmn-vad",   # 语音活动检测
                "punc_model": "ct-punc",   # 标点恢复
            }

            # 添加说话人分离模型
            if self._enable_speaker_diarization:
                model_kwargs["spk_model"] = "cam++"

            # 只有在设备是 cuda 且可用时才添加 device 参数
            if self._device == "cuda":
                model_kwargs["device"] = "cuda"

            self._model = AutoModel(**model_kwargs)
            self._current_device = self._device

            load_time = time.time() - start_time
            print(f"模型加载完成 (使用 {self._device.upper()}{speaker_info}), 耗时: {load_time:.2f} 秒")

        except Exception as e:
            print(f"模型加载失败: {e}")
            raise

    def transcribe(
        self,
        audio_path: str,
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        识别单个音频文件

        Args:
            audio_path: 音频文件路径
            language: 语言类型（默认中文）

        Returns:
            包含识别结果的字典
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        if self._model is None:
            raise RuntimeError("模型未加载")

        start_time = time.time()

        try:
            # 调用模型进行识别
            result = self._model.generate(
                input=audio_path,
                batch_size_s=300,
            )

            process_time = time.time() - start_time

            # 解析结果
            if result and len(result) > 0:
                text = result[0].get("text", "")

                response = {
                    "success": True,
                    "text": text,
                    "audio_path": audio_path,
                    "process_time": round(process_time, 2),
                    "speaker_diarization_enabled": self._enable_speaker_diarization,
                }

                # 如果启用了说话人分离，添加说话人信息
                if self._enable_speaker_diarization:
                    sentence_info = result[0].get("sentence_info", [])

                    # 格式化说话人信息
                    speakers = []
                    for sentence in sentence_info:
                        speakers.append({
                            "speaker": str(sentence.get("spk", "unknown")),
                            "text": sentence.get("text", ""),
                            "start": sentence.get("start", 0),
                            "end": sentence.get("end", 0),
                        })

                    response["sentences"] = speakers

                    # 统计说话人
                    unique_speakers = set(str(s["speaker"]) for s in speakers)
                    response["speaker_count"] = len(unique_speakers)
                    response["speakers"] = list(unique_speakers)

                return response
            else:
                return {
                    "success": False,
                    "text": "",
                    "audio_path": audio_path,
                    "process_time": round(process_time, 2),
                    "error": "未识别到语音内容"
                }

        except Exception as e:
            return {
                "success": False,
                "text": "",
                "audio_path": audio_path,
                "process_time": round(time.time() - start_time, 2),
                "error": str(e)
            }

    def batch_transcribe(
        self,
        audio_paths: list,
        callback=None
    ) -> list:
        """
        批量识别音频文件

        Args:
            audio_paths: 音频文件路径列表
            callback: 进度回调函数 callback(current, total, result)

        Returns:
            识别结果列表
        """
        results = []
        total = len(audio_paths)

        for i, audio_path in enumerate(audio_paths):
            result = self.transcribe(audio_path)
            results.append(result)

            if callback:
                callback(i + 1, total, result)

        return results

    @property
    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model is not None


# 全局 ASR 引擎实例
_asr_engine: Optional[ASREngine] = None


def get_asr_engine(device="cpu", enable_speaker_diarization=False) -> ASREngine:
    """
    获取 ASR 引擎单例

    Args:
        device: 设备类型，"cpu" 或 "cuda"
        enable_speaker_diarization: 是否启用说话人分离

    Returns:
        ASR 引擎实例
    """
    global _asr_engine
    if _asr_engine is None or _asr_engine._device != device or getattr(_asr_engine, '_speaker_enabled', False) != enable_speaker_diarization:
        _asr_engine = ASREngine(device=device, enable_speaker_diarization=enable_speaker_diarization)
    return _asr_engine


def get_device_status() -> dict:
    """
    获取设备状态信息

    Returns:
        设备状态字典
    """
    status = {
        "cuda_available": False,
        "current_device": "cpu"
    }

    try:
        import torch
        status["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            status["cuda_device_count"] = torch.cuda.device_count()
            status["cuda_device_name"] = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    if _asr_engine:
        status["current_device"] = _asr_engine._device

    return status
