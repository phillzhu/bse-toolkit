import requests
import json
import pandas as pd
import io
import pdfplumber
import time
import os
from datetime import datetime, timedelta
import argparse

# ====================================================================
# 1. 配置加载模块
# ====================================================================

def get_config():
    """从项目根目录的 config.json 加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ 配置文件未找到: {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"❌ 配置文件格式错误: {config_path}")
        return None

# ====================================================================
# 2. 函数定义 (重构后)
# ====================================================================

def extract_json_from_string(text: str) -> dict:
    """从模型返回的文本中稳健地提取JSON对象"""
    try:
        start_index = text.find('{')
        end_index = text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = text[start_index : end_index + 1]
            return json.loads(json_str)
        else:
            print("  [解析警告] 未在模型返回的文本中找到有效的JSON结构。")
            return {"error": "No valid JSON structure found"}
    except (json.JSONDecodeError, TypeError):
        print("  [解析警告] 提取的字符串无法被解析为JSON。")
        return {"error": "Failed to decode string as JSON"}

def get_announcements_from_ifind(config: dict, start_date: str, end_date: str, stock_source: str = 'all') -> pd.DataFrame:
    """使用配置和指定日期范围从iFind获取公告"""
    print(f"--- 1. 正在从 iFind 获取 {start_date} 到 {end_date} 的公告数据 ---")
    
    ifind_config = config.get('ifind', {})
    api_token = ifind_config.get('accessToken')
    api_url = ifind_config.get('reportQueryUrl')
    
    if not api_token or not api_url:
        print("❌ iFind 配置不完整 (accessToken, reportQueryUrl)。")
        return pd.DataFrame()

    payload = config.get('ifindPayload', {})
    if not payload:
        print("❌ iFind payload 配置 (ifindPayload) 未找到。")
        return pd.DataFrame()
        
    # -- 根据设置动态选择股票代码列表 --
    if stock_source == 'custom':
        codes_list = config.get('customStockPool', '')
        print("  - 使用 '自选股池' 进行查询。")
    else:
        codes_list = payload.get('codes', '')
        print("  - 使用 '北交所全市场' 进行查询。")
    
    if not codes_list:
        print("❌ 股票代码列表为空，无法查询。")
        return pd.DataFrame()

    # 构造请求体
    # 注意：必须创建一个新的字典，避免修改原始配置中的 payload 对象
    request_payload = payload.copy()
    request_payload['codes'] = codes_list
    request_payload['beginrDate'] = start_date
    request_payload['endrDate'] = end_date
    
    # 严格从 config.json 读取 outputpara
    if 'outputpara' in payload:
        request_payload['outputpara'] = payload['outputpara']
    else:
        # 如果 config.json 中没有定义，使用默认值
        request_payload['outputpara'] = "reportDate:Y,secName:Y,reportTitle:Y,pdfURL:Y"

    # 移除之前可能错误添加的 'reqBody' 嵌套
    # 根据 notebook 示例，iFind API 接受扁平的 JSON 结构
    final_payload = request_payload
    
    headers = {"Content-Type": "application/json", "access_token": api_token}

    try:
        print(f"  [DEBUG] Sending Payload: {json.dumps(final_payload, ensure_ascii=False)[:200]}...") # Log payload start
        response = requests.post(api_url, headers=headers, data=json.dumps(final_payload), timeout=120)
        response.raise_for_status()
        data = response.json()

        if data.get('errorcode') != 0:
            print(f"❌ iFind API 业务错误: {data.get('errmsg', '未知错误')}")
            return pd.DataFrame()

        if 'tables' in data and data['tables'] and 'table' in data['tables'][0]:
            result_data = data['tables'][0]['table']
            if not result_data or not result_data.get('reportDate'):
                print(f"✅ iFind API 调用成功，但 {start_date} 到 {end_date} 期间无任何相关公告。")
                return pd.DataFrame()
            
            result_df = pd.DataFrame(result_data)
            print(f"✅ 成功获取 {len(result_df)} 条公告。")
            return result_df
        else:
            print("❌ iFind API 返回的数据结构不符合预期。")
            return pd.DataFrame()

    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ 获取公告数据时发生未知错误: {e}")
        return pd.DataFrame()

def is_title_important(title: str, config: dict) -> bool:
    """(AI Step 1) 使用配置的快速模型判断标题是否重要"""
    # ... (此函数无需修改)
    llm_config = config.get('llm', {})
    provider = llm_config.get('provider')
    prompt = f"""作为一名金融分析师助理，你的任务是快速判断一则公告标题是否可能涉及重要内容。重要内容通常关于：业绩预告/快报、利润分配/分红、重组、收购、重大合同、增发、回购、股权激励、高管重大变动、收到监管函/处罚、年报、季报、半年报、做市、反馈意见、专精特新、专利。常规内容通常关于：董事会/监事会/股东大会决议、会议通知、章程修订、日常关联交易。根据以下标题，判断它是否可能重要。请只回答 "YES" 或 "NO"。标题: "{title}" """
    try:
        if provider == "dashscope":
            from dashscope import Generation
            ds_config = llm_config.get('dashscope', {})
            api_key, fast_model = ds_config.get('apiKey'), ds_config.get('fastModel')
            if not all([api_key, fast_model]): return False
            response = Generation.call(model=fast_model, api_key=api_key, prompt=prompt, temperature=0.0)
            return "YES" in response.output.text.strip().upper()
        elif provider == "openai":
            from openai import OpenAI
            openai_config = llm_config.get('openai', {})
            api_key, base_url, fast_model = openai_config.get('apiKey'), openai_config.get('baseUrl'), openai_config.get('fastModel')
            if not all([api_key, base_url, fast_model]): return False
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(model=fast_model, messages=[{"role": "user", "content": prompt}], temperature=0.0)
            return "YES" in response.choices[0].message.content.strip().upper()
        else:
            return False
    except Exception as e:
        print(f"  [预筛选失败] 调用快速模型API时出错: {e}")
        return False


def get_text_from_pdf_url(pdf_url: str) -> str:
    """从PDF链接中下载并提取文本 (最多5页)"""
    # ... (此函数无需修改)
    if not pdf_url or not pdf_url.startswith('http'): return ""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        with io.BytesIO(response.content) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                return "".join(page.extract_text() for i, page in enumerate(pdf.pages) if page.extract_text() and i < 5)
    except Exception:
        return ""

def analyze_announcement(text: str, title: str, config: dict) -> dict:
    """(AI Step 2) 使用配置的深度模型分析公告内容"""
    # ... (此函数无需修改)
    if not text: return {"error": "文本为空"}
    llm_config = config.get('llm', {})
    provider = llm_config.get('provider')
    prompt = f"""作为一名专业的金融分析师，请分析以下这篇来自北交所的上市公司公告。公告标题: "{title}" 公告内容:\n---\n{text[:8000]}""" \
             f"""\n---\n请根据内容，以JSON格式返回你的分析，包含三个字段：1. "summary": (String)""" \
             f""" 用不超过3句话，精准地总结公告的核心内容。2. "importance": (Integer)""" \
             f""" 评估此公告对股价的潜在影响，给出1-5的整数评分。1代表例行公事；3代表有关注价值；5""" \
             f""" 代表可能引发股价剧烈波动的重大事件。3. "reason": (String)""" \
             f""" 用一句话解释你给出该重要性评分的理由。""" \
             f""" 重要：你的回答必须包含一个能被直接解析的JSON代码块。"""
    try:
        if provider == "dashscope":
            from dashscope import Generation
            ds_config = llm_config.get('dashscope', {})
            api_key, deep_model = ds_config.get('apiKey'), ds_config.get('deepModel')
            if not api_key: return {"error": "DashScope API Key 未配置。"}
            response = Generation.call(model=deep_model, api_key=api_key, prompt=prompt, temperature=0.1)
            if response.status_code == 200 and response.output and response.output.text:
                return extract_json_from_string(response.output.text)
            else: return {"error": f"API Error: {response.message}"}
        elif provider == "openai":
            from openai import OpenAI
            openai_config = llm_config.get('openai', {})
            api_key, base_url, deep_model = openai_config.get('apiKey'), openai_config.get('baseUrl'), openai_config.get('deepModel')
            if not all([api_key, base_url, deep_model]): return {"error": "OpenAI 深度模型配置不完整。"}
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(model=deep_model, messages=[{"role": "user", "content": prompt}], temperature=0.1, response_format={"type": "json_object"})
            return json.loads(response.choices[0].message.content)
        else:
            return {"error": f"不支持的LLM提供商: {provider}"}
    except Exception as e:
        print(f"  [分析失败] 调用深度模型API时出错: {e}")
        return {"error": str(e)}

def generate_html_briefing(analyzed_announcements: list, start_date: str, end_date: str) -> str:
    """生成格式化的每日简报 HTML 内容"""
    # ... (更新标题)
    if start_date == end_date:
        date_str = start_date
    else:
        date_str = f"{start_date} 至 {end_date}"
    
    important_announcements = sorted([ann for ann in analyzed_announcements if 'importance' in ann and ann.get('importance', 0) >= 3], key=lambda x: x.get('importance', 0), reverse=True)
    html_template = f"""
