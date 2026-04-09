"""
OCR 处理模块
使用 mimo-v2-omni 多模态模型提取截图中的笔记信息。
"""

from __future__ import annotations

import json
import logging
import os
import re

from app.agents.base_agent import (
    _bytes_to_image_data_url,
    _is_mimo_openai_compat,
    _parse_json_from_llm_text,
)

logger = logging.getLogger("noterx.ocr")


def _salvage_ocr_json_fragment(text: str) -> dict | None:
    """
    MiMo 等在 max_tokens 截断时常见「content 字符串未闭合」；从残缺 JSON 中抢救 title/content/tags。
    @returns 至少含一个非空字段时返回 dict，否则 None
    """
    title = ""
    content = ""
    tags: list[str] = []

    tm = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
    if tm:
        title = tm.group(1)

    cm = re.search(r'"content"\s*:\s*"', text)
    if cm:
        rest = text[cm.end() :]
        parts: list[str] = []
        i = 0
        esc = False
        while i < len(rest):
            c = rest[i]
            if esc:
                parts.append(c)
                esc = False
                i += 1
                continue
            if c == "\\":
                esc = True
                i += 1
                continue
            if c == '"':
                break
            parts.append(c)
            i += 1
        content = "".join(parts)

    tags_m = re.search(r'"tags"\s*:\s*\[', text)
    if tags_m:
        slice_start = tags_m.end()
        bracket = text[slice_start : slice_start + 800]
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', bracket):
            tags.append(m.group(1))

    if title.strip() or content.strip() or tags:
        return {"title": title.strip(), "content": content.strip(), "tags": tags}
    return None


class OCRProcessor:
    """从图片中提取文本内容。"""

    async def extract_text(
        self,
        image_bytes: bytes,
        client=None,
        *,
        max_tokens_override: int | None = None,
    ) -> dict:
        if client is None:
            return self._fallback_result()

        data_url = _bytes_to_image_data_url(image_bytes)
        ocr_model = os.getenv("LLM_MODEL_OMNI", "mimo-v2-omni")

        try:
            msg_body: list | str = [
                {"type": "text", "text": "请基于截图语义提取标题、正文要点和标签；无需逐字 OCR 整屏。"},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
            kwargs = {
                "model": ocr_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是一个小红书截图信息提取助手。"
                            "请优先做内容理解，再提取关键字段；看不清就留空，不要臆造。"
                            "content 只写画面可见文字要点，一句一行用 \\n；避免长篇场景描述以控制长度。"
                            "tags 无则 []。"
                            '仅输出合法 JSON：{"title": "...", "content": "...", "tags": []}'
                        ),
                    },
                    {"role": "user", "content": msg_body},
                ],
            }
            env_cap = int(os.getenv("LLM_OCR_MAX_TOKENS", "2048"))
            if max_tokens_override is not None:
                # 原先 min(env, override) 会把快识压到 1024 导致 JSON 半截；改为取较大者再夹上限
                env_cap = min(max(env_cap, max_tokens_override), 8192)
            if _is_mimo_openai_compat():
                kwargs["max_completion_tokens"] = min(env_cap, 8192)
            else:
                kwargs["max_tokens"] = min(env_cap, 8192)

            response = await client.chat.completions.create(**kwargs)
            raw = response.choices[0].message.content or ""
            clean = raw.strip()
            if not clean:
                logger.debug("OCR 模型返回空内容（可能 max_tokens 过小或被安全策略拦截）")
                return self._fallback_result()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            try:
                parsed = json.loads(clean)
            except json.JSONDecodeError:
                try:
                    parsed = _parse_json_from_llm_text(clean)
                except json.JSONDecodeError:
                    salvaged = _salvage_ocr_json_fragment(clean)
                    if salvaged:
                        logger.info(
                            "OCR JSON 不完整已抢救字段: title_len=%s content_len=%s",
                            len(salvaged.get("title", "")),
                            len(salvaged.get("content", "")),
                        )
                        return salvaged
                    logger.warning(
                        "OCR 输出无法解析为 JSON，前 240 字: %r",
                        clean[:240],
                    )
                    return self._fallback_result()
            if not isinstance(parsed, dict):
                return self._fallback_result()
            return parsed
        except Exception as e:
            logger.warning("OCR 提取失败: %s", e)
            return self._fallback_result()

    def _fallback_result(self) -> dict:
        return {"title": "", "content": "", "tags": []}
