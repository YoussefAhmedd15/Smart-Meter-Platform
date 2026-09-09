"""
ai_training/agent/policy.py
TECHNICAL vs GENERAL KNOWLEDGE POLICY ENFORCER

Enforces the strict distinction between:
  A. TECHNICAL / COMPANY-SPECIFIC QUESTIONS (Local Knowledge Base ONLY, no guessing/hallucinations)
  B. GENERAL / NON-TECHNICAL QUESTIONS (General LLM knowledge allowed)

When in doubt, always prefers TECHNICAL / COMPANY-SPECIFIC (safe behavior).
"""

import re
from typing import Tuple, Optional
from .models import CaseState


DOMAIN_TECHNICAL_COMPANY = "TECHNICAL_COMPANY"
DOMAIN_GENERAL_NON_TECHNICAL = "GENERAL_NON_TECHNICAL"

MISSING_TECHNICAL_INFO_EN = "This information is not available in the current ISKRA knowledge base (documentation currently available)."
MISSING_TECHNICAL_INFO_AR = "هذه المعلومة غير متوفرة في قاعدة معرفة إسكرا الحالية (الوثائق المعتمدة المتاحة حالياً)."


class KnowledgePolicy:
    """
    Enforces the Technical vs General Knowledge Policy for the ISKRA AI Agent.
    """

    # 1. Direct Company & Brand Identifiers
    COMPANY_PATTERNS = [
        r"\biskra(?:emeco)?\b",
        r"\bإسكرا\b",
        r"\bاسكرا\b",
        r"\bالشركة\b",
        r"\bcompany\b",
    ]

    # 2. ISKRA Smart Meter Models & Families
    METER_MODEL_PATTERNS = [
        r"\bmt174\b",
        r"\bmt514\b",
        r"\bme514\b",
        r"\bmt880\b",
        r"\bmt514-ct\b",
        r"\bme514-5\b",
        r"\bam550\b",
        r"\bzsk08206\b",
        r"\bscdc\b",
        r"\bmpms\s*3000\b",
        r"\bmpms\b",
        r"\bsymbiot\b",
        r"\bvending\b",
        r"\bncdc\b",
        r"\bpem\b",
        r"\baqua\b",
        r"\bdunes\b",
        r"\btravco\b",
        r"\b(?:mt|me)\s*\d{3}\b",
    ]

    # 3. Meter Hardware, Meter Generic References & Components
    METER_HARDWARE_PATTERNS = [
        r"\bmeters?\b",
        r"\bsmart\s+meters?\b",
        r"\belectricity\s+meters?\b",
        r"\bعداد(?:ات|ين)?\b",
        r"\bالعداد(?:ات)?\b",
        r"\bterminal\s+cover\b",
        r"\bmain\s+cover\b",
        r"\bcontactor\b",
        r"\brelay\b",
        r"\boptical\s+port\b",
        r"\boptical\s+probe\b",
        r"\bpush\s*button\b",
        r"\bseal\b",
        r"\bcard\s+slot\b",
        r"\bغطاء\s+العداد\b",
        r"\bغطاء\s+الروزتة\b",
        r"\bالريلاي\b",
        r"\bالمفتاح\s+الداخلي\b",
        r"\bمنفذ\s+الكروت\b",
        r"\bالوصلة\s+الضوئية\b",
    ]

    # 4. Technical Measurements, Registers, Specifications, OBIS
    MEASUREMENT_SPEC_PATTERNS = [
        r"\bwhat\s+(?:can|does)\s+(?:the\s+)?meter\s+measure\b",
        r"\bmeasure(?:ment|ments|s|d)?\b",
        r"\bactive\s+energy\b",
        r"\breactive\s+energy\b",
        r"\bapparent\s+power\b",
        r"\binstantaneous\b",
        r"\bpower\s+factor\b",
        r"\bload\s+profile\b",
        r"\bmaximum\s+demand\b",
        r"\btamper\b",
        r"\btariff\b",
        r"\bvoltage\b",
        r"\bcurrent\b",
        r"\bfrequency\b",
        r"\bkwh\b",
        r"\bkvarh\b",
        r"\bkva\b",
        r"\bobis\b",
        r"\bregisters?\b",
        r"\bقياس(?:ات)?\b",
        r"\bيقيس\b",
        r"\bبيسجل\b",
        r"\bبيحسب\b",
        r"\bسجل(?:ات)?\b",
        r"\bالجهد\b",
        r"\bالتيار\b",
        r"\bمعامل\s+القدرة\b",
        r"\bالتردد\b",
        r"\bأقصى\s+حمل\b",
        r"\bشريحة\b",
        r"\bشرائح\b",
        r"\bرصيد\b",
        r"\bكيلو\s*وات\b",
    ]

    # 5. Communication Protocols & Industrial Specs
    COMMUNICATION_PATTERNS = [
        r"\bdlms\b",
        r"\bcosem\b",
        r"\bobis\b",
        r"\bhdlc\b",
        r"\biec\s*62056\b",
        r"\brs485\b",
        r"\brs232\b",
        r"\bm-?bus\b",
        r"\bcs\s+interface\b",
        r"\bcommunication\s+protocol\b",
        r"\bprotocols?\s+(?:does|used)\b",
        r"\bwhich\s+protocol\b",
        r"\bبروتوكول(?:ات)?\b",
    ]

    # 6. Error Codes, Alarms, Display Codes
    ERROR_CODE_PATTERNS = [
        r"\b(?:error|code|err)\s*[:#\-]?\s*\d+\b",
        r"\b(?:كود|خطأ)\s*[:#\-]?\s*\d+\b",
        r"\b(?:ouer-p|op-couer|top_open|op-tcou|ter-open|e-date|battery|e-batter|e-uolt|ouer-u|cur-re|reuerse|e-steal|e-rela4|e-relay|l-credit|non-cred|l-leu\d|e-load|e-sequen|miss-ne|drop-u-i|miss-u|magnet)\b",
    ]

    # 7. Meter Procedures: Calibration, Installation, Wiring, L1/L2 Support
    PROCEDURE_PATTERNS = [
        r"\binstall(?:ation|ing)?\b",
        r"\bwiring\b",
        r"\bcalibrat(?:ion|ing)?\b",
        r"\btroubleshoot(?:ing)?\b",
        r"\bmaintenance\b",
        r"\bl1\b",
        r"\bl2\b",
        r"\bتركيب\b",
        r"\bتوصيل\b",
        r"\bمعايرة\b",
        r"\bصيانة\b",
        r"\bتصعيد\b",
    ]

    # 8. Explicit General Knowledge Concepts (Whitelisted as purely general if NOT combined with company context)
    GENERAL_CONCEPT_PATTERNS = [
        r"^(?:what\s+(?:is|does|are|mean)|explain|define|tell\s+me\s+about)\s+(?:a\s+|an\s+|the\s+)?(login|database|python|api|tcp\/?ip|http|https|html|css|javascript|sql|ip\s+address|subnet|firewall|operating\s+system|cpu|ram|cloud|server|rest\s+api|encryption|dns|algorithm|computer)\b",
        r"what\s+does\s+(login|database|python|api|tcp\/?ip|http|https|sql|dns)\s+mean\b",
        r"^(?:ما\s*(?:هو|هي|معنى)|ماهو|ماهي|اشرح|يعني\s*(?:ايه|إيه)|معنى)\s+(?:مفهوم\s+|بروتوكول\s+|تقنية\s+|لغة\s+)?(?:ال)?(login|database|python|api|tcp\/?ip|http|https|sql|dns|تسجيل\s+الدخول|قاعدة\s+البيانات|بايثون|البرمجة|الانترنت|الشبكة|الكمبيوتر|نظام\s+التشغيل)\b",
        r"\b(?:يعني\s*(?:ايه|إيه)|معنى)\s+(login|database|python|api|tcp\/?ip)\b",
    ]

    # 9. Contextual Modifiers that FORCE a general concept into COMPANY-SPECIFIC
    COMPANY_CONTEXT_MODIFIERS = [
        r"\bin\s+(?:the\s+)?iskra\b",
        r"\bin\s+(?:the\s+)?meter\b",
        r"\bin\s+(?:the\s+)?system\b",
        r"\bfor\s+(?:the\s+)?meter\b",
        r"\bfor\s+iskra\b",
        r"\bdoes\s+iskra\b",
        r"\biskra\s+use\b",
        r"\biskra\s+application\b",
        r"\biskra\s+system\b",
        r"\bفي\s+إسكرا\b",
        r"\bفي\s+العداد\b",
        r"\bفي\s+السيستم\b",
        r"\bفي\s+نظام\b",
        r"\bخاص\s+بالعداد\b",
        r"\bبتاع\s+العداد\b",
    ]

    @classmethod
    def classify_domain(cls, query: str, state: Optional[CaseState] = None) -> Tuple[str, str]:
        """
        Classifies query into:
          - DOMAIN_TECHNICAL_COMPANY: Must use local ISKRA Knowledge Base ONLY. No external guessing.
          - DOMAIN_GENERAL_NON_TECHNICAL: General language/model knowledge allowed.

        Follows Rule D: When in doubt, prefer DOMAIN_TECHNICAL_COMPANY.
        """
        q_clean = query.lower().strip()

        # Step 1: Check for explicit company context modifiers (forces company-specific)
        for mod in cls.COMPANY_CONTEXT_MODIFIERS:
            if re.search(mod, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query attaches company/meter context via modifier: '{mod}'",
                )

        # Step 2: Check for direct company references (ISKRA, Iskraemeco)
        for pat in cls.COMPANY_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query directly mentions company: '{pat}'",
                )

        # Step 3: Check for specific meter models & company systems
        for pat in cls.METER_MODEL_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query references meter model or company system: '{pat}'",
                )

        # Step 4: Check for meter hardware & generic meter terms
        for pat in cls.METER_HARDWARE_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query references meter hardware or meter device: '{pat}'",
                )

        # Step 4.5: Check for Whitelisted General Non-Technical Concepts (Rule B)
        # If the query is free from ISKRA, meter models, and hardware, and matches general concepts:
        for g_pat in cls.GENERAL_CONCEPT_PATTERNS:
            if re.search(g_pat, q_clean):
                return (
                    DOMAIN_GENERAL_NON_TECHNICAL,
                    f"Matched general, non-technical concept query: '{g_pat}'",
                )

        # Step 5: Check for technical measurements, registers, OBIS
        for pat in cls.MEASUREMENT_SPEC_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query references meter measurement, register, or spec: '{pat}'",
                )


        # Step 6: Check for industrial protocols (DLMS, COSEM, RS485, etc.)
        for pat in cls.COMMUNICATION_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query references industrial communication protocol: '{pat}'",
                )

        # Step 7: Check for error codes
        for pat in cls.ERROR_CODE_PATTERNS:
            if re.search(pat, q_clean):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    f"Query references diagnostic error code: '{pat}'",
                )

        # Step 8: Check for meter procedures (installation, calibration, wiring)
        for pat in cls.PROCEDURE_PATTERNS:
            if re.search(pat, q_clean):
                # Only if not a purely abstract generic word
                if any(w in q_clean for w in ["meter", "عداد", "wiring", "calibration", "l1", "l2", "معايرة", "تركيب"]):
                    return (
                        DOMAIN_TECHNICAL_COMPANY,
                        f"Query references meter technical procedure: '{pat}'",
                    )

        # Step 9: Check if active case state already has a technical meter/error context
        # If user has an ongoing discussion about a specific meter error, follow-ups are technical
        if state and (state.error_code or state.meter_model or state.system):
            # If the user asks a follow-up about that meter issue, keep it technical
            if any(k in q_clean for k in ["fix", "solve", "how", "what", "حل", "ازاي", "اعمل"]):
                return (
                    DOMAIN_TECHNICAL_COMPANY,
                    "Follow-up inherits technical context from active case state",
                )

        # Step 10: Check for Whitelisted General Non-Technical Concepts
        for g_pat in cls.GENERAL_CONCEPT_PATTERNS:
            if re.search(g_pat, q_clean):
                return (
                    DOMAIN_GENERAL_NON_TECHNICAL,
                    f"Matched general, non-technical concept query: '{g_pat}'",
                )

        # Common general greeting / pleasantry checks
        greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
            "can you help me", "help me", "who are you", "what can you do", "thank you", "thanks",
            "مرحبا", "اهلا", "أهلا", "السلام عليكم", "صباح الخير", "مساء الخير", "شكرا", "شكراً",
        ]
        if any(re.search(rf"(?:\b|^){re.escape(g)}(?:\b|$)", q_clean) for g in greetings) and len(q_clean.split()) <= 4:
            return (
                DOMAIN_GENERAL_NON_TECHNICAL,
                "General greeting / conversational pleasantry",
            )

        # Step 11: RULE D — WHEN IN DOUBT, PREFER TECHNICAL / COMPANY-SPECIFIC
        # If there are any technical words or if it's uncertain, treat as technical
        technical_suspicious_words = [
            "phase", "terminal", "contactor", "relay", "power", "tamper", "alarm", "pulse",
            "battery", "card", "display", "screen", "button", "clock", "rtc", "firmware",
            "فازة", "طرفي", "ريلاي", "باور", "كارت", "شاشة", "نبضة", "تلاعب"
        ]
        if any(w in q_clean for w in technical_suspicious_words):
            return (
                DOMAIN_TECHNICAL_COMPANY,
                "Rule D fallback: Contains suspicious technical terms; defaulting to technical.",
            )

        # If it's a short general "what is X?" where X is not a meter term, check if X is a general word
        m_what_is = re.search(r"^(?:what\s+(?:is|are|does\s+\w+\s+mean)|explain|define)\s+(?:a\s+|an\s+|the\s+)?([a-zA-Z\s]+)\??$", q_clean)
        if m_what_is:
            term = m_what_is.group(1).strip()
            # If the term contains no meter/technical words, treat as general
            if not any(w in term for w in ["meter", "iskra", "mt174", "mt514", "me514", "error", "relay", "wire"]):
                return (
                    DOMAIN_GENERAL_NON_TECHNICAL,
                    f"General definitional inquiry for '{term}'",
                )

        # Final default under Rule D: When in doubt, prefer the safer behavior (TECHNICAL_COMPANY)
        return (
            DOMAIN_TECHNICAL_COMPANY,
            "Rule D: Uncertainty detected; safer behavior is to treat as technical/company-specific.",
        )
