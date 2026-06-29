"""
Base agent class — provides Qwen API integration via OpenAI-compatible client.
All agents inherit from this to get consistent LLM access.
"""

import os
import json
import logging
from openai import OpenAI
import instructor
from config import settings

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    Base class for all NeuralSwarm agents.
    Provides both raw OpenAI client and instructor-patched client for structured output.
    """

    def __init__(self, model: str | None = None, temperature: float = 0.7):
        self.model = model or settings.qwen_model_fast
        self.temperature = temperature

        # Raw OpenAI-compatible client for Qwen
        self.client = OpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.qwen_base_url,
        )

        # Instructor-patched client for reliable structured output
        self.structured_client = instructor.from_openai(
            OpenAI(
                api_key=settings.dashscope_api_key,
                base_url=settings.qwen_base_url,
            ),
            mode=instructor.Mode.JSON,
        )

    def _chat(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Send a chat completion request and return the text response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _structured_chat(self, system_prompt: str, user_prompt: str, response_model, max_retries: int = 3):
        """
        Send a chat completion and parse the response into a Pydantic model.
        Uses instructor for automatic validation and retry.
        """
        try:
            result = self.structured_client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_model=response_model,
                max_retries=max_retries,
                max_tokens=8000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return result
        except Exception as e:
            logger.error(f"Structured LLM call failed: {e}")
            raise
