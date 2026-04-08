"""
Step 6: 用户画像系统
使用 step 1 已导入的 research_comments，LLM 分类 + 画像生成。

Usage:
    python scripts/research/06_user_persona.py
"""
from __future__ import annotations

import sqlite3
import json
import asyncio
import sys
from pathlib import Path

import httpx
from openai import AsyncOpenAI

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    RESEARCH_DB, LLM_DIR,
    API_KEY, API_BASE, MODEL_FAST, MODEL_PRO,
    FLASH_CONCURRENCY, ALL_CATEGORIES,
)


def get_client() -> AsyncOpenAI:
    http_client = httpx.AsyncClient(proxy=None, trust_env=False, timeout=httpx.Timeout(120.0, connect=30.0))
    return AsyncOpenAI(api_key=API_KEY, base_url=API_BASE, http_client=http_client)


def ensure_classification_columns(cursor):
    """确保 research_comments 表有 LLM 分类列"""
    existing = {r[1] for r in cursor.execute("PRAGMA table_info(research_comments)")}
    additions = {
        "category": "TEXT",
        "sentiment": "TEXT",
        "user_type": "TEXT",
        "intent": "TEXT",
        "emotion_level": "INTEGER",
        "classified_at": "TIMESTAMP",
    }
    for col, dtype in additions.items():
        if col not in existing:
            cursor.execute(f"ALTER TABLE research_comments ADD COLUMN {col} {dtype}")


def assign_categories(cursor):
    """通过 note_id 关联，给评论分配品类"""
    cursor.execute("""
        UPDATE research_comments
        SET category = (
            SELECT rn.category FROM research_notes rn
            WHERE rn.note_id = research_comments.note_id
        )
        WHERE category IS NULL AND note_id IS NOT NULL AND note_id != ''
    """)
    cursor.execute("SELECT COUNT(*) FROM research_comments WHERE category IS NOT NULL")
    assigned = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM research_comments")
    total = cursor.fetchone()[0]
    print(f"  品类关联: {assigned}/{total} 条评论已分配品类")


# ─── LLM 分类 ───

CLASSIFY_PROMPT = """对以下小红书评论进行分类。每条评论输出一个 JSON 对象。

分类维度：
- sentiment: positive / negative / neutral
- user_type: 种草型 / 经验型 / 质疑型 / 求购型 / 调侃型 / 路人型
- intent: 赞美 / 追问 / 分享经验 / 质疑 / 求链接 / 吐槽 / 互动 / 争论
- emotion_level: 1-5 (1=平淡, 5=激动)

输出 JSON 数组：
[
  {{"id": "评论ID", "sentiment": "...", "user_type": "...", "intent": "...", "emotion_level": N}},
  ...
]

评论数据：
{comments}"""


