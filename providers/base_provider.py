"""
AI提供者基类

定义统一的AI服务接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
import time
from datetime import datetime

from ..models.document import DocumentSection
from ..models.slide import SlideContent, QualityScore, SlideGenerationContext


class AIProvider(ABC):
    """AI服务提供者基类"""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get('base_url')
        self.timeout = kwargs.get('timeout', 30)
        self.max_retries = kwargs.get('max_retries', 3)
        self.retry_delay = kwargs.get('retry_delay', 1.0)

        # 统计信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0

    @abstractmethod
    async def parse_document_structure(
        self,
        content: str,
        filename: str,
        options: Optional[Dict[str, Any]] = None
    ) -> List[DocumentSection]:
        """解析文档结构"""
        pass

    @abstractmethod
    async def generate_slide_content(
        self,
        section: DocumentSection,
        context: SlideGenerationContext
    ) -> SlideContent:
        """生成幻灯片内容"""
        pass

    @abstractmethod
    async def evaluate_slide_quality(
        self,
        slide: SlideContent,
        section: DocumentSection,
        threshold: float = 0.8
    ) -> QualityScore:
        """评估幻灯片质量"""
        pass

    @abstractmethod
    async def optimize_slide_content(
        self,
        slide: SlideContent,
        quality_score: QualityScore,
        section: DocumentSection
    ) -> SlideContent:
        """优化幻灯片内容"""
        pass

    @abstractmethod
    async def generate_narration(
        self,
        slide: SlideContent,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成旁白文本"""
        pass

    @abstractmethod
    async def generate_speaker_script(
        self,
        slides: List[SlideContent],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成完整演讲稿"""
        pass

    async def execute_with_retry(self, func, *args, **kwargs):
        """带重试的执行函数"""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                self.total_requests += 1
                start_time = time.time()

                result = await func(*args, **kwargs)

                # 记录成功统计
                self.successful_requests += 1
                execution_time = time.time() - start_time

                return result

            except Exception as e:
                last_exception = e
                self.failed_requests += 1

                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # 指数退避
                    continue
                else:
                    break

        # 所有重试都失败了
        raise last_exception

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = self.successful_requests / self.total_requests

        return {
            'provider_name': self.__class__.__name__,
            'model': self.model,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': round(success_rate, 3),
            'total_tokens_used': self.total_tokens_used,
            'total_cost_usd': round(self.total_cost, 4),
            'last_updated': datetime.now().isoformat()
        }

    def reset_statistics(self):
        """重置统计信息"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        self.total_cost = 0.0

    @property
    def is_healthy(self) -> bool:
        """检查提供者是否健康"""
        if self.total_requests == 0:
            return True  # 尚未使用，假设健康

        success_rate = self.successful_requests / self.total_requests
        return success_rate >= 0.8  # 成功率至少80%

    @property
    def provider_name(self) -> str:
        """获取提供者名称"""
        return self.__class__.__name__

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """估算成本（子类应重写此方法提供具体的定价）"""
        # 默认定价（每1000 token约0.002美元）
        return (input_tokens + output_tokens) / 1000 * 0.002

    def _count_tokens(self, text: str) -> int:
        """简单的token计数（实际应用中应使用tiktoken等工具）"""
        # 简化的token计数，实际应根据具体模型调整
        return len(text.split()) * 1.3  # 大致估算

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """解析JSON响应"""
        import json
        try:
            # 提取JSON部分（处理可能的前后文本）
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start >= 0 and end > start:
                json_text = response_text[start:end]
                return json.loads(json_text)
            else:
                raise ValueError("未找到有效的JSON内容")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {e}")

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        # 移除多余的空白字符
        lines = text.strip().split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        return '\n'.join(cleaned_lines)

    def _validate_slide_content(self, slide_data: Dict[str, Any]) -> bool:
        """验证幻灯片内容数据"""
        required_fields = ['title', 'bullet_points']
        return all(field in slide_data for field in required_fields)

    def _create_default_quality_score(self, passed: bool = False) -> QualityScore:
        """创建默认质量评分"""
        return QualityScore(
            overall_score=0.5,
            accuracy_score=0.5,
            coherence_score=0.5,
            clarity_score=0.5,
            completeness_score=0.5,
            feedback="AI服务调用失败，使用默认评分",
            passed=passed,
            suggestions=["请检查网络连接和API配置"]
        )