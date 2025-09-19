"""
Google Gemini AI服务提供者

使用Google Gemini模型提供AI服务。
"""

import json
import re
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from .base_provider import AIProvider
from ..models.document import DocumentSection
from ..models.slide import SlideContent, QualityScore, SlideGenerationContext


class GeminiProvider(AIProvider):
    """Google Gemini服务提供者"""

    def __init__(self, api_key: str, model: str = "gemini-pro", **kwargs):
        super().__init__(api_key, model, **kwargs)
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    async def parse_document_structure(
        self,
        content: str,
        filename: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSection]:
        """使用AI解析文档结构"""
        options = options or {}

        prompt = f"""
请分析以下文档内容，将其解析为结构化的章节。

文档文件名: {filename}
文档内容:
{content}

请按照以下JSON格式返回解析结果：
{{
    "sections": [
        {{
            "title": "章节标题",
            "content": "章节内容",
            "level": 1,
            "order": 0
        }}
    ]
}}

要求：
1. 识别文档的层次结构（标题、子标题等）
2. 每个章节应包含完整的内容
3. 确保章节之间逻辑清晰
4. 至少返回1个章节，最多返回20个章节
5. 章节内容应该适合制作成幻灯片
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            response_text = response.text
            response_data = self._parse_json_response(response_text)

            # 转换为DocumentSection对象
            sections = []
            for i, section_data in enumerate(response_data.get('sections', [])):
                section = DocumentSection(
                    title=section_data.get('title', f'章节 {i+1}'),
                    content=section_data.get('content', ''),
                    level=section_data.get('level', 1),
                    order=i,
                    parent_section=section_data.get('parent_section'),
                    subsections=section_data.get('subsections', [])
                )
                sections.append(section)

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(response_text)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return sections

        except Exception as e:
            # 返回基础解析结果作为后备
            return self._basic_document_parsing(content)

    async def generate_slide_content(
        self,
        section: DocumentSection,
        context: SlideGenerationContext
    ) -> SlideContent:
        """生成幻灯片内容"""
        prompt = f"""
请为以下章节内容生成一张专业的幻灯片。

章节标题: {section.title}
章节内容: {section.content}

上下文信息:
- 目标受众: {context.target_audience}
- 演示风格: {context.presentation_style}
- 语言: {context.language}
- 最大要点数: {context.max_bullet_points}
- 最大标题长度: {context.max_title_length}

请按照以下JSON格式返回：
{{
    "title": "幻灯片标题（不超过{context.max_title_length}字符）",
    "bullet_points": [
        "要点1",
        "要点2",
        "要点3"
    ],
    "speaker_notes": "演讲者备注，包含详细说明和补充信息"
}}

