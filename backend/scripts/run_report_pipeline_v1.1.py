import os
import subprocess
import sys
import glob
import pandas as pd
import re
import shutil

# Try to import matplotlib, provide guidance if it fails.
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def run_step(command, description, working_dir=None):
    """Runs a command as a subprocess and prints status."""
    print(f"--- {description} ---")
    try:
        process = subprocess.run(
            command,
            shell=True, # Use shell=True to handle commands like 'python3 script.py'
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=working_dir
        )
        # Print stdout only if it's not excessively long
        stdout_lines = process.stdout.splitlines()
        if len(stdout_lines) < 20:
            for line in stdout_lines:
                print(line)
        else:
            print(f"(输出内容过长，已省略... 共 {len(stdout_lines)} 行)")

        if process.stderr:
            print("Stderr:", process.stderr)
        print(f"✅ {description} 完成\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} 失败")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ 命令 '{command}' 未找到。请确保它在你的 PATH 中。")
        return False

def generate_market_chart(data_path, output_path, ticker):
    """Generates a market price chart from the given data."""
    print("--- 正在生成市场趋势图表 ---")
    if not MATPLOTLIB_AVAILABLE:
        print("⚠️ 跳过图表生成：缺少 `matplotlib` 库。")
        print("   请运行 'pip install matplotlib' 来安装绘图库。")
        return False
        
    try:
        df = pd.read_json(data_path)
        if 'close' not in df.columns:
            print("❌ market_data.json 文件格式不正确，缺少 'close' 列。")
            return False

        df = df.sort_index()

        # 1. 先设置绘图风格
        plt.style.use('seaborn-v0_8-whitegrid')

        # 2. 【核心修改】设置中文字体
        # 这是一个兼容列表，Matplotlib 会依次尝试，直到找到可用的字体
        # Windows: SimHei (黑体), Microsoft YaHei (微软雅黑)
        # Mac: Arial Unicode MS, PingFang HK, Heiti TC
        # Linux: WenQuanYi Micro Hei
        plt.rcParams['font.sans-serif'] = [
            'SimHei', 
            'Microsoft YaHei', 
            'Arial Unicode MS', 
            'PingFang HK', 
            'Heiti TC', 
            'WenQuanYi Micro Hei', 
            'sans-serif'
        ]
        # 解决负号显示为方块的问题
        plt.rcParams['axes.unicode_minus'] = False

        fig, ax = plt.subplots(figsize=(8, 4))
        
        ax.plot(df.index, df['close'], marker='.', linestyle='-', color='#003366', label='收盘价')

        title = f'{ticker} 近30日收盘价走势'
        ax.set_title(title, fontsize=15, weight='bold', pad=15)
        ax.set_ylabel('收盘价 (元)', fontsize=11)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        ax.set_xlabel('')
        ax.set_xticklabels([])
        ax.tick_params(axis='x', length=0)

        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        print(f"✅ 图表已保存至: {output_path}\n")
        return True
    except Exception as e:
        print(f"❌ 生成图表失败: {e}")
        import traceback
        traceback.print_exc() # 打印详细错误信息以便调试
        return False

def enhance_markdown_report(original_md_path, chart_image_name):
    """Injects the chart into the markdown report."""
    print(f"--- 正在增强 Markdown 报告 (注入图表) ---")
    try:
        with open(original_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 在“二级市场情况”部分插入图表
        if chart_image_name:
            chart_tag = f"\n\n![近30日收盘价走势]({chart_image_name})\n\n"
            # Use a regex to be more robust against small variations in the heading
            content = re.sub(r"(##\s*三、\s*二级市场情况)", rf"\1{chart_tag}", content)
        
        # 保存增强版文件
        enhanced_md_path = os.path.splitext(original_md_path)[0] + "_v1.1.md"
        with open(enhanced_md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 增强版 Markdown 已保存: {enhanced_md_path}\n")
        return enhanced_md_path
    except Exception as e:
        print(f"❌ 增强 Markdown 报告失败: {e}")
        return None

def main():
    """Main pipeline execution function."""
    # --- 配置路径 ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    report_dir = os.path.join(base_dir, "report")
    stock_analyzer_script = os.path.join(base_dir, "stock_analyzer.py")
    html_generator_script = os.path.join(report_dir, "generate_html_report.py")
    
    print("="*60)
    print("自动化投研报告生成流程 v1.1")
    print("="*60 + "\n")

    # --- 第1步: 运行股票分析脚本 ---
    if not run_step(f'python3 "{stock_analyzer_script}"', "第1步: 运行股票分析脚本"):
        sys.exit(1)

    # --- 查找最新生成的报告 ---
    list_of_md_files = glob.glob(os.path.join(report_dir, 'Report_*.md'))
    list_of_md_files = [f for f in list_of_md_files if '_v1.1' not in f]
    if not list_of_md_files:
        print("❌ 未找到由 stock_analyzer.py 生成的原始 Markdown 报告。")
        sys.exit(1)
    latest_md_file = max(list_of_md_files, key=os.path.getctime)
    print(f"ℹ️ 找到最新的原始报告: {os.path.basename(latest_md_file)}\n")
    
    ticker_match = re.search(r'Report_(.+?)_\d{8}\.md', os.path.basename(latest_md_file))
    ticker = ticker_match.group(1).replace('_', '.') if ticker_match else "Unknown Ticker"

    # --- 第2步: 生成图表 ---
    market_data_path = os.path.join(report_dir, "market_data.json")
    chart_output_path = os.path.join(report_dir, "market_chart_v1.1.png")
    chart_generated = generate_market_chart(market_data_path, chart_output_path, ticker)

    # --- 第3步: 增强 Markdown 报告 ---
    chart_filename = os.path.basename(chart_output_path) if chart_generated else None
    enhanced_md_path = enhance_markdown_report(latest_md_file, chart_filename)
    if not enhanced_md_path:
        sys.exit(1)

    # --- 第4步: 转换增强版报告为 HTML ---
    html_command = f'python3 generate_html_report.py "{os.path.basename(enhanced_md_path)}"'
    if not run_step(html_command, "第4步: 转换增强版报告为 HTML", working_dir=report_dir):
        sys.exit(1)
        
    # --- 第5步: 移动 HTML 报告到 generated_reports ---
    print("--- 正在移动报告文件 ---")
    generated_reports_dir = os.path.join(base_dir, "..", "generated_reports")
    os.makedirs(generated_reports_dir, exist_ok=True)
    
    # 查找最新生成的 HTML (在 report_dir 中)
    list_of_htmls = glob.glob(os.path.join(report_dir, '*.html'))
    if list_of_htmls:
        latest_html = max(list_of_htmls, key=os.path.getctime)
        dest_path = os.path.join(generated_reports_dir, os.path.basename(latest_html))
        shutil.copy2(latest_html, dest_path)
        print(f"✅ 报告已移动至: {dest_path}\n")
    else:
        print("❌ 未在 report 目录找到生成的 HTML 文件。")
        sys.exit(1)

    print("="*60)
    print("🎉 全部流程执行完毕！")
    print("="*60)

if __name__ == "__main__":
    main()
