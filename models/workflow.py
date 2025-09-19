"""
工作流状态数据模型

定义LangGraph工作流中的状态数据结构。
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from .document import ProcessedDocument, DocumentProcessingOptions
from .slide import PresentationData, SlideGenerationContext, PresentationNarration


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ProcessingStep(str, Enum):
    """处理步骤枚举"""
    DOCUMENT_PARSING = "document_parsing"
    QUALITY_CHECK = "quality_check"
    SLIDE_GENERATION = "slide_generation"
    QUALITY_EVALUATION = "quality_evaluation"
    SLIDE_OPTIMIZATION = "slide_optimization"
    NARRATION_GENERATION = "narration_generation"
    OUTPUT_ASSEMBLY = "output_assembly"


class StepResult(BaseModel):
    """步骤执行结果"""
    step: ProcessingStep = Field(description="处理步骤")
    status: WorkflowStatus = Field(description="步骤状态")
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = Field(default=None, description="结束时间")
    duration: Optional[float] = Field(default=None, description="执行时长（秒）")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    retry_count: int = Field(default=0, description="重试次数")
    data: Optional[Dict[str, Any]] = Field(default=None, description="步骤数据")

    def mark_completed(self, data: Optional[Dict[str, Any]] = None):
        """标记步骤完成"""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now().isoformat()
        if self.start_time and self.end_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.duration = (end_dt - start_dt).total_seconds()
        if data:
            self.data = data

    def mark_failed(self, error_message: str):
        """标记步骤失败"""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now().isoformat()
        self.error_message = error_message
        if self.start_time and self.end_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.duration = (end_dt - start_dt).total_seconds()


class WorkflowError(BaseModel):
    """工作流错误信息"""
    step: ProcessingStep = Field(description="出错步骤")
    error_type: str = Field(description="错误类型")
    error_message: str = Field(description="错误消息")
    retry_count: int = Field(default=0, description="重试次数")
    is_recoverable: bool = Field(default=True, description="是否可恢复")
    occurred_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class WorkflowConfiguration(BaseModel):
    """工作流配置"""
    # AI提供者配置
    ai_provider: str = Field(default="openai", description="AI提供者")
    ai_model: str = Field(default="gpt-4", description="AI模型")

    # 重试配置
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delay: float = Field(default=1.0, description="重试延迟（秒）")

    # 质量控制配置
    quality_threshold: float = Field(default=0.8, description="质量阈值")
    enable_quality_control: bool = Field(default=True, description="启用质量控制")
    enable_optimization: bool = Field(default=True, description="启用优化")

    # 文档处理配置
    document_options: DocumentProcessingOptions = Field(
        default_factory=DocumentProcessingOptions,
        description="文档处理选项"
    )

    # 幻灯片生成配置
    slide_context: SlideGenerationContext = Field(
        default_factory=SlideGenerationContext,
        description="幻灯片生成上下文"
    )

    # 输出配置
    output_format: str = Field(default="json", description="输出格式")
    save_intermediate_results: bool = Field(default=False, description="保存中间结果")


class WorkflowState(BaseModel):
    """工作流状态"""
    # 基础信息
    workflow_id: str = Field(description="工作流ID")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="整体状态")
    current_step: Optional[ProcessingStep] = Field(default=None, description="当前步骤")

    # 输入数据
    input_file_path: str = Field(description="输入文件路径")
    output_directory: str = Field(description="输出目录")
    configuration: WorkflowConfiguration = Field(description="工作流配置")

    # 处理数据
    processed_document: Optional[ProcessedDocument] = Field(default=None, description="处理后的文档")
    presentation_data: Optional[PresentationData] = Field(default=None, description="演示文稿数据")
    narration_data: Optional[PresentationNarration] = Field(default=None, description="旁白数据")

    # 执行记录
    step_results: List[StepResult] = Field(default_factory=list, description="步骤结果列表")
    errors: List[WorkflowError] = Field(default_factory=list, description="错误列表")

    # 时间记录
    start_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = Field(default=None, description="结束时间")
    total_duration: Optional[float] = Field(default=None, description="总时长（秒）")

    # 统计信息
    total_cost: float = Field(default=0.0, description="总成本")
    api_calls_count: int = Field(default=0, description="API调用次数")

    def start_step(self, step: ProcessingStep) -> StepResult:
        """开始新步骤"""
        self.current_step = step
        step_result = StepResult(step=step, status=WorkflowStatus.RUNNING)
        self.step_results.append(step_result)
        return step_result

    def complete_step(self, step: ProcessingStep, data: Optional[Dict[str, Any]] = None):
        """完成步骤"""
        for result in reversed(self.step_results):
            if result.step == step and result.status == WorkflowStatus.RUNNING:
                result.mark_completed(data)
                break

    def fail_step(self, step: ProcessingStep, error_message: str):
        """步骤失败"""
        for result in reversed(self.step_results):
            if result.step == step and result.status == WorkflowStatus.RUNNING:
                result.mark_failed(error_message)
                break

    def add_error(self, step: ProcessingStep, error_type: str, error_message: str, is_recoverable: bool = True):
        """添加错误"""
        error = WorkflowError(
            step=step,
            error_type=error_type,
            error_message=error_message,
            is_recoverable=is_recoverable
        )
        self.errors.append(error)

    def get_step_result(self, step: ProcessingStep) -> Optional[StepResult]:
        """获取步骤结果"""
        for result in reversed(self.step_results):
            if result.step == step:
                return result
        return None

    def is_step_completed(self, step: ProcessingStep) -> bool:
        """检查步骤是否完成"""
        result = self.get_step_result(step)
        return result is not None and result.status == WorkflowStatus.COMPLETED

    def is_step_failed(self, step: ProcessingStep) -> bool:
        """检查步骤是否失败"""
        result = self.get_step_result(step)
        return result is not None and result.status == WorkflowStatus.FAILED

    def get_retry_count(self, step: ProcessingStep) -> int:
        """获取步骤重试次数"""
        count = 0
        for result in self.step_results:
            if result.step == step:
                count += 1
        return max(0, count - 1)  # 减去第一次执行

    def should_retry(self, step: ProcessingStep) -> bool:
        """判断是否应该重试"""
        retry_count = self.get_retry_count(step)
        return retry_count < self.configuration.max_retries

    def mark_completed(self):
        """标记工作流完成"""
        self.status = WorkflowStatus.COMPLETED
        self.end_time = datetime.now().isoformat()
        if self.start_time and self.end_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.total_duration = (end_dt - start_dt).total_seconds()

    def mark_failed(self, error_message: str):
        """标记工作流失败"""
        self.status = WorkflowStatus.FAILED
        self.end_time = datetime.now().isoformat()
        if self.start_time and self.end_time:
            start_dt = datetime.fromisoformat(self.start_time)
            end_dt = datetime.fromisoformat(self.end_time)
            self.total_duration = (end_dt - start_dt).total_seconds()

    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0

    @property
    def has_unrecoverable_errors(self) -> bool:
        """是否有不可恢复的错误"""
        return any(not error.is_recoverable for error in self.errors)

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if not self.step_results:
            return 0.0
        completed_steps = sum(1 for result in self.step_results if result.status == WorkflowStatus.COMPLETED)
        return completed_steps / len(self.step_results)


class WorkflowOutput(BaseModel):
    """工作流输出结果"""
    workflow_id: str = Field(description="工作流ID")
    status: WorkflowStatus = Field(description="最终状态")

    # 输出文件
    output_files: Dict[str, str] = Field(default_factory=dict, description="输出文件路径")

    # 处理结果
    presentation_data: Optional[PresentationData] = Field(default=None, description="演示文稿数据")
    narration_data: Optional[PresentationNarration] = Field(default=None, description="旁白数据")

    # 统计信息
    processing_statistics: Dict[str, Any] = Field(default_factory=dict, description="处理统计")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="性能指标")

    # 错误信息
    errors: List[WorkflowError] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")

    # 元数据
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    total_duration: Optional[float] = Field(default=None, description="总处理时长")
    total_cost: float = Field(default=0.0, description="总成本")

    @property
    def is_successful(self) -> bool:
        """是否成功"""
        return self.status == WorkflowStatus.COMPLETED and not any(not error.is_recoverable for error in self.errors)

    @property
    def has_presentation(self) -> bool:
        """是否有演示文稿"""
        return self.presentation_data is not None and self.presentation_data.total_slides > 0