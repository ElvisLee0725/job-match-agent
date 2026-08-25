import json
from functools import lru_cache
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from app.config import settings

ModelT = TypeVar("ModelT", bound=BaseModel)


@lru_cache
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def structured_completion(prompt: str, schema: type[ModelT], *, max_tokens: int = 2048) -> ModelT:
    """Call Claude and force its reply into the shape of `schema` via tool-use, then parse it.

    This is the single seam between our code and the real Anthropic API — tests mock this
    function directly so LLM-dependent logic can be tested deterministically and offline.
    """
    client = get_client()
    tool_name = "emit_result"
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        tools=[
            {
                "name": tool_name,
                "description": "Emit the structured result.",
                "input_schema": schema.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": prompt}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return schema.model_validate(block.input)

    raise ValueError(f"Claude did not return a '{tool_name}' tool call: {response.content!r}")


def raw_json_completion(prompt: str, *, max_tokens: int = 2048) -> dict:
    """Fallback for cases where we want a plain JSON dict back without a fixed pydantic schema."""
    client = get_client()
    response = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return json.loads(text)
