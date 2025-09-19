"""
幻灯片相关数据模型

从主项目简化移植的幻灯片数据结构。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class SlideContent(BaseModel):
    """幻灯片内容模型"""
    title: str = Field(description="幻灯片标题")
    bullet_points: List[str] = Field(default_factory=list, description="要点列表")
    speaker_notes: str = Field(default="", description="演讲者备注")
    slide_number: int = Field(description="幻灯片编号")
    section_reference: str = Field(description="所属章节引用")
    narration: Optional[str] = Field(default=None, description="旁白文本")

    @property
    def has_content(self) -> bool:
        """检查是否有内容"""
        return bool(self.title.strip() or self.bullet_points or self.speaker_notes.strip())

    @property
    def content_length(self) -> int:
        """计算内容总长度"""
        total_length = len(self.title)
        total_length += sum(len(point) for point in self.bullet_points)
        total_length += len(self.speaker_notes)
        if self.narration:
            total_length += len(self.narration)
        return total_length


class QualityScore(BaseModel):
    """质量评分模型"""
    overall_score: float = Field(description="总体评分")
    accuracy_score: float = Field(description="准确性评分")
    coherence_score: float = Field(description="连贯性评分")
    clarity_score: float = Field(description="清晰度评分")
    completeness_score: float = Field(description="完整性评分")
    feedback: str = Field(default="", description="反馈意见")
    passed: bool = Field(description="是否通过质量检查")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")

    @property
    def needs_improvement(self) -> bool:
        """是否需要改进"""
        return not self.passed or self.overall_score < 0.8


class SlideGenerationContext(BaseModel):
    """幻灯片生成上下文"""
    document_filename: str = Field(default="", description="文档文件名")
    total_sections: int = Field(description="总章节数")
    current_section_index: int = Field(description="当前章节索引")
    target_audience: str = Field(default="professional", description="目标受众")
    presentation_style: str = Field(default="informative", description="演示风格")
    language: str = Field(default="zh-CN", description="语言")
    slide_template: str = Field(default="standard", description="幻灯片模板")
    max_bullet_points: int = Field(default=6, description="最大要点数")
    max_title_length: int = Field(default=50, description="最大标题长度")


class SlideGenerationResult(BaseModel):
    """幻灯片生成结果"""
    slide: SlideContent = Field(description="生成的幻灯片")
    quality_info: QualityScore = Field(description="质量信息")
    generation_attempts: int = Field(default=1, description="生成尝试次数")
    estimated_cost: float = Field(default=0.0, description="估算成本")
    generation_time: float = Field(default=0.0, description="生成时间（秒）")
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class SlidesGenerationSummary(BaseModel):
    """幻灯片生成汇总"""
    total_sections: int = Field(description="总章节数")
    successful_slides: int = Field(description="成功生成的幻灯片数")
    failed_slides: int = Field(description="失败的幻灯片数")
    overall_quality_score: float = Field(description="整体质量评分")
    total_cost_usd: float = Field(description="总成本（美元）")
    total_generation_time: float = Field(description="总生成时间（秒）")
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PresentationData(BaseModel):
    """演示文稿完整数据"""
    slides: List[SlideContent] = Field(description="幻灯片列表")
    failed_slides: List[Dict[str, Any]] = Field(default_factory=list, description="失败的幻灯片")
    speaker_script: str = Field(default="", description="演讲者讲稿")
    generation_summary: SlidesGenerationSummary = Field(description="生成汇总")
    generation_options: Dict[str, Any] = Field(default_factory=dict, description="生成选项")

    @property
    def total_slides(self) -> int:
        """获取总幻灯片数"""
        return len(self.slides)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.generation_summary.total_sections
        if total == 0:
            return 0.0
        return self.generation_summary.successful_slides / total

    @property
    def has_failures(self) -> bool:
        """是否有失败的幻灯片"""
        return len(self.failed_slides) > 0


class NarrationContent(BaseModel):
    """旁白内容模型"""
    slide_number: int = Field(description="幻灯片编号")
    slide_title: str = Field(description="幻灯片标题")
    narration_text: str = Field(description="旁白文本")
    estimated_duration: float = Field(description="预估时长（秒）")
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class PresentationNarration(BaseModel):
    """演示文稿旁白完整数据"""
    slide_narrations: List[NarrationContent] = Field(description="各幻灯片旁白")
    full_script: str = Field(description="完整演讲稿")
    total_duration: float = Field(description="总时长（秒）")
    generation_summary: Dict[str, Any] = Field(default_factory=dict, description="生成汇总")

    @property
    def total_slides(self) -> int:
        """获取总幻灯片数"""
        return len(self.slide_narrations)

    @property
    def average_duration_per_slide(self) -> float:
        """计算每张幻灯片平均时长"""
        if self.total_slides == 0:
            return 0.0
        return self.total_duration / self.total_slides


class SlideOptimizationOptions(BaseModel):
    """幻灯片优化选项"""
    quality_threshold: float = Field(default=0.8, description="质量阈值")
    max_optimization_attempts: int = Field(default=3, description="最大优化尝试次数")
    focus_areas: List[str] = Field(default_factory=list, description="优化重点领域")
    preserve_style: bool = Field(default=True, description="保持风格一致性")
    target_audience: str = Field(default="professional", description="目标受众")


class SlideOptimizationResult(BaseModel):
    """幻灯片优化结果"""
    optimized_slide: SlideContent = Field(description="优化后的幻灯片")
    quality_improvement: Dict[str, Any] = Field(description="质量改进信息")
    optimization_applied: bool = Field(description="是否应用了优化")
    optimization_attempts: int = Field(default=1, description="优化尝试次数")
    optimized_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    message: Optional[str] = Field(default=None, description="优化消息")