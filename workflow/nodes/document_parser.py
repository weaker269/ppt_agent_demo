"""
文档解析节点

从主项目移植并简化的文档解析逻辑。
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...models.document import (
    DocumentSection, DocumentInfo, DocumentAnalysis,
    DocumentEstimates, ProcessedDocument, DocumentValidationResult
)
from ...providers.provider_factory import ProviderRouter


class DocumentParserNode:
    """文档解析节点"""

    def __init__(self, provider_router: ProviderRouter):
        self.provider_router = provider_router

    async def parse_document(
        self,
        content: str,
        filename: str,
        options: Optional[Dict[str, Any]] = None
    ) -> ProcessedDocument:
        """
        解析文档内容

        Args:
            content: 文档内容
            filename: 文件名
            options: 解析选项

        Returns:
            ProcessedDocument: 处理后的文档数据
        """
        options = options or {}

        # 预处理内容
        processed_content = self._preprocess_content(content)

        # 生成文档信息
        document_info = self._create_document_info(content, processed_content, filename)

        # 分析文档
        content_analysis = self._analyze_document_structure(processed_content)

        # 解析章节
        sections = await self._parse_document_sections(processed_content, filename)

        # 优化章节结构
        optimized_sections = self._optimize_sections(sections, options)

        # 计算预估信息
        estimates = self._calculate_estimates(optimized_sections, processed_content)

        # 构建处理后的文档
        processed_document = ProcessedDocument(
            document_info=document_info,
            content_analysis=content_analysis,
            sections=optimized_sections,
            estimates=estimates,
            processing_options=options
        )

        return processed_document

    async def validate_document_quality(
        self,
        processed_document: ProcessedDocument
    ) -> DocumentValidationResult:
        """验证文档质量"""
        issues = []
        warnings = []
        statistics = {
            'total_sections': len(processed_document.sections),
            'empty_sections': 0,
            'short_sections': 0,
            'long_sections': 0,
            'total_content_length': 0
        }

        # 验证章节
        for i, section in enumerate(processed_document.sections):
            content_length = len(section.content.strip())
            statistics['total_content_length'] += content_length

            # 检查空章节
            if content_length == 0:
                statistics['empty_sections'] += 1
                issues.append({
                    'type': 'empty_section',
                    'section_index': i,
                    'section_title': section.title,
                    'message': '章节内容为空'
                })

            # 检查过短章节
            elif content_length < 50:
                statistics['short_sections'] += 1
                warnings.append({
                    'type': 'short_section',
                    'section_index': i,
                    'section_title': section.title,
                    'content_length': content_length,
                    'message': f'章节内容过短（{content_length}字符）'
                })

            # 检查过长章节
            elif content_length > 2000:
                statistics['long_sections'] += 1
                warnings.append({
                    'type': 'long_section',
                    'section_index': i,
                    'section_title': section.title,
                    'content_length': content_length,
                    'message': f'章节内容过长（{content_length}字符），可能需要拆分'
                })

            # 检查标题
            if not section.title.strip():
                issues.append({
                    'type': 'missing_title',
                    'section_index': i,
                    'message': '章节缺少标题'
                })

        # 计算质量评分
        quality_score = self._calculate_quality_score(statistics, issues, warnings)

        return DocumentValidationResult(
            is_valid=len(issues) == 0,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            statistics=statistics
        )

    def _preprocess_content(self, content: str) -> str:
        """预处理文档内容"""
        # 清理内容
        processed = content.strip()

        # 统一换行符
        processed = processed.replace('\r\n', '\n').replace('\r', '\n')

        # 移除过多的空行
        lines = processed.split('\n')
        cleaned_lines = []
        empty_line_count = 0

        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                empty_line_count = 0
            else:
                empty_line_count += 1
                if empty_line_count <= 2:  # 最多保留2个连续空行
                    cleaned_lines.append(line)

        processed = '\n'.join(cleaned_lines)

        # 处理Markdown格式
        processed = self._preprocess_markdown(processed)

        return processed

    def _preprocess_markdown(self, content: str) -> str:
        """预处理Markdown内容"""
        lines = content.split('\n')
        processed_lines = []

        for line in lines:
            # 标准化标题格式
            if line.strip().startswith('#'):
                line = line.strip()
                level = 0
                while level < len(line) and line[level] == '#':
                    level += 1
                if level < len(line) and line[level] != ' ':
                    line = '#' * level + ' ' + line[level:]
                processed_lines.append(line)
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines)

    def _create_document_info(self, original_content: str, processed_content: str, filename: str) -> DocumentInfo:
        """创建文档信息"""
        return DocumentInfo(
            filename=filename,
            file_type=self._detect_file_type(filename, original_content),
            original_size=len(original_content),
            processed_size=len(processed_content),
            document_hash=hashlib.md5(processed_content.encode('utf-8')).hexdigest()
        )

    def _detect_file_type(self, filename: str, content: str) -> str:
        """检测文件类型"""
        if filename.lower().endswith(('.md', '.markdown')):
            return 'text/markdown'
        elif filename.lower().endswith('.txt'):
            return 'text/plain'
        elif '# ' in content or '## ' in content:
            return 'text/markdown'
        else:
            return 'text/plain'

    def _analyze_document_structure(self, content: str) -> DocumentAnalysis:
        """分析文档结构"""
        return DocumentAnalysis(
            total_length=len(content),
            line_count=len(content.split('\n')),
            word_count=len(content.split()),
            paragraph_count=len([p for p in content.split('\n\n') if p.strip()]),
            language=self._detect_language(content),
            complexity_score=self._calculate_complexity_score(content),
            readability_score=self._calculate_readability_score(content),
            structure_type=self._detect_structure_type(content)
        )

    def _detect_language(self, content: str) -> str:
        """检测文档语言"""
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        total_chars = len(content.replace(' ', '').replace('\n', ''))

        if total_chars > 0:
            chinese_ratio = chinese_chars / total_chars
            if chinese_ratio > 0.3:
                return 'zh-CN'

        return 'en-US'

    def _calculate_complexity_score(self, content: str) -> float:
        """计算内容复杂度评分"""
        factors = {
            'length': min(2.0, len(content) / 10000),
            'structure': len(content.split('\n\n')) / 100,
            'vocabulary': len(set(content.lower().split())) / 1000,
        }
        return max(0.5, min(2.0, sum(factors.values())))

    def _calculate_readability_score(self, content: str) -> float:
        """计算可读性评分"""
        sentences = len([s for s in content.split('.') if s.strip()])
        words = len(content.split())

        if sentences == 0 or words == 0:
            return 0.5

        avg_sentence_length = words / sentences
        readability = max(0, min(1, 1 - (avg_sentence_length - 15) / 30))
        return readability

    def _detect_structure_type(self, content: str) -> str:
        """检测文档结构类型"""
        heading_count = len([line for line in content.split('\n') if self._is_heading_line(line.strip())])

        if heading_count > 5:
            return 'hierarchical'
        elif heading_count > 0:
            return 'sectioned'
        else:
            return 'linear'

    async def _parse_document_sections(self, content: str, filename: str) -> List[DocumentSection]:
        """解析文档章节"""
        try:
            # 尝试使用AI解析
            provider = self.provider_router.get_provider()
            sections = await provider.parse_document_structure(content, filename)

            if sections and len(sections) > 0:
                return sections

        except Exception as e:
            print(f"AI解析失败，使用基础解析: {e}")

        # 基础解析作为后备
        return self._parse_sections_basic(content)

    def _parse_sections_basic(self, content: str) -> List[DocumentSection]:
        """基础章节解析"""
        sections = []
        lines = content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()

            # 检测标题
            if self._is_heading_line(line):
                # 保存前一个章节
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                    current_content = []

                # 创建新章节
                level = self._get_heading_level(line)
                title = self._extract_title(line)

                current_section = DocumentSection(
                    title=title,
                    content='',
                    level=level,
                    order=len(sections),
                    parent_section=self._find_parent_section_title(sections, level)
                )
            else:
                # 添加到当前章节内容
                if line:
                    current_content.append(line)

        # 保存最后一个章节
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)

        # 如果没有识别到章节，将整个文档作为一个章节
        if not sections:
            sections.append(DocumentSection(
                title="文档内容",
                content=content.strip(),
                level=1,
                order=0
            ))

        return sections

    def _is_heading_line(self, line: str) -> bool:
        """判断是否为标题行"""
        if not line:
            return False

        # Markdown标题
        if line.startswith('#'):
            return True

        # 数字编号标题
        if re.match(r'^\d+\.?\s+.+', line):
            return True

        # 中文数字编号
        if re.match(r'^[一二三四五六七八九十]+[、．.]\s*.+', line):
            return True

        # 全大写标题（短于50字符）
        if line.isupper() and len(line) < 50 and not line.isdigit():
            return True

        return False

    def _get_heading_level(self, line: str) -> int:
        """获取标题级别"""
        if line.startswith('#'):
            return min(6, len(line) - len(line.lstrip('#')))

        # 其他类型默认为1级标题
        return 1

    def _extract_title(self, line: str) -> str:
        """提取标题文本"""
        # 移除Markdown标记
        if line.startswith('#'):
            return line.lstrip('#').strip()

        # 移除编号
        match = re.match(r'^\d+\.?\s+(.+)', line)
        if match:
            return match.group(1).strip()

        # 中文数字编号
        match = re.match(r'^[一二三四五六七八九十]+[、．.]\s*(.+)', line)
        if match:
            return match.group(1).strip()

        return line.strip()

    def _find_parent_section_title(self, sections: List[DocumentSection], level: int) -> Optional[str]:
        """查找父级章节标题"""
        for section in reversed(sections):
            if section.level < level:
                return section.title
        return None

    def _optimize_sections(self, sections: List[DocumentSection], options: Dict[str, Any]) -> List[DocumentSection]:
        """优化章节结构"""
        optimized = []
        min_content_length = options.get('min_section_length', 100)
        max_content_length = options.get('max_section_length', 2000)

        temp_section = None

        for section in sections:
            content_length = len(section.content.strip())

            # 合并过短的章节
            if content_length < min_content_length and temp_section is not None:
                temp_section.content += f"\n\n{section.content}"
                if section.subsections:
                    temp_section.subsections.extend(section.subsections)
            else:
                if temp_section:
                    optimized.append(temp_section)

                # 拆分过长的章节
                if content_length > max_content_length:
                    split_sections = self._split_long_section(section, max_content_length)
                    optimized.extend(split_sections)
                    temp_section = None
                else:
                    temp_section = section

        if temp_section:
            optimized.append(temp_section)

        # 重新编号
        for i, section in enumerate(optimized):
            section.order = i

        return optimized

    def _split_long_section(self, section: DocumentSection, max_length: int) -> List[DocumentSection]:
        """拆分过长的章节"""
        content = section.content
        if len(content) <= max_length:
            return [section]

        # 按段落拆分
        paragraphs = content.split('\n\n')
        split_sections = []
        current_content = []
        current_length = 0
        part_number = 1

        for paragraph in paragraphs:
            paragraph_length = len(paragraph)

            if current_length + paragraph_length > max_length and current_content:
                # 创建新的分段
                split_section = DocumentSection(
                    title=f"{section.title} (第{part_number}部分)",
                    content='\n\n'.join(current_content).strip(),
                    level=section.level,
                    order=section.order,
                    parent_section=section.parent_section
                )
                split_sections.append(split_section)

                current_content = [paragraph]
                current_length = paragraph_length
                part_number += 1
            else:
                current_content.append(paragraph)
                current_length += paragraph_length

        # 添加最后一部分
        if current_content:
            split_section = DocumentSection(
                title=f"{section.title} (第{part_number}部分)" if part_number > 1 else section.title,
                content='\n\n'.join(current_content).strip(),
                level=section.level,
                order=section.order,
                parent_section=section.parent_section
            )
            split_sections.append(split_section)

        return split_sections

    def _calculate_estimates(self, sections: List[DocumentSection], content: str) -> DocumentEstimates:
        """计算预估信息"""
        total_words = len(content.split())
        total_chars = len(content)
        estimated_slides = len(sections)

        # 估算演示时长（每张幻灯片30-60秒）
        estimated_duration_min = estimated_slides * 30
        estimated_duration_max = estimated_slides * 60

        # 复杂度因子
        complexity_factor = self._calculate_complexity_score(content)

        return DocumentEstimates(
            total_words=total_words,
            total_chars=total_chars,
            estimated_slides=estimated_slides,
            estimated_duration_seconds={
                'min': estimated_duration_min,
                'max': estimated_duration_max,
                'average': (estimated_duration_min + estimated_duration_max) // 2
            },
            complexity_factor=complexity_factor
        )

    def _calculate_quality_score(
        self,
        statistics: Dict[str, Any],
        issues: List[Dict[str, Any]],
        warnings: List[Dict[str, Any]]
    ) -> float:
        """计算结构质量评分"""
        base_score = 1.0

        # 扣除问题分数
        base_score -= len(issues) * 0.2
        base_score -= len(warnings) * 0.1

        # 基于统计信息调整
        if statistics['empty_sections'] > 0:
            base_score -= statistics['empty_sections'] * 0.1

        if statistics['total_sections'] == 0:
            base_score = 0.0

        return max(0.0, min(1.0, base_score))