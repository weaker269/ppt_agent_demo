"""
质量评估节点

评估幻灯片质量并提供改进建议。
"""

import asyncio
from typing import List, Dict, Any, Optional

from ...models.document import DocumentSection
from ...models.slide import SlideContent, PresentationData, QualityScore
from ...providers.provider_factory import ProviderRouter


class QualityEvaluatorNode:
    """质量评估节点"""

    def __init__(self, provider_router: ProviderRouter):
        self.provider_router = provider_router

    async def evaluate_presentation_quality(
        self,
        presentation_data: PresentationData,
        sections: List[DocumentSection],
        quality_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """
        评估整个演示文稿的质量

        Args:
            presentation_data: 演示文稿数据
            sections: 原始文档章节
            quality_threshold: 质量阈值

        Returns:
            Dict: 评估结果
        """
        provider = self.provider_router.get_provider()
        quality_assessments = []
        failed_assessments = []

        # 并行评估所有幻灯片
        evaluation_tasks = []
        for slide in presentation_data.slides:
            # 找到对应的章节
            section = next((s for s in sections if s.title == slide.section_reference), None)
            if section:
                task = self._evaluate_single_slide(provider, slide, section, quality_threshold)
                evaluation_tasks.append(task)

        # 执行评估
        results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)

        # 处理结果
        total_score = 0.0
        passed_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_assessments.append({
                    'slide_index': i,
                    'slide_title': presentation_data.slides[i].title,
                    'error': str(result)
                })
            else:
                quality_assessments.append(result)
                total_score += result['overall_score']
                if result['passed']:
                    passed_count += 1

        # 计算统计信息
        avg_score = total_score / len(quality_assessments) if quality_assessments else 0.0
        pass_rate = passed_count / len(quality_assessments) if quality_assessments else 0.0

        # 分析质量问题
        quality_issues = self._analyze_quality_issues(quality_assessments)

        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(quality_assessments)

        return {
            'quality_assessments': quality_assessments,
            'failed_assessments': failed_assessments,
            'average_quality_score': avg_score,
            'pass_rate': pass_rate,
            'passed_slides': passed_count,
            'total_slides': len(presentation_data.slides),
            'needs_optimization': avg_score < quality_threshold or pass_rate < 0.8,
            'quality_issues': quality_issues,
            'improvement_suggestions': improvement_suggestions,
            'quality_threshold': quality_threshold
        }

    async def _evaluate_single_slide(
        self,
        provider,
        slide: SlideContent,
        section: DocumentSection,
        threshold: float
    ) -> Dict[str, Any]:
        """评估单个幻灯片"""
        try:
            quality_score = await provider.evaluate_slide_quality(slide, section, threshold)

            return {
                'slide_index': slide.slide_number - 1,
                'slide_title': slide.title,
                'overall_score': quality_score.overall_score,
                'accuracy_score': quality_score.accuracy_score,
                'coherence_score': quality_score.coherence_score,
                'clarity_score': quality_score.clarity_score,
                'completeness_score': quality_score.completeness_score,
                'feedback': quality_score.feedback,
                'passed': quality_score.passed,
                'suggestions': quality_score.suggestions
            }

        except Exception as e:
            # 评估失败时返回默认评分
            return {
                'slide_index': slide.slide_number - 1,
                'slide_title': slide.title,
                'overall_score': 0.6,
                'accuracy_score': 0.6,
                'coherence_score': 0.6,
                'clarity_score': 0.6,
                'completeness_score': 0.6,
                'feedback': f"评估失败: {e}",
                'passed': False,
                'suggestions': ["请检查网络连接和API配置"]
            }

    def _analyze_quality_issues(self, quality_assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析质量问题"""
        issues = {
            'low_accuracy': [],
            'poor_coherence': [],
            'unclear_content': [],
            'incomplete_information': [],
            'overall_low_quality': []
        }

        for assessment in quality_assessments:
            slide_info = {
                'slide_index': assessment['slide_index'],
                'slide_title': assessment['slide_title'],
                'score': assessment['overall_score']
            }

            # 分析具体问题
            if assessment.get('accuracy_score', 1.0) < 0.7:
                issues['low_accuracy'].append(slide_info)

            if assessment.get('coherence_score', 1.0) < 0.7:
                issues['poor_coherence'].append(slide_info)

            if assessment.get('clarity_score', 1.0) < 0.7:
                issues['unclear_content'].append(slide_info)

            if assessment.get('completeness_score', 1.0) < 0.7:
                issues['incomplete_information'].append(slide_info)

            if assessment.get('overall_score', 1.0) < 0.6:
                issues['overall_low_quality'].append(slide_info)

        return issues

    def _generate_improvement_suggestions(self, quality_assessments: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        total_slides = len(quality_assessments)

        if total_slides == 0:
            return ["没有可评估的幻灯片"]

        # 统计低质量维度
        low_accuracy_count = sum(1 for a in quality_assessments if a.get('accuracy_score', 1.0) < 0.7)
        low_coherence_count = sum(1 for a in quality_assessments if a.get('coherence_score', 1.0) < 0.7)
        low_clarity_count = sum(1 for a in quality_assessments if a.get('clarity_score', 1.0) < 0.7)
        low_completeness_count = sum(1 for a in quality_assessments if a.get('completeness_score', 1.0) < 0.7)

        if low_accuracy_count > total_slides * 0.3:
            suggestions.append("建议：检查原始文档内容的准确性，确保关键信息正确传达")

        if low_coherence_count > total_slides * 0.3:
            suggestions.append("建议：改善幻灯片之间的逻辑关系，增强整体连贯性")

        if low_clarity_count > total_slides * 0.3:
            suggestions.append("建议：简化表达方式，使用更清晰的语言和结构")

        if low_completeness_count > total_slides * 0.3:
            suggestions.append("建议：确保每张幻灯片包含完整的关键信息")

        if not suggestions:
            suggestions.append("整体质量良好，建议保持当前的生成策略")

        return suggestions