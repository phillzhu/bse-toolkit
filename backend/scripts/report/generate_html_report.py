import markdown
from jinja2 import Template
import datetime
import os
import glob

# ==========================================
# 1. HTML/CSS 模板 (专业投研风格)
# ==========================================
html_template_string = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{{ meta.title }}</title>
    <style>
        /* --- 全局字体与排版 --- */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Roboto:wght@300;400;700&display=swap');

        :root {
            --primary-color: #003366; /* 投行深蓝 */
            --accent-color: #c5a065;  /* 金色点缀 */
            --text-color: #333333;
            --bg-color: #ffffff;
            --light-gray: #f4f4f4;
        }

        body {
            font-family: "Roboto", "Noto Serif SC", serif;
            color: var(--text-color);
            background-color: #eef2f5; /* 屏幕阅读时的背景色 */
            margin: 0;
            padding: 20px;
            line-height: 1.6;
            -webkit-print-color-adjust: exact;
        }

        /* --- 纸张模拟 (A4) --- */
        .page {
            background: white;
            width: 210mm;
            min-height: 297mm;
            margin: 0 auto 20px auto;
            padding: 20mm;
            box-sizing: border-box;
            box-shadow: 0 0 15px rgba(0,0,0,0.1);
            position: relative;
        }

        /* --- 封面样式 --- */
        .cover-page {
            display: flex;
            flex-direction: column;
            justify-content: center;
            text-align: center;
            height: 250mm; /* 给页脚留空间 */
            border-bottom: 2px solid var(--primary-color);
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: var(--primary-color);
            margin-bottom: 40px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        h1.report-title {
            font-size: 36px;
            color: var(--primary-color);
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 20px;
            color: #666;
            font-weight: 300;
            margin-bottom: 60px;
        }

        .meta-info {
            margin-top: auto;
            font-size: 14px;
            color: #555;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            width: 100%;
        }

        /* --- 正文样式 --- */
        .content {
            margin-top: 20px;
            text-align: justify;
        }

        .content img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1.5em auto;
        }
        
        .content h1, .content h2, .content h3, .content h4 {
             page-break-after: avoid;
        }

        .content h1 {
            font-size: 24px;
            color: var(--primary-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 10px;
            margin-top: 20px;
        }

        .content h2 {
            color: var(--primary-color);
            border-left: 5px solid var(--accent-color);
            padding-left: 15px;
            margin-top: 30px;
            font-size: 22px;
        }

        .content h3 {
            color: #444;
            font-size: 18px;
            margin-top: 25px;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }

        p { margin-bottom: 15px; }

        /* --- 重点引用块 --- */
        blockquote {
            background: var(--light-gray);
            border-left: 4px solid var(--primary-color);
            margin: 20px 0;
            padding: 15px 20px;
            font-style: italic;
            color: #444;
        }

        blockquote strong { color: var(--primary-color); }

        /* --- 表格样式 --- */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 14px;
            page-break-inside: avoid;
        }

        th {
            background-color: var(--primary-color);
            color: white;
            padding: 10px;
            text-align: left;
        }

        td {
            border-bottom: 1px solid #ddd;
            padding: 10px;
        }

        tr:nth-child(even) { background-color: #f9f9f9; }

        /* --- 页眉页脚 (打印专用) --- */
        .print-footer {
            display: none; /* 屏幕上不显示 */
        }

        .disclaimer-box {
            margin-top: 50px;
            padding: 15px;
            border: 1px solid #ddd;
            background: #fafafa;
            font-size: 12px;
            color: #777;
            page-break-inside: avoid;
        }

        /* --- 打印控制 (关键) --- */
        @media print {
            body {
                background: none;
                margin: 0;
                padding: 0;
            }
            
            .page {
                width: 100%;
                margin: 0;
                padding: 0; /* 让浏览器控制边距 */
                box-shadow: none;
                border: none;
                min-height: auto;
            }

            .cover-page {
                height: 90vh; /* 强制封面占满第一页 */
                page-break-after: always;
            }
            
            table, blockquote, img {
                break-inside: avoid; /* 避免表格/图片跨页切断 */
            }
            
            /* 去除链接的下划线和颜色 */
            a { text-decoration: none; color: black; }
        }
    </style>
</head>
<body>

    <!-- 封面页 -->
    <div class="page">
        <div class="cover-page">
            <div class="logo">{{ meta.company_name }}</div>
            <h1 class="report-title">{{ meta.title }}</h1>
            <div class="subtitle">{{ meta.subtitle }}</div>
            
            <div class="meta-info">
                <p><strong>分析师:</strong> {{ meta.author }}</p>
                <p><strong>发布日期:</strong> {{ meta.date }}</p>
            </div>
        </div>
    </div>

    <!-- 正文页 -->
    <div class="page">
        <div class="content">
            {{ content }}
        </div>

        <div class="disclaimer-box">
            <strong>法律声明：</strong> {{ meta.disclaimer }}
        </div>
    </div>

</body>
</html>
"""

# ==========================================
# 2. 核心处理逻辑
# ==========================================
def create_html_report(markdown_file_path):
    """
    Reads a markdown report, converts it to HTML, and saves it.
    """
    print(f"正在处理 Markdown 文件: {markdown_file_path}")

    try:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            report_body_markdown = f.read()
    except FileNotFoundError:
        print(f"❌ 错误: 未找到 Markdown 文件 '{markdown_file_path}'")
        return

    # --- 解析元数据 ---
    lines = report_body_markdown.splitlines()
    title = "投资研究报告"
    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()

    report_metadata = {
        "title": title,
        "subtitle": "由 Gemini Pro 生成的自动化投资分析",
        "author": "Gemini Pro (AI 分析师)",
        "date": datetime.datetime.now().strftime("%Y年%m月%d日"),
        "company_name": "Phill Zhu's AI Lab",
        "disclaimer": "本报告由AI生成，仅供参考，不构成投资建议。市场有风险，投资需谨慎。"
    }

    # --- 转换与渲染 ---
    # 1. 将 Markdown 正文转换为 HTML
    html_content = markdown.markdown(
        report_body_markdown, 
        extensions=['tables', 'fenced_code']
    )

    # 2. 使用 Jinja2 渲染完整 HTML
    template = Template(html_template_string)
    final_html = template.render(
        meta=report_metadata,
        content=html_content
    )

    # 3. 输出文件
    base_name = os.path.basename(markdown_file_path)
    output_filename = os.path.splitext(base_name)[0] + ".html"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_html)
    
    print(f"✅ HTML 报告已生成: {os.path.abspath(output_filename)}")
    print("   请在浏览器中打开该文件，然后右键选择 '打印' -> '另存为 PDF'")

# ==========================================
# 3. 主程序
# ==========================================
if __name__ == "__main__":
    # 寻找当前目录中最新的 .md 文件
    print("正在寻找最新的 Markdown 报告...")
    list_of_md_files = glob.glob('*.md')
    if not list_of_md_files:
        print("❌ 错误: 在当前目录中未找到任何 .md 报告文件。")
    else:
        latest_md_file = max(list_of_md_files, key=os.path.getctime)
        
        # 检查依赖库
        try:
            import markdown
            import jinja2
        except ImportError:
            print("\n⚠️ 警告: 缺少必要的 Python 库。")
            print("   请运行以下命令安装: pip install markdown jinja2")
        else:
            create_html_report(latest_md_file)
