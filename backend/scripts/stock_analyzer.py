import requests
import json
from datetime import datetime, timedelta
import pandas as pd
import os
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
# 2. 依赖库初始化 (动态)
# ====================================================================

def initialize_llm_library(provider):
    """根据配置动态导入库"""
    if provider == "dashscope":
        try:
            from dashscope import Generation
            return Generation
        except ImportError:
            print("提示: DashScope 提供者需要安装 'dashscope' (pip install dashscope)")
            return None
    elif provider == "openai":
        try:
            from openai import OpenAI
            return OpenAI
        except ImportError:
            print("提示: OpenAI 提供者需要安装 'openai' (pip install openai)")
            return None
    return None

# ====================================================================
# 3. 数据获取模块
# ====================================================================

def get_ifind_data(config: dict) -> dict:
    """从iFind获取数据，使用传入的配置"""
    ifind_config = config.get('ifind', {})
    ticker = config.get('ticker')
    user_info = config.get('userInfo') # 虽然此函数不用，但保持数据完整性
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始获取 {ticker} 数据...")
    
    # 从配置中读取参数
    calc_date = datetime.now().strftime("%Y-%m-%d")
    report_period = ifind_config.get("reportPeriod", "3") # 默认中报
    table_type = ifind_config.get("tableType", "1") # 默认合并报表
    
    print(f"  - 基准日期: {calc_date} | 报表类型: {report_period} | 数据类型: {table_type}")
    
    all_data = {"ticker": ticker, "userInfo": user_info}
    headers = {"Content-Type": "application/json", "access_token": ifind_config.get('accessToken')}
    
    if not headers["access_token"]:
        print("  - ❌ iFind Access Token 未在 config.json 中配置。")
        return None

    try:
        # --- 3.1 基础资料与财务指标 ---
        indicators_list = [
            {"indicator":"ths_revenue_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_np_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_prime_oi_old_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_net_sales_rate_stock","indiparams":[report_period]},
            {"indicator":"ths_gross_selling_rate_stock","indiparams":[report_period]},
            {"indicator":"ths_mo_product_name_stock","indiparams":[]},
            {"indicator":"ths_mo_product_type_stock","indiparams":[]},
            {"indicator":"ths_corp_profile_stock","indiparams":[]},
            {"indicator":"ths_the_csrc_industry_stock","indiparams":["1", calc_date]},
            {"indicator":"ths_ncf_from_oa_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_pe_ttm_stock","indiparams":[calc_date,"100"]},
            {"indicator":"ths_pb_latest_stock","indiparams":[calc_date,"100"]},
            {"indicator":"ths_total_asset_rr_stock","indiparams":[report_period, table_type,"101"]},
            {"indicator":"ths_total_liab_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_current_ratio_stock","indiparams":[report_period]},
            {"indicator":"ths_quick_ratio_stock","indiparams":[report_period]},
            {"indicator":"ths_operating_total_revenue_stock","indiparams":[report_period, table_type]},
            {"indicator":"ths_roe_ttm_stock","indiparams":[calc_date,"100"]},
            {"indicator":"ths_eps_basic_stock","indiparams":[report_period]}
        ]

        payload_profile = {"codes": ticker, "indipara": indicators_list}
        
        res_profile = requests.post(ifind_config.get('basicDataUrl'), headers=headers, data=json.dumps(payload_profile), timeout=60)
        res_profile.raise_for_status()
        profile_json = res_profile.json()

        if profile_json.get("errorcode") == 0 and profile_json.get("tables"):
            table = profile_json["tables"][0]["table"]
            all_data["profile"] = {k: (v[0] if isinstance(v, list) and v else v) for k, v in table.items()}
            print("  - ✅ 基础财务及估值数据获取成功")
        else:
            print(f"  - ❌ 基础数据获取失败: {profile_json.get('errmsg')}")
            all_data["profile"] = None

        # --- 3.2 二级市场数据 ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        payload_market = {
            "reqBody": {
                "codes": ticker,
                "indicators": "pre_close,open,high,low,close,vwap,chg,pct_chg,volume,amt,turn",
                "startdate": start_date.strftime("%Y-%m-%d"),
                "enddate": end_date.strftime("%Y-%m-%d")
            }
        }

        res_market = requests.post(ifind_config.get('historyDataUrl'), headers=headers, data=json.dumps(payload_market), timeout=60)
        res_market.raise_for_status()
        market_json = res_market.json()

        if market_json.get("errorcode") == 0 and market_json.get("tables"):
            df = pd.DataFrame(market_json["tables"][0]["table"])
            cols = ['open','close','vwap','chg','pct_chg','volume','amt','turn']
            for c in cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')

            all_data["market_latest"] = df.iloc[-1].to_dict() if not df.empty else {}
            all_data["market_stats"] = {
                "avg_close": df['close'].mean(), "avg_volume": df['volume'].mean(),
                "avg_turn": df['turn'].mean(), "max_price": df['close'].max(),
                "min_price": df['close'].min()
            }
            print("  - ✅ 二级市场数据获取成功")

            # 为生成图表，将市场数据保存到文件
            script_dir = os.path.dirname(os.path.abspath(__file__))
            report_dir = os.path.join(script_dir, "report")
            os.makedirs(report_dir, exist_ok=True)
            market_data_path = os.path.join(report_dir, "market_data.json")
            df.to_json(market_data_path, orient="records", force_ascii=False)
            print(f"  - 📈 市场日线数据已保存，用于生成图表")
        else:
            print(f"  - ❌ 市场数据获取失败: {market_json.get('errmsg')}")
            all_data["market_latest"] = None

    except Exception as e:
        print(f"  - ❌ 请求异常: {e}")
        return None

    return all_data

