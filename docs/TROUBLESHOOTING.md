# 故障排除指南

## 常见问题与解决方案

### 1. 环境配置问题

#### 问题：`ModuleNotFoundError: No module named 'xxx'`

**症状**：
```bash
ModuleNotFoundError: No module named 'langgraph'
ModuleNotFoundError: No module named 'rich'
```

**原因**：依赖包未安装或虚拟环境未激活

**解决方案**：
```bash
# 1. 确认虚拟环境已激活
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 2. 重新安装依赖
pip install -r requirements.txt

# 3. 验证安装
pip list | grep langgraph
```

#### 问题：`ValueError: OpenAI API密钥未配置`

**症状**：
```
ValueError: OpenAI API key not configured
```

**原因**：环境变量未正确设置

**解决方案**：
```bash
# 1. 检查环境变量文件
cat .env

# 2. 确保API密钥格式正确
OPENAI_API_KEY=sk-...（至少51个字符）
GEMINI_API_KEY=AI...（以AI开头）

# 3. 验证配置
python main.py info
```

#### 问题：`ImportError: cannot import name 'xxx' from 'yyy'`

**症状**：
```
ImportError: cannot import name 'StateGraph' from 'langgraph'
```

**原因**：包版本不兼容

**解决方案**：
```bash
# 1. 检查包版本
pip show langgraph

# 2. 升级到最新版本
pip install --upgrade langgraph

# 3. 如果仍有问题，重新安装
pip uninstall langgraph
pip install langgraph>=0.1.0
```

### 2. API调用问题

#### 问题：`OpenAI API调用失败`

**症状**：
```
openai.RateLimitError: Rate limit exceeded
openai.AuthenticationError: Invalid API key
openai.BadRequestError: Invalid request
```

**诊断步骤**：
```bash
# 1. 检查API密钥有效性
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# 2. 检查余额（如果有web界面）
# 访问 https://platform.openai.com/account/billing

# 3. 测试简单请求
python -c "
import openai
client = openai.OpenAI()
print(client.models.list())
"
```

**解决方案**：
- **Rate limit exceeded**: 降低并发数或添加重试延迟
- **Invalid API key**: 检查密钥格式和有效性
- **Insufficient credits**: 充值账户或切换提供者

#### 问题：`Gemini API调用失败`

**症状**：
```
google.api_core.exceptions.PermissionDenied
google.api_core.exceptions.ResourceExhausted
```

**解决方案**：
```bash
# 1. 验证Gemini API密钥
export GEMINI_API_KEY="your_key_here"
python -c "
import google.generativeai as genai
genai.configure(api_key='$GEMINI_API_KEY')
print(genai.list_models())
"

# 2. 检查API配额和限制
# 访问 Google AI Studio

# 3. 切换到OpenAI提供者
python main.py process sample1.md --provider openai
```

### 3. 文档处理问题

#### 问题：`UnicodeDecodeError`

**症状**：
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff
```

**原因**：文件编码不是UTF-8

**解决方案**：
```bash
# 1. 检查文件编码
file -i document.md

# 2. 转换为UTF-8
iconv -f GBK -t UTF-8 document.md > document_utf8.md

# 3. 或在Windows上使用记事本另存为UTF-8
```

#### 问题：文档解析结果为空

**症状**：
```
生成了 0 张幻灯片
Document parsing returned empty sections
```

**原因**：文档格式不符合预期

**诊断步骤**：
```bash
# 1. 验证文档格式
python main.py validate document.md

# 2. 检查文档内容结构
head -20 document.md

# 3. 查看详细日志
python main.py process document.md --verbose
```

**解决方案**：
- 确保文档有明确的标题结构（# ## ###）
- 每个章节有足够的内容（至少50字符）
- 避免纯代码或表格内容

### 4. 质量控制问题

#### 问题：质量评估失败，反复重试

**症状**：
```
Quality evaluation failed, retrying...
Max retries exceeded, using fallback content
```

**原因**：
- AI服务不稳定
- 质量阈值设置过高
- 文档内容质量问题

**解决方案**：
```bash
# 1. 降低质量阈值
python main.py process document.md --quality-threshold 0.6

# 2. 增加重试次数
python main.py process document.md --max-retries 5

# 3. 检查文档内容质量
python main.py validate document.md

# 4. 临时禁用质量控制
# 编辑 .env 文件
ENABLE_QUALITY_CONTROL=false
```

#### 问题：生成内容质量不佳

**症状**：
- 幻灯片内容过于简单
- 要点重复或不相关
- 旁白文本质量差

**解决方案**：
```bash
# 1. 使用更好的AI模型
# 在 .env 中设置
OPENAI_MODEL=gpt-4
GEMINI_MODEL=gemini-pro

# 2. 改善输入文档质量
# - 增加详细描述
# - 明确章节结构
# - 提供更多上下文

# 3. 调整生成参数
python main.py process document.md \
    --quality-threshold 0.85 \
    --max-retries 3 \
    --provider openai
```

### 5. 性能问题

#### 问题：处理速度过慢

**症状**：
```
处理时间超过5分钟
单个幻灯片生成耗时过长
```

**诊断步骤**：
```bash
# 1. 使用verbose模式查看瓶颈
python main.py process document.md --verbose

