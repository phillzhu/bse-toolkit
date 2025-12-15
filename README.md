
# BSE Toolkit v1.2 - 北交所辅助决策系统

一个利用大语言模型（LLM）为北京证券交易所（BSE）提供辅助投资决策支持的全栈应用系统。

该系统集成了数据获取、AI分析、图表生成和报告渲染等功能，通过一个现代化的Web界面提供给用户。

## ✨ 主要功能

- **每日公告简报**:
    - 支持**日期范围**查询，可生成单日、单周或任意时段的简报。
    - 支持**股票范围**选择，可在“北交所全市场”和“自选股池”之间动态切换。
    - 自动获取公告，通过AI进行两阶段（快速初筛+深度分析）处理，生成HTML格式简报。
- **投资研究报告**:
    - 针对单一股票，在执行时可**动态指定财报报告期**。
    - 自动执行完整的数据获取、图表绘制、AI分析和报告生成流程，产出专业精美的投研报告。
- **动态配置中心**:
    - 提供一个用户友好的“设置”页面，对配置项进行了清晰的逻辑分组。
    - 支持在多种大语言模型（通义千问/OpenAI兼容接口）之间切换，并为不同任务（初筛/深度分析）配置不同模型。
    - 支持管理全局API Keys、自选股池、iFind参数等。
- **一键启动**:
    - 在项目根目录提供 `npm start` 命令，可一键并行启动前后端服务，并自动打开浏览器。

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
bsetoolkit v1.2/
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

在首次运行项目前，需要完成以下配置和依赖安装。

1.  **创建并配置 `config.json` 文件**:
    ```bash
    # 进入后端目录
    cd "/Users/phillzhu/bsetoolkit v1.2/backend"
    # 将模板文件复制为您的本地配置文件
    cp config.example.json config.json
    ```
    复制后，请打开 `config.json` 文件，并将里面的占位符 (`YOUR_..._HERE`) 替换为您自己的真实密钥。

2.  **安装后端依赖**:
    ```bash
    # 确保您仍在 backend 目录下
    # 安装 Python 依赖
    pip install fastapi uvicorn python-multipart requests pandas pdfplumber dashscope openai markdown jinja2 matplotlib
    ```

3.  **安装前端依赖**:
    ```bash
    # 进入前端目录
    cd "../frontend"
    # 安装 Node.js 依赖
    npm install
    ```
    
4.  **安装主控制器依赖**:
    ```bash
    # 进入项目根目录
    cd ".."
    # 安装 Node.js 依赖
    npm install
    ```

### 一键启动

完成首次设置后，每次启动项目只需执行以下命令：

```bash
# 1. 进入项目根目录
cd "/Users/phillzhu/bsetoolkit v1.2"

# 2. 启动！
npm start
```

此命令将同时启动后端和前端服务，并在几秒后自动打开浏览器访问 `http://localhost:9201`。
要停止所有服务，只需在运行 `npm start` 的终端窗口中按下 `Ctrl + C`。

## 💻 使用说明

1.  确保后端和前端服务都已根据上述指南成功启动。
2.  打开浏览器并访问 **http://localhost:9201**。
3.  **首次使用**: 强烈建议先进入 **设置** 页面，检查并填入您自己的API Keys等信息，然后点击页面底部的“保存设置”按钮。
4.  进入 **每日公告简报** 或 **投资研究报告** 页面，开始使用各项功能。
