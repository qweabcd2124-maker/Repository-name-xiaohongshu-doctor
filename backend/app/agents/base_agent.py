"""
Agent 基类
封装 LLM 调用、prompt 模板、结构化输出解析。
支持 OpenAI / Anthropic 切换；兼容小米 MiMo（OpenAI 格式）等第三方网关。
"""
import json
import os
import logging
import re
from typing import Optional
from pathlib import Path

from dotenv import load_dotenv

for p in [Path(__file__).resolve().parents[2] / ".env", Path.cwd() / ".env", Path.cwd().parent / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

logger = logging.getLogger("noterx.agent")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()


def _is_mimo_openai_compat() -> bool:
    """
    是否按小米 MiMo OpenAPI（OpenAI 兼容）处理参数。
    可由 OPENAI_COMPAT=mimo 显式开启，或由 BASE_URL / 模型名推断。
    """
    if os.getenv("OPENAI_COMPAT", "").strip().lower() == "mimo":
        return True
    base = (os.getenv("OPENAI_BASE_URL") or "").lower()
    if "xiaomimimo.com" in base or "mimo-v2.com" in base:
        return True
    model = (os.getenv("LLM_MODEL") or "").lower()
    return model.startswith("mimo-")


def _resolve_openai_base_url() -> Optional[str]:
    """
    解析 OpenAI 兼容服务的 base_url；误把 Key 填进 OPENAI_BASE_URL 时给出默认 MiMo 地址提示。
    """
    raw = (os.getenv("OPENAI_BASE_URL") or "").strip()
    if raw.startswith("sk-") and len(raw) > 30:
        logger.warning(
            "OPENAI_BASE_URL 的值看起来像 API Key。请把密钥放在 OPENAI_API_KEY，"
            "此处填写网关地址，例如 https://api.xiaomimimo.com/v1"
        )
        raw = ""
    if raw:
        return raw.rstrip("/")
    if _is_mimo_openai_compat():
        return "https://api.xiaomimimo.com/v1"
    return None


def _get_client():
    """根据 LLM_PROVIDER 环境变量获取对应 API 客户端"""
    if LLM_PROVIDER == "anthropic":
        from anthropic import AsyncAnthropic
        return AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    from openai import AsyncOpenAI
    return AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        base_url=_resolve_openai_base_url(),
    )


def _parse_json_from_llm_text(raw: Optional[str]) -> dict:
    """从模型输出中提取 JSON（支持 ```json 代码块）。"""
    if not raw or not raw.strip():
        raise json.JSONDecodeError("empty", "", 0)
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\s*```\s*$", "", clean)
    return json.loads(clean)


def _should_retry_openai_without_json_format(exc: BaseException) -> bool:
    """部分兼容网关不支持 response_format=json_object，可去掉后重试。"""
    msg = str(exc).lower()
    if "response_format" in msg or "json_object" in msg:
        return True
    code = getattr(exc, "status_code", None)
    if code is None and hasattr(exc, "response"):
        code = getattr(getattr(exc, "response", None), "status_code", None)
    return code in (400, 422)


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

        @param user_message - 用户消息
        @param system_override - 可选的 system prompt 覆盖
        @returns dict - 解析后的 JSON 响应
        """
        sys_prompt = system_override or self.system_prompt

        if LLM_PROVIDER == "anthropic":
            return await self._call_anthropic(sys_prompt, user_message)
        return await self._call_openai(sys_prompt, user_message)

    async def _call_openai(self, sys_prompt: str, user_message: str) -> dict:
        """OpenAI 兼容调用（含小米 MiMo 等网关的参数与 JSON 模式兼容）。"""
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message},
        ]
        mimo = _is_mimo_openai_compat()
        max_out = int(os.getenv("LLM_MAX_COMPLETION_TOKENS", "2048"))
        skip_json_mode = os.getenv("LLM_SKIP_JSON_RESPONSE_FORMAT", "").strip() in ("1", "true", "yes")

        async def _create(with_json_object: bool):
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.7")),
            }
            if mimo:
                kwargs["max_completion_tokens"] = max_out
            else:
                kwargs["max_tokens"] = max_out
            if with_json_object and not skip_json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            return await self.client.chat.completions.create(**kwargs)

        response = None
        last_err: Optional[BaseException] = None
        attempts: list[bool] = []
        if not skip_json_mode:
            attempts.append(True)
        attempts.append(False)

        for use_json in attempts:
            try:
                response = await _create(with_json_object=use_json)
                break
            except Exception as e:
                last_err = e
                if use_json and _should_retry_openai_without_json_format(e):
                    logger.info("网关可能不支持 response_format=json_object，将不带该参数重试: %s", e)
                    continue
                logger.warning("OpenAI 调用失败: %s", e)
                return self._error_response(str(e))

        if response is None:
            return self._error_response(str(last_err) if last_err else "LLM 无响应")

        try:
            raw = response.choices[0].message.content
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                result = _parse_json_from_llm_text(raw)
            usage = response.usage
            if usage:
                result["_meta"] = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "model": response.model,
                }
            return result
        except json.JSONDecodeError:
            logger.warning("LLM 原始输出（非 JSON）: %s", (raw or "")[:500])
            return self._error_response("LLM 返回了非 JSON 格式的内容")
        except Exception as e:
            logger.warning("解析 LLM 响应失败: %s", e)
            return self._error_response(str(e))

    async def _call_anthropic(self, sys_prompt: str, user_message: str) -> dict:
        """Anthropic Claude 调用"""
        try:
            response = await self.client.messages.create(
                model=self.model if "claude" in self.model else "claude-sonnet-4-20250514",
                max_tokens=2000,
                system=sys_prompt,
                messages=[{"role": "user", "content": user_message + "\n\n请以 JSON 格式输出。"}],
            )
            raw = response.content[0].text
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(clean)
            usage = response.usage
            if usage:
                result["_meta"] = {
                    "prompt_tokens": usage.input_tokens,
                    "completion_tokens": usage.output_tokens,
                    "total_tokens": usage.input_tokens + usage.output_tokens,
                    "model": response.model,
                }
            return result
        except json.JSONDecodeError:
            return self._error_response("Claude 返回了非 JSON 格式的内容")
        except Exception as e:
            logger.warning("Anthropic 调用失败: %s", e)
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