# 2. 检查网络连接
ping api.openai.com
curl -w "@curl-format.txt" https://api.openai.com/v1/models

# 3. 监控资源使用
top -p $(pgrep python)
```

**解决方案**：
```python
# 1. 启用并行处理（在代码中已默认启用）
# 检查 workflow/nodes/slide_generator.py 中的并行逻辑

# 2. 减少API调用次数
# 在 .env 中设置
ENABLE_QUALITY_CONTROL=false

# 3. 使用更快的模型
OPENAI_MODEL=gpt-3.5-turbo
```

#### 问题：内存使用过高

**症状**：
```
MemoryError
系统内存占用过高
```

**解决方案**：
```python
# 1. 分批处理大文档
# 在 workflow/nodes/document_parser.py 中限制章节数量

# 2. 清理缓存
import gc
gc.collect()

# 3. 优化数据结构
# 使用生成器而不是列表
```

### 6. 输出问题

#### 问题：输出文件生成失败

**症状**：
```
PermissionError: [Errno 13] Permission denied
FileNotFoundError: [Errno 2] No such file or directory
```

**解决方案**：
```bash
# 1. 检查输出目录权限
ls -la ./output/
chmod 755 ./output/

# 2. 创建输出目录
mkdir -p ./output

# 3. 指定不同的输出目录
python main.py process document.md --output ~/Documents/ppt_output
```

#### 问题：输出格式异常

**症状**：
- JSON文件格式错误
- 缺少必要字段
- 编码问题

**解决方案**：
```bash
# 1. 验证JSON格式
python -m json.tool output/presentation.json

# 2. 检查输出文件编码
file -i output/narration.txt

# 3. 查看详细错误信息
python main.py process document.md --verbose 2>&1 | tee debug.log
```

### 7. 网络问题

#### 问题：代理或防火墙阻止API调用

**症状**：
```
requests.exceptions.ConnectionError
ssl.SSLError
ProxyError
```

**解决方案**：
```bash
# 1. 配置代理（在 .env 中）
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080

# 2. 测试直接连接
curl https://api.openai.com/v1/models

# 3. 使用不同的网络环境
# 尝试手机热点或其他网络
```

## 诊断工具

### 1. 系统信息检查

```bash
# 运行内置诊断
python main.py info

# 检查Python环境
python --version
pip --version

# 检查依赖版本
pip list | grep -E "(langgraph|openai|google)"
```

### 2. 连接测试

```bash
# 创建测试脚本
cat > test_connection.py << 'EOF'
import asyncio
import os
from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider

async def test_providers():
    # 测试OpenAI
    if os.getenv('OPENAI_API_KEY'):
        openai_provider = OpenAIProvider(os.getenv('OPENAI_API_KEY'))
        try:
            result = await openai_provider.parse_document("# Test\nContent")
            print("✅ OpenAI连接正常")
        except Exception as e:
            print(f"❌ OpenAI连接失败: {e}")

    # 测试Gemini
    if os.getenv('GEMINI_API_KEY'):
        gemini_provider = GeminiProvider(os.getenv('GEMINI_API_KEY'))
        try:
            result = await gemini_provider.parse_document("# Test\nContent")
            print("✅ Gemini连接正常")
        except Exception as e:
            print(f"❌ Gemini连接失败: {e}")

asyncio.run(test_providers())
EOF

python test_connection.py
```

### 3. 日志分析

```bash
# 启用详细日志
export DEBUG=1
python main.py process document.md --verbose > debug.log 2>&1

# 分析错误模式
grep -i error debug.log
grep -i exception debug.log
grep -i timeout debug.log
```

## 性能调优

### 1. AI API优化

```python
# 在 providers/base_provider.py 中添加
class AIProvider:
    def __init__(self):
        self.request_timeout = 30      # API请求超时
        self.max_concurrent = 3        # 最大并发请求
        self.retry_delay = 1.0         # 重试延迟
```

### 2. 缓存配置

```python
# 添加简单缓存
import hashlib
import json
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_api_call(prompt_hash: str, prompt: str):
    # 基于prompt哈希的缓存
    return actual_api_call(prompt)
```

### 3. 资源监控

```bash
# 创建监控脚本
cat > monitor.py << 'EOF'
import psutil
import time

def monitor_process():
    process = psutil.Process()
    while True:
        print(f"CPU: {process.cpu_percent():.1f}%")
        print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        time.sleep(5)

monitor_process()
EOF
```

## 联系支持

如果以上解决方案都无法解决问题：

1. **收集信息**：
   - 运行 `python main.py info` 并保存输出
   - 保存完整的错误日志
   - 记录重现步骤

2. **检查文档**：
   - 查看 [API参考文档](API_REFERENCE.md)
   - 查看 [架构文档](ARCHITECTURE.md)
   - 查看 [开发指南](DEVELOPMENT.md)

3. **社区支持**：
   - 搜索已知问题
   - 提交详细的问题报告
   - 包含环境信息和错误日志

4. **调试模式**：
   ```bash
   # 启用最详细的调试输出
   export PYTHONPATH=.
   export DEBUG=1
   python -u main.py process document.md --verbose
   ```