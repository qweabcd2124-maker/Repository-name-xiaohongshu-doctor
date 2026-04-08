"""
数据驱动模块：基于 874 条真实小红书笔记的研究成果。
提供品类评分参数、数据驱动提示词注入、Model A 预评分。
"""
from __future__ import annotations

import re
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# Model A 品类评分参数（从真实数据训练得出）
# ═══════════════════════════════════════════════════════════════

MODEL_PARAMS: dict[str, dict] = {
    "food": {
        "weights": {"title_quality": 0.573, "content_quality": 0.132, "visual_quality": 0.086, "tag_strategy": 0.097, "engagement_potential": 0.111},
        "title_length": {"min": 11, "max": 19, "viral_avg": 18.3},
        "content_length": {"min": 105, "max": 342},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 10},
        "baseline": {"avg_engagement": 33462, "median": 7333, "viral_threshold": 112965, "sample_size": 183},
    },
    "fashion": {
        "weights": {"title_quality": 0.395, "content_quality": 0.125, "visual_quality": 0.250, "tag_strategy": 0.058, "engagement_potential": 0.172},
        "title_length": {"min": 11, "max": 20, "viral_avg": 14.0},
        "content_length": {"min": 92, "max": 224},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 10},
        "baseline": {"avg_engagement": 7507, "median": 2069, "viral_threshold": 18037, "sample_size": 278},
    },
    "tech": {
        "weights": {"title_quality": 0.411, "content_quality": 0.125, "visual_quality": 0.103, "tag_strategy": 0.095, "engagement_potential": 0.267},
        "title_length": {"min": 12, "max": 20, "viral_avg": 17.5},
        "content_length": {"min": 87, "max": 517},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 1, "max": 6},
        "baseline": {"avg_engagement": 1275, "median": 175, "viral_threshold": 3325, "sample_size": 235},
    },
    "travel": {
        "weights": {"title_quality": 0.376, "content_quality": 0.050, "visual_quality": 0.120, "tag_strategy": 0.312, "engagement_potential": 0.142},
        "title_length": {"min": 11, "max": 20, "viral_avg": 14.3},
        "content_length": {"min": 123, "max": 737},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 4, "max": 14},
        "baseline": {"avg_engagement": 16563, "median": 4538, "viral_threshold": 39426, "sample_size": 130},
    },
    "beauty": {
        "weights": {"title_quality": 0.40, "content_quality": 0.15, "visual_quality": 0.20, "tag_strategy": 0.10, "engagement_potential": 0.15},
        "title_length": {"min": 10, "max": 20, "viral_avg": 16.0},
        "content_length": {"min": 100, "max": 400},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 3, "max": 9},
        "baseline": {"avg_engagement": 5000, "median": 1500, "viral_threshold": 15000, "sample_size": 0},
    },
    "fitness": {
        "weights": {"title_quality": 0.35, "content_quality": 0.15, "visual_quality": 0.15, "tag_strategy": 0.15, "engagement_potential": 0.20},
        "title_length": {"min": 10, "max": 22, "viral_avg": 16.0},
        "content_length": {"min": 80, "max": 500},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 2, "max": 8},
        "baseline": {"avg_engagement": 4000, "median": 1000, "viral_threshold": 12000, "sample_size": 0},
    },
    "lifestyle": {
        "weights": {"title_quality": 0.407, "content_quality": 0.083, "visual_quality": 0.071, "tag_strategy": 0.277, "engagement_potential": 0.162},
        "title_length": {"min": 10, "max": 20, "viral_avg": 19.4},
        "content_length": {"min": 24, "max": 148},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 1, "max": 8},
        "baseline": {"avg_engagement": 8038, "median": 773, "viral_threshold": 17097, "sample_size": 48},
    },
    "home": {
        "weights": {"title_quality": 0.35, "content_quality": 0.15, "visual_quality": 0.20, "tag_strategy": 0.15, "engagement_potential": 0.15},
        "title_length": {"min": 10, "max": 20, "viral_avg": 15.0},
        "content_length": {"min": 100, "max": 500},
        "tag_count": {"min": 4, "max": 8, "best": 6},
        "image_count": {"min": 4, "max": 12},
        "baseline": {"avg_engagement": 6000, "median": 2000, "viral_threshold": 18000, "sample_size": 0},
    },
}

# 品类中文名
CATEGORY_CN = {
    "food": "美食", "fashion": "穿搭", "tech": "科技", "travel": "旅游",
    "beauty": "美妆", "fitness": "健身", "lifestyle": "生活", "home": "家居",
}


# ═══════════════════════════════════════════════════════════════
# 特征提取 + Model A 预评分
# ═══════════════════════════════════════════════════════════════

def _detect_emoji(text: str) -> bool:
    return bool(re.search(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
        "\U0001F900-\U0001F9FF\U00002702-\U000027B0\u2728\U0001F525\U0001F49A\u203C\u2B50]",
        text or "",
    ))


def _count_hooks(title: str) -> int:
    hooks = 0
    if re.search(r'\d+', title): hooks += 1
    if re.search(r'[！!？?]', title): hooks += 1
    if re.search(r'[｜|]', title): hooks += 1
    if re.search(r'[\u2728\U0001F525\u203C\u2B50\U0001F4AF]', title): hooks += 1
    if re.search(r'(必|绝了|太|超|巨|神仙|宝藏|救命)', title): hooks += 1
    return hooks


def _range_score(value: float, opt_min: float, opt_max: float, base: float = 80) -> float:
    if opt_min <= value <= opt_max:
        mid = (opt_min + opt_max) / 2
        half = (opt_max - opt_min) / 2 + 1
        return base + (100 - base) * (1 - abs(value - mid) / half)
    elif value < opt_min:
        return max(20, base * value / max(opt_min, 1))
    else:
        return max(40, base - (value - opt_max) * 2)


