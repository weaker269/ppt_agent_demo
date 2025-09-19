# 开发指南

## 开发环境设置

### 系统要求

- Python 3.8+
- 支持async/await的环境
- 网络连接（用于AI服务API调用）

### 快速设置

```bash
# 1. 克隆项目
git clone <repository-url>
cd ppt_agent/demo

# 2. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
# 编辑 .env 文件，添加API密钥

# 5. 验证安装
python main.py info
```

### 依赖说明

#### 核心依赖
- **langgraph**: LangChain的图形工作流框架
- **langchain**: LangChain核心库
- **openai**: OpenAI API客户端
- **google-generativeai**: Google Gemini API客户端

#### 开发工具
- **pydantic**: 数据验证和序列化
- **click**: 命令行界面框架
- **rich**: 命令行输出美化
- **python-dotenv**: 环境变量管理

## 项目结构详解

```
demo/
├── docs/                    # 文档目录
│   ├── ARCHITECTURE.md      # 架构设计文档
│   ├── API_REFERENCE.md     # API参考
│   └── DEVELOPMENT.md       # 开发指南
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── document.py          # 文档相关模型
│   ├── slide.py            # 幻灯片相关模型
│   └── workflow.py         # 工作流相关模型
├── providers/              # AI提供者
│   ├── __init__.py
│   ├── base_provider.py    # 抽象基类
│   ├── openai_provider.py  # OpenAI实现
│   ├── gemini_provider.py  # Gemini实现
│   └── provider_factory.py # 提供者工厂
├── utils/                  # 工具函数
│   ├── __init__.py
│   └── file_utils.py       # 文件处理工具
├── workflow/               # LangGraph工作流
│   ├── nodes/              # 工作流节点
│   │   ├── __init__.py
│   │   ├── document_parser.py      # 文档解析
│   │   ├── slide_generator.py      # 幻灯片生成
│   │   ├── quality_evaluator.py    # 质量评估
│   │   └── narration_generator.py  # 旁白生成
│   ├── __init__.py
│   └── ppt_workflow.py     # 主工作流定义
├── sample_docs/            # 示例文档
│   ├── sample1.md
│   └── sample2.txt
├── .env.example           # 环境变量模板
├── requirements.txt       # Python依赖
├── main.py               # 命令行入口
├── README.md             # 项目说明
└── QUICK_START.md        # 快速开始指南
```

## 开发流程

### 1. 添加新的AI提供者

#### 步骤1：实现提供者类

```python
# providers/new_provider.py
from typing import List, Dict, Any
from .base_provider import AIProvider
from ..models.document import DocumentSection
from ..models.slide import SlideContent, QualityScore

class NewProvider(AIProvider):
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.client = NewProviderClient(api_key)

    async def parse_document(self, content: str, context: Dict[str, Any] = None) -> List[DocumentSection]:
        # 实现文档解析逻辑
        pass

    async def generate_slide_content(self, section: DocumentSection, context: Dict[str, Any] = None) -> SlideContent:
        # 实现幻灯片生成逻辑
        pass

    # ... 实现其他必需方法
```

#### 步骤2：注册提供者

```python
# providers/provider_factory.py
from .new_provider import NewProvider

class ProviderRouter:
    def __init__(self):
        self.providers = {
            'openai': OpenAIProvider,
            'gemini': GeminiProvider,
            'new_provider': NewProvider,  # 添加新提供者
        }
```

#### 步骤3：添加配置

```bash
# .env
NEW_PROVIDER_API_KEY=your_api_key_here
```

#### 步骤4：更新CLI选项

```python
# main.py
@click.option('--provider', '-p',
              default='openai',
              type=click.Choice(['openai', 'gemini', 'new_provider']),  # 添加新选项
              help='AI提供者')
```

### 2. 扩展工作流节点

#### 添加新的处理节点

```python
# workflow/nodes/new_node.py
from typing import Dict, Any
from ...models.workflow import WorkflowState

async def new_processing_node(state: WorkflowState) -> Dict[str, Any]:
    """
    新的处理节点

    Args:
        state: 当前工作流状态

    Returns:
        Dict: 更新的状态数据
    """
    # 实现处理逻辑
    result = process_data(state.current_data)

    return {
        "processed_data": result,
        "current_step": "new_processing",
        "processing_status": "completed"
    }
```

#### 在工作流中集成

```python
# workflow/ppt_workflow.py
from .nodes.new_node import new_processing_node

def create_workflow(self) -> StateGraph:
    workflow = StateGraph(WorkflowState)

    # 添加现有节点...
    workflow.add_node("new_processing", new_processing_node)

    # 添加边
    workflow.add_edge("previous_step", "new_processing")
    workflow.add_edge("new_processing", "next_step")

    return workflow
```

### 3. 修改数据模型

#### 扩展现有模型

```python
# models/slide.py
from pydantic import BaseModel, Field
from typing import List, Optional

class SlideContent(BaseModel):
    title: str
    bullet_points: List[str]
    speaker_notes: str
    slide_number: int
    section_reference: str

    # 添加新字段
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    estimated_duration: Optional[float] = None
```

#### 版本兼容性

