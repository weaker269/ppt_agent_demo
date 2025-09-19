"""
旁白生成节点

生成演示文稿的旁白内容。
"""

import asyncio
from typing import List, Dict, Any, Optional

from ...models.slide import SlideContent, NarrationContent, PresentationNarration
from ...providers.provider_factory import ProviderRouter


class NarrationGeneratorNode:
    """旁白生成节点"""

    def __init__(self, provider_router: ProviderRouter):
        self.provider_router = provider_router

    async def generate_presentation_narration(
        self,
        slides: List[SlideContent],
        context: Optional[Dict[str, Any]] = None
    ) -> PresentationNarration:
        """
        生成演示文稿旁白

        Args:
            slides: 幻灯片列表
            context: 生成上下文

        Returns:
            PresentationNarration: 旁白数据
        """
        context = context or {}
        provider = self.provider_router.get_provider()

        # 并行生成各幻灯片的旁白
        narration_tasks = []
        for slide in slides:
            task = self._generate_slide_narration(provider, slide, context)
            narration_tasks.append(task)

        # 执行并行生成
        narration_results = await asyncio.gather(*narration_tasks, return_exceptions=True)

        # 处理结果
        slide_narrations = []
        total_duration = 0.0

        for i, result in enumerate(narration_results):
            if isinstance(result, Exception):
                # 生成失败，使用备用旁白
                narration = self._create_fallback_narration(slides[i])
            else:
                narration = result

            slide_narrations.append(narration)
            total_duration += narration.estimated_duration

        # 生成完整演讲稿
        full_script = await self._generate_full_script(provider, slides, slide_narrations, context)

        # 创建生成汇总
        generation_summary = {
            'total_slides': len(slides),
            'successful_narrations': len([n for n in slide_narrations if n.narration_text]),
            'average_duration': total_duration / len(slides) if slides else 0,
            'generation_method': 'ai_enhanced'
        }

        return PresentationNarration(
            slide_narrations=slide_narrations,
            full_script=full_script,
            total_duration=total_duration,
            generation_summary=generation_summary
        )

    async def _generate_slide_narration(
        self,
        provider,
        slide: SlideContent,
        context: Dict[str, Any]
    ) -> NarrationContent:
        """生成单个幻灯片的旁白"""
        try:
            # 使用AI生成旁白
            narration_text = await provider.generate_narration(slide, context)

            # 估算时长（基于字数，中文约每分钟200字）
            estimated_duration = self._estimate_narration_duration(narration_text)

            return NarrationContent(
                slide_number=slide.slide_number,
                slide_title=slide.title,
                narration_text=narration_text,
                estimated_duration=estimated_duration
            )

        except Exception as e:
            # 生成失败，创建备用旁白
            return self._create_fallback_narration(slide)

    async def _generate_full_script(
        self,
        provider,
        slides: List[SlideContent],
        slide_narrations: List[NarrationContent],
        context: Dict[str, Any]
    ) -> str:
        """生成完整演讲稿"""
        try:
            # 使用AI生成完整演讲稿
            full_script = await provider.generate_speaker_script(slides, context)
            return full_script

        except Exception as e:
            # 生成失败，拼接各幻灯片旁白
            return self._create_fallback_full_script(slide_narrations)

    def _estimate_narration_duration(self, narration_text: str) -> float:
        """估算旁白时长"""
        if not narration_text:
            return 0.0

        # 中文：约每分钟200字，英文：约每分钟150词
        char_count = len(narration_text)
        word_count = len(narration_text.split())

        # 简单判断中英文
        chinese_chars = sum(1 for char in narration_text if '\u4e00' <= char <= '\u9fff')
        is_mainly_chinese = chinese_chars > char_count * 0.3

        if is_mainly_chinese:
            # 中文按字符计算
            duration = char_count / 200 * 60  # 秒
        else:
            # 英文按词数计算
            duration = word_count / 150 * 60  # 秒

        # 最少15秒，最多180秒
        return max(15.0, min(180.0, duration))

    def _create_fallback_narration(self, slide: SlideContent) -> NarrationContent:
        """创建备用旁白"""
        # 基于幻灯片内容创建简单旁白
        narration_parts = []

        narration_parts.append(f"现在我们来看{slide.title}。")

        if slide.bullet_points:
            narration_parts.append("主要内容包括：")
            for i, point in enumerate(slide.bullet_points[:3]):  # 最多3个要点
                narration_parts.append(f"{i+1}、{point}")

        if slide.speaker_notes:
            # 取演讲者备注的前100字符
            notes_excerpt = slide.speaker_notes[:100]
            if len(slide.speaker_notes) > 100:
                notes_excerpt += "..."
            narration_parts.append(f"具体来说，{notes_excerpt}")

        narration_text = " ".join(narration_parts)
        estimated_duration = self._estimate_narration_duration(narration_text)

        return NarrationContent(
            slide_number=slide.slide_number,
            slide_title=slide.title,
            narration_text=narration_text,
            estimated_duration=estimated_duration
        )

    def _create_fallback_full_script(self, slide_narrations: List[NarrationContent]) -> str:
        """创建备用完整演讲稿"""
        script_parts = []

        # 开场白
        script_parts.append("各位听众，大家好！")
        script_parts.append("今天我将为大家介绍以下内容。")
        script_parts.append("")

        # 各幻灯片旁白
        for narration in slide_narrations:
            script_parts.append(narration.narration_text)
            script_parts.append("")  # 添加空行分隔

        # 结束语
        script_parts.append("以上就是今天的全部内容。")
        script_parts.append("谢谢大家的聆听！")

        return "\n".join(script_parts)