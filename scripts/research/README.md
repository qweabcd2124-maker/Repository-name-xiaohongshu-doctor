# NoteRx 数据研究系统

## 研究目标

从真实小红书笔记和评论数据中，训练出两个「模型」（参数集 + 提示词），提升薯医诊断准确性：

- **Model A：内容评分模型** — 预测笔记互动表现，输出维度评分参数
- **Model B：用户画像模型** — 生成真实感评论，输出画像模板和评论生成提示词

## 流程总览

```
原始数据（xlsx/csv）
  │
  ├─ 01_normalize.py ─────── 格式统一 → unified CSV + SQLite
  ├─ 02_download_covers.py ─ 批量下载封面图片
  ├─ 03_feature_engineering.py ── 衍生特征计算
  │
  ├─── Track A: 传统统计 ─────────────────────────────────
  │    ├─ 04_traditional_analysis.py  描述统计/相关性/回归
  │    └─ 输出: stats/*.json + charts/*.png
  │
  ├─── Track B: LLM 深度分析 ─────────────────────────────
  │    ├─ 05_cover_vision.py    mimo-v2-omni 封面视觉理解
  │    ├─ 06_content_llm.py     mimo-v2-pro 内容模式总结
  │    └─ 输出: llm/*.json
  │
  ├─── Track C: 用户画像 ─────────────────────────────────
  │    ├─ 07_comment_persona.py  评论分类 + 画像生成
  │    └─ 输出: personas/*.json
  │
  ├─ 08_build_scoring_model.py ── 合并双轨 → 评分参数
  ├─ 09_generate_prompts.py ───── 生成增强版 Agent 提示词
  ├─ 10_validate_model.py ─────── 用已知爆款反向验证
  └─ 11_final_report.py ──────── 最终研究报告 + 可视化

产出目录: data/research_output/
研究日志: scripts/research/research_journal.md
```

## 运行方式

```bash
# 全流程（数据放在 data/帖子数据_待处理/ 和 data/评论数据/）
python3 scripts/research/run_all.py

# 单步运行
python3 scripts/research/01_normalize.py
python3 scripts/research/04_traditional_analysis.py
python3 scripts/research/05_cover_vision.py --category food
# ...

# 模型使用（三档）
MODEL_FAST=mimo-v2-flash   # 评论快速分类，批量处理
MODEL_PRO=mimo-v2-pro      # 1M上下文，内容模式总结，报告生成
MODEL_OMNI=mimo-v2-omni    # 多模态，封面/视频视觉分析
```

## 依赖

```bash
pip install openpyxl pandas numpy scipy scikit-learn matplotlib seaborn openai httpx
```
