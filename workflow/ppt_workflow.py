"""
PPT生成工作流

基于LangGraph构建的智能文档转PPT工作流。
"""

import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage

from models.workflow import (
    WorkflowState, WorkflowStatus, ProcessingStep, WorkflowConfiguration,
    WorkflowOutput, WorkflowError
)
from models.document import ProcessedDocument
from models.slide import PresentationData, PresentationNarration
from providers.provider_factory import ProviderRouter
from utils.file_utils import FileUtils

from workflow.nodes.document_parser import DocumentParserNode
from workflow.nodes.slide_generator import SlideGeneratorNode
from workflow.nodes.quality_evaluator import QualityEvaluatorNode
from workflow.nodes.narration_generator import NarrationGeneratorNode


class PPTWorkflow:
    """PPT生成工作流类"""

    def __init__(self, config: Optional[WorkflowConfiguration] = None):
        self.config = config or WorkflowConfiguration()
        self.provider_router = ProviderRouter(self.config.ai_provider)

        # 初始化节点
        self.document_parser = DocumentParserNode(self.provider_router)
        self.slide_generator = SlideGeneratorNode(self.provider_router)
        self.quality_evaluator = QualityEvaluatorNode(self.provider_router)
        self.narration_generator = NarrationGeneratorNode(self.provider_router)

        # 构建工作流图
        self.workflow_graph = self._build_workflow_graph()

    def _build_workflow_graph(self) -> StateGraph:
        """构建LangGraph工作流图"""
        # 创建状态图
        workflow = StateGraph(WorkflowState)

        # 添加节点
        workflow.add_node("document_parser", self._document_parsing_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("slide_generator", self._slide_generation_node)
        workflow.add_node("quality_evaluator", self._quality_evaluation_node)
        workflow.add_node("slide_optimizer", self._slide_optimization_node)
        workflow.add_node("narration_generator", self._narration_generation_node)
        workflow.add_node("output_assembler", self._output_assembly_node)
        workflow.add_node("error_handler", self._error_handler_node)

        # 设置入口点
        workflow.set_entry_point("document_parser")

        # 添加边和条件边
        workflow.add_edge("document_parser", "quality_check")

        # 质量检查的条件分支
        workflow.add_conditional_edges(
            "quality_check",
            self._should_continue_after_quality_check,
            {
                "continue": "slide_generator",
                "error": "error_handler"
            }
        )

        # 幻灯片生成后的质量评估
        workflow.add_edge("slide_generator", "quality_evaluator")

        # 质量评估的条件分支
        workflow.add_conditional_edges(
            "quality_evaluator",
            self._should_optimize_slides,
            {
                "optimize": "slide_optimizer",
                "continue": "narration_generator",
                "retry": "slide_generator"
            }
        )

        # 优化后继续到旁白生成
        workflow.add_edge("slide_optimizer", "narration_generator")

        # 旁白生成后到输出组装
        workflow.add_edge("narration_generator", "output_assembler")

        # 输出组装完成
        workflow.add_edge("output_assembler", END)

        # 错误处理结束
        workflow.add_edge("error_handler", END)

        return workflow.compile()

    async def process_document(
        self,
        input_file_path: str,
        output_directory: str = "./output",
        workflow_config: Optional[WorkflowConfiguration] = None
    ) -> WorkflowOutput:
        """
        处理文档生成PPT

        Args:
            input_file_path: 输入文件路径
            output_directory: 输出目录
            workflow_config: 工作流配置（可选）

        Returns:
            WorkflowOutput: 工作流输出结果
        """
        # 使用传入的配置或默认配置
        if workflow_config:
            self.config = workflow_config

        # 创建工作流状态
        workflow_id = str(uuid.uuid4())
        initial_state = WorkflowState(
            workflow_id=workflow_id,
            input_file_path=input_file_path,
            output_directory=output_directory,
            configuration=self.config
        )

        try:
            # 执行工作流
            final_state = await self._execute_workflow(initial_state)

            # 创建输出结果
            output = self._create_workflow_output(final_state)

            # 保存输出文件
            if output.is_successful:
                output_files = FileUtils.create_complete_output(output, output_directory)
                output.output_files = output_files

            return output

        except Exception as e:
            # 创建失败的输出结果
            error_output = WorkflowOutput(
                workflow_id=workflow_id,
                status=WorkflowStatus.FAILED,
                errors=[WorkflowError(
                    step=ProcessingStep.DOCUMENT_PARSING,  # 使用有效的枚举值
                    error_type=type(e).__name__,
                    error_message=str(e),
                    is_recoverable=False
                )]
            )
            return error_output

    async def _execute_workflow(self, initial_state: WorkflowState) -> WorkflowState:
        """执行工作流"""
        current_state = initial_state
        current_state.status = WorkflowStatus.RUNNING

        try:
            # 执行LangGraph工作流
            result = await self.workflow_graph.ainvoke(current_state)
            return result

        except Exception as e:
            current_state.mark_failed(str(e))
            raise

    # 工作流节点实现

    async def _document_parsing_node(self, state: WorkflowState) -> Dict[str, Any]:
        """文档解析节点"""
        step_result = state.start_step(ProcessingStep.DOCUMENT_PARSING)

        try:
            # 读取文档
            content, file_type = FileUtils.read_document(state.input_file_path)

            # 解析文档
            processed_document = await self.document_parser.parse_document(
                content=content,
                filename=state.input_file_path,
                options=state.configuration.document_options.model_dump()
            )

            state.processed_document = processed_document
            state.complete_step(ProcessingStep.DOCUMENT_PARSING, {
                'sections_count': len(processed_document.sections),
                'document_hash': processed_document.document_info.document_hash
            })

            return {"processed_document": processed_document}

        except Exception as e:
            state.fail_step(ProcessingStep.DOCUMENT_PARSING, str(e))
            state.add_error(ProcessingStep.DOCUMENT_PARSING, type(e).__name__, str(e))
            raise

    async def _quality_check_node(self, state: WorkflowState) -> Dict[str, Any]:
        """质量检查节点"""
        step_result = state.start_step(ProcessingStep.QUALITY_CHECK)

        try:
            if not state.processed_document or not state.processed_document.has_content:
                raise ValueError("文档解析结果为空或无有效内容")

            # 进行文档质量检查
            validation_result = await self.document_parser.validate_document_quality(
                state.processed_document
            )

            if not validation_result['is_valid']:
                raise ValueError(f"文档质量检查失败: {validation_result.get('issues', [])}")

            state.complete_step(ProcessingStep.QUALITY_CHECK, {
                'quality_score': validation_result.get('quality_score', 0.0),
                'issues_count': len(validation_result.get('issues', []))
            })

            return {"quality_check_result": validation_result}

        except Exception as e:
            state.fail_step(ProcessingStep.QUALITY_CHECK, str(e))
            state.add_error(ProcessingStep.QUALITY_CHECK, type(e).__name__, str(e))
            raise

    async def _slide_generation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """幻灯片生成节点"""
        step_result = state.start_step(ProcessingStep.SLIDE_GENERATION)

        try:
            if not state.processed_document:
                raise ValueError("没有可用的文档数据")

            # 生成幻灯片
            presentation_data = await self.slide_generator.generate_slides(
                state.processed_document.sections,
                state.configuration.slide_context
            )

            state.presentation_data = presentation_data
            state.complete_step(ProcessingStep.SLIDE_GENERATION, {
                'slides_generated': presentation_data.total_slides,
                'success_rate': presentation_data.success_rate,
                'overall_quality': presentation_data.generation_summary.overall_quality_score
            })

            return {"presentation_data": presentation_data}

        except Exception as e:
            state.fail_step(ProcessingStep.SLIDE_GENERATION, str(e))
            state.add_error(ProcessingStep.SLIDE_GENERATION, type(e).__name__, str(e))
            raise

    async def _quality_evaluation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """质量评估节点"""
        step_result = state.start_step(ProcessingStep.QUALITY_EVALUATION)

        try:
            if not state.presentation_data or not state.processed_document:
                raise ValueError("缺少必要的数据进行质量评估")

            # 评估幻灯片质量
            evaluation_result = await self.quality_evaluator.evaluate_presentation_quality(
                state.presentation_data,
                state.processed_document.sections,
                state.configuration.quality_threshold
            )

            state.complete_step(ProcessingStep.QUALITY_EVALUATION, {
                'average_quality_score': evaluation_result.get('average_quality_score', 0.0),
                'passed_slides': evaluation_result.get('passed_slides', 0),
                'needs_optimization': evaluation_result.get('needs_optimization', False)
            })

            return {"evaluation_result": evaluation_result}

        except Exception as e:
            state.fail_step(ProcessingStep.QUALITY_EVALUATION, str(e))
            state.add_error(ProcessingStep.QUALITY_EVALUATION, type(e).__name__, str(e))
            raise

    async def _slide_optimization_node(self, state: WorkflowState) -> Dict[str, Any]:
        """幻灯片优化节点"""
        step_result = state.start_step(ProcessingStep.SLIDE_OPTIMIZATION)

        try:
            if not state.presentation_data or not state.processed_document:
                raise ValueError("缺少必要的数据进行优化")

            # 优化低质量的幻灯片
            optimized_data = await self.slide_generator.optimize_low_quality_slides(
                state.presentation_data,
                state.processed_document.sections,
                state.configuration.quality_threshold
            )

            state.presentation_data = optimized_data
            state.complete_step(ProcessingStep.SLIDE_OPTIMIZATION, {
                'optimized_slides': len(optimized_data.slides),
                'final_quality_score': optimized_data.generation_summary.overall_quality_score
            })

            return {"optimized_presentation": optimized_data}

        except Exception as e:
            state.fail_step(ProcessingStep.SLIDE_OPTIMIZATION, str(e))
            state.add_error(ProcessingStep.SLIDE_OPTIMIZATION, type(e).__name__, str(e))
            raise

    async def _narration_generation_node(self, state: WorkflowState) -> Dict[str, Any]:
        """旁白生成节点"""
        step_result = state.start_step(ProcessingStep.NARRATION_GENERATION)

        try:
            if not state.presentation_data:
                raise ValueError("没有可用的演示文稿数据")

            # 生成旁白
            narration_data = await self.narration_generator.generate_presentation_narration(
                state.presentation_data.slides
            )

            state.narration_data = narration_data
            state.complete_step(ProcessingStep.NARRATION_GENERATION, {
                'narration_slides': narration_data.total_slides,
                'total_duration': narration_data.total_duration
            })

            return {"narration_data": narration_data}

        except Exception as e:
            state.fail_step(ProcessingStep.NARRATION_GENERATION, str(e))
            state.add_error(ProcessingStep.NARRATION_GENERATION, type(e).__name__, str(e))
            raise

    async def _output_assembly_node(self, state: WorkflowState) -> Dict[str, Any]:
        """输出组装节点"""
        step_result = state.start_step(ProcessingStep.OUTPUT_ASSEMBLY)

        try:
            # 标记工作流完成
            state.mark_completed()

            state.complete_step(ProcessingStep.OUTPUT_ASSEMBLY, {
                'total_slides': state.presentation_data.total_slides if state.presentation_data else 0,
                'has_narration': state.narration_data is not None,
                'final_status': state.status
            })

            return {"assembly_complete": True}

        except Exception as e:
            state.fail_step(ProcessingStep.OUTPUT_ASSEMBLY, str(e))
            state.add_error(ProcessingStep.OUTPUT_ASSEMBLY, type(e).__name__, str(e))
            raise

    async def _error_handler_node(self, state: WorkflowState) -> Dict[str, Any]:
        """错误处理节点"""
        # 标记工作流失败
        error_message = "工作流执行失败"
        if state.errors:
            error_message = state.errors[-1].error_message

        state.mark_failed(error_message)

        return {"error_handled": True}

    # 条件判断函数

    def _should_continue_after_quality_check(self, state: WorkflowState) -> str:
        """质量检查后是否继续"""
        if state.is_step_failed(ProcessingStep.QUALITY_CHECK):
            return "error"
        return "continue"

    def _should_optimize_slides(self, state: WorkflowState) -> str:
        """是否需要优化幻灯片"""
        if state.is_step_failed(ProcessingStep.QUALITY_EVALUATION):
            # 如果评估失败，检查是否应该重试
            retry_count = state.get_retry_count(ProcessingStep.SLIDE_GENERATION)
            if retry_count < state.configuration.max_retries:
                return "retry"
            else:
                return "continue"  # 超过重试次数，继续到下一步

        # 检查是否需要优化
        last_evaluation = state.get_step_result(ProcessingStep.QUALITY_EVALUATION)
        if last_evaluation and last_evaluation.data:
            needs_optimization = last_evaluation.data.get('needs_optimization', False)
            if needs_optimization and state.configuration.enable_optimization:
                return "optimize"

        return "continue"

    def _create_workflow_output(self, final_state: WorkflowState) -> WorkflowOutput:
        """创建工作流输出结果"""
        # 收集统计信息
        processing_statistics = {
            'total_steps': len(final_state.step_results),
            'completed_steps': sum(1 for r in final_state.step_results if r.status == WorkflowStatus.COMPLETED),
            'failed_steps': sum(1 for r in final_state.step_results if r.status == WorkflowStatus.FAILED),
            'total_duration': final_state.total_duration,
            'ai_provider_stats': self.provider_router.get_statistics()
        }

        performance_metrics = {
            'success_rate': final_state.success_rate,
            'api_calls': final_state.api_calls_count,
            'total_cost': final_state.total_cost,
            'average_step_duration': final_state.total_duration / len(final_state.step_results) if final_state.step_results else 0
        }

        # 创建输出对象
        output = WorkflowOutput(
            workflow_id=final_state.workflow_id,
            status=final_state.status,
            presentation_data=final_state.presentation_data,
            narration_data=final_state.narration_data,
            processing_statistics=processing_statistics,
            performance_metrics=performance_metrics,
            errors=final_state.errors,
            total_duration=final_state.total_duration,
            total_cost=final_state.total_cost
        )

        return output