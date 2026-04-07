# 💊 薯医 NoteRx

**AI驱动的小红书笔记诊断平台 —— 用数据告诉你，你的笔记为什么没火。**

> 你的笔记，值得被看见。

## 产品简介

薯医（NoteRx）是一个面向小红书创作者的 AI 笔记诊断工具。用户上传笔记的标题、正文、封面和标签后，平台通过 **多 Agent 辩论架构** 和 **真实数据 Baseline 对比**，从内容、视觉、增长策略、用户反应四个维度生成全面的诊断报告。

### 核心特色

- **多 Agent 辩论诊断**：5 个 AI 专家（内容分析师、视觉诊断师、增长策略师、用户模拟器、综合裁判）并行诊断，互相质疑，给出更全面准确的诊断
- **量化 Baseline 对比**：基于数千条真实小红书笔记数据建立评价基线，用数据而非玄学给建议
- **AI 模拟评论区**：预测真实用户看到笔记后的反应
- **可分享诊断卡片**：一键导出精美诊断报告卡片，本身就是社交内容

## 技术架构

```
前端 (React + TypeScript + Tailwind CSS + ECharts)
  ↓
API Gateway (FastAPI + Pydantic)
  ↓
┌─────────────────────────────────────────┐
│         多模态解析层                       │
│  文本分析(jieba) | 图像分析(OpenCV) | OCR  │
└──────────────────┬──────────────────────┘
                   ↓
         Baseline 对比引擎 (SQLite)
                   ↓
┌─────────────────────────────────────────┐
│       多 Agent 编排引擎 (GPT-4o)          │
│                                          │
│  内容Agent ←→ 视觉Agent (并行诊断)        │
│  增长Agent ←→ 用户Agent                  │
│           ↓                              │
│      Agent 辩论轮                         │
│           ↓                              │
│      综合裁判Agent → 最终报告              │
└─────────────────────────────────────────┘
```

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.9
- OpenAI API Key (GPT-4o)

### 安装与运行

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/noterx.git
cd noterx

# 2. 配置环境变量
cp .env.example backend/.env
# 编辑 backend/.env，填入你的 API Key

# 3. 初始化数据库
python3 scripts/init_db.py
python3 scripts/seed_data.py
python3 scripts/compute_baseline.py

# 4. 一键启动
./start.sh
```

访问 `http://localhost:5173` 开始使用。

### 手动启动

```bash
# 后端
cd backend
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 项目结构

```
noterx/
├── frontend/                 # React 前端
│   └── src/
│       ├── components/       # UI 组件
│       ├── pages/            # 页面（首页/诊断/报告）
│       └── utils/            # API 工具和 fallback 数据
├── backend/                  # Python 后端
│   ├── app/
│   │   ├── api/              # FastAPI 路由
│   │   ├── agents/           # 多 Agent 模块
│   │   │   └── prompts/      # Agent System Prompt
│   │   ├── analysis/         # 多模态分析（文本/图像/OCR）
│   │   ├── baseline/         # Baseline 对比引擎
│   │   └── models/           # Pydantic 数据模型
│   └── data/                 # SQLite 数据库
└── scripts/                  # 数据初始化脚本
```

## 团队

**PageOne** — 五个13岁的创作者，用AI解决自己的问题。

## License

Apache License 2.0

---

*小红书黑客松巅峰赛作品 #小红书黑客松巅峰赛*
