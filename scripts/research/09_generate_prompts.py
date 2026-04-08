"""
Step 9: 生成增强版 Agent 提示词
基于 Model A（评分参数）+ Model B（用户画像），生成数据驱动的提示词。

Usage:
    python scripts/research/09_generate_prompts.py
"""
from __future__ import annotations

import json
import asyncio
import sys
from pathlib import Path

import httpx
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).parent))
from config import OUTPUT_DIR, LLM_DIR, API_KEY, API_BASE, MODEL_PRO, ALL_CATEGORIES


def get_client() -> AsyncOpenAI:
    http_client = httpx.AsyncClient(proxy=None, trust_env=False, timeout=httpx.Timeout(180.0, connect=30.0))
    return AsyncOpenAI(api_key=API_KEY, base_url=API_BASE, http_client=http_client)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


PROMPT_GEN_TEMPLATE = """你是一个 AI 系统设计专家。基于以下数据研究成果，为小红书笔记诊断系统的各个 Agent 生成优化后的提示词片段。

## 数据研究成果（{category} 品类）

### 量化评分参数
{scoring_params}

### 内容模式发现
{content_patterns}

### 用户画像（如有）
{personas}

## 要求

为以下 5 个 Agent 各生成一段「数据注入提示词」（200-300 字），用于拼接到现有 system prompt 之后，让 Agent 的诊断更精准：

1. **ContentAgent（内容分析师）**：注入标题模式、内容结构、最优参数
2. **VisualAgent（视觉诊断师）**：注入封面风格分布、最佳视觉参数
3. **GrowthAgent（增长策略师）**：注入标签策略、发布时段、互动数据
4. **UserSimAgent（用户模拟器）**：注入用户画像、评论风格模板
5. **JudgeAgent（综合裁判）**：注入评分权重、基线数据

输出 JSON：
{{
  "content_agent_data_prompt": "...",
  "visual_agent_data_prompt": "...",
  "growth_agent_data_prompt": "...",
  "user_sim_agent_data_prompt": "...",
  "judge_agent_data_prompt": "..."
}}
"""


async def main():
    print("=" * 60)
    print("Step 9: 生成增强版 Agent 提示词")
    print("=" * 60)

    model_a = load_json(OUTPUT_DIR / "model_a_scoring.json")
    personas = load_json(LLM_DIR / "user_personas.json")

    if not model_a:
        print("Model A 未找到，请先运行 08_build_scoring_model.py")
        return

    client = get_client()
    all_prompts = {}

    for cat in ALL_CATEGORIES:
        if cat not in model_a:
            continue

        scoring = model_a[cat]
        cat_personas = personas.get(cat, {})

        prompt = PROMPT_GEN_TEMPLATE.format(
            category=cat,
            scoring_params=json.dumps(scoring, ensure_ascii=False, indent=1)[:2000],
            content_patterns=json.dumps({
                "title_patterns": scoring.get("title_patterns", []),
                "content_structure": scoring.get("content_structure", []),
                "top_tags": scoring.get("top_tags", []),
            }, ensure_ascii=False, indent=1),
            personas=json.dumps(cat_personas, ensure_ascii=False, indent=1)[:1500] if cat_personas else "暂无评论数据",
        )

        print(f"  [{cat}] 生成提示词...")
        try:
            response = await client.chat.completions.create(
                model=MODEL_PRO,
                messages=[
                    {"role": "system", "content": "你是 AI 系统设计专家，只输出 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(raw)
            all_prompts[cat] = result
            print(f"    生成 {len(result)} 个 Agent 提示词")
        except Exception as e:
            print(f"    失败: {e}")

    out = OUTPUT_DIR / "enhanced_agent_prompts.json"
    out.write_text(json.dumps(all_prompts, ensure_ascii=False, indent=2))
    print(f"\n提示词已保存: {out}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
