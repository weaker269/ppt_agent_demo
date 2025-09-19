# API 参考文档

## 命令行接口 (CLI)

### 主命令

```bash
python main.py [OPTIONS] COMMAND [ARGS]...
```

PPT Agent Demo - 智能文档转PPT工具

### 子命令

#### `process` - 处理文档生成PPT

```bash
python main.py process [OPTIONS] INPUT_FILE
```

**参数**：
- `INPUT_FILE`: 输入文档路径（必需）

**选项**：
- `--output, -o TEXT`: 输出目录 [默认: ./output]
- `--provider, -p [openai|gemini]`: AI提供者 [默认: openai]
- `--max-retries INTEGER`: 最大重试次数 [默认: 3]
- `--quality-threshold FLOAT`: 质量阈值 [默认: 0.8]
- `--verbose, -v`: 显示详细日志

**示例**：
```bash
# 基础用法
python main.py process sample_docs/sample1.md

# 指定提供者和输出目录
python main.py process sample_docs/sample1.md --provider gemini --output ./results

# 调整质量参数
python main.py process sample_docs/sample1.md --quality-threshold 0.9 --max-retries 5

# 显示详细信息
python main.py process sample_docs/sample1.md --verbose
```

#### `validate` - 验证文档格式

```bash
python main.py validate [OPTIONS] INPUT_FILE
```

验证文档格式和内容，检查是否可以正常处理。

**参数**：
- `INPUT_FILE`: 要验证的文档路径（必需）

**示例**：
```bash
python main.py validate sample_docs/sample1.md
```

#### `info` - 显示系统信息

```bash
python main.py info [OPTIONS]
```

显示系统配置信息，包括环境变量和支持的格式。

**示例**：
```bash
python main.py info
```

#### `clean` - 清理输出目录

```bash
python main.py clean [OPTIONS] OUTPUT_DIR
```

清理指定的输出目录。

**参数**：
- `OUTPUT_DIR`: 要清理的目录路径（必需）

**示例**：
```bash
python main.py clean ./output
```

## Python API

### 工作流类

#### `PPTWorkflow`

主工作流类，协调整个文档处理流程。

```python
from workflow.ppt_workflow import PPTWorkflow
from models.workflow import WorkflowConfiguration

# 创建工作流实例
workflow = PPTWorkflow(config)

# 处理文档
result = await workflow.process_document(
    input_file_path="document.md",
    output_directory="./output",
    workflow_config=config
)
```

**方法**：

##### `__init__(config: WorkflowConfiguration)`
初始化工作流。

**参数**：
- `config`: 工作流配置对象

##### `async process_document(input_file_path, output_directory, workflow_config) -> WorkflowResult`
处理文档生成PPT。

**参数**：
- `input_file_path`: 输入文档路径
- `output_directory`: 输出目录路径
- `workflow_config`: 工作流配置

**返回**：`WorkflowResult` 对象，包含处理结果

### 配置类

#### `WorkflowConfiguration`

```python
from models.workflow import WorkflowConfiguration

config = WorkflowConfiguration(
    ai_provider="openai",           # AI提供者
    max_retries=3,                  # 最大重试次数
    quality_threshold=0.8,          # 质量阈值
    enable_optimization=True,       # 启用优化
    output_format="json",          # 输出格式
    enable_parallel_processing=True # 启用并行处理
)
```

**字段**：
- `ai_provider`: AI服务提供者 ("openai" | "gemini")
- `max_retries`: 失败时的最大重试次数
- `quality_threshold`: 质量评估阈值 (0.0-1.0)
- `enable_optimization`: 是否启用质量优化
- `output_format`: 输出格式 ("json" | "yaml")
- `enable_parallel_processing`: 是否启用并行处理

### 数据模型

#### `DocumentSection`

文档章节模型。

```python
from models.document import DocumentSection

section = DocumentSection(
    title="章节标题",
    content="章节内容...",
    level=1,              # 标题层级
    order=0               # 章节顺序
)
```

#### `SlideContent`

幻灯片内容模型。

```python
from models.slide import SlideContent

slide = SlideContent(
    title="幻灯片标题",
    bullet_points=["要点1", "要点2", "要点3"],
    speaker_notes="演讲者备注...",
    slide_number=1,
    section_reference="对应章节标题"
)
```

#### `PresentationData`

演示文稿数据模型。

```python
from models.slide import PresentationData

presentation = PresentationData(
    slides=slides_list,              # 幻灯片列表
    failed_slides=[],                # 失败的幻灯片
    speaker_script="完整演讲稿...",    # 演讲稿
    generation_summary=summary,       # 生成摘要
    generation_options=options        # 生成选项
)
```

**属性**：
- `total_slides`: 总幻灯片数
- `success_rate`: 成功率
- `average_quality_score`: 平均质量分

#### `WorkflowResult`

工作流结果模型。

