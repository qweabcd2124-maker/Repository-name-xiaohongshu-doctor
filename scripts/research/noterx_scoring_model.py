#!/usr/bin/env python3
"""
NoteRx 内容评分模型 (Model A) — 独立可运行程序
基于 874 条真实小红书笔记数据训练，双轨分析（传统统计 + LLM）。

Usage:
    # 评分单条笔记
    python noterx_scoring_model.py --title "5分钟学会这个做法" --content "今天教大家..." --category food --tags 5 --images 6

    # 批量评分 CSV
    python noterx_scoring_model.py --csv input.csv --output scored.csv

    # 输出模型参数
    python noterx_scoring_model.py --show-params

研究方法:
    Track A: Spearman 相关性 + 线性回归 + K-Means 聚类 + Kruskal-Wallis 检验
    Track B: LLM 内容模式分析 + 封面视觉分析 + 标签策略分析
    Model A: 基于回归系数的加权评分模型，per-category 参数优化
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from typing import Optional


# ═══════════════════════════════════════════════════════════════
# 模型参数（从 874 条真实数据训练得出）
# ═══════════════════════════════════════════════════════════════

MODEL_PARAMS = {
    "food": {
        "weights": {"title_quality": 0.573, "content_quality": 0.132, "visual_quality": 0.086, "tag_strategy": 0.097, "engagement_potential": 0.111},
        "title_length": {"min": 11, "max": 19, "viral_avg": 18.3},
        "content_length": {"min": 105, "max": 342},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 10},
        "baseline": {"avg_engagement": 33462, "median": 7333, "viral_threshold": 112965, "sample_size": 183},
        "r_squared": 0.106,
    },
    "fashion": {
        "weights": {"title_quality": 0.395, "content_quality": 0.125, "visual_quality": 0.250, "tag_strategy": 0.058, "engagement_potential": 0.172},
        "title_length": {"min": 11, "max": 20, "viral_avg": 14.0},
        "content_length": {"min": 92, "max": 224},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 10},
        "baseline": {"avg_engagement": 7507, "median": 2069, "viral_threshold": 18037, "sample_size": 278},
        "r_squared": 0.017,
    },
    "tech": {
        "weights": {"title_quality": 0.411, "content_quality": 0.125, "visual_quality": 0.103, "tag_strategy": 0.095, "engagement_potential": 0.267},
        "title_length": {"min": 12, "max": 20, "viral_avg": 17.5},
        "content_length": {"min": 87, "max": 517},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 1, "max": 6},
        "baseline": {"avg_engagement": 1275, "median": 175, "viral_threshold": 3325, "sample_size": 235},
        "r_squared": 0.177,
    },
    "travel": {
        "weights": {"title_quality": 0.376, "content_quality": 0.050, "visual_quality": 0.120, "tag_strategy": 0.312, "engagement_potential": 0.142},
        "title_length": {"min": 11, "max": 20, "viral_avg": 14.3},
        "content_length": {"min": 123, "max": 737},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 4, "max": 14},
        "baseline": {"avg_engagement": 16563, "median": 4538, "viral_threshold": 39426, "sample_size": 130},
        "r_squared": 0.138,
    },
    "lifestyle": {
        "weights": {"title_quality": 0.407, "content_quality": 0.083, "visual_quality": 0.071, "tag_strategy": 0.277, "engagement_potential": 0.162},
        "title_length": {"min": 10, "max": 20, "viral_avg": 19.4},
        "content_length": {"min": 24, "max": 148},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 1, "max": 8},
        "baseline": {"avg_engagement": 8038, "median": 773, "viral_threshold": 17097, "sample_size": 48},
        "r_squared": 0.396,
    },
    "beauty": {
        "weights": {"title_quality": 0.40, "content_quality": 0.15, "visual_quality": 0.20, "tag_strategy": 0.10, "engagement_potential": 0.15},
        "title_length": {"min": 10, "max": 20, "viral_avg": 16.0},
        "content_length": {"min": 100, "max": 400},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 3, "max": 9},
        "baseline": {"avg_engagement": 5000, "median": 1500, "viral_threshold": 15000, "sample_size": 0},
        "r_squared": None,
    },
    "fitness": {
        "weights": {"title_quality": 0.35, "content_quality": 0.15, "visual_quality": 0.15, "tag_strategy": 0.15, "engagement_potential": 0.20},
        "title_length": {"min": 10, "max": 22, "viral_avg": 16.0},
        "content_length": {"min": 80, "max": 500},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 8},
        "baseline": {"avg_engagement": 4000, "median": 1000, "viral_threshold": 12000, "sample_size": 0},
        "r_squared": None,
    },
    "home": {
        "weights": {"title_quality": 0.35, "content_quality": 0.15, "visual_quality": 0.20, "tag_strategy": 0.15, "engagement_potential": 0.15},
        "title_length": {"min": 10, "max": 20, "viral_avg": 15.0},
        "content_length": {"min": 100, "max": 500},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 4, "max": 12},
        "baseline": {"avg_engagement": 6000, "median": 2000, "viral_threshold": 18000, "sample_size": 0},
        "r_squared": None,
    },
}


# ═══════════════════════════════════════════════════════════════
# 特征提取
# ═══════════════════════════════════════════════════════════════

def detect_emoji(text: str) -> bool:
    return bool(re.search(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F900-\U0001F9FF\U00002702-\U000027B0✨🔥💚‼️⭐📸📊👍]",
        text or ""
    ))


def count_hooks(title: str) -> int:
    hooks = 0
    if re.search(r'\d+', title): hooks += 1
    if re.search(r'[！!？?]', title): hooks += 1
    if re.search(r'[｜|]', title): hooks += 1
    if re.search(r'[✨🔥‼️⭐💯]', title): hooks += 1
    if re.search(r'(必|绝了|太|超|巨|神仙|宝藏|救命)', title): hooks += 1
    return hooks


@dataclass
class NoteFeatures:
    title: str = ""
    content: str = ""
    category: str = "lifestyle"
    tag_count: int = 0
    image_count: int = 0

    @property
    def title_length(self) -> int:
        return len(self.title)

    @property
    def content_length(self) -> int:
        return len(self.content)

    @property
    def has_numbers(self) -> bool:
        return bool(re.search(r'\d+', self.title))

    @property
    def has_emoji(self) -> bool:
        return detect_emoji(self.title + self.content)

    @property
    def hook_count(self) -> int:
        return count_hooks(self.title)


# ═══════════════════════════════════════════════════════════════
# 评分引擎
# ═══════════════════════════════════════════════════════════════

def range_score(value: float, opt_min: float, opt_max: float, base: float = 80) -> float:
    """值在最优区间内得高分，区间外衰减"""
    if opt_min <= value <= opt_max:
        mid = (opt_min + opt_max) / 2
        half = (opt_max - opt_min) / 2 + 1
        return base + (100 - base) * (1 - abs(value - mid) / half)
    elif value < opt_min:
        return max(20, base * value / max(opt_min, 1))
    else:
        return max(40, base - (value - opt_max) * 2)


def score_note(features: NoteFeatures) -> dict:
    """
    对一条笔记进行多维度评分。

    Returns:
        {
            "total_score": float,           # 总分 0-100
            "dimensions": {                  # 各维度评分
                "title_quality": float,
                "content_quality": float,
                "visual_quality": float,
                "tag_strategy": float,
                "engagement_potential": float,
            },
            "diagnosis": [str, ...],         # 诊断建议
            "percentile_estimate": str,      # 预估百分位
        }
    """
    cat = features.category
    if cat not in MODEL_PARAMS:
        cat = "lifestyle"
    params = MODEL_PARAMS[cat]
    w = params["weights"]

    # ── 标题质量 ──
    tl = params["title_length"]
    title_score = range_score(features.title_length, tl["min"], tl["max"])
    title_score += features.has_numbers * 5
    title_score += min(features.hook_count, 3) * 3
    title_score += features.has_emoji * 2
    title_score = min(title_score, 100)

    # ── 内容质量 ──
    cl = params["content_length"]
    content_score = range_score(features.content_length, cl["min"], cl["max"], 85)
    content_score = min(content_score, 100)

    # ── 视觉质量（基于图片数量，无图像分析时的近似）──
    ic = params["image_count"]
    visual_score = range_score(features.image_count, ic["min"], ic["max"])
    visual_score = min(visual_score, 100)

    # ── 标签策略 ──
    tc = params["tag_count"]
    tag_score = max(0, 100 - abs(features.tag_count - tc["best"]) * 10)

    # ── 互动潜力（综合信号）──
    engagement_signals = 0
    if features.title_length >= tl["min"]: engagement_signals += 25
    if features.has_numbers: engagement_signals += 15
    if features.hook_count >= 2: engagement_signals += 20
    if tc["min"] <= features.tag_count <= tc["max"]: engagement_signals += 20
    if ic["min"] <= features.image_count <= ic["max"]: engagement_signals += 20
    engagement_score = min(engagement_signals, 100)

    # ── 加权总分 ──
    dimensions = {
        "title_quality": round(title_score, 1),
        "content_quality": round(content_score, 1),
        "visual_quality": round(visual_score, 1),
        "tag_strategy": round(tag_score, 1),
        "engagement_potential": round(engagement_score, 1),
    }

    total = sum(dimensions[k] * w[k] for k in w)
    total = min(round(total, 1), 100)

    # ── 诊断建议 ──
    diagnosis = []
    if features.title_length < tl["min"]:
        diagnosis.append(f"标题过短({features.title_length}字)，建议 {tl['min']}-{tl['max']} 字")
    elif features.title_length > tl["max"]:
        diagnosis.append(f"标题过长({features.title_length}字)，建议精简到 {tl['max']} 字内")
    if not features.has_numbers:
        diagnosis.append("标题缺少数字，加入数字可提升点击率")
    if features.hook_count == 0:
        diagnosis.append("标题缺少钩子元素（数字/emoji/感叹号/热词）")
    if features.content_length < cl["min"]:
        diagnosis.append(f"正文过短({features.content_length}字)，建议 {cl['min']}-{cl['max']} 字")
    if features.tag_count < tc["min"]:
        diagnosis.append(f"标签过少({features.tag_count}个)，建议 {tc['min']}-{tc['max']} 个")
    elif features.tag_count > tc["max"]:
        diagnosis.append(f"标签过多({features.tag_count}个)，建议精简到 {tc['max']} 个")
    if features.image_count < ic["min"]:
        diagnosis.append(f"图片过少({features.image_count}张)，建议 {ic['min']}-{ic['max']} 张")

    if not diagnosis:
        diagnosis.append("各项参数均在最优区间内，继续保持！")

    # ── 百分位预估 ──
    bl = params["baseline"]
    if total >= 85:
        pct = "前 10%（爆款潜力）"
    elif total >= 75:
        pct = "前 25%（优质内容）"
    elif total >= 65:
        pct = "中位水平（50%）"
    else:
        pct = "低于中位，建议优化"

    return {
        "total_score": total,
        "dimensions": dimensions,
        "weights": w,
        "diagnosis": diagnosis,
        "percentile_estimate": pct,
        "baseline": bl,
    }


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def show_params():
    print("NoteRx Model A — 品类评分参数")
    print("=" * 60)
    print(f"训练数据: 874 条真实小红书笔记 (5 品类有数据)")
    print(f"方法: Spearman 相关 + 线性回归 + K-Means 聚类")
    print()

    for cat, p in MODEL_PARAMS.items():
        n = p["baseline"]["sample_size"]
        r2 = p["r_squared"]
        print(f"── {cat} ({n} samples, R²={r2}) ──")
        print(f"  权重: {json.dumps(p['weights'], indent=2)}")
        print(f"  标题长度: {p['title_length']['min']}-{p['title_length']['max']} 字")
        print(f"  内容长度: {p['content_length']['min']}-{p['content_length']['max']} 字")
        print(f"  标签数量: {p['tag_count']['min']}-{p['tag_count']['max']} (最佳 {p['tag_count']['best']})")
        print(f"  图片数量: {p['image_count']['min']}-{p['image_count']['max']} 张")
        print(f"  基线互动: avg={p['baseline']['avg_engagement']}, median={p['baseline']['median']}")
        print()


def score_single(args):
    features = NoteFeatures(
        title=args.title or "",
        content=args.content or "",
        category=args.category,
        tag_count=args.tags,
        image_count=args.images,
    )
    result = score_note(features)

    print(f"\n{'='*50}")
    print(f"NoteRx 笔记诊断报告")
    print(f"{'='*50}")
    print(f"品类: {features.category}")
    print(f"标题: {features.title[:50]}{'...' if len(features.title)>50 else ''}")
    print(f"\n总分: {result['total_score']:.1f}/100  ({result['percentile_estimate']})")
    print(f"\n各维度评分:")
    for dim, score in result["dimensions"].items():
        w = result["weights"][dim]
        bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
        print(f"  {dim:22s} {bar} {score:5.1f} (×{w:.3f})")
    print(f"\n诊断建议:")
    for d in result["diagnosis"]:
        print(f"  • {d}")
    print(f"\n基线数据 ({features.category}):")
    bl = result["baseline"]
    print(f"  平均互动: {bl['avg_engagement']}, 中位数: {bl['median']}, 爆款线: {bl['viral_threshold']}")


def score_csv(args):
    with open(args.csv, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    results = []
    for row in rows:
        features = NoteFeatures(
            title=row.get("title", row.get("笔记标题", "")),
            content=row.get("content", row.get("笔记内容", "")),
            category=row.get("category", row.get("品类", "lifestyle")),
            tag_count=int(row.get("tag_count", row.get("标签数", 0)) or 0),
            image_count=int(row.get("image_count", row.get("图片数", 0)) or 0),
        )
        result = score_note(features)
        results.append({
            "title": features.title[:50],
            "category": features.category,
            "total_score": result["total_score"],
            **{f"dim_{k}": v for k, v in result["dimensions"].items()},
            "percentile": result["percentile_estimate"],
            "top_diagnosis": result["diagnosis"][0] if result["diagnosis"] else "",
        })

    out_path = args.output or "scored_output.csv"
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)
    print(f"评分完成: {len(results)} 条 → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="NoteRx 内容评分模型 (Model A)")
    parser.add_argument("--title", help="笔记标题")
    parser.add_argument("--content", help="笔记正文", default="")
    parser.add_argument("--category", default="lifestyle", choices=list(MODEL_PARAMS.keys()))
    parser.add_argument("--tags", type=int, default=5, help="标签数量")
    parser.add_argument("--images", type=int, default=4, help="图片数量")
    parser.add_argument("--csv", help="批量评分 CSV 文件")
    parser.add_argument("--output", help="输出 CSV 路径")
    parser.add_argument("--show-params", action="store_true", help="显示模型参数")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    args = parser.parse_args()

    if args.show_params:
        show_params()
    elif args.csv:
        score_csv(args)
    elif args.title:
        if args.json:
            features = NoteFeatures(
                title=args.title, content=args.content,
                category=args.category, tag_count=args.tags, image_count=args.images,
            )
            print(json.dumps(score_note(features), ensure_ascii=False, indent=2))
        else:
            score_single(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
