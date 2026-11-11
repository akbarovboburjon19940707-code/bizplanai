"""LLM provayderlari. Kaliti berilganlari eski saytdagi tartibda navbat bilan sinaladi."""
from dataclasses import dataclass

import httpx

from app.core.config import Settings


@dataclass
class Completion:
    text: str
    tokens: int
    provider: str


Message = dict[str, str]  # {"role": "user" | "assistant", "content": "..."}


class Provider:
    name = "base"

    async def chat(self, client: httpx.AsyncClient, system: str, messages: list[Message],
                   max_tokens: int = 2000, temperature: float = 0.7) -> Completion: ...

    async def complete(self, client: httpx.AsyncClient, system: str, prompt: str) -> Completion:
        return await self.chat(client, system, [{"role": "user", "content": prompt}])


class OpenAICompatible(Provider):
    def __init__(self, name: str, base_url: str, api_key: str, model: str):
        self.name, self.base_url, self.api_key, self.model = name, base_url, api_key, model

    async def chat(self, client, system, messages, max_tokens=2000, temperature=0.7):
        r = await client.post(f"{self.base_url}/chat/completions",
                              headers={"Authorization": f"Bearer {self.api_key}"},
                              json={"model": self.model, "temperature": temperature, "max_tokens": max_tokens,
                                    "messages": [{"role": "system", "content": system}, *messages]})
        r.raise_for_status()
        data = r.json()
        return Completion(data["choices"][0]["message"]["content"] or "",
                          int((data.get("usage") or {}).get("total_tokens") or 0), self.name)


class Gemini(Provider):
    name = "gemini"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    async def chat(self, client, system, messages, max_tokens=2000, temperature=0.7):
        contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
                    for m in messages]
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            headers={"x-goog-api-key": self.api_key},
            json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
                  "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}})
        r.raise_for_status()
        data = r.json()
        parts = data["candidates"][0]["content"]["parts"]
        return Completion("".join(p.get("text", "") for p in parts),
                          int((data.get("usageMetadata") or {}).get("totalTokenCount") or 0), self.name)


class Anthropic(Provider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    async def chat(self, client, system, messages, max_tokens=2000, temperature=0.7):
        r = await client.post("https://api.anthropic.com/v1/messages",
                              headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                              json={"model": self.model, "max_tokens": max_tokens, "temperature": temperature,
                                    "system": system, "messages": messages})
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") or {}
        return Completion("".join(b.get("text", "") for b in data.get("content", [])),
                          int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0)), self.name)


def configured_providers(s: Settings) -> list[Provider]:
    out: list[Provider] = []
    if s.groq_api_key:
        out.append(OpenAICompatible("groq", "https://api.groq.com/openai/v1", s.groq_api_key, s.groq_model))
    if s.openai_api_key:
        out.append(OpenAICompatible("openai", "https://api.openai.com/v1", s.openai_api_key, s.openai_model))
    if s.deepseek_api_key:
        out.append(OpenAICompatible("deepseek", "https://api.deepseek.com", s.deepseek_api_key, s.deepseek_model))
    if s.anthropic_api_key:
        out.append(Anthropic(s.anthropic_api_key, s.anthropic_model))
    if s.gemini_api_key:
        out.append(Gemini(s.gemini_api_key, s.gemini_model))
    return out
