import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

from src.utils.config import settings
from src.utils.logging import get_logger

logger = get_logger("llm")

# This key is allowed to call gpt-5-nano. The openai/gpt-5-nano id is rejected.
CANDIDATE_MODELS = [
    "gpt-5-nano",
]


def _parse_json_text(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        parsed = json.loads(cleaned[start:end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Model returned JSON that is not an object")
    return parsed


class GeminiLLMClient:
    """
    OpenAI-compatible chat client. The name stays so existing agents keep working.
    Requests go to LLM_BASE_URL (AI Credits) with LLM_API_KEY.
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY or os.environ.get("LLM_API_KEY", "")
        self.base_url = (settings.LLM_BASE_URL or "https://aicredits.in/v1").rstrip("/")
        self.primary_model = settings.LLM_MODEL or "gpt-5-nano"
        if self.api_key:
            logger.info(f"LLM ready at {self.base_url} with model {self.primary_model}")
        else:
            logger.info("No LLM_API_KEY set. Running in grounded deterministic intelligence mode.")

    def _models(self) -> List[str]:
        models = [self.primary_model] + [m for m in CANDIDATE_MODELS if m != self.primary_model]
        return models

    def _post(self, payload: Dict[str, Any], timeout: int = 20) -> requests.Response:
        return requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )

    def _complete(self, messages: List[Dict[str, str]], model_name: str, json_mode: bool, timeout: int = 20) -> str:
        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.4,
            # GPT-5 Nano spends a few hundred tokens on reasoning before the visible answer.
            "max_completion_tokens": 8000,
            "reasoning_effort": "low",
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = self._post(payload, timeout=timeout)
        # A 400 means the proxy rejected a field. A 500 should not be retried.
        if response.status_code in (400, 422) and "reasoning_effort" in payload:
            payload.pop("reasoning_effort", None)
            response = self._post(payload, timeout=timeout)
        if response.status_code in (400, 422) and "response_format" in payload:
            payload.pop("response_format", None)
            response = self._post(payload, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        return (body["choices"][0]["message"].get("content") or "").strip()

    def generate_json(self, prompt: str, system_instruction: Optional[str] = None, fallback_handler=None, timeout: int = 20) -> Dict[str, Any]:
        """Ask the model for a JSON object. Falls back to the rule engine if every model fails."""
        if self.api_key:
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({
                "role": "user",
                "content": f"{prompt}\n\nRespond ONLY with valid JSON.",
            })
            for model_name in self._models():
                try:
                    text = self._complete(messages, model_name, json_mode=True, timeout=timeout)
                    parsed = _parse_json_text(text)
                    logger.info(f"JSON generation successful with model: {model_name}")
                    return parsed
                except Exception as e:
                    logger.warning(f"LLM call with {model_name} failed: {e}. Trying next model...")
                    continue

        if fallback_handler:
            logger.info("LLM unavailable. Using deterministic fallback handler.")
            return fallback_handler()

        return {"error": "LLM client not configured and no fallback provided"}

    def chat(self, messages: List[Dict[str, str]], system_instruction: str, fallback_text: str = "") -> str:
        """Multi-turn chat. messages are user and assistant turns only."""
        if not self.api_key:
            return fallback_text
        payload_messages = [{"role": "system", "content": system_instruction}]
        for message in messages:
            role = message.get("role")
            content = (message.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                payload_messages.append({"role": role, "content": content})
        for model_name in self._models():
            try:
                text = self._complete(payload_messages, model_name, json_mode=False)
                logger.info(f"Chat reply successful with model: {model_name}")
                return text
            except Exception as e:
                logger.warning(f"Chat with {model_name} failed: {e}. Trying next model...")
                continue
        return fallback_text

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None, fallback_text: str = "") -> str:
        if not self.api_key:
            return fallback_text
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        for model_name in self._models():
            try:
                text = self._complete(messages, model_name, json_mode=False)
                logger.info(f"Text generation successful with model: {model_name}")
                return text
            except Exception as e:
                logger.warning(f"Text generation with {model_name} failed: {e}. Trying next model...")
                continue
        return fallback_text


gemini_client = GeminiLLMClient()
