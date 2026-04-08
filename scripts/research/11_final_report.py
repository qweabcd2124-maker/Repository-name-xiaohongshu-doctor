"""
Step 11: 最终研究报告生成
汇总所有分析结果，调用 LLM 生成完整研究报告 + 故事性叙述。

Usage:
    python scripts/research/11_final_report.py
"""
from __future__ import annotations

import json
import asyncio
import sys
from pathlib import Path
from datetime import datetime

import httpx
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_DIR, STATS_DIR, LLM_DIR, CHARTS_DIR, API_KEY, API_BASE, MODEL_PRO


def get_client() -> AsyncOpenAI:
    http_client = httpx.AsyncClient(proxy=None, trust_env=False, timeout=httpx.Timeout(300.0, connect=30.0))
    return AsyncOpenAI(api_key=API_KEY, base_url=API_BASE, http_client=http_client)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


REPORT_PROMPT = """你是一位数据科学研究员，正在为一个黑客松竞赛项目撰写研究报告。
这份报告需要体现专业深度，同时具备故事性——能在 PPT 和路演中使用。

## 研究背景

薯医 NoteRx 是一个小红书笔记诊断平台。我们采集了真实小红书笔记数据，
通过「传统统计分析 + LLM 深度分析」双轨方法，建立了量化评分模型。

## 输入数据

### Model A 评分模型
{model_a}

### 模型验证结果
{validation}

### 用户画像（Model B，如有）
{personas}

### 统计发现摘要
{stats_summary}

## 要求

请撰写一份 **中文研究报告**，Markdown 格式，包含：

1. **研究概览**（100字）：样本量、方法、核心发现
2. **方法论**（200字）：双轨分析如何互补
3. **核心发现**（每品类一段，每段 100-150 字）：
   - 最关键的 2-3 个发现
   - 具体数字支撑
   - 反直觉的结论（如果有）
4. **量化评分标准**：每品类的「黄金参数」表格
5. **模型验证**：准确率、相关性、可信度分析
6. **用户画像研究**（如有数据）
7. **局限性**（诚实但简短）
8. **故事性收尾**：用一两句话总结这项研究的价值——
   "这不是 AI 拍脑袋，而是用数据说话"

每个发现都要配一个**可以在 PPT 上直接使用的金句**，用 `> ` 引用格式标出。

报告目标读者：黑客松评委（产品人、技术人、投资人）。
"""


async def main():
    print("=" * 60)
    print("Step 11: 最终研究报告")
    print("=" * 60)

    model_a = load_json(OUTPUT_DIR / "model_a_scoring.json")
    validation = load_json(OUTPUT_DIR / "model_validation.json")
    personas = load_json(LLM_DIR / "user_personas.json")
    desc_stats = load_json(STATS_DIR / "descriptive_stats.json")

    # 精简统计摘要
    stats_summary = {}
    for cat, d in desc_stats.items():
        stats_summary[cat] = {
            "total": d.get("total", 0),
            "viral_count": d.get("viral_count", 0),
            "avg_engagement": d.get("engagement", {}).get("mean", 0),
            "image_vs_video": d.get("image_vs_video", {}),
        }

    prompt = REPORT_PROMPT.format(
        model_a=json.dumps(model_a, ensure_ascii=False, indent=1)[:3000],
        validation=json.dumps(validation, ensure_ascii=False, indent=1)[:1500],
        personas=json.dumps(
            {k: {"persona_count": len(v.get("personas", []))} for k, v in personas.items()},
            ensure_ascii=False, indent=1
        ) if personas else "暂无评论数据，画像研究待后续数据",
        stats_summary=json.dumps(stats_summary, ensure_ascii=False, indent=1)[:1500],
    )

    client = get_client()
    print("调用 mimo-v2-pro 生成研究报告...")

    try:
        response = await client.chat.completions.create(
            model=MODEL_PRO,
            messages=[
                {"role": "system", "content": "你是数据科学研究员，输出 Markdown 格式研究报告。"},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=6000,
        )
        report_text = response.choices[0].message.content

        # 添加头部元信息
        header = f"""---
title: NoteRx 数据研究报告
date: {datetime.now().strftime('%Y-%m-%d')}
method: 传统统计 (Track A) + LLM 深度分析 (Track B)
model: {MODEL_PRO}
---

"""

        # 添加图表引用
        charts = list(CHARTS_DIR.glob("*.png"))
        if charts:
            chart_section = "\n\n---\n\n## 附录：研究图表\n\n"
            for c in sorted(charts):
                chart_section += f"### {c.stem}\n\n![{c.stem}](../../data/research_output/charts/{c.name})\n\n"
            report_text += chart_section

        out = OUTPUT_DIR / "final_research_report.md"
        out.write_text(header + report_text)
        print(f"\n报告已生成: {out}")
        print(f"报告长度: {len(report_text)} 字符")

    except Exception as e:
        print(f"报告生成失败: {e}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
