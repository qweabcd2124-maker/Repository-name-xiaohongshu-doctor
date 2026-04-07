"""
文本分析模块
分析笔记标题和正文的文案质量。
"""
import re
import math

import jieba
import jieba.analyse


EMOTION_WORDS = {
    "positive": [
        "绝了", "好用", "必备", "推荐", "神仙", "宝藏", "治愈", "值得",
        "惊艳", "爱了", "无敌", "巨好", "超赞", "完美", "舒服", "开心",
        "幸福", "甜", "暖", "美", "棒", "赞",
    ],
    "negative": [
        "避雷", "踩坑", "难吃", "失望", "后悔", "垃圾", "劝退", "翻车",
        "不推荐", "差评", "坑", "难用",
    ],
    "urgency": [
        "必看", "必入", "别再", "千万", "赶紧", "速看", "快来",
        "不要错过", "最后", "限时",
    ],
}

HOOK_PATTERNS = [
    r"\d+[种个款件招步]",          # 数字+量词
    r"[！!]{2,}",                  # 多个感叹号
    r"[?？]",                      # 问号（悬念）
    r"｜|[|]",                     # 分隔符
    r"[\U0001f300-\U0001f9ff]",   # emoji
]


class TextAnalyzer:
    """分析笔记文案质量"""

    def analyze_title(self, title: str) -> dict:
        """
        分析标题质量。

        @param title - 笔记标题
        @returns dict 包含 length, keywords, emotion_words, hook_count, score 等
        """
        length = len(title)
        keywords = jieba.analyse.extract_tags(title, topK=10, withWeight=True)
        keyword_list = [{"word": w, "weight": round(s, 3)} for w, s in keywords]

        emotion_found = self._find_emotion_words(title)
        hook_count = sum(1 for p in HOOK_PATTERNS if re.search(p, title))
        has_numbers = bool(re.search(r"\d+", title))

        score = self._score_title(length, hook_count, len(emotion_found), has_numbers)

        return {
            "length": length,
            "keywords": keyword_list,
            "emotion_words": emotion_found,
            "hook_count": hook_count,
            "has_numbers": has_numbers,
            "score": score,
        }

    def analyze_content(self, content: str) -> dict:
        """
        分析正文质量。

        @param content - 笔记正文
        @returns dict 包含 length, paragraph_count, avg_sentence_length 等
        """
        if not content or not content.strip():
            return {
                "length": 0,
                "paragraph_count": 0,
                "avg_sentence_length": 0,
                "has_emoji": False,
                "readability_score": 0,
                "info_density": 0,
            }

        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
        sentences = re.split(r"[。！？!?;\n]", content)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sent_len = sum(len(s) for s in sentences) / max(len(sentences), 1)

        emoji_pattern = re.compile(r"[\U0001f300-\U0001f9ff]")
        has_emoji = bool(emoji_pattern.search(content))

        words = list(jieba.cut(content))
        unique_words = set(words)
        info_density = len(unique_words) / max(len(words), 1)

        readability = self._calc_readability(avg_sent_len, len(paragraphs), has_emoji)

        return {
            "length": len(content),
            "paragraph_count": len(paragraphs),
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sent_len, 1),
            "has_emoji": has_emoji,
            "readability_score": readability,
            "info_density": round(info_density, 3),
        }

    def _find_emotion_words(self, text: str) -> list[dict]:
        """查找文本中的情绪词"""
        found = []
        for category, words in EMOTION_WORDS.items():
            for w in words:
                if w in text:
                    found.append({"word": w, "type": category})
        return found

    def _score_title(
        self, length: int, hooks: int, emotions: int, has_num: bool
    ) -> float:
        """
        综合评分标题 (0-100)。
        最优标题长度: 12-22字。
        """
        score = 50.0
        if 12 <= length <= 22:
            score += 15
        elif 8 <= length < 12 or 22 < length <= 30:
            score += 8
        else:
            score -= 10

        score += min(hooks, 3) * 8
        score += min(emotions, 2) * 6
        if has_num:
            score += 5

        return min(max(round(score, 1), 0), 100)

    def _calc_readability(
        self, avg_sent_len: float, para_count: int, has_emoji: bool
    ) -> float:
        """计算可读性评分 (0-100)"""
        score = 50.0
        if 15 <= avg_sent_len <= 35:
            score += 20
        elif avg_sent_len < 15:
            score += 10
        else:
            score -= 10

        if para_count >= 3:
            score += 15
        elif para_count >= 2:
            score += 8

        if has_emoji:
            score += 10

        return min(max(round(score, 1), 0), 100)