<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>北交所公告简报 - {date_str}</title><style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }}
.container {{ max-width: 900px; margin: 20px auto; background-color: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); }}
h1 {{ color: #1a3a6e; border-bottom: 2px solid #1a3a6e; padding-bottom: 10px; font-size: 24px; }}
.announcement-card {{ border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; border-radius: 6px; background-color: #ffffff; transition: box-shadow 0.3s ease; }}
.announcement-card:hover {{ box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1); }}
.title-secname {{ font-size: 18px; font-weight: 600; margin-bottom: 8px; color: #333; }}
.secname {{ color: #0056b3; margin-right: 10px; }}
.importance {{ margin-bottom: 12px; font-size: 16px; display: flex; align-items: center; }}
.star-filled {{ color: #ffc107; }} .star-empty {{ color: #ccc; }}
.summary, .reason {{ margin-top: 10px; border-left: 3px solid #0056b3; padding-left: 15px; font-size: 14px; line-height: 1.6; }}
.label {{ font-weight: bold; color: #555; }}
.link {{ display: inline-block; margin-top: 15px; font-size: 13px; color: #007bff; text-decoration: none; }}
.no-announcements {{ text-align: center; padding: 40px; color: #999; }}
</style></head><body><div class="container"><h1>北交所公告简报 - {date_str}</h1>
    """
    html_content = html_template
    if not important_announcements:
        html_content += '<div class="no-announcements">该时段内无重要公告（或所有公告经AI分析后均不重要）。</div>'
    else:
        for ann in important_announcements:
            stars_html = "".join(['<span class="star-filled">★</span>' if i < ann.get('importance', 0) else '<span class="star-empty">★</span>' for i in range(5)])
            html_content += f"""
        <div class="announcement-card">
            <div class="title-secname"><span class="secname">【{ann.get('secName', 'N/A')}】</span>{ann.get('reportTitle', '无标题')}</div>
            <div class="importance"><span class="label">重要性:</span>&nbsp;{stars_html}&nbsp;({ann.get('importance', 0)}/5)</div>
            <p class="summary"><span class="label">摘要:</span> {ann.get('summary', '无摘要')}</p>
            <p class="reason"><span class="label">理由:</span> {ann.get('reason', '无理由')}</p>
            <a class="link" href="{ann.get('pdfURL', '#')}" target="_blank">查看PDF原文 &rarr;</a>
        </div>"""
    html_content += "</div></body></html>"
    return html_content

# ====================================================================
# 4. 主运行逻辑
# ====================================================================

def main(config: dict, start_date: str, end_date: str, stock_source: str):
    """主函数，接收配置和日期范围作为参数"""
    announcements_df = get_announcements_from_ifind(config, start_date, end_date, stock_source)

    analyzed_list = []
    
    if not announcements_df.empty:
        print("\n--- 2. 开始进行公告筛选和深度分析 ---")

        for index, row in announcements_df.iterrows():
            title, pdf_url, sec_name = row.get('reportTitle'), row.get('pdfURL'), row.get('secName')
            if not all([title, pdf_url, sec_name]) or not pdf_url.startswith('http'):
                print(f"\n[{index+1}/{len(announcements_df)}] **警告**: 数据不完整或PDF链接无效，跳过。")
                continue
            print(f"\n[{index+1}/{len(announcements_df)}] 预筛选: {sec_name} - '{title}'")
            if not is_title_important(title, config):
                print("  -> AI初判: 不重要，跳过深度分析。")
                continue
            print("  -> AI初判: **可能重要**，进行深度分析。")
            announcement_text = get_text_from_pdf_url(pdf_url)
            if len(announcement_text) < 50:
                print("  [处理失败] 提取到的文本过短，跳过。")
                continue
            time.sleep(1)
            analysis_result = analyze_announcement(announcement_text, title, config)
            if "summary" in analysis_result and "importance" in analysis_result:
                full_analysis = {**row.to_dict(), **analysis_result}
                analyzed_list.append(full_analysis)
                print(f"  [分析完成] 重要性评分: {analysis_result['importance']}/5。")
            else:
                print(f"  [分析失败] {analysis_result.get('error', '未知错误')}")
    else:
        print("未获取到公告数据，准备生成空报告。")

    html_report = generate_html_briefing(analyzed_list, start_date, end_date)
    
    # --- 文件保存 ---
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'generated_reports')
    os.makedirs(output_dir, exist_ok=True)
    
    start_date_fmt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y%m%d")
    end_date_fmt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m%d")
    
    if start_date_fmt == end_date_fmt:
        filename = f"daily_briefing_{start_date_fmt}.html"
    else:
        filename = f"daily_briefing_{start_date_fmt}_{end_date_fmt}.html"
        
    output_path = os.path.join(output_dir, filename)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print("\n" + "="*40)
        print("✅ 简报生成成功!")
        print(f"文件已保存至: {output_path}")
        print("="*40)
    except Exception as e:
        print(f"\n[错误] 无法保存文件到指定路径: {e}")

if __name__ == "__main__":
    import sys
    print(f"[DEBUG] Arguments received: {sys.argv}")

    parser = argparse.ArgumentParser(description="生成北交所公告简报")
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Add a new --date argument
    parser.add_argument("--date", type=str, default=None, help="指定单日日期，格式 YYYY-MM-DD。如果使用此参数，将忽略 --start-date 和 --end-date")
    parser.add_argument("--start-date", type=str, default=today_str, help="开始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=today_str, help="结束日期，格式 YYYY-MM-DD")
    parser.add_argument("--stock-source", type=str, default="all", help="股票代码来源: 'all' (全市场) 或 'custom' (自选股)")
    
    args = parser.parse_args()
    
    # Logic to handle the new --date argument
    start_date = args.start_date
    end_date = args.end_date
    
    if args.date:
        start_date = args.date
        end_date = args.date
        
    main_config = get_config()
    if main_config:
        main(main_config, start_date, end_date, args.stock_source)