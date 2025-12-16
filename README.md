# General Stock Investment Decision System (Project Seed)

### An AI-native Investment Decision Support & Strategy Toolkit for General Stock Markets
### AI股票投资决策辅助系统 (项目种子) - 面向全市场

![Version](https://img.shields.io/badge/version-v0.1--seed-blue.svg)
![Framework](https://img.shields.io/badge/framework-Next.js%20/%20FastAPI-lightgrey.svg)
![Python Version](https://img.shields.io/badge/python-3.9+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

这是一个**项目种子 (Project Seed)**，旨在启动一个全新的、通用的 **AI股票投资决策辅助系统**。它基于成熟的 `bsetoolkit v1.2 - 北交所辅助决策系统` 的代码基础，但将范围扩展至整个A股市场，并展望更宏大的AI驱动投资决策与执行的未来。

本项目旨在通过先进的AI技术，模拟专业投资团队的工作流程，为个人和机构投资者提供深度分析、智能决策和策略生成的能力。

## 核心功能 (Foundation & Vision)

本项目继承了 `bsetoolkit v1.2` 的强大基础，并将在此之上构建未来的AI投资系统。

### **现有基础 (Inherited from bsetoolkit v1.2)**
*   **📰 每日公告速递**: 自动获取、处理并由AI分析每日上市公司公告，生成摘要简报。已具备支持所有A股上市公司的底层能力。
*   **🔍 投资研究报告**: 对单一标的进行全面的自动化数据获取、图表绘制、AI分析，生成专业级研报。同样具备支持所有A股上市公司的底层能力。
*   **⚙️ 动态配置中心**: 灵活切换不同的大语言模型（兼容通义千问/OpenAI），管理API Keys、自定义股票池等。

### **未来展望 (Roadmap & Vision for this New Project)**
在此基础上，本新项目将逐步实现以下目标：
*   **🤖 多智能体投研决策委员会**: 建立一个由分析师、投资经理、决策委员会Agent组成，模拟真实投研机构的AI决策系统。
*   **📈 策略交易建议**: 基于委员会的决策，提供具体的交易策略生成与建议。
*   **📊 做市报价建议**: 提供动态、智能的买卖双边报价建议，服务于更专业的市场交易。

## 🛠️ 技术栈

- **前端 (Frontend)**:
    - **框架**: Next.js (App Router)
    - **语言**: TypeScript
    - **UI**: Bootstrap
    - **HTTP客户端**: Axios

- **后端 (Backend)**:
    - **框架**: FastAPI
    - **语言**: Python
    - **服务器**: Uvicorn

- **核心脚本依赖**:
    - **数据处理**: Pandas
    - **AI模型**: Dashscope, OpenAI
    - **PDF解析**: pdfplumber
    - **图表**: Matplotlib
    - **模板渲染**: Jinja2

## 📂 项目结构

```
general-stock-project/
├── frontend/               # Next.js 前端应用
│   ├── src/app/            # 页面和组件
│   ├── next.config.mjs     # Next.js 配置 (含代理)
│   └── package.json        # 前端依赖
├── backend/                # FastAPI 后端服务
│   ├── scripts/            # 核心Python脚本
│   │   ├── report/         # 投研报告的子模块
│   │   └── ...
│   ├── generated_reports/  # 每日简报的输出目录
│   ├── main.py             # API服务主文件
│   └── config.json         # 全局配置文件
└── README.md               # 本文件
```

## 🚀 安装与运行

### 首次设置

在首次运行项目前，请确保您的电脑已安装 Python 和 Node.js 环境，然后在项目根目录下按顺序执行以下步骤。

1.  **配置并安装后端**:
    ```bash
    # 进入后端目录
    cd backend
    
    # (重要) 从模板复制配置文件，然后用您自己的密钥填充它
    cp config.example.json config.json
    
    # 安装 Python 依赖
    pip install fastapi uvicorn python-multipart requests pandas pdfplumber dashscope openai markdown jinja2 matplotlib
    ```

2.  **安装前端依赖**:
    ```bash
    # 回到根目录，再进入前端目录
    cd ../frontend
    
    # 安装 Node.js 依赖
    npm install
    ```
    
3.  **安装主控制器依赖**:
    ```bash
    # 回到根目录
    cd ..
    
    # 安装 Node.js 依赖
    npm install
    ```

### 一键启动

完成首次设置后，每次启动项目只需在**项目根目录**下执行一个命令：

```bash
npm start
```

此命令将同时启动后端和前端服务，并在几秒后自动打开浏览器访问 `http://localhost:9201`。
要停止所有服务，只需在运行 `npm start` 的终端窗口中按下 `Ctrl + C`。

<h2> 💻 使用说明 </h2>

此项目基于 `bsetoolkit v1.2` 衍化而来。当前版本已包含其所有核心功能。未来的迭代将在此基础上，逐步实现更高级的AI投资决策功能。

1.  确保后端和前端服务都已根据上述指南成功启动。
2.  打开浏览器并访问 **http://localhost:9201**。
3.  **首次使用**: 强烈建议先进入 **设置** 页面，检查并填入您自己的API Keys等信息，然后点击页面底部的“保存设置”按钮。
4.  进入 **每日公告简报** 或 **投资研究报告** 页面，开始使用各项功能。

<h2> 路线图 (Roadmap for General Stock Project) </h2>

本项目旨在逐步实现以下目标：

1.  **策略库扩展与回测平台增强 (Strategy Hub & Backtesting Platform)**
    *   **策略多样化**: 引入更多经典的量化策略（如海龟交易法则、均值回归、动量策略），形成一个丰富的“策略市场”，让AI委员会根据不同市况推荐不同策略。
    *   **专业回测引擎**: 构建一个更强大、更可视化，支持多策略对比、参数敏感性分析、夏普比率等专业指标评估的回测平台。

2.  **AI系统自进化 (Self-Evolving AI)**
    *   **强化学习闭环**: 将回测平台的输出（策略盈亏、胜率等）作为反馈信号 (Reward），反向输入给“AI投研决策委员会”。
    *   **自我优化**: 系统可以通过强化学习，自主发现“哪种辩论结构”、“哪个Agent的权重更高”或“哪种决策倾向”在历史数据中能取得更好的收益。这使得整个AI决策系统能够自我迭代和进化。

3.  **投资组合管理 (Portfolio Management)**
    *   **多标的协同决策**: 从当前的“单标的深度分析”，升级为“多标的投资组合管理”。AI委员会不仅分析单个股票，更能给出资产配置、仓位管理、风险对冲的建议。
    *   **风险监控**: 实时监控整个投资组合的风险敞口，并提供动态调仓预警。

4.  **自动化交易集成 (Automated Trading Integration)**
    *   **模拟与实盘**: 利用券商API，实现从“策略建议”到“一键下单至模拟账户”甚至“（在严格监督下的）实盘交易”的最终闭环。

<h2> 贡献 (Contributing) </h2>

欢迎所有形式的贡献！无论是提交PR、报告Bug还是提出新功能的建议，都对项目非常有价值。

<h2> 许可 (License) </h2>

本项目采用 [MIT License](LICENSE) 授权。