async def classify_batch(client: AsyncOpenAI, batch: list[dict], semaphore: asyncio.Semaphore) -> list[dict]:
    async with semaphore:
        try:
            comments_text = "\n".join(
                f'ID:{c["id"]} 内容:{c["text"][:100]}'
                for c in batch
            )
            response = await client.chat.completions.create(
                model=MODEL_FAST,
                messages=[
                    {"role": "system", "content": "你是评论分析专家，只输出 JSON 数组。"},
                    {"role": "user", "content": CLASSIFY_PROMPT.format(comments=comments_text)},
                ],
                max_completion_tokens=1500,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            return json.loads(raw)
        except Exception as e:
            print(f"    分类失败: {e}")
            return []


async def run_classification():
    print("\n=== 6.2 LLM 评论分类 (mimo-v2-flash) ===")

    conn = sqlite3.connect(RESEARCH_DB)
    cursor = conn.cursor()
    client = get_client()
    semaphore = asyncio.Semaphore(FLASH_CONCURRENCY)

    cursor.execute(
        "SELECT comment_id, content FROM research_comments WHERE sentiment IS NULL AND content != '' LIMIT 5000"
    )
    rows = cursor.fetchall()
    if not rows:
        print("  无待分类评论")
        conn.close()
        return

    print(f"  待分类: {len(rows)} 条")

    batch_size = 10
    total_classified = 0
    tasks = []

    for i in range(0, len(rows), batch_size):
        batch = [{"id": r[0], "text": r[1]} for r in rows[i:i+batch_size]]
        tasks.append((i, classify_batch(client, batch, semaphore)))

    # Run in concurrent batches of 10
    for chunk_start in range(0, len(tasks), 10):
        chunk = tasks[chunk_start:chunk_start+10]
        results = await asyncio.gather(*(t[1] for t in chunk))

        for (i, _), batch_results in zip(chunk, results):
            for r in batch_results:
                cid = r.get("id")
                if not cid:
                    continue
                cursor.execute("""
                    UPDATE research_comments
                    SET sentiment=?, user_type=?, intent=?, emotion_level=?, classified_at=CURRENT_TIMESTAMP
                    WHERE comment_id=?
                """, (r.get("sentiment"), r.get("user_type"), r.get("intent"),
                      r.get("emotion_level"), cid))
                total_classified += 1

        conn.commit()
        done = min(chunk_start + 10, len(tasks)) * batch_size
        print(f"    进度: {min(done, len(rows))}/{len(rows)}")

    print(f"  已分类: {total_classified} 条")
    conn.close()
    await client.close()


# ─── 画像生成 ───

PERSONA_PROMPT = """你是小红书用户研究专家。以下是 {category} 品类评论的分类统计结果和示例评论。

请生成 5-8 种典型用户画像，输出 JSON：
{{
  "personas": [
    {{
      "name": "画像名称",
      "ratio": 0.30,
      "description": "简短描述",
      "language_style": "语言风格特征",
      "typical_phrases": ["常用短语1", "常用短语2", "常用短语3"],
      "comment_templates": ["模板1：{{product}}好好用！", "模板2"],
      "triggers": "什么内容会触发这类评论",
      "interaction_style": "倾向点赞/回复/争论/默默收藏"
    }}
  ],
  "controversy_patterns": [
    {{
      "topic": "争议话题",
      "side_a": "正方观点模板",
      "side_b": "反方观点模板",
      "escalation_path": ["起始→", "升级→", "爆发"]
    }}
  ],
  "category_characteristics": "该品类评论区的独特生态描述"
}}

分类统计：
{stats}

示例评论（按类型分组）：
{examples}"""


async def generate_personas():
    print("\n=== 6.3 用户画像生成 (mimo-v2-pro) ===")

    conn = sqlite3.connect(RESEARCH_DB)
    cursor = conn.cursor()
    client = get_client()

    all_personas = {}
    for cat in ALL_CATEGORIES:
        cursor.execute("""
            SELECT user_type, COUNT(*), AVG(emotion_level)
            FROM research_comments
            WHERE category=? AND user_type IS NOT NULL
            GROUP BY user_type
        """, (cat,))
        type_stats = cursor.fetchall()
        if not type_stats:
            continue

        stats = [{"type": r[0], "count": r[1], "avg_emotion": round(r[2] or 0, 1)} for r in type_stats]

        examples = {}
        for s in stats:
            cursor.execute("""
                SELECT content FROM research_comments
                WHERE category=? AND user_type=?
                ORDER BY likes DESC LIMIT 5
            """, (cat, s["type"]))
            examples[s["type"]] = [r[0] for r in cursor.fetchall()]

        prompt = PERSONA_PROMPT.format(
            category=cat,
            stats=json.dumps(stats, ensure_ascii=False, indent=1),
            examples=json.dumps(examples, ensure_ascii=False, indent=1),
        )

        print(f"  [{cat}] 生成画像...")
        try:
            response = await client.chat.completions.create(
                model=MODEL_PRO,
                messages=[
                    {"role": "system", "content": "你是用户研究专家，只输出 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                max_completion_tokens=3000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(raw)
            all_personas[cat] = result
            n = len(result.get("personas", []))
            print(f"    生成 {n} 种画像")
        except Exception as e:
            print(f"    失败: {e}")

    out = LLM_DIR / "user_personas.json"
    out.write_text(json.dumps(all_personas, ensure_ascii=False, indent=2))
    print(f"  → {out}")

    conn.close()
    await client.close()
    return all_personas


async def main():
    print("=" * 60)
    print("Step 6: 用户画像系统")
    print("=" * 60)

    conn = sqlite3.connect(RESEARCH_DB)
    cursor = conn.cursor()

    # 确保分类列存在
    ensure_classification_columns(cursor)

    # 通过 note_id 关联品类
    print("\n=== 6.1 品类关联 ===")
    assign_categories(cursor)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM research_comments WHERE content != ''")
    total = cursor.fetchone()[0]
    conn.close()

    if total > 0:
        print(f"  评论总数: {total}")
        await run_classification()
        await generate_personas()
    else:
        print("\n无评论数据。请先运行 01_import_data.py 导入数据。")

    print("\n" + "=" * 60)
    print("Step 6 完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
