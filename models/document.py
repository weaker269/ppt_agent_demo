"""
文档相关数据模型

从主项目简化移植的文档数据结构。
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentSection(BaseModel):
    """文档章节模型"""
    title: str = Field(description="章节标题")
    content: str = Field(description="章节内容")
    level: int = Field(default=1, description="章节层级")
    order: int = Field(default=0, description="章节顺序")
    parent_section: Optional[str] = Field(default=None, description="父级章节标题")
    subsections: List[str] = Field(default_factory=list, description="子章节列表")
    word_count: Optional[int] = Field(default=None, description="字数统计")

    def calculate_word_count(self) -> int:
        """计算字数"""
        self.word_count = len(self.content.split())
        return self.word_count


class DocumentInfo(BaseModel):
    """文档基础信息"""
    filename: str = Field(description="文件名")
    file_type: str = Field(description="文件类型")
    original_size: int = Field(description="原始文件大小")
    processed_size: int = Field(description="处理后大小")
    document_hash: str = Field(description="文档哈希值")
    processed_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DocumentAnalysis(BaseModel):
    """文档分析结果"""
    total_length: int = Field(description="总字符数")
    line_count: int = Field(description="行数")
    word_count: int = Field(description="词数")
    paragraph_count: int = Field(description="段落数")
    language: str = Field(default="zh-CN", description="语言")
    complexity_score: float = Field(default=1.0, description="复杂度评分")
    readability_score: float = Field(default=0.8, description="可读性评分")
    structure_type: str = Field(default="sectioned", description="结构类型")


class DocumentEstimates(BaseModel):
    """文档预估信息"""
    total_words: int = Field(description="总词数")
    total_chars: int = Field(description="总字符数")
    estimated_slides: int = Field(description="预估幻灯片数量")
    estimated_duration_seconds: Dict[str, int] = Field(description="预估时长")
    complexity_factor: float = Field(description="复杂度因子")


class ProcessedDocument(BaseModel):
    """处理后的文档完整数据"""
    document_info: DocumentInfo = Field(description="文档基础信息")
    content_analysis: DocumentAnalysis = Field(description="内容分析")
    sections: List[DocumentSection] = Field(description="文档章节列表")
    estimates: DocumentEstimates = Field(description="预估信息")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="处理选项")

    @property
    def total_sections(self) -> int:
        """获取总章节数"""
        return len(self.sections)

    @property
    def has_content(self) -> bool:
        """检查是否有内容"""
        return len(self.sections) > 0 and any(section.content.strip() for section in self.sections)


class DocumentValidationResult(BaseModel):
    """文档验证结果"""
    is_valid: bool = Field(description="是否有效")
    quality_score: float = Field(description="质量评分")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="问题列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")
    statistics: Dict[str, Any] = Field(default_factory=dict, description="统计信息")
    validated_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class DocumentProcessingOptions(BaseModel):
    """文档处理选项"""
    min_section_length: int = Field(default=50, description="最小章节长度")
    max_section_length: int = Field(default=2000, description="最大章节长度")
    max_title_length: int = Field(default=100, description="最大标题长度")
    language: str = Field(default="zh-CN", description="文档语言")
    enable_quality_validation: bool = Field(default=True, description="启用质量验证")
    merge_short_sections: bool = Field(default=True, description="合并短章节")
    split_long_sections: bool = Field(default=True, description="拆分长章节")