import subprocess
import json
import os
import glob
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

# ====================================================================
# 1. App 和路径配置
# ====================================================================
app = FastAPI()

backend_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(backend_dir, "scripts")
reports_dir = os.path.join(backend_dir, "generated_reports")
investment_reports_dir = os.path.join(scripts_dir, "report")

os.makedirs(reports_dir, exist_ok=True)
os.makedirs(investment_reports_dir, exist_ok=True)

config_path = os.path.join(backend_dir, "config.json")
config_example_path = os.path.join(backend_dir, "config.example.json")

app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")
app.mount("/investment_reports", StaticFiles(directory=investment_reports_dir), name="investment_reports")

# ====================================================================
# 2. Pydantic 模型
# ====================================================================
class ConfigModel(BaseModel):
    llm: dict
    ifind: dict
    dailyBriefing: dict
    customStockPool: str
    ifindPayload: dict
    ticker: str

class DailyBriefingRequest(BaseModel):
    startDate: str
    endDate: str
    stockSource: str

class InvestmentReportRequest(BaseModel):
    ticker: str
    userInfo: Optional[str] = ""
    reportPeriod: str

# ====================================================================
# 3. 核心辅助函数 (重构后)
# ====================================================================

def get_config_safely() -> dict[str, Any]:
    """
    安全地获取配置。
    - 如果 config.json 存在，读取它。
    - 如果不存在，读取 config.example.json。
    - 如果两者都不存在，抛出异常。
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        elif os.path.exists(config_example_path):
            with open(config_example_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise HTTPException(status_code=404, detail="配置文件 config.json 和模板文件 config.example.json 均未找到。")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="配置文件格式错误。")

def check_secrets(config: dict):
    """检查关键密钥是否已配置，如果未配置则抛出异常。"""
    ifind_token = config.get("ifind", {}).get("accessToken", "")
    if "YOUR_IFIND_TOKEN_HERE" in ifind_token or not ifind_token:
        raise HTTPException(status_code=400, detail="iFind Access Token 未配置，请先前往“设置”页面填写。")

    provider = config.get("llm", {}).get("provider")
    api_key = config.get("llm", {}).get(provider, {}).get("apiKey", "")
    if "YOUR_" in api_key or not api_key:
        raise HTTPException(status_code=400, detail=f"LLM 提供商 ({provider}) 的 API Key 未配置，请先前往“设置”页面填写。")

# ====================================================================
# 4. API Endpoints (重构后)
# ====================================================================

@app.get("/api/config", response_model=ConfigModel)
def get_config_api():
    """读取并返回配置，如果主配置不存在则返回模板配置。"""
    return get_config_safely()

@app.post("/api/config")
def update_config(new_config: ConfigModel):
    """更新并保存配置。"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config.dict(), f, indent=2, ensure_ascii=False)
        return {"message": "配置已成功更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入配置文件失败: {e}")

@app.post("/api/run/daily_briefing")
def run_daily_briefing(request: DailyBriefingRequest):
    """执行每日公告简报脚本，前置检查密钥。"""
    config = get_config_safely()
    check_secrets(config) # 前置检查

    # 在执行前，将运行时选项写入config，以便脚本读取
    config['dailyBriefing']['stockSource'] = request.stockSource
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行前更新配置文件失败: {e}")


    script_path = os.path.join(scripts_dir, "daily_briefing.py")
    command = ["python3", script_path, "--start-date", request.startDate, "--end-date", request.endDate]
    
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', cwd=backend_dir)
        
        # 构造预期的文件名并返回 URL
        start_date_formatted = datetime.strptime(request.startDate, "%Y-%m-%d").strftime("%Y%m%d")
        end_date_formatted = datetime.strptime(request.endDate, "%Y-%m-%d").strftime("%Y%m%d")
        
        if start_date_formatted == end_date_formatted:
            report_filename = f"daily_briefing_{start_date_formatted}.html"
        else:
            report_filename = f"daily_briefing_{start_date_formatted}_{end_date_formatted}.html"

        if not os.path.exists(os.path.join(reports_dir, report_filename)):
             raise HTTPException(status_code=500, detail=f"脚本执行成功，但未找到预期的报告文件: {report_filename}")

        return {"report_url": f"/reports/{report_filename}"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"每日简报脚本执行失败: {e.stderr or e.stdout}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未知错误: {e}")

@app.post("/api/run/investment_report")
def run_investment_report(request: InvestmentReportRequest):
    """执行投资研究报告流水线，前置检查密钥。"""
    config = get_config_safely()
    check_secrets(config) # 前置检查

    # 更新 config.json 中的运行时参数
    config['ticker'] = request.ticker
    config['userInfo'] = request.userInfo
    config['ifind']['reportPeriod'] = request.reportPeriod
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行前更新配置文件失败: {e}")

    script_path = os.path.join(scripts_dir, "run_report_pipeline_v1.1.py")
    command = ["python3", script_path]
    
    try:
        subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', cwd=scripts_dir)
        
        list_of_html_files = glob.glob(os.path.join(investment_reports_dir, '*.html'))
        if not list_of_html_files:
            raise HTTPException(status_code=500, detail="脚本执行成功，但未在 'scripts/report' 目录中找到任何HTML报告。")
        
        latest_report = max(list_of_html_files, key=os.path.getctime)
        return {"report_url": f"/investment_reports/{os.path.basename(latest_report)}"}

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"投研报告脚本执行失败: {e.stderr or e.stdout}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未知错误: {e}")

# ====================================================================
# 5. 启动命令
# ====================================================================
if __name__ == "__main__":
    import uvicorn
    print("启动 FastAPI 服务，访问 http://127.0.0.1:9200")
    uvicorn.run(app, host="127.0.0.1", port=9200)