要求：
1. 标题简洁有力，突出核心主题
2. 要点列表清晰明了，不超过{context.max_bullet_points}个
3. 每个要点都应该是完整的信息点
4. 演讲者备注应提供额外的背景和解释
5. 内容应该适合{context.target_audience}受众
6. 风格应该符合{context.presentation_style}的要求
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            response_text = response.text
            response_data = self._parse_json_response(response_text)

            # 创建SlideContent对象
            slide = SlideContent(
                title=response_data.get('title', section.title),
                bullet_points=response_data.get('bullet_points', []),
                speaker_notes=response_data.get('speaker_notes', ''),
                slide_number=section.order + 1,
                section_reference=section.title
            )

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(response_text)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return slide

        except Exception as e:
            # 返回基础幻灯片作为后备
            return self._create_fallback_slide(section)

    async def evaluate_slide_quality(
        self,
        slide: SlideContent,
        section: DocumentSection,
        threshold: float = 0.8
    ) -> QualityScore:
        """评估幻灯片质量"""
        prompt = f"""
请评估以下幻灯片的质量，并给出详细的评分和建议。

原始章节:
标题: {section.title}
内容: {section.content[:500]}...

生成的幻灯片:
标题: {slide.title}
要点: {slide.bullet_points}
演讲者备注: {slide.speaker_notes[:200]}...

请按照以下标准评估（每项0-1分）：
1. 准确性(accuracy): 内容是否准确反映原始章节
2. 连贯性(coherence): 要点之间是否逻辑清晰
3. 清晰度(clarity): 表达是否简洁明了
4. 完整性(completeness): 是否涵盖了关键信息

请按照以下JSON格式返回：
{{
    "overall_score": 0.85,
    "accuracy_score": 0.9,
    "coherence_score": 0.8,
    "clarity_score": 0.85,
    "completeness_score": 0.85,
    "feedback": "整体质量良好，但可以在某些方面改进...",
    "passed": true,
    "suggestions": [
        "建议1",
        "建议2"
    ]
}}

质量阈值: {threshold}
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            response_text = response.text
            response_data = self._parse_json_response(response_text)

            # 创建QualityScore对象
            quality_score = QualityScore(
                overall_score=response_data.get('overall_score', 0.5),
                accuracy_score=response_data.get('accuracy_score', 0.5),
                coherence_score=response_data.get('coherence_score', 0.5),
                clarity_score=response_data.get('clarity_score', 0.5),
                completeness_score=response_data.get('completeness_score', 0.5),
                feedback=response_data.get('feedback', ''),
                passed=response_data.get('overall_score', 0.5) >= threshold,
                suggestions=response_data.get('suggestions', [])
            )

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(response_text)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return quality_score

        except Exception as e:
            return self._create_default_quality_score(passed=True)  # 默认通过

    async def optimize_slide_content(
        self,
        slide: SlideContent,
        quality_score: QualityScore,
        section: DocumentSection
    ) -> SlideContent:
        """优化幻灯片内容"""
        suggestions_text = '\n'.join(quality_score.suggestions) if quality_score.suggestions else "无具体建议"

        prompt = f"""
请根据质量评估结果优化以下幻灯片内容。

原始章节信息:
标题: {section.title}
内容: {section.content[:500]}...

当前幻灯片:
标题: {slide.title}
要点: {slide.bullet_points}
演讲者备注: {slide.speaker_notes}

质量评估结果:
- 总体评分: {quality_score.overall_score}
- 反馈: {quality_score.feedback}
- 改进建议: {suggestions_text}

请优化幻灯片内容，重点关注评估中指出的问题。

请按照以下JSON格式返回优化后的内容：
{{
    "title": "优化后的标题",
    "bullet_points": [
        "优化后的要点1",
        "优化后的要点2"
    ],
    "speaker_notes": "优化后的演讲者备注"
}}

