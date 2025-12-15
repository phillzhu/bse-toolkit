
import subprocess
import json
import os
import glob
from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ====================================================================
# 1. App 和路径配置
# ====================================================================
app = FastAPI()

# 获取 main.py 所在的目录
backend_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(backend_dir, "scripts")
reports_dir = os.path.join(backend_dir, "generated_reports")
investment_reports_dir = os.path.join(scripts_dir, "report")

# 确保报告目录存在
os.makedirs(reports_dir, exist_ok=True)
os.makedirs(investment_reports_dir, exist_ok=True)

# 配置文件路径
config_path = os.path.join(backend_dir, "config.json")

# --- 静态文件服务 ---
# 将 generated_reports 目录挂载到 /reports URL 路径
app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")
# 将 scripts/report 目录 (用于存放投研报告的图和html) 挂载到 /investment_reports
app.mount("/investment_reports", StaticFiles(directory=investment_reports_dir), name="investment_reports")


# ====================================================================
# 2. Pydantic 模型定义 (用于请求体验证)
# ====================================================================
class ConfigModel(BaseModel):
    llm: dict
    ifind: dict
    ifindPayload: dict
    ticker: str
    userInfo: str

class DailyBriefingRequest(BaseModel):
    date: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))

class InvestmentReportRequest(BaseModel):
    ticker: str
    userInfo: Optional[str] = ""

# ====================================================================
# 3. API Endpoints
# ====================================================================

@app.get("/api/config", response_model=ConfigModel)
def get_config():
    """读取并返回当前的配置"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="配置文件 config.json 未找到")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="配置文件格式错误")

@app.post("/api/config")
def update_config(new_config: ConfigModel):
    """更新并保存配置"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(new_config.dict(), f, indent=2, ensure_ascii=False)
        return {"message": "配置已成功更新"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入配置文件失败: {e}")

@app.post("/api/run/daily_briefing")
def run_daily_briefing(request: DailyBriefingRequest):
    """执行每日公告简报脚本"""
    script_path = os.path.join(scripts_dir, "daily_briefing.py")
    command = ["python3", script_path, "--date", request.date]
    
    print(f"正在执行命令: {' '.join(command)}")
    
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            cwd=backend_dir # 在 backend 目录执行
        )
        print("脚本输出:", process.stdout)
        if process.stderr:
            print("脚本错误输出:", process.stderr)

        # 构造预期的文件名并返回 URL
        date_formatted = datetime.strptime(request.date, "%Y-%m-%d").strftime("%Y%m%d")
        report_filename = f"daily_briefing_{date_formatted}.html"
        report_url = f"/reports/{report_filename}"
        
        # 检查文件是否真的生成了
        if not os.path.exists(os.path.join(reports_dir, report_filename)):
             raise HTTPException(status_code=500, detail=f"脚本执行成功，但未找到预期的报告文件: {report_filename}")

        return {"report_url": report_url}

    except subprocess.CalledProcessError as e:
        print(f"脚本执行失败: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"每日简报脚本执行失败: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未知错误: {e}")


@app.post("/api/run/investment_report")
def run_investment_report(request: InvestmentReportRequest):
    """执行投资研究报告流水线"""
    # 1. 更新 config.json 中的 ticker 和 userInfo
    try:
        with open(config_path, 'r+', encoding='utf-8') as f:
            config_data = json.load(f)
            config_data['ticker'] = request.ticker
            config_data['userInfo'] = request.userInfo
            f.seek(0)
            f.truncate()
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置文件以设置 Ticker 失败: {e}")

    # 2. 执行主流水线脚本
    script_path = os.path.join(scripts_dir, "run_report_pipeline_v1.1.py")
    command = ["python3", script_path]
    
    print(f"正在执行命令: {' '.join(command)}")

    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8',
            cwd=scripts_dir # 在 scripts 目录执行，因为流水线脚本中的路径是相对的
        )
        print("脚本输出:", process.stdout)
        if process.stderr:
            print("脚本错误输出:", process.stderr)

        # 3. 查找最新生成的 HTML 报告
        # run_report_pipeline_v1.1.py 会在 report 子目录中生成 html
        list_of_html_files = glob.glob(os.path.join(investment_reports_dir, '*.html'))
        if not list_of_html_files:
            raise HTTPException(status_code=500, detail="脚本执行成功，但未在 'scripts/report' 目录中找到任何HTML报告。")
        
        latest_report = max(list_of_html_files, key=os.path.getctime)
        report_filename = os.path.basename(latest_report)
        report_url = f"/investment_reports/{report_filename}"
        
        return {"report_url": report_url}

    except subprocess.CalledProcessError as e:
        print(f"脚本执行失败: {e}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise HTTPException(status_code=500, detail=f"投研报告脚本执行失败: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未知错误: {e}")

# ====================================================================
# 4. 启动命令 (用于本地开发)
# ====================================================================
if __name__ == "__main__":
    import uvicorn
    print("启动 FastAPI 服务，访问 http://127.0.0.1:8000")
    # 在 backend 目录运行: uvicorn main:app --reload
    uvicorn.run(app, host="127.0.0.1", port=8000)