```python
from models.workflow import WorkflowResult

# 结果访问
result.is_successful              # 是否成功
result.presentation_data          # 演示文稿数据
result.narration_data            # 旁白数据
result.output_files              # 输出文件路径
result.processing_statistics     # 处理统计
result.errors                    # 错误信息
result.warnings                  # 警告信息
```

### 工具函数

#### `FileUtils`

文件处理工具类。

```python
from utils.file_utils import FileUtils

# 验证文件格式
is_valid = FileUtils.validate_file_format("document.md")

# 读取文档
content, file_type = FileUtils.read_document("document.md")

# 保存结果
FileUtils.save_presentation_data(presentation_data, "output/")
FileUtils.save_narration_text(narration_data, "output/")

# 格式化文件大小
size_str = FileUtils.format_file_size(1024)  # "1.0 KB"
```

**方法**：
- `validate_file_format(file_path)`: 验证文件格式
- `read_document(file_path)`: 读取文档内容
- `save_presentation_data(data, output_dir)`: 保存演示文稿数据
- `save_narration_text(data, output_dir)`: 保存旁白文本
- `format_file_size(size_bytes)`: 格式化文件大小

### AI提供者

#### `AIProvider` (抽象基类)

```python
from providers.base_provider import AIProvider

# 自定义提供者需要实现的方法
class CustomProvider(AIProvider):
    async def parse_document(self, content: str, context: dict = None) -> List[DocumentSection]:
        # 文档解析实现
        pass

    async def generate_slide_content(self, section: DocumentSection, context: dict = None) -> SlideContent:
        # 幻灯片生成实现
        pass

    async def evaluate_slide_quality(self, slide: SlideContent, section: DocumentSection, threshold: float) -> QualityScore:
        # 质量评估实现
        pass

    async def optimize_slide_content(self, slide: SlideContent, quality_score: QualityScore, section: DocumentSection) -> SlideContent:
        # 内容优化实现
        pass

    async def generate_narration(self, slide: SlideContent, context: dict = None) -> str:
        # 旁白生成实现
        pass

    async def generate_speaker_script(self, slides: List[SlideContent], context: dict = None) -> str:
        # 演讲稿生成实现
        pass
```

#### `ProviderRouter`

提供者路由管理。

```python
from providers.provider_factory import ProviderRouter

router = ProviderRouter()

# 获取当前提供者
provider = router.get_provider()

# 检查提供者健康状态
health = router.check_provider_health("openai")

# 切换提供者
router.switch_provider("gemini")
```

## 输出格式

### JSON输出

#### `presentation.json`
```json
{
  "slides": [
    {
      "title": "幻灯片标题",
      "bullet_points": ["要点1", "要点2"],
      "speaker_notes": "演讲者备注",
      "slide_number": 1,
      "section_reference": "原始章节标题",
      "narration": "旁白文本"
    }
  ],
  "speaker_script": "完整演讲稿...",
  "generation_summary": {
    "total_slides": 5,
    "overall_quality_score": 0.85,
    "successful_slides": 5,
    "failed_slides": 0,
    "total_cost_usd": 0.0234
  }
}
```

#### `narration.txt`
```
现在我们来看人工智能在教育中的应用。

引言部分，人工智能正在深刻地改变着我们的世界...

接下来讲AI在教育中的主要应用...
```

#### `report.json`
```json
{
  "workflow_id": "uuid",
  "status": "completed",
  "processing_statistics": {
    "total_steps": 7,
    "completed_steps": 7,
    "total_duration": 45.2
  },
  "performance_metrics": {
    "success_rate": 1.0,
    "total_cost": 0.0234
  }
}
```

### 单独幻灯片文件

`slides/slide_01.json`, `slides/slide_02.json`, ...

每个文件包含单张幻灯片的完整信息。

## 错误代码

| 代码 | 说明 | 解决方案 |
|------|------|----------|
| `CONFIG_ERROR` | 配置错误 | 检查环境变量和配置文件 |
| `FILE_NOT_FOUND` | 文件不存在 | 确认文件路径正确 |
| `INVALID_FORMAT` | 不支持的文件格式 | 使用.md或.txt文件 |
| `API_ERROR` | AI服务API错误 | 检查API密钥和网络连接 |
| `QUALITY_THRESHOLD_NOT_MET` | 质量阈值未达到 | 降低质量阈值或增加重试次数 |
| `GENERATION_FAILED` | 生成失败 | 检查输入内容和服务状态 |

## 环境变量

| 变量名 | 说明 | 默认值 | 必需 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API密钥 | - | 是* |
| `GEMINI_API_KEY` | Gemini API密钥 | - | 是* |
| `DEFAULT_PROVIDER` | 默认AI提供者 | `openai` | 否 |
| `MAX_RETRIES` | 默认最大重试次数 | `3` | 否 |
| `QUALITY_THRESHOLD` | 默认质量阈值 | `0.8` | 否 |
| `DEFAULT_OUTPUT_DIR` | 默认输出目录 | `./output` | 否 |

*至少需要配置一个AI提供者的API密钥。