# ====================================================================
# 4. 报告生成模块
# ====================================================================

def format_data_for_prompt(data: dict) -> str:
    """格式化数据字符串"""
    p = data.get("profile", {})
    m = data.get("market_latest", {})
    s = data.get("market_stats", {})
    
    txt = f"【目标股票】: {data['ticker']}\n"
    txt += f"【数据基准日】: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    
    # ... (rest of the formatting is fine, no need to change)
    txt += "【1. 公司概况与基本面】\n"
    if p:
        name = p.get('ths_corp_cn_name_stock') or data['ticker']
        txt += f"- 公司名称: {name}\n"
        txt += f"- 所属行业: {p.get('ths_the_csrc_industry_stock', 'N/A')}\n"
        desc = str(p.get('ths_corp_profile_stock', 'N/A'))
        txt += f"- 公司简介: {desc[:200]}...\n" 
        txt += f"- 主营产品: {p.get('ths_mo_product_name_stock', 'N/A')}\n"
        txt += f"- 产品类型: {p.get('ths_mo_product_type_stock', 'N/A')}\n\n"
        
        txt += "【2. 核心财务数据 (最新报告期)】\n"
        txt += f"- 营业总收入: {p.get('ths_operating_total_revenue_stock', 'N/A')} | 营收: {p.get('ths_revenue_stock', 'N/A')}\n"
        txt += f"- 净利润: {p.get('ths_np_stock', 'N/A')} | EPS(基本): {p.get('ths_eps_basic_stock', 'N/A')}\n"
        txt += f"- 经营性现金流净额: {p.get('ths_ncf_from_oa_stock', 'N/A')}\n"
        txt += f"- 资产合计: {p.get('ths_total_asset_rr_stock', 'N/A')} | 负债合计: {p.get('ths_total_liab_stock', 'N/A')}\n\n"

        txt += "【3. 关键财务比率】\n"
        txt += f"- 盈利能力: 毛利率 {p.get('ths_gross_selling_rate_stock', 'N/A')}% | 净利率 {p.get('ths_net_sales_rate_stock', 'N/A')}% | ROE(TTM) {p.get('ths_roe_ttm_stock', 'N/A')}%\n"
        txt += f"- 偿债能力: 流动比率 {p.get('ths_current_ratio_stock', 'N/A')} | 速动比率 {p.get('ths_quick_ratio_stock', 'N/A')}\n\n"
        
        txt += "【4. 估值指标】\n"
        txt += f"- PE(TTM): {p.get('ths_pe_ttm_stock', 'N/A')}\n"
        txt += f"- PB(最新): {p.get('ths_pb_latest_stock', 'N/A')}\n"
    
    txt += "\n【5. 二级市场数据 (近30天)】\n"
    if m and s:
        txt += f"- 最新收盘: {m.get('close')} (涨跌幅: {m.get('pct_chg')}%)\n"
        txt += f"- 价格区间: {s.get('min_price')} - {s.get('max_price')} (均价: {s.get('avg_close'):.2f})\n"
        txt += f"- 最新换手: {m.get('turn')}% | 月均换手: {s.get('avg_turn'):.2f}%\n"
        
    return txt

