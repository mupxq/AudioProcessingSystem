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
        speaker_diarization_enabled = result.get("speaker_diarization_enabled", False)

        # 获取文件信息
        audio_name = os.path.basename(audio_path)

        # 如果有错误，显示错误信息
        if not success:
            content = "# 音频识别结果\n\n"
            content += f"**文件名**: {audio_name}\n"
            content += f"**文件路径**: {audio_path}\n"
            content += "**识别状态**: 失败\n"
            content += f"**识别时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "## 错误信息\n\n"
            content += f"{error}\n"
        else:
            # 获取文件大小
            file_size = "未知"
            if os.path.exists(audio_path):
                size_bytes = os.path.getsize(audio_path)
                file_size = ResultExporter._format_size(size_bytes)

            content = "# 音频识别结果\n\n"
            content += f"**文件名**: {audio_name}\n"
            content += f"**文件路径**: {audio_path}\n"
            content += f"**文件大小**: {file_size}\n"
            content += "**识别状态**: 成功\n"
            content += f"**识别时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"**处理耗时**: {process_time} 秒\n\n"

            # 如果启用了说话人分离
            if speaker_diarization_enabled and result.get("sentences"):
                sentences = result.get("sentences", [])
                speakers = result.get("speakers", [])
                speaker_count = result.get("speaker_count", 0)

                # 确保 speakers 都是字符串
                speakers = [str(s) for s in speakers]

                content += f"**说话人数量**: {speaker_count}\n"
                content += f"**说话人**: {', '.join(speakers)}\n\n"
                content += "---\n\n"
                content += "## 识别文本（按说话人标注）\n\n"

                # 创建说话人名称映射
                speaker_names = {}
                for i, spk in enumerate(speakers):
                    speaker_names[str(spk)] = f"说话人{chr(65 + i)}"  # 说话人A, 说话人B, ...

                # 按时间顺序输出，每句话标注说话人
                for sentence in sentences:
                    speaker = str(sentence.get("speaker", "unknown"))
                    speaker_name = speaker_names.get(speaker, speaker)
                    start_time = sentence.get("start", 0) / 1000
                    end_time = sentence.get("end", 0) / 1000
                    sentence_text = sentence.get("text", "")

                    time_range = "({:.1f}s - {:.1f}s)".format(start_time, end_time)
                    content += "**[{}]** {}\n\n{}\n\n".format(speaker_name, time_range, sentence_text)

                content += "---\n\n"
                content += "## 按说话人分类\n\n"

                # 按说话人分组
                speaker_text = {}
                for sentence in sentences:
                    speaker = str(sentence.get("speaker", "unknown"))
                    if speaker not in speaker_text:
                        speaker_text[speaker] = []
                    speaker_text[speaker].append(sentence)

                # 输出每个说话人的内容
                for speaker, speaker_sentences in speaker_text.items():
                    speaker_name = speaker_names.get(speaker, speaker)
                    content += f"### {speaker_name}\n\n"

                    for sentence in speaker_sentences:
                        start_time = sentence.get("start", 0) / 1000
                        end_time = sentence.get("end", 0) / 1000
                        sentence_text = sentence.get("text", "")
                        content += f"[{start_time:.1f}s - {end_time:.1f}s] {sentence_text}\n\n"

                content += "---\n\n"
                content += "## 完整文本\n\n"
                content += f"{text}\n\n"
                content += "---\n\n"
                content += "*本文件由 Fun-ASR 语音识别系统自动生成（含说话人分离）*\n"
            else:
                # 没有说话人分离，直接输出文本
                content += "## 识别文本\n\n"
                content += f"{text}\n\n"
                content += "---\n\n"
                content += "*本文件由 Fun-ASR 语音识别系统自动生成*\n"

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
