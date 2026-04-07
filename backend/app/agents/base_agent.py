"""
Agent 基类
封装 LLM 调用、prompt 模板、结构化输出解析。
"""
import json
import os
from typing import Optional

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()


def _get_client() -> AsyncOpenAI:
    """获取 OpenAI 兼容的 API 客户端"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", None)
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


class BaseAgent:
    """所有诊断 Agent 的基类"""

    agent_name: str = "BaseAgent"
    system_prompt: str = ""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.client = _get_client()

    async def call_llm(
        self,
        user_message: str,
        system_override: Optional[str] = None,
    ) -> dict:
        """
        调用 LLM 并解析 JSON 响应。

        @param user_message - 用户消息（包含笔记数据和 baseline 对比信息）
        @param system_override - 可选的 system prompt 覆盖
        @returns dict - 解析后的 JSON 响应
        """
        sys_prompt = system_override or self.system_prompt

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.7,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except json.JSONDecodeError:
            return self._error_response("LLM 返回了非 JSON 格式的内容")
        except Exception as e:
            return self._error_response(str(e))

    def _error_response(self, error_msg: str) -> dict:
        """生成错误响应"""
        return {
            "agent_name": self.agent_name,
            "dimension": "error",
            "score": 0,
            "issues": [f"诊断出错: {error_msg}"],
            "suggestions": ["请稍后重试"],
            "reasoning": f"Error: {error_msg}",
        }

    def build_user_message(self, **kwargs) -> str:
        """子类实现：构建发送给 LLM 的用户消息"""
        raise NotImplementedError
