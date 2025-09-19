# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

PPT Agent Demo是一个基于LangGraph的智能文档转PPT演示文稿生成工具。项目采用状态机工作流架构，支持Markdown和文本文档的智能解析，并通过AI生成高质量的演示文稿内容和旁白文本。

## 核心架构

### LangGraph工作流系统
项目使用LangGraph构建状态机工作流，实现复杂的AI处理流程：
- **工作流节点链**: `document_parsing → quality_check → slide_generation → quality_evaluation → optimization → narration_generation`
- **条件分支**: 支持质量评估后的优化决策和重试机制
- **状态管理**: 通过`WorkflowState`统一管理处理状态和数据流

### AI提供者架构
采用工厂模式管理多AI提供者：
- **ProviderFactory**: 统一的AI提供者创建和配置管理
- **提供者实现**: OpenAI Provider、Gemini Provider
- **路由系统**: ProviderRouter支持智能路由和故障转移

### 数据模型设计
- **文档模型** (`models/document.py`): 处理文档解析和章节结构化
- **幻灯片模型** (`models/slide.py`): 管理演示文稿数据和生成元数据
- **工作流模型** (`models/workflow.py`): 定义工作流状态、配置和错误处理

## 开发命令

### 环境配置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置 OPENAI_API_KEY, GEMINI_API_KEY
```

### 基本使用
```bash
# 处理文档
python main.py process sample_docs/sample1.md

# 指定输出目录和AI提供者
python main.py process sample_docs/sample1.md --output ./my_output --provider openai

# 详细模式
python main.py process sample_docs/sample1.md --verbose

# 自定义质量阈值和重试次数
python main.py process sample_docs/sample1.md --quality-threshold 0.9 --max-retries 5
```

### 验证和诊断
```bash
# 验证文档格式
python main.py validate sample_docs/sample1.md

# 系统信息检查
python main.py info

# 清理输出目录
python main.py clean ./output
```

### 测试和调试
```bash
# 基础功能测试（使用sample文档验证完整流程）
python main.py process sample_docs/sample1.md --verbose

# 测试不同AI提供者
python main.py process sample_docs/sample1.md --provider openai
python main.py process sample_docs/sample1.md --provider gemini

# 文档格式验证
python main.py validate sample_docs/sample1.md
python main.py validate sample_docs/sample2.txt
```

## 关键实现细节

### 工作流节点系统
工作流节点位于`workflow/nodes/`目录，每个节点负责特定的处理任务：
- **DocumentParserNode**: 文档解析和结构化
- **SlideGeneratorNode**: AI驱动的幻灯片内容生成
- **QualityEvaluatorNode**: 多维度质量评估
- **NarrationGeneratorNode**: 演讲旁白文本生成

### 质量控制循环
系统实现自动质量控制机制：
1. 生成内容后进行质量评估
2. 低于阈值时触发优化流程
3. 支持多次重试和智能回退
4. 质量评估包括准确性、连贯性、清晰度、完整性四个维度

### 配置管理
通过`WorkflowConfiguration`和环境变量管理所有配置：
- AI提供者选择和模型配置
- 质量阈值和重试策略
- 文档处理选项
- 输出格式设置

### 错误处理策略
分层错误处理机制：
- **节点级**: 单个处理步骤的错误捕获和重试
- **工作流级**: 整体流程的异常处理和状态恢复
- **用户级**: 友好的错误信息展示和诊断建议

## 输出格式

处理完成后生成以下文件：
- `presentation.json`: 完整的演示文稿数据（幻灯片内容、元数据）
- `narration.txt`: 完整的演讲旁白文本
- `slides/`: 单独的幻灯片文件目录
- `report.json`: 处理报告和统计信息（API调用次数、成本、质量评分等）

## 环境变量配置

必需的环境变量：
- `OPENAI_API_KEY`: OpenAI API密钥
- `GEMINI_API_KEY`: Google Gemini API密钥

可选配置：
- `DEFAULT_PROVIDER`: 默认AI提供者（openai/gemini）
- `OPENAI_MODEL`: OpenAI模型（默认gpt-4）
- `GEMINI_MODEL`: Gemini模型（默认gemini-pro）
- `QUALITY_THRESHOLD`: 质量阈值（默认0.8）
- `MAX_RETRIES`: 最大重试次数（默认3）

## 项目结构模式

遵循以下组织模式：
- **单一入口**: `main.py`提供统一的CLI界面
- **功能分离**: workflow、models、providers、utils分别管理不同职责
- **配置集中**: 环境变量和配置文件统一管理
- **样例驱动**: `sample_docs/`提供测试文档

## 与主项目的关系

这是主项目的简化版本，主要差异：
- **去除复杂度**: 无Redis/Celery、Docker、监控系统
- **保留核心**: AI生成、质量控制、多提供者支持
- **添加LangGraph**: 使用状态机替代传统任务队列
- **仅文本输出**: 无音频合成功能

适用场景：快速验证、原型开发、算法研究、技术演示。