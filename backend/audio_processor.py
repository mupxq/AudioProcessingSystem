"""
音频处理模块
负责扫描文件夹、获取音频信息
"""
import os
from typing import List, Dict, Any
from pathlib import Path

from backend.utils.config import SUPPORTED_AUDIO_FORMATS


class AudioProcessor:
    """音频文件处理器"""

    @staticmethod
    def scan_folder(folder_path: str) -> List[Dict[str, Any]]:
        """
        扫描文件夹，获取所有音频文件

        Args:
            folder_path: 文件夹路径

        Returns:
            音频文件信息列表
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是文件夹: {folder_path}")

        audio_files = []

        try:
            # 遍历文件夹
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()

                    # 检查是否是支持的音频格式
                    if file_ext in SUPPORTED_AUDIO_FORMATS:
                        info = AudioProcessor.get_audio_info(file_path)
                        audio_files.append(info)

        except PermissionError as e:
            raise PermissionError(f"没有权限访问文件夹: {folder_path}")

        return audio_files

    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, Any]:
        """
        获取音频文件信息

        Args:
            file_path: 音频文件路径

        Returns:
            文件信息字典
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 获取文件基本信息
        stat = os.stat(file_path)
        file_size = stat.st_size

        # 获取文件名
        file_name = os.path.basename(file_path)

        return {
            "name": file_name,
            "path": file_path,
            "size": file_size,
            "size_mb": round(file_size / (1024 * 1024), 2),
            "extension": os.path.splitext(file_name)[1].lower(),
            "status": "pending",  # pending, processing, completed, failed
            "result": None,
        }

    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """
        获取音频时长（秒）
        需要 librosa 或其他音频库

        Args:
            file_path: 音频文件路径

        Returns:
            音频时长（秒）
        """
        try:
            import librosa
            duration = librosa.get_duration(filename=file_path)
            return round(duration, 2)
        except ImportError:
            # 如果没有 librosa，返回 None
            return None
        except Exception:
            return None

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时长"""
        if seconds is None:
            return "未知"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """
        检查是否是支持的音频文件

        Args:
            file_path: 文件路径

        Returns:
            是否是音频文件
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in SUPPORTED_AUDIO_FORMATS
