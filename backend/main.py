import subprocess
import json
import os
import glob
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime
import time

# ====================================================================
# 1. App, 路径配置 和 任务存储
# ====================================================================
app = FastAPI()

# --- 任务存储 ---
# 使用一个字典来存储正在运行的子进程
# 结构: { "task_id": {"process": Popen_object, "start_time": timestamp} }
tasks: Dict[str, Dict[str, Any]] = {}

backend_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(backend_dir, "scripts")
reports_dir = os.path.join(backend_dir, "generated_reports")
investment_reports_dir = reports_dir

os.makedirs(reports_dir, exist_ok=True)

config_path = os.path.join(backend_dir, "config.json")
config_example_path = os.path.join(backend_dir, "config.example.json")

app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")
app.mount("/investment_reports", StaticFiles(directory=reports_dir), name="investment_reports")

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
# 3. 核心辅助函数
# ====================================================================

def get_config_safely() -> dict[str, Any]:
    """安全地获取配置。"""
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
    """检查关键密钥是否已配置。"""
    ifind_token = config.get("ifind", {}).get("accessToken", "")
    if "YOUR_IFIND_TOKEN_HERE" in ifind_token or not ifind_token:
        raise HTTPException(status_code=400, detail="iFind Access Token 未配置，请先前往“设置”页面填写。")

    provider = config.get("llm", {}).get("provider")
    api_key = config.get("llm", {}).get(provider, {}).get("apiKey", "")
    if "YOUR_" in api_key or not api_key:
        raise HTTPException(status_code=400, detail=f"LLM 提供商 ({provider}) 的 API Key 未配置，请先前往“设置”页面填写。")

def get_expected_report_filename(start_date_str: str, end_date_str: str) -> str:
    """根据日期构造预期的报告文件名"""
    start_date_formatted = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%Y%m%d")
    end_date_formatted = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%Y%m%d")
    
    if start_date_formatted == end_date_formatted:
        return f"daily_briefing_{start_date_formatted}.html"
    else:
        return f"daily_briefing_{start_date_formatted}_{end_date_formatted}.html"

# ====================================================================
# 4. API Endpoints (已升级为异步任务模式)
# ====================================================================

@app.get("/api/config", response_model=ConfigModel)
def get_config_api():
    """读取并返回配置。"""
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

@app.post("/api/run/daily_briefing", status_code=status.HTTP_202_ACCEPTED)
def run_daily_briefing_async(request: DailyBriefingRequest):
    """
    异步启动每日公告简报脚本。
    立即返回一个任务ID，客户端需要轮询状态接口。
    """
    print(f"--- [INFO] Received async request for daily briefing: {request.startDate} to {request.endDate} ---")
    
    config = get_config_safely()
    check_secrets(config)

    task_id = get_expected_report_filename(request.startDate, request.endDate)
    
    # 清理旧的已完成任务
    for tid in list(tasks.keys()):
        if tasks[tid]["process"].poll() is not None:
            del tasks[tid]

    # 如果任务已在运行，则不重复启动
    if task_id in tasks and tasks[task_id]["process"].poll() is None:
        raise HTTPException(status_code=409, detail=f"任务 '{task_id}' 已在运行中。")

    script_path = os.path.join(scripts_dir, "daily_briefing.py")
    command = [
        "python3", 
        script_path, 
        "--start-date", request.startDate, 
        "--end-date", request.endDate,
        "--stock-source", request.stockSource
    ]
    print(f"--- [INFO] Executing command in background: {' '.join(command)} ---")
    
    # 使用 Popen 在后台启动脚本
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', cwd=backend_dir)
    
    # 存储进程对象
    tasks[task_id] = {"process": process, "start_time": time.time()}
    
    return {"message": "任务已启动", "task_id": task_id}

@app.get("/api/status/daily_briefing/{task_id}")
def get_daily_briefing_status(task_id: str):
    """
    查询每日简报任务的状态。
    """
    task = tasks.get(task_id)
    if not task:
        # 如果任务不在内存中，检查文件是否已存在（适用于服务重启后查询旧任务）
        report_path = os.path.join(reports_dir, task_id)
        if os.path.exists(report_path):
            return {"status": "complete", "report_url": f"/reports/{task_id}"}
        raise HTTPException(status_code=404, detail="任务不存在或已完成并被清理。")

    process = task["process"]
    return_code = process.poll()

    if return_code is None:
        # 进程仍在运行
        elapsed_time = round(time.time() - task["start_time"])
        return {"status": "running", "message": f"任务正在运行中... 已持续 {elapsed_time} 秒。"}
    else:
        # 进程已结束，从任务字典中移除
        del tasks[task_id]
        
        if return_code == 0:
            # 成功
            report_path = os.path.join(reports_dir, task_id)
            if os.path.exists(report_path):
                return {"status": "complete", "report_url": f"/reports/{task_id}"}
            else:
                stdout, stderr = process.communicate()
                return {"status": "error", "detail": f"脚本执行成功但未找到报告文件。脚本输出: {stdout or stderr}"}
        else:
            # 失败
            stdout, stderr = process.communicate()
            return {"status": "error", "detail": f"脚本执行失败。错误: {stderr or stdout}"}

@app.post("/api/run/investment_report")
def run_investment_report(request: InvestmentReportRequest):
    """执行投资研究报告流水线，前置检查密钥。"""
    config = get_config_safely()
    check_secrets(config) 

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
        # 这个任务通常较快，暂时保持同步执行，如果未来也变慢，可改造成异步
        subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', cwd=scripts_dir, timeout=300)
        
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