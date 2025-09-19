"""
幻灯片生成节点

从主项目移植并简化的幻灯片生成逻辑。
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...models.document import DocumentSection
from ...models.slide import (
    SlideContent, SlideGenerationContext, PresentationData,
    SlidesGenerationSummary, QualityScore
)
from ...providers.provider_factory import ProviderRouter


class SlideGeneratorNode:
    """幻灯片生成节点"""

    def __init__(self, provider_router: ProviderRouter):
        self.provider_router = provider_router
        self.max_retry_attempts = 3
        self.quality_threshold = 0.8

    async def generate_slides(
        self,
        sections: List[DocumentSection],
        context: SlideGenerationContext
    ) -> PresentationData:
        """
        生成幻灯片

        Args:
            sections: 文档章节列表
            context: 生成上下文

        Returns:
            PresentationData: 演示文稿数据
        """
        successful_slides = []
        failed_slides = []
        total_cost = 0.0

        # 并行生成所有幻灯片
        tasks = []
        for section in sections:
            task = self._generate_single_slide_with_quality_control(section, context)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_slides.append({
                    'section_index': i,
                    'section_title': sections[i].title,
                    'error': str(result)
                })
            else:
                successful_slides.append(result['slide'])
                total_cost += result.get('cost', 0.0)

        # 生成演讲者讲稿
        speaker_script = ""
        if successful_slides:
            try:
                provider = self.provider_router.get_provider()
                speaker_script = await provider.generate_speaker_script(
                    successful_slides,
                    {'document_filename': context.document_filename}
                )
            except Exception as e:
                print(f"演讲者讲稿生成失败: {e}")

        # 计算整体质量评分
        overall_quality = self._calculate_overall_quality(successful_slides)

        # 创建生成汇总
        generation_summary = SlidesGenerationSummary(
            total_sections=len(sections),
            successful_slides=len(successful_slides),
            failed_slides=len(failed_slides),
            overall_quality_score=overall_quality,
            total_cost_usd=total_cost,
            total_generation_time=0.0  # 简化版本不追踪时间
        )

        return PresentationData(
            slides=successful_slides,
            failed_slides=failed_slides,
            speaker_script=speaker_script,
            generation_summary=generation_summary,
            generation_options=context.model_dump()
        )

    async def optimize_low_quality_slides(
        self,
        presentation_data: PresentationData,
        sections: List[DocumentSection],
        quality_threshold: float
    ) -> PresentationData:
        """优化低质量幻灯片"""
        optimized_slides = []
        optimization_tasks = []

        provider = self.provider_router.get_provider()

        for slide in presentation_data.slides:
            # 找到对应的章节
            section = next((s for s in sections if s.title == slide.section_reference), None)
            if not section:
                optimized_slides.append(slide)
                continue

            # 评估质量
            try:
                quality_score = await provider.evaluate_slide_quality(slide, section, quality_threshold)
                if quality_score.passed:
                    optimized_slides.append(slide)
                else:
                    # 需要优化
                    task = provider.optimize_slide_content(slide, quality_score, section)
                    optimization_tasks.append(task)
            except Exception:
                # 评估失败，保留原幻灯片
                optimized_slides.append(slide)

        # 执行优化
        if optimization_tasks:
            optimization_results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
            for result in optimization_results:
                if isinstance(result, Exception):
                    # 优化失败，使用原幻灯片（这里简化处理）
                    pass
                else:
                    optimized_slides.append(result)

        # 更新演示文稿数据
        new_overall_quality = self._calculate_overall_quality(optimized_slides)
        presentation_data.slides = optimized_slides
        presentation_data.generation_summary.overall_quality_score = new_overall_quality

        return presentation_data

    async def _generate_single_slide_with_quality_control(
        self,
        section: DocumentSection,
        context: SlideGenerationContext
    ) -> Dict[str, Any]:
        """
        生成单个幻灯片并进行质量控制

        Args:
            section: 文档章节
            context: 生成上下文

        Returns:
            Dict: 生成结果
        """
        provider = self.provider_router.get_provider()
        best_slide = None
        best_quality = None
        total_cost = 0.0

        for attempt in range(self.max_retry_attempts):
            try:
                # 生成幻灯片内容
                slide_content = await provider.generate_slide_content(section, context)

                # 评估质量
                try:
                    quality_score = await provider.evaluate_slide_quality(
                        slide_content, section, self.quality_threshold
                    )
                except Exception:
                    # 评估失败，创建默认质量评分
                    quality_score = QualityScore(
                        overall_score=0.7,
                        accuracy_score=0.7,
                        coherence_score=0.7,
                        clarity_score=0.7,
                        completeness_score=0.7,
                        feedback="质量评估服务不可用",
                        passed=True,
                        suggestions=[]
                    )

                # 估算成本
                estimated_cost = self._estimate_generation_cost(section, context)
                total_cost += estimated_cost

                # 如果质量达标，直接返回
                if quality_score.passed:
                    return {
                        'slide': slide_content,
                        'quality_info': quality_score,
                        'attempts': attempt + 1,
                        'cost': total_cost
                    }

                # 记录最佳结果
                if best_quality is None or quality_score.overall_score > best_quality.overall_score:
                    best_slide = slide_content
                    best_quality = quality_score

                # 如果未达标且还有重试机会，尝试优化
                if attempt < self.max_retry_attempts - 1:
                    try:
                        optimized_slide = await provider.optimize_slide_content(
                            slide_content, quality_score, section
                        )

                        # 重新评估优化后的质量
                        optimized_quality = await provider.evaluate_slide_quality(
                            optimized_slide, section, self.quality_threshold
                        )

                        estimated_cost = self._estimate_generation_cost(section, context)
                        total_cost += estimated_cost

                        # 如果优化后质量达标，返回
                        if optimized_quality.passed:
                            return {
                                'slide': optimized_slide,
                                'quality_info': optimized_quality,
                                'attempts': attempt + 1,
                                'cost': total_cost
                            }

                        # 更新最佳结果
                        if optimized_quality.overall_score > best_quality.overall_score:
                            best_slide = optimized_slide
                            best_quality = optimized_quality

                    except Exception:
                        # 优化失败，继续重试
                        pass

            except Exception as e:
                # 生成失败，如果是最后一次尝试，返回错误
                if attempt == self.max_retry_attempts - 1:
                    raise e

        # 所有尝试都未达标，返回最佳结果
        return {
            'slide': best_slide or self._create_fallback_slide(section),
            'quality_info': best_quality or self._create_fallback_quality(),
            'attempts': self.max_retry_attempts,
            'cost': total_cost
        }

    def _calculate_overall_quality(self, slides: List[SlideContent]) -> float:
        """计算整体质量评分"""
        if not slides:
            return 0.0

        # 简化版本：基于幻灯片内容的完整性评分
        total_score = 0.0
        for slide in slides:
            score = 0.0
            if slide.title.strip():
                score += 0.3
            if slide.bullet_points:
                score += 0.4
            if slide.speaker_notes.strip():
                score += 0.3
            total_score += score

        return total_score / len(slides)

    def _estimate_generation_cost(self, section: DocumentSection, context: SlideGenerationContext) -> float:
        """估算生成成本"""
        # 基于内容长度估算
        content_length = len(section.content)
        base_cost = (content_length / 1000) * 0.01  # 每1000字符约0.01美元
        return base_cost

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

    def _create_fallback_quality(self) -> QualityScore:
        """创建备用质量评分"""
        return QualityScore(
            overall_score=0.5,
            accuracy_score=0.5,
            coherence_score=0.5,
            clarity_score=0.5,
            completeness_score=0.5,
            feedback="内容生成失败，质量评估不可用",
            passed=False,
            suggestions=["重新生成幻灯片内容"]
        )