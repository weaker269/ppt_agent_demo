# PPT Agent Demo - 架构设计文档

## 概述

本demo项目采用基于LangGraph的智能工作流架构，实现文档到PPT的自动转换。设计目标是简化主项目的复杂度，专注于核心AI处理流程的验证。

## 架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文档输入      │───▶│  LangGraph      │───▶│   输出结果      │
│ (.md/.txt)      │    │   工作流        │    │ (JSON/文本)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AI提供者路由     │
                    │ (OpenAI/Gemini)     │
                    └─────────────────────┘
```

## 核心组件

### 1. LangGraph工作流 (`workflow/ppt_workflow.py`)

基于状态机的智能工作流，包含以下节点：

```python
# 工作流节点链
document_parsing → quality_check → slide_generation →
quality_evaluation → optimization → narration_generation
```

**条件分支逻辑**：
- 质量检查：决定是否需要优化
- 重试控制：失败时的回退机制
- 并行处理：幻灯片生成和质量评估

### 2. 数据模型 (`models/`)

#### 文档模型 (`document.py`)
```python
class DocumentSection:
    title: str          # 章节标题
    content: str        # 章节内容
    level: int          # 标题层级
    order: int          # 章节顺序
```

#### 幻灯片模型 (`slide.py`)
```python
class SlideContent:
    title: str                    # 幻灯片标题
    bullet_points: List[str]      # 要点列表
    speaker_notes: str            # 演讲者备注
    slide_number: int             # 幻灯片编号
    section_reference: str        # 对应章节
```

#### 工作流模型 (`workflow.py`)
```python
class WorkflowState:
    input_document: str           # 输入文档路径
    document_sections: List[DocumentSection]  # 解析后的章节
    presentation_data: PresentationData      # 幻灯片数据
    narration_data: PresentationNarration    # 旁白数据
    current_step: str            # 当前步骤
    processing_status: WorkflowStatus        # 处理状态
```

### 3. AI提供者系统 (`providers/`)

#### 抽象基类 (`base_provider.py`)
```python
class AIProvider(ABC):
    async def parse_document(self, content: str) -> List[DocumentSection]
    async def generate_slide_content(self, section: DocumentSection) -> SlideContent
    async def evaluate_slide_quality(self, slide: SlideContent) -> QualityScore
    async def optimize_slide_content(self, slide: SlideContent) -> SlideContent
    async def generate_narration(self, slide: SlideContent) -> str
```

#### 实现类
- **OpenAI Provider** (`openai_provider.py`): GPT-4集成
- **Gemini Provider** (`gemini_provider.py`): Google Gemini集成

#### 提供者路由 (`provider_factory.py`)
```python
class ProviderRouter:
    def get_provider(self) -> AIProvider
    def fallback_to_next(self) -> AIProvider
    def health_check(self) -> Dict[str, bool]
```

### 4. 工作流节点 (`workflow/nodes/`)

#### 文档解析器 (`document_parser.py`)
- 支持Markdown和纯文本格式
- 智能章节分割和层级识别
- 内容清理和标准化

#### 幻灯片生成器 (`slide_generator.py`)
- 并行生成多张幻灯片
- 质量控制循环（生成→评估→优化）
- 失败重试机制

#### 质量评估器 (`quality_evaluator.py`)
- 多维度质量评分（准确性、连贯性、清晰度、完整性）
- 质量问题分析
- 改进建议生成

#### 旁白生成器 (`narration_generator.py`)
- 为每张幻灯片生成演讲旁白
- 时长估算（中文约200字/分钟）
- 完整演讲稿生成

## 数据流

### 1. 输入阶段
```
文档文件 → FileUtils.read_document() → 原始文档内容
```

### 2. 解析阶段
```
原始内容 → DocumentParser.parse() → List[DocumentSection]
```

### 3. 生成阶段
```
DocumentSection → SlideGenerator.generate() → SlideContent
                ↓
         QualityEvaluator.evaluate() → QualityScore
                ↓
    (如果质量不达标) SlideGenerator.optimize() → 优化后的SlideContent
```

### 4. 旁白阶段
```
List[SlideContent] → NarrationGenerator.generate() → PresentationNarration
```

### 5. 输出阶段
```
PresentationData + PresentationNarration → 输出文件
```

## 配置系统

### 环境变量 (`.env`)
```bash
# AI提供者配置
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
DEFAULT_PROVIDER=openai

# 质量控制
MAX_RETRIES=3
QUALITY_THRESHOLD=0.8
ENABLE_QUALITY_CONTROL=true

# 输出配置
DEFAULT_OUTPUT_DIR=./output
```

### 工作流配置 (`WorkflowConfiguration`)
```python
ai_provider: str = "openai"
max_retries: int = 3
quality_threshold: float = 0.8
enable_optimization: bool = True
output_format: str = "json"
```

## 错误处理

### 分层错误处理策略

1. **提供者级别**：API调用失败、网络超时
   - 自动重试（指数退避）
   - 提供者切换
   - 降级服务

2. **节点级别**：处理逻辑错误
   - 异常捕获和记录
   - 备用方案激活
   - 状态回滚

3. **工作流级别**：整体流程控制
   - 检查点保存
   - 部分结果保留
   - 优雅降级

### 容错机制

- **备用内容生成**：AI调用失败时生成基础内容
- **质量阈值调整**：动态降低质量要求确保完成
- **并行处理容错**：部分幻灯片失败不影响整体流程

## 性能优化

### 并行处理
- 幻灯片生成：多个章节并行处理
- 质量评估：批量评估提高效率
- 旁白生成：并行生成减少等待时间

### 缓存策略
- 文档解析结果缓存
- AI响应缓存（相同输入）
- 质量评估结果缓存

### 资源管理
- 异步IO减少阻塞
- 连接池复用
- 内存使用优化

## 扩展性

### 新增AI提供者
1. 继承`AIProvider`基类
2. 实现所有抽象方法
3. 在`ProviderFactory`中注册
4. 添加配置项

### 新增工作流节点
1. 定义节点函数
2. 更新`WorkflowState`模型
3. 在LangGraph中添加节点和边
4. 配置条件分支逻辑

### 输出格式扩展
1. 定义新的输出格式类
2. 实现格式转换器
3. 更新配置选项
4. 添加对应的CLI参数

## 与主项目的关系

### 简化对比

| 功能 | 主项目 | Demo版本 |
|------|--------|----------|
| 任务队列 | Celery + Redis | 直接调用 |
| 数据库 | PostgreSQL | 内存对象 |
| 音频合成 | ElevenLabs TTS | 仅文本旁白 |
| 监控 | Prometheus + Grafana | 基础日志 |
| 缓存 | Redis | 内存缓存 |
| API | FastAPI + 认证 | CLI命令 |

### 保留特性
- AI提供者抽象和路由
- 质量控制循环
- 文档解析逻辑
- 数据模型设计
- 错误处理模式

### 验证目标
- LangGraph工作流可行性
- AI提供者切换稳定性
- 质量控制效果
- 整体处理流程