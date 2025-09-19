# PPT Agent Demo - 快速开始指南

## 🚀 5分钟快速体验

### 1. 环境准备

```bash
# 进入demo目录
cd demo

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
```

### 2. 配置API密钥

编辑 `.env` 文件，添加你的API密钥：

```bash
# 至少配置其中一个
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# 设置默认提供者
DEFAULT_PROVIDER=openai  # 或 gemini
```

### 3. 运行demo

```bash
# 处理示例文档
python main.py process sample_docs/sample1.md

# 使用不同的AI提供者
python main.py process sample_docs/sample1.md --provider gemini

# 指定输出目录
python main.py process sample_docs/sample1.md --output ./my_output

# 显示详细信息
python main.py process sample_docs/sample1.md --verbose
```

### 4. 查看结果

处理完成后，检查输出目录：

```
output/
├── presentation.json     # 完整演示文稿数据
├── narration.txt        # 演讲旁白文本
├── slides/              # 单独的幻灯片文件
│   ├── slide_01.json
│   ├── slide_02.json
│   └── ...
└── report.json          # 处理报告
```

## 📋 命令参考

### 主要命令

```bash
# 处理文档
python main.py process <input_file> [options]

# 验证文档
python main.py validate <input_file>

# 显示系统信息
python main.py info

# 清理输出目录
python main.py clean <output_dir>
```

### 选项参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output, -o` | 输出目录 | `./output` |
| `--provider, -p` | AI提供者 | `openai` |
| `--max-retries` | 最大重试次数 | `3` |
| `--quality-threshold` | 质量阈值 | `0.8` |
| `--verbose, -v` | 显示详细日志 | `False` |

## 🔧 自定义文档

### 支持的格式

- **Markdown** (`.md`, `.markdown`)
- **纯文本** (`.txt`)

### 文档结构建议

为了获得最佳效果，建议文档具备以下结构：

```markdown
# 主标题

## 引言
介绍内容...

## 主要概念
### 概念1
详细说明...

### 概念2
详细说明...

## 应用场景
实际应用...

## 结论
总结内容...
```

### 最佳实践

1. **清晰的标题层次**：使用 `#`、`##`、`###` 标记标题
2. **适中的章节长度**：每个章节100-2000字符
3. **结构化内容**：使用列表、段落组织信息
4. **关键信息突出**：重要概念放在章节开头

## 🐛 常见问题

### API配置问题

**问题**：`ValueError: OpenAI API密钥未配置`

**解决**：
```bash
# 检查环境变量
python main.py info

# 确保.env文件中有正确的API密钥
OPENAI_API_KEY=sk-...
```

### 网络连接问题

**问题**：API调用失败

**解决**：
1. 检查网络连接
2. 验证API密钥有效性
3. 尝试切换AI提供者：`--provider gemini`

### 文档格式问题

**问题**：文档解析失败

**解决**：
1. 确保文件编码为UTF-8
2. 检查文档结构（标题、段落）
3. 使用验证命令：`python main.py validate your_file.md`

### 质量问题

**问题**：生成的幻灯片质量不佳

**解决**：
1. 调整质量阈值：`--quality-threshold 0.9`
2. 增加重试次数：`--max-retries 5`
3. 优化原始文档的结构和内容

## 📊 输出格式说明

### presentation.json

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
    "overall_quality_score": 0.85
  }
}
```

### narration.txt

```
现在我们来看人工智能在教育中的应用。

引言部分，人工智能正在深刻地改变着我们的世界...

接下来讲AI在教育中的主要应用...
```

### report.json

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

## 🎯 下一步

1. **尝试不同的文档**：用你自己的文档测试
2. **调整配置**：实验不同的质量阈值和重试次数
3. **比较AI提供者**：测试OpenAI vs Gemini的效果差异
4. **集成到项目**：将核心逻辑集成到你的应用中

## 💡 技术细节

如果你想了解更多技术实现细节，查看：

- `workflow/ppt_workflow.py` - LangGraph工作流定义
- `providers/` - AI服务提供者实现
- `models/` - 数据模型定义
- `workflow/nodes/` - 各个处理节点

## 🆘 获取帮助

如果遇到问题：

1. 查看详细日志：`--verbose`
2. 检查系统状态：`python main.py info`
3. 验证文档格式：`python main.py validate your_file.md`
4. 参考主项目文档：`../README.md`