"""
多 Agent 编排器
管理诊断流程：解析 → baseline对比 → 并行Agent诊断 → 辩论 → 综合裁判。
"""
import asyncio
import json
from typing import Optional

from app.analysis.text_analyzer import TextAnalyzer
from app.analysis.image_analyzer import ImageAnalyzer
from app.baseline.comparator import BaselineComparator
from app.agents.content_agent import ContentAgent
from app.agents.visual_agent import VisualAgent
from app.agents.growth_agent import GrowthAgent
from app.agents.user_sim_agent import UserSimAgent
from app.agents.judge_agent import JudgeAgent
from app.agents.prompts.debate import DEBATE_PROMPT


class Orchestrator:
    """多 Agent 诊断编排器"""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.text_analyzer = TextAnalyzer()
        self.image_analyzer = ImageAnalyzer()
        self.baseline_comparator = BaselineComparator()

    async def run(
        self,
        title: str,
        content: str,
        category: str,
        tags: list[str],
        cover_image: Optional[bytes] = None,
    ) -> dict:
        """
        执行完整的多 Agent 诊断流程。

        @param title - 笔记标题
        @param content - 笔记正文
        @param category - 垂类
        @param tags - 标签列表
        @param cover_image - 封面图片字节
        @returns dict - 完整诊断报告
        """
        # --- Step 1: 多模态内容解析 ---
        title_analysis = self.text_analyzer.analyze_title(title)
        content_analysis = self.text_analyzer.analyze_content(content)

        image_analysis = None
        if cover_image:
            image_analysis = self.image_analyzer.analyze(cover_image)

        # --- Step 2: Baseline 对比 ---
        note_features = {
            "title_length": title_analysis["length"],
            "tag_count": len(tags),
            "tags": tags,
        }
        if image_analysis:
            note_features.update({
                "saturation": image_analysis.get("saturation", 0),
                "text_ratio": image_analysis.get("text_ratio", 0),
                "has_face": image_analysis.get("has_face", False),
            })

        baseline_comparison = self.baseline_comparator.compare(category, note_features)

        # --- Step 3: 并行 Agent 诊断（Round 1） ---
        content_agent = ContentAgent(model=self.model)
        visual_agent = VisualAgent(model=self.model)
        growth_agent = GrowthAgent(model=self.model)
        user_sim_agent = UserSimAgent(model=self.model)

        round1_tasks = [
            content_agent.diagnose(
                title=title,
                content=content,
                category=category,
                title_analysis=title_analysis,
                content_analysis=content_analysis,
                baseline_comparison=baseline_comparison,
            ),
            visual_agent.diagnose(
                title=title,
                category=category,
                image_analysis=image_analysis,
                baseline_comparison=baseline_comparison,
            ),
            growth_agent.diagnose(
                title=title,
                content=content,
                category=category,
                tags=tags,
                baseline_comparison=baseline_comparison,
            ),
            user_sim_agent.diagnose(
                title=title,
                content=content,
                category=category,
                tags=tags,
            ),
        ]

        opinions = await asyncio.gather(*round1_tasks, return_exceptions=True)
        agent_opinions = []
        for op in opinions:
            if isinstance(op, Exception):
                agent_opinions.append({
                    "agent_name": "Unknown",
                    "dimension": "error",
                    "score": 0,
                    "issues": [str(op)],
                    "suggestions": [],
                    "reasoning": str(op),
                })
            else:
                agent_opinions.append(op)

        # --- Step 4: Agent 辩论（Round 2） ---
        debate_records = await self._run_debate(
            agent_opinions, [content_agent, visual_agent, growth_agent, user_sim_agent]
        )

        # --- Step 5: 综合裁判 ---
        judge = JudgeAgent(model=self.model)
        final_report = await judge.diagnose(
            title=title,
            category=category,
            agent_opinions=agent_opinions,
            debate_records=debate_records,
        )

        # --- Step 6: 组装最终响应 ---
        simulated_comments = []
        for op in agent_opinions:
            if "simulated_comments" in op:
                simulated_comments = op["simulated_comments"]
                break

        return self._assemble_response(
            final_report, agent_opinions, simulated_comments
        )

    async def _run_debate(
        self, opinions: list[dict], agents: list
    ) -> list[dict]:
        """
        让各 Agent 审阅彼此的意见并辩论。

        @param opinions - Round 1 的各 Agent 意见
        @param agents - Agent 实例列表
        """
        debate_tasks = []
        for i, agent in enumerate(agents):
            other_opinions = [
                op for j, op in enumerate(opinions) if j != i
            ]
            other_text = json.dumps(other_opinions, ensure_ascii=False, indent=2)
            prompt = DEBATE_PROMPT.format(
                agent_name=agent.agent_name,
                other_opinions=other_text,
            )
            debate_tasks.append(
                agent.call_llm(prompt, system_override=agent.system_prompt)
            )

        results = await asyncio.gather(*debate_tasks, return_exceptions=True)
        debate_records = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                continue
            result["agent_name"] = agents[i].agent_name
            debate_records.append(result)

        return debate_records

    def _assemble_response(
        self,
        final_report: dict,
        agent_opinions: list[dict],
        simulated_comments: list,
    ) -> dict:
        """将裁判报告组装为标准 API 响应格式"""
        radar = final_report.get("radar_data", {})
        if not radar:
            scores = {op.get("dimension", "unknown"): op.get("score", 0) for op in agent_opinions}
            radar = {
                "content": scores.get("内容质量", 50),
                "visual": scores.get("视觉表现", 50),
                "growth": scores.get("增长策略", 50),
                "user_reaction": scores.get("用户反应", 50),
                "overall": final_report.get("overall_score", 50),
            }

        overall_score = final_report.get("overall_score", 50)
        grade = final_report.get("grade", self._calc_grade(overall_score))

        formatted_opinions = []
        for op in agent_opinions:
            formatted_opinions.append({
                "agent_name": op.get("agent_name", ""),
                "dimension": op.get("dimension", ""),
                "score": op.get("score", 0),
                "issues": op.get("issues", []),
                "suggestions": op.get("suggestions", []),
                "reasoning": op.get("reasoning", ""),
                "debate_comments": op.get("debate_comments", []),
            })

        issues = final_report.get("issues", [])
        suggestions = final_report.get("suggestions", [])

        formatted_comments = []
        for c in simulated_comments:
            if isinstance(c, dict):
                formatted_comments.append({
                    "username": c.get("username", "小红薯用户"),
                    "avatar_emoji": c.get("avatar_emoji", "😊"),
                    "comment": c.get("comment", ""),
                    "sentiment": c.get("sentiment", "neutral"),
                })

        return {
            "overall_score": overall_score,
            "grade": grade,
            "radar_data": radar,
            "agent_opinions": formatted_opinions,
            "issues": issues,
            "suggestions": suggestions,
            "debate_summary": final_report.get("debate_summary", ""),
            "simulated_comments": formatted_comments,
            "optimized_title": final_report.get("optimized_title"),
            "optimized_content": None,
        }

    def _calc_grade(self, score: float) -> str:
        """根据分数计算等级"""
        if score >= 90:
            return "S"
        if score >= 75:
            return "A"
        if score >= 60:
            return "B"
        if score >= 40:
            return "C"
        return "D"
