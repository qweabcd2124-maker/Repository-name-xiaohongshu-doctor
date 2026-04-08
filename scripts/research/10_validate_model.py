"""
Step 10: 模型验证
用已知爆款 vs 普通笔记反向验证 Model A 的评分准确性。

Usage:
    python scripts/research/10_validate_model.py
"""
from __future__ import annotations

import sqlite3
import json
import sys
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from config import RESEARCH_DB, OUTPUT_DIR, CHARTS_DIR, ALL_CATEGORIES

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def score_note(note: dict, params: dict) -> float:
    """基于 Model A 参数给单条笔记打分"""
    weights = params.get("weights", {})
    sp = params.get("scoring_params", {})
    score = 0.0

    # 标题质量
    tl = note.get("title_length", 0)
    tl_opt = sp.get("title_length", {}).get("optimal", {})
    tl_min, tl_max = tl_opt.get("min", 10), tl_opt.get("max", 25)
    if tl_min <= tl <= tl_max:
        title_score = 80 + 20 * (1 - abs(tl - (tl_min + tl_max) / 2) / ((tl_max - tl_min) / 2 + 1))
    elif tl < tl_min:
        title_score = max(30, 80 * tl / tl_min)
    else:
        title_score = max(40, 80 - (tl - tl_max) * 2)

    title_score += note.get("has_numbers", 0) * 5
    title_score += min(note.get("title_hook_count", 0), 3) * 3
    score += min(title_score, 100) * weights.get("title_quality", 0.2)

    # 标签策略
    tc = note.get("tag_count", 0)
    tc_opt = sp.get("tag_count", {}).get("optimal", {})
    tc_best = tc_opt.get("best", 6) if isinstance(tc_opt, dict) else 6
    tag_score = max(0, 100 - abs(tc - tc_best) * 10)
    score += tag_score * weights.get("tag_strategy", 0.15)

    # 内容质量
    cl = note.get("content_length", 0)
    cl_opt = sp.get("content_length", {}).get("optimal", {})
    cl_min, cl_max = cl_opt.get("min", 100), cl_opt.get("max", 600)
    if cl_min <= cl <= cl_max:
        content_score = 85
    elif cl < cl_min:
        content_score = max(20, 85 * cl / max(cl_min, 1))
    else:
        content_score = max(50, 85 - (cl - cl_max) / 50)
    score += min(content_score, 100) * weights.get("content_quality", 0.15)

    # 图片数量
    ic = note.get("image_count", 0)
    ic_opt = sp.get("image_count", {}).get("optimal", {})
    ic_min, ic_max = ic_opt.get("min", 3), ic_opt.get("max", 9)
    if ic_min <= ic <= ic_max:
        img_score = 80
    else:
        img_score = max(30, 80 - abs(ic - (ic_min + ic_max) / 2) * 5)
    score += img_score * weights.get("engagement_potential", 0.15)

    # 视觉（暂用基础分）
    score += 60 * weights.get("visual_quality", 0.2)

    return min(round(score, 1), 100)


def main():
    print("=" * 60)
    print("Step 10: 模型验证")
    print("=" * 60)

    model_a = load_json(OUTPUT_DIR / "model_a_scoring.json")
    if not model_a:
        print("Model A 未找到，请先运行 08_build_scoring_model.py")
        return

    conn = sqlite3.connect(RESEARCH_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    validation_results = {}
    all_scores = []
    all_actuals = []

    for cat in ALL_CATEGORIES:
        if cat not in model_a:
            continue

        params = model_a[cat]
        cursor.execute("""
            SELECT title_length, content_length, tag_count, image_count,
                   has_numbers, title_hook_count, has_emoji,
                   engagement, is_viral
            FROM research_notes WHERE category=?
        """, (cat,))
        rows = cursor.fetchall()
        if not rows:
            continue

        scores = []
        actuals = []
        viral_scores = []
        normal_scores = []

        for row in rows:
            note = dict(row)
            s = score_note(note, params)
            scores.append(s)
            actuals.append(note["engagement"])
            if note["is_viral"]:
                viral_scores.append(s)
            else:
                normal_scores.append(s)

        all_scores.extend(scores)
        all_actuals.extend(actuals)

        # 相关性
        if len(scores) > 10:
            corr, p_val = stats.spearmanr(scores, actuals)
        else:
            corr, p_val = 0, 1

        # 爆款 vs 普通评分差异
        viral_mean = np.mean(viral_scores) if viral_scores else 0
        normal_mean = np.mean(normal_scores) if normal_scores else 0

        # 分类准确率（评分 > 中位数 → 预测为好笔记）
        median_score = np.median(scores)
        correct = sum(
            1 for s, r in zip(scores, rows)
            if (s > median_score and r["is_viral"]) or (s <= median_score and not r["is_viral"])
        )
        accuracy = correct / len(rows) * 100

        validation_results[cat] = {
            "sample_size": len(rows),
            "score_engagement_correlation": round(float(corr), 4),
            "p_value": round(float(p_val), 6),
            "significant": bool(p_val < 0.05),
            "viral_avg_score": round(float(viral_mean), 1),
            "normal_avg_score": round(float(normal_mean), 1),
            "score_gap": round(float(viral_mean - normal_mean), 1),
            "classification_accuracy": round(accuracy, 1),
        }

        sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
        print(f"  [{cat}] r={corr:.3f}{sig}, 爆款均分={viral_mean:.1f} vs 普通={normal_mean:.1f}, 准确率={accuracy:.1f}%")

    # 总体相关性
    if len(all_scores) > 20:
        total_corr, total_p = stats.spearmanr(all_scores, all_actuals)
        validation_results["_overall"] = {
            "total_samples": len(all_scores),
            "correlation": round(float(total_corr), 4),
            "p_value": round(float(total_p), 6),
        }
        print(f"\n  总体: r={total_corr:.3f}, n={len(all_scores)}")

    # 可视化：模型评分 vs 实际互动（散点图）
    if all_scores:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(all_scores, np.log1p(all_actuals), alpha=0.4, s=20, c="#ff2442")
        ax.set_xlabel("Model A 预测评分", fontsize=12)
        ax.set_ylabel("log(实际互动量+1)", fontsize=12)
        ax.set_title("模型验证：评分 vs 实际互动量", fontsize=14, fontweight="bold")

        # 添加趋势线
        z = np.polyfit(all_scores, np.log1p(all_actuals), 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(all_scores), max(all_scores), 100)
        ax.plot(x_line, p(x_line), "--", color="#333", linewidth=1.5, alpha=0.7,
                label=f"趋势线 (r={total_corr:.3f})")
        ax.legend()
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / "model_validation.png", dpi=150)
        plt.close()
        print(f"  → {CHARTS_DIR / 'model_validation.png'}")

    # 保存
    out = OUTPUT_DIR / "model_validation.json"
    out.write_text(json.dumps(validation_results, ensure_ascii=False, indent=2))
    print(f"\n验证结果: {out}")

    conn.close()


if __name__ == "__main__":
    main()
