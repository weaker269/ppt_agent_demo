# PPT Agent Demo - 精简化文档转PPT演示

这是一个精简化的demo项目，专注于验证文档解析→PPT生成→旁白文本的核心功能。使用LangGraph构建智能工作流，去除了生产级别的复杂度。

## 🎯 核心功能

- **智能文档解析**: 支持Markdown和文本文档的结构化解析
- **AI驱动的幻灯片生成**: 使用OpenAI/Gemini生成高质量幻灯片内容
- **质量控制循环**: 自动评估生成质量，不达标时重新生成
- **旁白文本生成**: 为每张幻灯片生成演讲旁白（无需音频合成）
- **LangGraph工作流**: 可视化的智能工作流，支持条件分支

## 🚀 快速开始

### 环境准备

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，添加你的API密钥
```

### 基础使用

```bash
# 处理示例文档
python main.py process sample_docs/sample1.md

# 指定输出目录
python main.py process sample_docs/sample1.md --output ./my_output

# 指定AI提供者
python main.py process sample_docs/sample1.md --provider openai
```

### Python API

```python
from workflow.ppt_workflow import PPTWorkflow

workflow = PPTWorkflow()
result = await workflow.process_document("path/to/document.md")
print(f"生成了 {len(result['slides'])} 张幻灯片")
```

## 📁 项目结构

```
demo/
├── README.md              # 项目说明
├── requirements.txt       # 依赖清单
├── .env.example          # 环境变量模板
├── main.py               # 主入口文件
├── workflow/             # LangGraph工作流
│   ├── __init__.py
│   ├── ppt_workflow.py   # 核心工作流定义
│   └── nodes/            # 工作流节点
│       ├── __init__.py
│       ├── document_parser.py    # 文档解析节点
│       ├── slide_generator.py    # 幻灯片生成节点
│       ├── quality_evaluator.py  # 质量评估节点
│       └── narration_generator.py # 旁白生成节点
├── models/               # 数据模型
│   ├── __init__.py
│   ├── document.py       # 文档相关模型
│   └── slide.py          # 幻灯片相关模型
├── providers/            # AI服务提供者
│   ├── __init__.py
│   ├── base_provider.py  # 基础提供者
│   ├── openai_provider.py
│   └── gemini_provider.py
├── utils/                # 工具函数
│   ├── __init__.py
│   └── file_utils.py     # 文件处理工具
├── output/               # 输出目录
└── sample_docs/          # 示例文档
    ├── sample1.md
    └── sample2.txt
```

## 🔄 工作流程

1. **文档解析**: 解析输入文档，提取章节结构和内容
2. **质量检查**: 验证解析结果的完整性和质量
3. **幻灯片生成**: 使用AI为每个章节生成幻灯片内容
4. **质量评估**: 评估生成的幻灯片质量，不达标时重新生成
5. **旁白生成**: 为每张幻灯片生成演讲旁白文本
6. **输出整合**: 生成最终的演示文稿文件

## 📊 输出格式

处理完成后，会在输出目录生成以下文件：

- `presentation.json`: 完整的演示文稿数据
- `narration.txt`: 完整的演讲旁白文本
- `slides/`: 单独的幻灯片文件目录
- `report.json`: 处理报告和统计信息

## 🔧 配置选项

### 环境变量

```bash
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Gemini配置
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro

