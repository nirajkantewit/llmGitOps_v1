"""
agent.py

A minimal, real agent implementation so the eval pipeline has something
actual to call instead of a NotImplementedError placeholder.

This is intentionally simple (rule-based, no external API/model call) so
the full prep -> version -> regression pipeline can run end-to-end with
zero secrets or external dependencies. Swap `run()` out for a real model
or API call whenever you're ready to evaluate your actual agent.
"""

import re


def run(input_text: str, version: str = "unversioned") -> str:
    """
    Very small rule-based 'agent' matching the sample test_cases.jsonl:
      - basic arithmetic ("What is 2 + 2?")
      - a couple of hardcoded facts ("capital of France")
      - simple string operations ("Reverse the string 'x'")

    Replace this function's body with a real call to your actual agent
    (an API request, a local model, a framework's .run()/.invoke(), etc.)
    when you're ready. Keep the same signature: takes the input text (and
    optionally the version being evaluated) and returns the agent's answer.
    """
    text = input_text.strip()
    lower = text.lower()

    # Arithmetic: "What is 2 + 2?"
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", text)
    if match and ("what is" in lower or "calculate" in lower or "compute" in lower):
        a, op, b = match.groups()
        a, b = float(a), float(b)
        result = {"+": a + b, "-": a - b, "*": a * b, "/": a / b if b else None}[op]
        if result is not None and result == int(result):
            result = int(result)
        return str(result)

    # Simple fact lookup
    facts = {
        "capital of france": "Paris",
        "capital of japan": "Tokyo",
        "capital of italy": "Rome",
    }
    for key, value in facts.items():
        if key in lower:
            return value

    # String reversal: "Reverse the string 'hello'"
    match = re.search(r"reverse the string ['\"](.+?)['\"]", text, re.IGNORECASE)
    if match:
        return match.group(1)[::-1]

    # Fallback: no rule matched
    return f"[no rule matched for input: {text!r}]"
