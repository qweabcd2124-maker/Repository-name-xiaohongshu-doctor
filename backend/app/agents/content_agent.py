"""
内容分析师 Agent
分析文案结构、信息密度、可读性。
"""
import json

from app.agents.base_agent import BaseAgent
from app.agents.prompts.content_agent import SYSTEM_PROMPT
from app.agents.research_data import build_data_prompt_for_agent


class ContentAgent(BaseAgent):
    """分析笔记文案质量"""

    agent_name = "内容分析师"
    system_prompt = SYSTEM_PROMPT

    def build_user_message(
        self,
        title: str,
        content: str,
        category: str,
        title_analysis: dict,
        content_analysis: dict,
        baseline_comparison: dict,
    ) -> str:
        """构建包含笔记内容和 baseline 对比数据的消息"""
        comparisons = baseline_comparison.get("comparisons", {})

        msg = f"""## 待诊断笔记
- **垂类**: {category}
- **标题**: {title}
- **正文**: {content if content else '（无正文）'}

## 标题分析数据
- 字数: {title_analysis.get('length', 0)}
- 关键词: {json.dumps(title_analysis.get('keywords', []), ensure_ascii=False)}
- 情绪词: {json.dumps(title_analysis.get('emotion_words', []), ensure_ascii=False)}
- 钩子数量: {title_analysis.get('hook_count', 0)}

## 正文分析数据
- 字数: {content_analysis.get('length', 0)}
- 段落数: {content_analysis.get('paragraph_count', 0)}
- 平均句长: {content_analysis.get('avg_sentence_length', 0)}
- 可读性评分: {content_analysis.get('readability_score', 0)}
- 信息密度: {content_analysis.get('info_density', 0)}

## Baseline对比（{category}垂类）
- 该垂类爆款平均标题字数: {comparisons.get('title_length', {}).get('viral_avg', 'N/A')}
- 该垂类平均标题字数: {comparisons.get('title_length', {}).get('category_avg', 'N/A')}
- 标题字数判定: {comparisons.get('title_length', {}).get('verdict', 'N/A')}

请基于以上数据给出你的专业诊断。"""
        msg += build_data_prompt_for_agent("content", category)
        return msg

    async def diagnose(self, **kwargs) -> dict:
        """执行内容诊断"""
        msg = self.build_user_message(**kwargs)
        return await self.call_llm(msg)
