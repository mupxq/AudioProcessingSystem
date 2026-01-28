"""
结果导出模块
将识别结果保存为 Markdown 文件
"""
import os
from datetime import datetime
from typing import Dict, Any, List

from backend.utils.config import OUTPUT_DIR


class ResultExporter:
    """结果导出器"""

    @staticmethod
    def export_to_markdown(result: Dict[str, Any], output_dir: str = None) -> str:
        """
        将单个识别结果导出为 Markdown 文件

        Args:
            result: 识别结果字典
            output_dir: 输出目录（默认使用配置的输出目录）

        Returns:
            导出文件的完整路径
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 获取音频文件名（不含扩展名）
        audio_name = os.path.splitext(os.path.basename(result["audio_path"]))[0]

        # 生成输出文件名
        output_filename = f"{audio_name}.md"
        output_path = os.path.join(output_dir, output_filename)

        # 构建 Markdown 内容
        content = ResultExporter._format_markdown(result)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    @staticmethod
    def export_batch(results: List[Dict[str, Any]], output_dir: str = None) -> List[str]:
        """
        批量导出识别结果

        Args:
            results: 识别结果列表
            output_dir: 输出目录

        Returns:
            导出文件路径列表
        """
        output_paths = []

        for result in results:
            if result.get("success") and result.get("text"):
                try:
                    output_path = ResultExporter.export_to_markdown(result, output_dir)
                    output_paths.append(output_path)
                except Exception as e:
                    print(f"导出失败 {result.get('audio_path')}: {e}")

        return output_paths

    @staticmethod
    def _format_markdown(result: Dict[str, Any]) -> str:
        """
        格式化为 Markdown 内容

        Args:
            result: 识别结果

        Returns:
            Markdown 格式的字符串
        """
        audio_path = result.get("audio_path", "")
        text = result.get("text", "")
        process_time = result.get("process_time", 0)
        success = result.get("success", False)
        error = result.get("error", "")

        # 获取文件信息
        audio_name = os.path.basename(audio_path)

        # 如果有错误，显示错误信息
        if not success:
            content = f"""# 音频识别结果

**文件名**: {audio_name}
**文件路径**: {audio_path}
**识别状态**: 失败
**识别时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 错误信息

{error}
"""
        else:
            # 获取文件大小
            file_size = "未知"
            if os.path.exists(audio_path):
                size_bytes = os.path.getsize(audio_path)
                file_size = ResultExporter._format_size(size_bytes)

            content = f"""# 音频识别结果

**文件名**: {audio_name}
**文件路径**: {audio_path}
**文件大小**: {file_size}
**识别状态**: 成功
**识别时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**处理耗时**: {process_time} 秒

## 识别文本

{text}

---

*本文件由 Fun-ASR 语音识别系统自动生成*
"""

        return content

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def create_summary(results: List[Dict[str, Any]], output_dir: str = None) -> str:
        """
        创建批量识别汇总文件

        Args:
            results: 所有识别结果
            output_dir: 输出目录

        Returns:
            汇总文件路径
        """
        if output_dir is None:
            output_dir = OUTPUT_DIR

        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")

        # 统计信息
        total = len(results)
        success_count = sum(1 for r in results if r.get("success"))
        failed_count = total - success_count
        total_time = sum(r.get("process_time", 0) for r in results)

        content = f"""# 批量识别汇总报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 统计信息

- **总文件数**: {total}
- **成功识别**: {success_count}
- **识别失败**: {failed_count}
- **总耗时**: {total_time:.2f} 秒
- **平均耗时**: {total_time / total if total > 0 else 0:.2f} 秒/文件

## 识别结果列表

"""

        for i, result in enumerate(results, 1):
            audio_name = os.path.basename(result.get("audio_path", ""))
            status = "✅ 成功" if result.get("success") else "❌ 失败"
            text = result.get("text", "")
            error = result.get("error", "")

            content += f"### {i}. {audio_name}\n\n"
            content += f"**状态**: {status}\n\n"

            if result.get("success"):
                content += f"**识别内容**: {text[:100]}{'...' if len(text) > 100 else ''}\n\n"
            else:
                content += f"**错误信息**: {error}\n\n"

            content += "---\n\n"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path
