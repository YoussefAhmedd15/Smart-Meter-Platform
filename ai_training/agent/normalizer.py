import re
from typing import Optional, Dict, List, Tuple
from .models import CaseState


class TextNormalizer:
    """
    Robust text normalization for ISKRA Smart Meter support agent.
    Silently normalizes user spelling mistakes, typos, grammar mistakes,
    informal language, abbreviations, and mixed Arabic/English inputs.

    Strict Safety Invariants:
    1. NEVER invent or convert unknown technical identifiers into known ones:
       - 'Error 999' remains 'Error 999' (never 70 or 96).
       - 'MT999' remains 'MT999' (never MT514).
       - 'Vending' remains 'Vending'.
    2. Protect all technical codes and models before word normalization.
    3. Normalization is internal; raw text is preserved for audit/history.
    """

    # Technical keywords to shield from any alteration
    PROTECTED_TECHNICAL_WORDS = [
        "vending",
        "billing",
        "symbiot",
        "meterverse",
        "aqua",
        "dlms",
        "cosem",
        "obis",
        "rs485",
        "rs232",
        "hdlc",
        "modbus",
        "tcp",
        "ip",
    ]

    # Technical meter model pattern (e.g. MT514, MT999, ME514, AM550, MT5144)
    MODEL_PATTERN = re.compile(
        r"\b((?:MT|ME|AM|MW|MV)\s*\d{2,4}[A-Za-z0-9_-]*)\b", re.IGNORECASE
    )

    # Typo variations of "error" prefix before an error code number
    ERROR_PREFIX_PATTERN = re.compile(
        r"\b(?:error|erorr|eror|errr|erro|errorr|eerror|irror|err|code|cdoe|coed|كود|الكود|خطأ|خطا|خطء|الخطأ|الخطا|إيرور|ايرور|ارور)\s*[:#\-]?\s*(\d+)\b",
        re.IGNORECASE,
    )
    # Compressed error like Error70, erorr70, err70
    COMPRESSED_ERROR_PATTERN = re.compile(
        r"\b(?:error|erorr|eror|errr|err)(\d+)\b", re.IGNORECASE
    )

    # Common English typos & informal abbreviations
    ENGLISH_TYPO_MAP: Dict[str, str] = {
        # Meaning
        "mwan": "mean",
        "maen": "mean",
        "mena": "mean",
        "meen": "mean",
        "mening": "meaning",
        "meanign": "meaning",
        # Working
        "wokring": "working",
        "workign": "working",
        "wroking": "working",
        "workin": "working",
        "wrking": "working",
        "woking": "working",
        # Meter
        "metter": "meter",
        "metr": "meter",
        "mter": "meter",
        "meeter": "meter",
        # Happening / happened
        "happend": "happened",
        "happenning": "happening",
        "hapening": "happening",
        "hapnd": "happened",
        # Question words & contractions
        "wat": "what",
        "wht": "what",
        "wats": "what is",
        "whats": "what is",
        "what's": "what is",
        "dont": "don't",
        "dnt": "don't",
        "dnot": "do not",
        "cant": "can't",
        "cnt": "can't",
        "cannott": "cannot",
        "didnt": "didn't",
        "isnt": "isn't",
        "wont": "won't",
        # Issue / problem
        "porblem": "problem",
        "probem": "problem",
        "problm": "problem",
        "problme": "problem",
        "isue": "issue",
        "issur": "issue",
        "issuee": "issue",
        # Fix / repair / solve
        "repiar": "repair",
        "repar": "repair",
        "fixx": "fix",
        "solv": "solve",
        "soulution": "solution",
        # Display / screen
        "disply": "display",
        "dispaly": "display",
        "dsiplay": "display",
        "scren": "screen",
        "scrn": "screen",
        # Common particles
        "ded": "dead",
        "hlp": "help",
        "becasue": "because",
        "bcoz": "because",
        "bcuz": "because",
        "coz": "because",
        "shud": "should",
        "shoud": "should",
        "cud": "could",
        "wud": "would",
        "stauts": "status",
        "statuse": "status",
    }

    # Multi-word phrase normalizations
    PHRASE_NORMALIZATIONS: List[Tuple[re.Pattern, str]] = [
        # Arabic: العداد مش شغل -> العداد مش شغال
        (re.compile(r"\bالعداد\s+مش\s+شغل\b", re.IGNORECASE), "العداد مش شغال"),
        (re.compile(r"\bمش\s+شغل\s+خالص\b", re.IGNORECASE), "مش شغال خالص"),
        # Arabic: مش عاوز أسئلة -> مش عايز أسئلة
        (
            re.compile(
                r"\bمش\s+(?:عاوز|عايز)\s+(?:اسئلة|أسئلة|اسئله|أسئله)(?:\s+كتير)?\b",
                re.IGNORECASE,
            ),
            "مش عايز أسئلة كتير",
        ),
        (
            re.compile(
                r"\b(?:كفاية|بلاش)\s+(?:اسئلة|أسئلة|اسئله|أسئله)\b",
                re.IGNORECASE,
            ),
            "كفاية أسئلة",
        ),
        # What happens now / what's happening now
        (
            re.compile(r"\b(?:what(?:\s+is|'s)?|whats)\s+happend\s+now\b", re.IGNORECASE),
            "what happens now",
        ),
        (
            re.compile(r"\b(?:what(?:\s+is|'s)?|whats)\s+happend\b", re.IGNORECASE),
            "what happened",
        ),
    ]

    @classmethod
    def normalize(
        cls, text: str, state: Optional[CaseState] = None
    ) -> str:
        """
        Main normalization method.
        Preserves technical identifiers (e.g. Error 999, MT999, Vending).
        Normalizes typos, common abbreviations, and dialect variations.
        """
        if not text:
            return ""

        result = text.strip()

        # Step 1: Shield technical meter models (e.g. MT514, MT999, ME514, AM550)
        protected_tokens: Dict[str, str] = {}
        counter = 0

        def protect_model(match: re.Match) -> str:
            nonlocal counter
            key = f"__MODEL_TOKEN_{counter}__"
            counter += 1
            # Normalize internal spaces in model like "MT 514" -> "MT514", but preserve unknown codes like "MT999"
            val = re.sub(r"\s+", "", match.group(1).upper())
            protected_tokens[key] = val
            return key

        result = cls.MODEL_PATTERN.sub(protect_model, result)

        # Step 2: Normalize error prefixes while STRICTLY PRESERVING error numbers
        # E.g. "erorr 70" -> "Error 70", "eror 96" -> "Error 96", "Error 999" -> "Error 999"
        def normalize_error(match: re.Match) -> str:
            code_num = match.group(1).strip()
            return f"Error {code_num}"

        result = cls.ERROR_PREFIX_PATTERN.sub(normalize_error, result)
        result = cls.COMPRESSED_ERROR_PATTERN.sub(normalize_error, result)

        # Step 3: Apply multi-word phrase normalizations
        for pattern, replacement in cls.PHRASE_NORMALIZATIONS:
            result = pattern.sub(replacement, result)

        # Step 4: Word-level normalization for common English typos
        # We split by whitespace and punctuation boundaries while preserving protected tokens
        tokens = re.split(r"(\s+|[.,!?;:\"'()\[\]])", result)
        normalized_tokens = []
        for tok in tokens:
            if not tok:
                continue
            lower_tok = tok.lower()

            # If it's a protected token or technical word, keep as-is
            if tok in protected_tokens or lower_tok in cls.PROTECTED_TECHNICAL_WORDS:
                normalized_tokens.append(tok)
                continue

            # Check typo map
            if lower_tok in cls.ENGLISH_TYPO_MAP:
                replacement = cls.ENGLISH_TYPO_MAP[lower_tok]
                # Preserve case if original was title-cased or uppercase
                if tok.isupper() and len(tok) > 1:
                    replacement = replacement.upper()
                elif tok.istitle():
                    replacement = replacement.title()
                normalized_tokens.append(replacement)
            else:
                normalized_tokens.append(tok)

        result = "".join(normalized_tokens)

        # Step 5: Contextual resolution if previous context exists
        # E.g. If user says "what does it mwan" and an error is in state,
        # it was normalized to "what does it mean" in Step 4.
        if state and state.error_code:
            # If user asks "what does error mean" without number, context supplies the number
            context_pattern = re.compile(
                r"\bwhat\s+(?:does|is)\s+(?:the\s+)?error\s+mean\b",
                re.IGNORECASE,
            )
            if context_pattern.search(result):
                result = context_pattern.sub(
                    f"what does Error {state.error_code} mean", result
                )

        # Step 6: Restore protected tokens
        for key, val in protected_tokens.items():
            result = result.replace(key, val)

        # Clean up excess whitespace
        result = re.sub(r"\s+", " ", result).strip()

        return result