def generate_report(data: dict, config: dict) -> str:
    """使用配置生成报告"""
    print("开始生成报告...")
    
    data_context = format_data_for_prompt(data)
    llm_config = config.get('llm', {})
    provider = llm_config.get('provider')
    
    prompt = f"""
你是一位资深证券分析师。你的任务是提供的【客观数据】和【用户补充信息】，为股票 {data['ticker']} 撰写一份专业翔实、客观、结构清晰的投资研究报告。

**用户补充参考信息：**
{data.get('userInfo', '无')}

**报告必须严格遵循以下结构和要求：**
# 股票 {data['ticker']} 投资研究报告
## 一、 综述
(最后完成此部分，请根据所有信息和生成报告的整体，概括核心观点，给出评级和目标价区间。)
## 二、 项目简介
(利用“公司简介”和“主营产品”以及你掌握的知识和搜索，详细介绍公司的主营业务和行业地位。**然后，请将核心财务数据（如营收、净利、EPS、ROE、毛利率、净利率）整理成一个Markdown表格进行展示，并基于此分析基本面质量。**)
## 三、 二级市场情况
(**请首先使用Markdown表格汇总关键市场数据（最新收盘价、近30日最高/最低价、近30日均价、PE、PB），然后再进行分析**，描述并分析该股票当前和最近一个月的市场表现，并与月度平均水平进行对比，以判断其当前估值在近期所处的位置。)
## 四、 投资亮点
(在此部分，请分点阐述，并严格使用 "1. **加粗小标题：** 正文内容" 的格式。)
## 五、 投资风险
(在此部分，请分点阐述，并严格使用 "1. **加粗小标题：** 正文内容" 的格式。)
## 六、 盈利预测和估值分析
(在此部分，请基于公司的财务数据和行业前景，给出一个未来1-2年的简要盈利预测。然后，**使用Markdown表格**结合市盈率(PE)或市净率(PB)等方法，进行估值分析，并给出一个明确的估值区间和未来6-12个月的目标价。)
---
**数据源：**
{data_context}
"""

    try:
        if provider == "dashscope":
            Generation = initialize_llm_library(provider)
            if not Generation: return "LLM库初始化失败"
            
            ds_config = llm_config.get('dashscope', {})
            response = Generation.call(
                model=ds_config.get('model', 'qwen-plus'), 
                api_key=ds_config.get('apiKey'), 
                prompt=prompt, 
                result_format='message'
            )
            if response.status_code == 200:
                return response.output.choices[0].message.content
            else:
                return f"Error: {response.message}"

        elif provider == "openai":
            OpenAI = initialize_llm_library(provider)
            if not OpenAI: return "LLM库初始化失败"
            
            openai_config = llm_config.get('openai', {})
            client = OpenAI(api_key=openai_config.get('apiKey'), base_url=openai_config.get('baseUrl'))
            response = client.chat.completions.create(
                model=openai_config.get('deepModel'),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
            
    except Exception as e:
        return f"LLM调用异常: {e}"
        
    return f"配置错误: 未知的LLM提供者 '{provider}'"

# ====================================================================
# 5. 主程序
# ====================================================================

def main():
    """主执行函数"""
    config = get_config()
    if not config:
        print("无法加载配置，程序终止。")
        return

    print("="*50)
    print(f"开始分析: {config.get('ticker', '未指定')}")
    print("="*50)
    
    data = get_ifind_data(config)
    if not data:
        return

    report = generate_report(data, config)
    
    # --- 文件保存逻辑 ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "report")
    os.makedirs(output_dir, exist_ok=True)
    
    ticker_sanitized = config.get('ticker', 'UNKNOWN').replace('.', '_')
    filename = os.path.join(output_dir, f"Report_{ticker_sanitized}_{datetime.now().strftime('%Y%m%d')}.md")
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ 报告已保存: {filename}")
    except Exception as e:
        print(f"保存失败: {e}\n{report}")

if __name__ == "__main__":
    main()