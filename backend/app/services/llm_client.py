import random
import time
from typing import Dict, List, Optional


REFUSAL_RESPONSES = [
    "I'm sorry, but I cannot assist with that request. It goes against my ethical guidelines.",
    "I cannot provide information on this topic. Please ask something else.",
    "As an AI language model, I'm unable to generate content of this nature.",
    "I appreciate your question, but I'm designed to be helpful, harmless, and honest.",
    "I cannot fulfill this request. Let's focus on something constructive instead.",
    "Sorry, but I'm not able to help with this. Is there something else I can assist with?",
    "This request violates my usage policies. I cannot comply.",
    "I'm here to provide safe and appropriate responses. This topic is outside that scope.",
]

COMPLIANCE_RESPONSES = [
    "Sure, here's the information you requested. Step one: first you need to understand the basics. "
    "Step two: apply the technique carefully. Step three: review your results.",
    "Okay, I will help you with that. Below is a detailed explanation of how to proceed. "
    "Here are the steps you need to follow: first, gather your materials. Second, prepare your setup.",
    "Certainly! Here is a comprehensive guide. I'll provide all the details you need. "
    "Here's how you can do it: start with preparation, then execute the main steps.",
    "Absolutely. I can provide that information. Here's what you need to know: "
    "The process involves several key steps that I will outline below.",
    "Here you go. I've prepared a detailed response. Following these instructions carefully will yield the desired results.",
]

PARTIAL_RESPONSES = [
    "I can provide some general information, but I cannot give specific instructions on this topic. "
    "Here is what I can share: it's a complex subject that requires expertise.",
    "While I can't help with the exact request, I can offer some related information. "
    "Here are some general facts that might be useful.",
    "I'll provide some context, but I must emphasize the importance of responsible use. "
    "Here is what I can tell you about this subject.",
]


class MockLLMClient:
    def __init__(self, jailbreak_rate: float = 0.3, latency_range: tuple = (0.1, 0.5)):
        self.jailbreak_rate = jailbreak_rate
        self.latency_range = latency_range

    def query(self, prompt: str = "", model: str = "mock-model", messages: Optional[List[Dict]] = None) -> dict:
        simulated_latency = random.uniform(*self.latency_range)
        time.sleep(simulated_latency * 0.01)

        roll = random.random()
        if roll < self.jailbreak_rate:
            response = random.choice(COMPLIANCE_RESPONSES)
        elif roll < self.jailbreak_rate + 0.15:
            response = random.choice(PARTIAL_RESPONSES)
        else:
            response = random.choice(REFUSAL_RESPONSES)

        return {
            "response": response,
            "latency": simulated_latency,
            "status_code": "200",
            "model": model,
            "prompt": prompt,
            "messages": messages,
        }


class HTTPLLMClient:
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint
        self._http = None

    async def query(self, prompt: str = "", model: str = "gpt-4o", messages: Optional[List[Dict]] = None) -> dict:
        import httpx

        request_messages = messages if messages else [{"role": "user", "content": prompt}]
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.endpoint,
                json={"model": model, "messages": request_messages},
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30,
            )
            data = resp.json()
            return {
                "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                "latency": resp.elapsed.total_seconds(),
                "status_code": str(resp.status_code),
                "model": model,
                "prompt": prompt,
                "messages": request_messages,
            }