使用Pydantic的字段默认值确保向后兼容：

```python
class SlideContent(BaseModel):
    # 现有字段...

    # 新字段使用默认值
    new_field: Optional[str] = None

    # 或使用Field指定默认值
    another_field: List[str] = Field(default_factory=list)
```

## 测试

### 单元测试

创建测试文件：

```python
# tests/test_providers.py
import pytest
from unittest.mock import AsyncMock
from providers.openai_provider import OpenAIProvider

@pytest.mark.asyncio
async def test_openai_provider_document_parsing():
    provider = OpenAIProvider(api_key="test_key")
    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    content = "# Test\nContent here"
    sections = await provider.parse_document(content)

    assert len(sections) > 0
    assert sections[0].title == "Test"
```

### 集成测试

```python
# tests/test_workflow.py
import pytest
from workflow.ppt_workflow import PPTWorkflow
from models.workflow import WorkflowConfiguration

@pytest.mark.asyncio
async def test_complete_workflow():
    config = WorkflowConfiguration(ai_provider="openai")
    workflow = PPTWorkflow(config)

    # 使用测试文档
    result = await workflow.process_document(
        "tests/fixtures/test_document.md",
        "./test_output",
        config
    )

    assert result.is_successful
    assert len(result.presentation_data.slides) > 0
```

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_providers.py

# 运行带覆盖率报告
pip install pytest-cov
pytest --cov=./ --cov-report=html
```

## 调试技巧

### 1. 日志配置

```python
import logging

# 在main.py或工作流中添加
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 在需要调试的地方
logger = logging.getLogger(__name__)
logger.debug(f"Processing section: {section.title}")
```

### 2. 工作流状态检查

```python
# 在工作流节点中添加状态输出
async def debug_node(state: WorkflowState) -> Dict[str, Any]:
    print(f"Current state: {state}")
    print(f"Current step: {state.current_step}")
    print(f"Document sections: {len(state.document_sections)}")
    return {}
```

### 3. API调用调试

```python
# 在提供者中添加请求/响应日志
async def generate_slide_content(self, section, context=None):
    logger.debug(f"Generating slide for: {section.title}")

    try:
        response = await self.client.chat.completions.create(...)
        logger.debug(f"API response: {response}")
        return result
    except Exception as e:
        logger.error(f"API call failed: {e}")
        raise
```

### 4. 使用pdb调试

```python
import pdb

async def problematic_function():
    pdb.set_trace()  # 设置断点
    # 调试代码...
```

## 性能优化

### 1. 异步并行处理

```python
import asyncio

# 并行处理多个章节
async def process_sections_parallel(sections: List[DocumentSection]):
    tasks = [process_single_section(section) for section in sections]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 2. 缓存机制

```python
from functools import lru_cache

class DocumentParser:
    @lru_cache(maxsize=128)
    def parse_cached(self, content_hash: str, content: str):
        # 基于内容哈希的缓存
        return self._parse_content(content)
```

### 3. 资源管理

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def ai_provider_context():
    provider = create_provider()
    try:
        await provider.connect()
        yield provider
    finally:
        await provider.close()
```

## 代码规范

### 1. 类型注解

```python
from typing import List, Dict, Optional, Union

async def process_document(
    content: str,
    options: Optional[Dict[str, Any]] = None
) -> List[DocumentSection]:
    """处理文档内容"""
    pass
```

### 2. 错误处理

```python
class PPTAgentError(Exception):
    """基础异常类"""
    pass

class DocumentParsingError(PPTAgentError):
    """文档解析错误"""
    pass

class SlideGenerationError(PPTAgentError):
    """幻灯片生成错误"""
    pass

# 使用具体的异常类型
try:
    sections = await parser.parse_document(content)
except DocumentParsingError as e:
    logger.error(f"Document parsing failed: {e}")
    raise
```

### 3. 配置验证

```python
from pydantic import BaseModel, validator

class ProviderConfig(BaseModel):
    api_key: str
    model: str = "gpt-4"
    timeout: int = 30

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid API key')
        return v
```

## 部署考虑

### 1. 环境变量管理

```bash
# 生产环境配置
OPENAI_API_KEY=prod_key_here
DEFAULT_PROVIDER=openai
QUALITY_THRESHOLD=0.9
MAX_RETRIES=5
ENABLE_DETAILED_LOGGING=true
```

### 2. 错误监控

```python
import sentry_sdk

# 初始化错误追踪
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=1.0
)
```

### 3. 资源限制

```python
# 限制并发请求数
SEMAPHORE = asyncio.Semaphore(5)

async def rate_limited_api_call():
    async with SEMAPHORE:
        return await make_api_call()
```

## 贡献指南

### 提交PR前检查

1. 代码通过所有测试
2. 添加适当的文档
3. 遵循代码规范
4. 更新相关配置文件

### 提交信息格式

```
feat: 添加新的AI提供者支持
fix: 修复文档解析边缘情况
docs: 更新API文档
test: 添加工作流集成测试
```

### 发布流程

1. 更新版本号
2. 更新CHANGELOG
3. 创建release tag
4. 构建和测试
5. 发布到仓库