"""
PPT Agent Demo - 主入口文件

命令行界面，用于运行文档转PPT的工作流。
"""

import asyncio
import sys
import os
from pathlib import Path
import click
from rich.console import Console
from rich.progress import track
from rich.table import Table
from rich.panel import Panel

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from workflow.ppt_workflow import PPTWorkflow
from models.workflow import WorkflowConfiguration, WorkflowStatus
from utils.file_utils import FileUtils

console = Console()


@click.group()
def cli():
    """PPT Agent Demo - 智能文档转PPT工具"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='./output', help='输出目录')
@click.option('--provider', '-p', default='openai', type=click.Choice(['openai', 'gemini']), help='AI提供者')
@click.option('--max-retries', default=3, help='最大重试次数')
@click.option('--quality-threshold', default=0.8, type=float, help='质量阈值')
@click.option('--verbose', '-v', is_flag=True, help='显示详细日志')
def process(input_file, output, provider, max_retries, quality_threshold, verbose):
    """处理文档生成PPT演示文稿"""

    console.print(Panel.fit(
        "[bold blue]PPT Agent Demo[/bold blue]\n"
        "[dim]智能文档转PPT工具[/dim]",
        border_style="blue"
    ))

    # 验证输入文件
    if not FileUtils.validate_file_format(input_file):
        console.print("[red]错误: 不支持的文件格式。支持的格式: .txt, .md, .markdown[/red]")
        return

    # 创建配置
    config = WorkflowConfiguration(
        ai_provider=provider,
        max_retries=max_retries,
        quality_threshold=quality_threshold
    )

    # 显示配置信息
    if verbose:
        config_table = Table(title="配置信息")
        config_table.add_column("配置项", style="cyan")
        config_table.add_column("值", style="magenta")

        config_table.add_row("输入文件", input_file)
        config_table.add_row("输出目录", output)
        config_table.add_row("AI提供者", provider)
        config_table.add_row("最大重试次数", str(max_retries))
        config_table.add_row("质量阈值", str(quality_threshold))

        console.print(config_table)
        console.print()

    # 运行工作流
    try:
        result = asyncio.run(run_workflow(input_file, output, config, verbose))

        if result.is_successful:
            console.print("[green]✅ 处理完成！[/green]")
            display_results(result, verbose)
        else:
            console.print("[red]❌ 处理失败[/red]")
            display_errors(result)

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ 用户中断操作[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ 发生错误: {e}[/red]")


async def run_workflow(input_file, output_dir, config, verbose):
    """运行工作流"""
    workflow = PPTWorkflow(config)

    with console.status("[bold green]正在处理文档...") as status:
        if verbose:
            console.print(f"[dim]开始处理文件: {input_file}[/dim]")

        result = await workflow.process_document(
            input_file_path=input_file,
            output_directory=output_dir,
            workflow_config=config
        )

    return result


def display_results(result, verbose=False):
    """显示处理结果"""
    # 基本结果信息
    result_table = Table(title="处理结果", show_header=False)
    result_table.add_column("项目", style="cyan")
    result_table.add_column("值", style="green")

    if result.presentation_data:
        result_table.add_row("成功生成幻灯片", f"{result.presentation_data.total_slides} 张")
        result_table.add_row("成功率", f"{result.presentation_data.success_rate:.1%}")
        result_table.add_row("质量评分", f"{result.presentation_data.generation_summary.overall_quality_score:.2f}")

    if result.narration_data:
        result_table.add_row("旁白时长", f"{result.narration_data.total_duration:.1f} 秒")

    if result.total_duration:
        result_table.add_row("处理时间", f"{result.total_duration:.2f} 秒")

    result_table.add_row("总成本", f"${result.total_cost:.4f}")

    console.print(result_table)

    # 输出文件信息
    if result.output_files:
        console.print("\n[bold cyan]输出文件:[/bold cyan]")
        for file_type, file_path in result.output_files.items():
            if isinstance(file_path, list):
                console.print(f"  📁 {file_type}: {len(file_path)} 个文件")
            else:
                console.print(f"  📄 {file_type}: {file_path}")

    # 详细信息
    if verbose and result.processing_statistics:
        stats_table = Table(title="详细统计")
        stats_table.add_column("统计项", style="cyan")
        stats_table.add_column("值", style="white")

        stats = result.processing_statistics
        stats_table.add_row("总步骤数", str(stats.get('total_steps', 0)))
        stats_table.add_row("完成步骤", str(stats.get('completed_steps', 0)))
        stats_table.add_row("失败步骤", str(stats.get('failed_steps', 0)))

        if 'ai_provider_stats' in stats:
            provider_stats = stats['ai_provider_stats']
            stats_table.add_row("API调用次数", str(provider_stats.get('total_requests', 0)))
            stats_table.add_row("API成功率", f"{provider_stats.get('success_rate', 0):.1%}")

        console.print(stats_table)


def display_errors(result):
    """显示错误信息"""
    if result.errors:
        console.print("\n[bold red]错误详情:[/bold red]")
        for error in result.errors:
            console.print(f"  🔸 {error.get('step', '未知')}: {error.get('error_message', '未知错误')}")

    if result.warnings:
        console.print("\n[bold yellow]警告信息:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  🔸 {warning}")


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
def validate(input_file):
    """验证文档格式和内容"""
    console.print(f"[cyan]验证文件: {input_file}[/cyan]")

    # 检查文件格式
    if not FileUtils.validate_file_format(input_file):
        console.print("[red]❌ 不支持的文件格式[/red]")
        return

    try:
        # 读取文件
        content, file_type = FileUtils.read_document(input_file)

        # 显示基本信息
        info_table = Table(title="文件信息")
        info_table.add_column("属性", style="cyan")
        info_table.add_column("值", style="white")

        info_table.add_row("文件类型", file_type)
        info_table.add_row("文件大小", FileUtils.format_file_size(len(content.encode('utf-8'))))
        info_table.add_row("字符数", str(len(content)))
        info_table.add_row("行数", str(len(content.split('\n'))))
        info_table.add_row("词数", str(len(content.split())))

        console.print(info_table)
        console.print("[green]✅ 文件格式有效，可以处理[/green]")

    except Exception as e:
        console.print(f"[red]❌ 文件验证失败: {e}[/red]")


@cli.command()
def info():
    """显示系统信息和配置"""
    console.print(Panel.fit(
        "[bold blue]PPT Agent Demo 系统信息[/bold blue]",
        border_style="blue"
    ))

    # 环境变量检查
    env_table = Table(title="环境配置")
    env_table.add_column("配置项", style="cyan")
    env_table.add_column("状态", style="white")

    # 检查API密钥
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    env_table.add_row("OpenAI API Key", "✅ 已配置" if openai_key else "❌ 未配置")
    env_table.add_row("Gemini API Key", "✅ 已配置" if gemini_key else "❌ 未配置")
    env_table.add_row("默认提供者", os.getenv('DEFAULT_PROVIDER', 'openai'))

    console.print(env_table)

    # 支持的格式
    formats_table = Table(title="支持的文件格式")
    formats_table.add_column("格式", style="cyan")
    formats_table.add_column("扩展名", style="white")

    formats_table.add_row("Markdown", ".md, .markdown")
    formats_table.add_row("纯文本", ".txt")

    console.print(formats_table)


@cli.command()
@click.argument('output_dir', type=click.Path())
def clean(output_dir):
    """清理输出目录"""
    output_path = Path(output_dir)

    if not output_path.exists():
        console.print(f"[yellow]目录不存在: {output_dir}[/yellow]")
        return

    if not output_path.is_dir():
        console.print(f"[red]路径不是目录: {output_dir}[/red]")
        return

    # 确认清理
    if click.confirm(f"确定要清理目录 {output_dir} 吗？"):
        try:
            import shutil
            shutil.rmtree(output_path)
            console.print(f"[green]✅ 已清理目录: {output_dir}[/green]")
        except Exception as e:
            console.print(f"[red]❌ 清理失败: {e}[/red]")


if __name__ == '__main__':
    cli()