# 默认设置
DEFAULT_PROVIDER=openai
MAX_RETRIES=3
QUALITY_THRESHOLD=0.8
```

### 命令行参数

- `--output`: 指定输出目录
- `--provider`: 指定AI提供者 (openai/gemini)
- `--max-retries`: 最大重试次数
- `--quality-threshold`: 质量阈值
- `--verbose`: 显示详细日志

## 🆚 相比主项目的简化

### 去除的复杂度
- ❌ Redis/Celery异步任务队列
- ❌ Docker容器化部署
- ❌ 监控和告警系统
- ❌ 成本追踪和预算控制
- ❌ 音频合成和TTS服务
- ❌ 复杂的错误恢复机制

### 保留的核心功能
- ✅ 智能文档解析
- ✅ AI驱动的内容生成
- ✅ 质量控制和优化
- ✅ 多AI提供者支持
- ✅ 结构化输出格式

## 🐛 故障排除

### 常见问题

1. **API密钥错误**: 检查 `.env` 文件中的API密钥是否正确
2. **网络连接问题**: 确保能够访问AI服务提供者的API
3. **文档格式不支持**: 目前只支持Markdown(.md)和纯文本(.txt)文件
4. **生成质量不佳**: 尝试调整质量阈值或使用不同的AI提供者

### 调试模式

```bash
python main.py process sample_docs/sample1.md --verbose
```

## 📚 文档

详细的文档位于 `docs/` 目录：

- **[架构设计](docs/ARCHITECTURE.md)**: 系统架构和组件详解
- **[API参考](docs/API_REFERENCE.md)**: 完整的API文档和使用示例
- **[开发指南](docs/DEVELOPMENT.md)**: 开发环境设置和扩展指南
- **[故障排除](docs/TROUBLESHOOTING.md)**: 常见问题和解决方案
- **[快速开始](QUICK_START.md)**: 5分钟快速体验指南

## 🎨 特性亮点

### LangGraph智能工作流
- 使用状态机模式管理复杂的AI处理流程
- 支持条件分支和错误恢复
- 可视化的工作流定义，易于理解和修改

### 质量控制系统
- 多维度质量评估（准确性、连贯性、清晰度、完整性）
- 自动质量优化循环
- 智能重试机制

### 多AI提供者支持
- 统一的AI提供者接口
- 智能路由和故障转移
- 灵活的配置管理

### 并行处理优化
- 多章节并行处理
- 异步API调用
- 资源使用优化

## 🚀 高级用法

### 批量处理
```bash
# 处理多个文档
for doc in docs/*.md; do
    python main.py process "$doc" --output "output/$(basename "$doc" .md)"
done
```

### 自定义配置
```python
from models.workflow import WorkflowConfiguration

# 高质量配置
config = WorkflowConfiguration(
    ai_provider="openai",
    quality_threshold=0.9,
    max_retries=5,
    enable_optimization=True
)

# 快速配置（降低质量要求）
config = WorkflowConfiguration(
    ai_provider="gemini",
    quality_threshold=0.6,
    max_retries=2,
    enable_optimization=False
)
```

### API集成示例
```python
import asyncio
from workflow.ppt_workflow import PPTWorkflow
from models.workflow import WorkflowConfiguration

async def generate_presentation(document_path):
    config = WorkflowConfiguration()
    workflow = PPTWorkflow(config)

    result = await workflow.process_document(
        input_file_path=document_path,
        output_directory="./output",
        workflow_config=config
    )

    if result.is_successful:
        print(f"✅ 成功生成 {result.presentation_data.total_slides} 张幻灯片")
        print(f"📊 平均质量评分: {result.presentation_data.generation_summary.overall_quality_score:.2f}")
        print(f"💰 总成本: ${result.total_cost:.4f}")
    else:
        print(f"❌ 生成失败: {result.errors}")

# 运行
asyncio.run(generate_presentation("document.md"))
```

## 🔍 性能指标

在标准硬件环境下的典型性能表现：

| 指标 | 数值 |
|------|------|
| 处理速度 | ~2分钟/5张幻灯片 |
| 并发处理 | 3个章节同时处理 |
| API成本 | ~$0.02/页 (GPT-4) |
| 内存使用 | <100MB |
| 质量评分 | 平均0.85+ |

## 🧪 测试

```bash
# 基础功能测试
python main.py validate sample_docs/sample1.md
python main.py info

# 完整流程测试
python main.py process sample_docs/sample1.md --verbose

# 不同提供者测试
python main.py process sample_docs/sample1.md --provider openai
python main.py process sample_docs/sample1.md --provider gemini
```

## 🔄 与主项目的关系

### 技术对比

| 特性 | 主项目 | Demo版本 |
|------|--------|----------|
| 工作流框架 | Celery + Redis | LangGraph |
| 数据存储 | PostgreSQL | 内存对象 |
| 音频合成 | ElevenLabs TTS | 仅文本旁白 |
| 容器化 | Docker Compose | 本地Python |
| 监控 | Prometheus + Grafana | 基础日志 |
| API服务 | FastAPI + 认证 | CLI命令 |
| 扩展性 | 生产级分布式 | 单机原型 |

### 迁移路径

1. **验证阶段**: 使用demo验证核心算法和质量
2. **原型阶段**: 在demo基础上快速迭代新功能
3. **生产阶段**: 将验证的功能集成到主项目

## 📝 开发说明

这个demo项目是从主项目中提取和简化的核心功能，主要用于：

1. **快速验证**: 测试文档转PPT的核心流程
2. **原型开发**: 为新功能开发提供轻量级测试平台
3. **学习参考**: 展示LangGraph在AI工作流中的应用
4. **技术演示**: 向客户或投资人展示核心能力
5. **算法研究**: 研究和优化AI生成算法

如果需要生产级别的功能（如音频合成、分布式处理等），请使用主项目。

## 🤝 贡献

欢迎提交问题和改进建议！请确保：

1. 代码符合项目规范
2. 添加适当的测试
3. 更新相关文档
4. 提供清晰的提交信息

## 📄 许可证

本项目采用与主项目相同的许可证。