"""
文件处理工具函数

提供文档读取、输出保存等功能。
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
import mimetypes

from models.slide import PresentationData
from models.workflow import WorkflowOutput


class FileUtils:
    """文件处理工具类"""

    @staticmethod
    def read_document(file_path: str) -> tuple[str, str]:
        """
        读取文档内容

        Returns:
            tuple: (content, file_type)
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        # 检测文件类型
        mime_type, _ = mimetypes.guess_type(str(file_path))
        file_type = mime_type or "text/plain"

        # 根据扩展名确定编码
        suffix = file_path.suffix.lower()
        encoding = 'utf-8'

        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content, file_type
        except UnicodeDecodeError:
            # 尝试其他编码
            for enc in ['gbk', 'gb2312', 'latin1']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    return content, file_type
                except UnicodeDecodeError:
                    continue

            raise ValueError(f"无法解码文件: {file_path}")

    @staticmethod
    def validate_file_format(file_path: str) -> bool:
        """验证文件格式是否支持"""
        supported_extensions = {'.txt', '.md', '.markdown'}
        file_path = Path(file_path)
        return file_path.suffix.lower() in supported_extensions

    @staticmethod
    def generate_file_hash(content: str) -> str:
        """生成文件内容哈希"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    @staticmethod
    def ensure_output_directory(output_dir: str) -> Path:
        """确保输出目录存在"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    @staticmethod
    def save_presentation_data(
        presentation_data: PresentationData,
        output_dir: str,
        filename: str = "presentation.json"
    ) -> str:
        """保存演示文稿数据为JSON"""
        output_path = FileUtils.ensure_output_directory(output_dir)
        file_path = output_path / filename

        # 转换为可序列化的字典
        data_dict = presentation_data.model_dump()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, ensure_ascii=False, indent=2)

        return str(file_path)

    @staticmethod
    def save_narration_text(
        narration_text: str,
        output_dir: str,
        filename: str = "narration.txt"
    ) -> str:
        """保存旁白文本"""
        output_path = FileUtils.ensure_output_directory(output_dir)
        file_path = output_path / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(narration_text)

        return str(file_path)

    @staticmethod
    def save_individual_slides(
        presentation_data: PresentationData,
        output_dir: str
    ) -> list[str]:
        """保存单独的幻灯片文件"""
        output_path = FileUtils.ensure_output_directory(output_dir)
        slides_dir = output_path / "slides"
        slides_dir.mkdir(exist_ok=True)

        saved_files = []

        for slide in presentation_data.slides:
            filename = f"slide_{slide.slide_number:02d}.json"
            file_path = slides_dir / filename

            slide_dict = slide.model_dump()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(slide_dict, f, ensure_ascii=False, indent=2)

            saved_files.append(str(file_path))

        return saved_files

    @staticmethod
    def save_processing_report(
        workflow_output: WorkflowOutput,
        output_dir: str,
        filename: str = "report.json"
    ) -> str:
        """保存处理报告"""
        output_path = FileUtils.ensure_output_directory(output_dir)
        file_path = output_path / filename

        report_dict = workflow_output.model_dump()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)

        return str(file_path)

    @staticmethod
    def create_complete_output(
        workflow_output: WorkflowOutput,
        output_dir: str
    ) -> Dict[str, str]:
        """创建完整的输出文件结构"""
        output_files = {}

        try:
            # 保存主要的演示文稿数据
            if workflow_output.presentation_data:
                output_files['presentation'] = FileUtils.save_presentation_data(
                    workflow_output.presentation_data,
                    output_dir
                )

                # 保存单独的幻灯片文件
                slide_files = FileUtils.save_individual_slides(
                    workflow_output.presentation_data,
                    output_dir
                )
                output_files['slides'] = slide_files

            # 保存旁白文本
            if workflow_output.narration_data:
                narration_text = workflow_output.narration_data.full_script
                if narration_text:
                    output_files['narration'] = FileUtils.save_narration_text(
                        narration_text,
                        output_dir
                    )

            # 保存处理报告
            output_files['report'] = FileUtils.save_processing_report(
                workflow_output,
                output_dir
            )

            return output_files

        except Exception as e:
            raise RuntimeError(f"创建输出文件失败: {e}")

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        return Path(file_path).stat().st_size

    @staticmethod
    def get_directory_size(directory: str) -> int:
        """获取目录总大小（字节）"""
        total_size = 0
        for file_path in Path(directory).rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size

    @staticmethod
    def cleanup_temp_files(file_paths: list[str]):
        """清理临时文件"""
        for file_path in file_paths:
            try:
                Path(file_path).unlink(missing_ok=True)
            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小显示"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        size = size_bytes
        i = 0

        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1

        return f"{size:.1f} {size_names[i]}"

    @staticmethod
    def create_summary_text(workflow_output: WorkflowOutput) -> str:
        """创建处理摘要文本"""
        summary_lines = []

        summary_lines.append("PPT Agent Demo - 处理摘要")
        summary_lines.append("=" * 50)
        summary_lines.append("")

        # 基本信息
        summary_lines.append(f"工作流ID: {workflow_output.workflow_id}")
        summary_lines.append(f"处理状态: {workflow_output.status}")
        summary_lines.append(f"总耗时: {workflow_output.total_duration:.2f}秒" if workflow_output.total_duration else "总耗时: 未知")
        summary_lines.append(f"总成本: ${workflow_output.total_cost:.4f}")
        summary_lines.append("")

        # 演示文稿信息
        if workflow_output.presentation_data:
            pres_data = workflow_output.presentation_data
            summary_lines.append("演示文稿信息:")
            summary_lines.append(f"  - 成功生成幻灯片: {pres_data.total_slides}张")
            summary_lines.append(f"  - 失败幻灯片: {len(pres_data.failed_slides)}张")
            summary_lines.append(f"  - 成功率: {pres_data.success_rate:.1%}")
            summary_lines.append(f"  - 整体质量评分: {pres_data.generation_summary.overall_quality_score:.2f}")

        # 旁白信息
        if workflow_output.narration_data:
            narr_data = workflow_output.narration_data
            summary_lines.append("")
            summary_lines.append("旁白信息:")
            summary_lines.append(f"  - 旁白幻灯片: {narr_data.total_slides}张")
            summary_lines.append(f"  - 总时长: {narr_data.total_duration:.1f}秒")
            summary_lines.append(f"  - 平均每张时长: {narr_data.average_duration_per_slide:.1f}秒")

        # 错误信息
        if workflow_output.errors:
            summary_lines.append("")
            summary_lines.append("错误信息:")
            for error in workflow_output.errors:
                summary_lines.append(f"  - {error.step}: {error.error_message}")

        # 警告信息
        if workflow_output.warnings:
            summary_lines.append("")
            summary_lines.append("警告信息:")
            for warning in workflow_output.warnings:
                summary_lines.append(f"  - {warning}")

        summary_lines.append("")
        summary_lines.append(f"报告生成时间: {workflow_output.created_at}")

        return "\n".join(summary_lines)

    @staticmethod
    def save_summary_text(
        workflow_output: WorkflowOutput,
        output_dir: str,
        filename: str = "summary.txt"
    ) -> str:
        """保存处理摘要文本"""
        output_path = FileUtils.ensure_output_directory(output_dir)
        file_path = output_path / filename

        summary_text = FileUtils.create_summary_text(workflow_output)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(summary_text)

        return str(file_path)