def pre_score(title: str, content: str, category: str, tag_count: int = 0, image_count: int = 0) -> dict:
    """
    Model A 预评分。返回各维度分数和总分，用于注入到 Agent prompt 中。
    """
    p = MODEL_PARAMS.get(category, MODEL_PARAMS["lifestyle"])
    w = p["weights"]

    tl = p["title_length"]
    title_score = _range_score(len(title), tl["min"], tl["max"])
    title_score += (5 if re.search(r'\d+', title) else 0)
    title_score += min(_count_hooks(title), 3) * 3
    title_score += (2 if _detect_emoji(title + content) else 0)
    title_score = min(title_score, 100)

    cl = p["content_length"]
    content_score = min(_range_score(len(content), cl["min"], cl["max"], 85), 100)

    ic = p["image_count"]
    visual_score = min(_range_score(image_count, ic["min"], ic["max"]), 100)

    tc = p["tag_count"]
    tag_score = max(0, 100 - abs(tag_count - tc["best"]) * 10)

    signals = 0
    if len(title) >= tl["min"]: signals += 25
    if re.search(r'\d+', title): signals += 15
    if _count_hooks(title) >= 2: signals += 20
    if tc["min"] <= tag_count <= tc["max"]: signals += 20
    if ic["min"] <= image_count <= ic["max"]: signals += 20
    engagement_score = min(signals, 100)

    dims = {
        "title_quality": round(title_score, 1),
        "content_quality": round(content_score, 1),
        "visual_quality": round(visual_score, 1),
        "tag_strategy": round(tag_score, 1),
        "engagement_potential": round(engagement_score, 1),
    }

    total = min(round(sum(dims[k] * w[k] for k in w), 1), 100)

    bl = p["baseline"]
    if total >= 85:
        level = "前10%（爆款潜力）"
    elif total >= 75:
        level = "前25%（优质内容）"
    elif total >= 65:
        level = "中位水平"
    else:
        level = "低于中位，建议优化"

    return {
        "total_score": total,
        "dimensions": dims,
        "weights": w,
        "level": level,
        "baseline": bl,
    }


def build_data_prompt_for_agent(agent_type: str, category: str) -> str:
    """
    为指定 Agent 和品类生成数据驱动的提示词片段，拼接到 system prompt 后。
    """
    p = MODEL_PARAMS.get(category, MODEL_PARAMS["lifestyle"])
    w = p["weights"]
    bl = p["baseline"]
    cn = CATEGORY_CN.get(category, category)

    if agent_type == "content":
        return (
            f"\n\n## 数据研究基准（{cn}品类，基于{bl['sample_size']}条真实数据）\n"
            f"- 标题最优长度：{p['title_length']['min']}-{p['title_length']['max']}字（爆款平均{p['title_length']['viral_avg']}字）\n"
            f"- 正文最优长度：{p['content_length']['min']}-{p['content_length']['max']}字\n"
            f"- 标题质量权重：{w['title_quality']:.1%}（{'该品类最重要的维度' if w['title_quality'] > 0.4 else '重要维度'}）\n"
            f"- 内容质量权重：{w['content_quality']:.1%}\n"
            f"- 基线互动量：平均{bl['avg_engagement']:,}，中位数{bl['median']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"请严格依据以上参数给出量化诊断，指出具体差距。"
        )
    elif agent_type == "visual":
        return (
            f"\n\n## 数据研究基准（{cn}品类）\n"
            f"- 图片最优数量：{p['image_count']['min']}-{p['image_count']['max']}张\n"
            f"- 视觉质量权重：{w['visual_quality']:.1%}"
            f"{'（穿搭品类视觉是核心驱动力，文本几乎无法预测互动）' if category == 'fashion' else ''}\n"
            f"请基于图片数量和视觉质量给出诊断。"
        )
    elif agent_type == "growth":
        return (
            f"\n\n## 数据研究基准（{cn}品类）\n"
            f"- 标签最优数量：{p['tag_count']['min']}-{p['tag_count']['max']}个（最佳{p['tag_count']['best']}个）\n"
            f"- 标签策略权重：{w['tag_strategy']:.1%}"
            f"{'（旅游品类标签是最强预测因子β=0.52）' if category == 'travel' else ''}\n"
            f"- 互动潜力权重：{w['engagement_potential']:.1%}\n"
            f"- 基线：平均互动{bl['avg_engagement']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"- 最佳发布时段：17:00（数据平均互动22,632）\n"
            f"请基于以上数据给出增长策略。"
        )
    elif agent_type == "user_sim":
        return (
            f"\n\n## 用户画像数据（{cn}品类）\n"
            f"- 基于2500条真实评论的用户类型分布：种草型/经验型/调侃型/质疑型/求购型/路人型\n"
            f"- 模拟评论时请参考真实分布，{'穿搭评论区63%正面情绪，种草型占25%' if category == 'fashion' else '科技评论区经验型占37%，质疑型占17%' if category == 'tech' else '生活评论区调侃型占30%，共鸣驱动高互动'}\n"
            f"请生成符合真实品类用户画像的模拟评论。"
        )
    elif agent_type == "judge":
        w_str = "、".join(f"{k}({v:.1%})" for k, v in sorted(w.items(), key=lambda x: -x[1]))
        return (
            f"\n\n## 数据驱动评分标准（{cn}品类，{bl['sample_size']}条数据训练）\n"
            f"- 评分权重优先级：{w_str}\n"
            f"- 基线对比：平均互动{bl['avg_engagement']:,}，中位数{bl['median']:,}，爆款线{bl['viral_threshold']:,}\n"
            f"- 请严格按权重加权计算总分，并与基线对标。"
        )
    return ""
