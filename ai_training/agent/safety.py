import re
import json
from typing import Dict, Any, Optional, Tuple


class SafetyGuard:
    """
    Guards the agent against prompt injections, hallucinations,
    and output corruption.
    """

    INJECTION_PATTERNS = [
        r"ignore\s+(?:all\s+|previous\s+|your\s+|system\s+|the\s+)*instructions",
        r"disregard\s+(?:all\s+|previous\s+|your\s+|system\s+|the\s+)*instructions",
        r"tell\s+me\s+your\s+system\s+prompt",
        r"what\s+is\s+your\s+system\s+prompt",
        r"pretend\s+(?:error|that|you)",
        r"invent\s+(?:an?\s+)?(?:error|solution|fake|meter)",
        r"fake\s+solution",
        r"bypass\s+rules",
        r"act\s+as\s+an?\s+unrestricted",
        r"تجاهل\s+(?:كل\s+|أي\s+)?التعليمات",
        r"اخترع\s+(?:حل|كود)",
        r"اعتبر\s+نفسك",
    ]

    @classmethod
    def is_prompt_injection(cls, text: str) -> bool:
        """Check whether the user message contains jailbreak or prompt injection attempts."""
        t_lower = text.lower()
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, t_lower):
                return True
        return False

    @classmethod
    def sanitize_llm_output(cls, raw_output: str) -> str:
        """
        Clean output from thinking models (such as Granite 4.2).
        Strips <think>...</think> blocks, leading think fragments,
        and internal system leaks.
        """
        if not raw_output:
            return ""

        # Remove explicit <think>...</think> blocks
        cleaned = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL)

        # Handle unclosed or leading </think>
        if "</think>" in cleaned:
            cleaned = cleaned.split("</think>")[-1]

        # Strip remaining angle-bracket tags like <output>, etc.
        cleaned = re.sub(r"</?[a-zA-Z0-9_-]+>", "", cleaned)

        # Filter out untagged chain-of-thought monologues if present
        thinking_triggers = [
            r"^(?:okay|ok),?\s+(?:the\s+user|i\s+need|let's|we\s+need|the\s+rule).*",
            r"^i\s+(?:need|should|will)\s+to\s+ask.*",
            r"^the\s+rule\s+says.*",
            r"^thinking\s+process:?.*"
        ]
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        filtered_lines = []
        for line in lines:
            if any(re.match(pattern, line, flags=re.IGNORECASE) for pattern in thinking_triggers):
                continue
            filtered_lines.append(line)

        cleaned = "\n".join(filtered_lines).strip()

        # Normalize whitespace
        return cleaned.strip()

    @classmethod
    def safe_parse_json(cls, raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Safely extract and parse JSON object from LLM response.
        Handles markdown fences (```json ... ```) and text padding.
        """
        if not raw_text:
            return None

        # Clean thinking tags first
        text = cls.sanitize_llm_output(raw_text)

        # Look for code block fences
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Look for outermost curly braces
            match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = text

        try:
            return json.loads(json_str)
        except Exception:
            return None