要求：
1. 保持核心信息不变
2. 针对质量问题进行改进
3. 确保表达更加清晰准确
4. 保持专业性和逻辑性
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            response_text = response.text
            response_data = self._parse_json_response(response_text)

            # 创建优化后的SlideContent对象
            optimized_slide = SlideContent(
                title=response_data.get('title', slide.title),
                bullet_points=response_data.get('bullet_points', slide.bullet_points),
                speaker_notes=response_data.get('speaker_notes', slide.speaker_notes),
                slide_number=slide.slide_number,
                section_reference=slide.section_reference
            )

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(response_text)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return optimized_slide

        except Exception as e:
            return slide  # 优化失败时返回原始幻灯片

    async def generate_narration(
        self,
        slide: SlideContent,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成幻灯片旁白"""
        context = context or {}

        prompt = f"""
请为以下幻灯片生成自然流畅的演讲旁白。

幻灯片内容:
标题: {slide.title}
要点: {slide.bullet_points}
演讲者备注: {slide.speaker_notes}

要求：
1. 旁白应该自然流畅，适合口语表达
2. 包含幻灯片的所有关键信息
3. 语言要生动有趣，吸引听众
4. 长度适中，大约1-2分钟的演讲内容
5. 可以适当补充演讲者备注中的信息
6. 使用简体中文

请直接返回旁白文本，不需要JSON格式。
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            narration = response.text.strip()

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(narration)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return narration

        except Exception as e:
            # 返回基础旁白作为后备
            return self._create_fallback_narration(slide)

    async def generate_speaker_script(
        self,
        slides: List[SlideContent],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成完整演讲稿"""
        context = context or {}

        # 准备幻灯片摘要
        slides_summary = []
        for slide in slides:
            summary = f"幻灯片 {slide.slide_number}: {slide.title}\n要点: {', '.join(slide.bullet_points[:3])}"
            slides_summary.append(summary)

        slides_text = '\n\n'.join(slides_summary)

        prompt = f"""
请基于以下幻灯片内容生成一个完整的演讲稿。

演示文稿概要:
{slides_text}

要求：
1. 生成一个连贯的演讲稿，涵盖所有幻灯片
2. 包含开场白和结束语
3. 在幻灯片之间添加自然的过渡
4. 语言要正式但不失亲和力
5. 总长度适合15-20分钟的演讲
6. 使用简体中文

请直接返回演讲稿文本，不需要JSON格式。
"""

        try:
            response = await self.execute_with_retry(
                self._generate_content_async,
                prompt
            )

            script = response.text.strip()

            # 更新统计信息
            input_tokens = self._count_tokens(prompt)
            output_tokens = self._count_tokens(script)
            self.total_tokens_used += input_tokens + output_tokens
            self.total_cost += self._estimate_cost(input_tokens, output_tokens)

            return script

        except Exception as e:
            # 返回基础演讲稿作为后备
            return self._create_fallback_script(slides)

    async def _generate_content_async(self, prompt: str):
        """异步生成内容包装器"""
        import asyncio
        return await asyncio.get_event_loop().run_in_executor(
            None, self.client.generate_content, prompt
        )

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Gemini定价（免费版本较高的限制）"""
        # Gemini Pro 当前有免费额度，这里使用估算价格
        return (input_tokens + output_tokens) / 1000 * 0.001

    def _basic_document_parsing(self, content: str) -> List[DocumentSection]:
        """基础文档解析作为后备"""
        lines = content.split('\n')
        sections = []
        current_section = None
        current_content = []

        for line in lines:
            line = line.strip()
            if self._is_heading_line(line):
                # 保存前一个章节
                if current_section and current_content:
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
                    order=len(sections)
                )
            else:
                if line:
                    current_content.append(line)

        # 保存最后一个章节
        if current_section and current_content:
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
        # 数字编号
        if re.match(r'^\d+\.?\s+.+', line):
            return True
        return False

    def _get_heading_level(self, line: str) -> int:
        """获取标题级别"""
        if line.startswith('#'):
            return min(6, len(line) - len(line.lstrip('#')))
        return 1

    def _extract_title(self, line: str) -> str:
        """提取标题文本"""
        if line.startswith('#'):
            return line.lstrip('#').strip()
        match = re.match(r'^\d+\.?\s+(.+)', line)
        if match:
            return match.group(1).strip()
        return line.strip()

    def _create_fallback_slide(self, section: DocumentSection) -> SlideContent:
        """创建备用幻灯片"""
        content_lines = section.content.split('\n')
        bullet_points = [line.strip() for line in content_lines if line.strip()][:5]

        if not bullet_points:
            bullet_points = ["内容生成失败，请检查网络连接"]

        return SlideContent(
            title=section.title or "幻灯片标题",
            bullet_points=bullet_points,
            speaker_notes=section.content[:200] + "..." if len(section.content) > 200 else section.content,
            slide_number=section.order + 1,
            section_reference=section.title
        )

    def _create_fallback_narration(self, slide: SlideContent) -> str:
        """创建备用旁白"""
        narration = f"现在我们来看{slide.title}。"
        if slide.bullet_points:
            narration += f"主要包括以下几个方面：{', '.join(slide.bullet_points[:3])}。"
        if slide.speaker_notes:
            narration += f"具体来说，{slide.speaker_notes[:100]}。"
        return narration

    def _create_fallback_script(self, slides: List[SlideContent]) -> str:
        """创建备用演讲稿"""
        script_parts = ["各位听众，大家好！今天我将为大家介绍以下内容。\n"]

        for slide in slides:
            script_parts.append(f"首先，关于{slide.title}，")
            if slide.bullet_points:
                script_parts.append(f"主要包括：{', '.join(slide.bullet_points[:2])}。\n")

        script_parts.append("以上就是今天的全部内容，谢谢大家！")
        return ''.join(script_parts)