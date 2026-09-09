import re
from typing import Optional
from .models import AgentIntent


class IntentDetector:
    """
    Detects customer conversational intent.
    Supports English and Arabic, and recognizes follow-ups and direct questions.
    """

    @classmethod
    def detect_intent(
        cls,
        text: str,
        has_previous_context: bool = False,
        last_intent: Optional[str] = None,
        last_question_field: Optional[str] = None,
    ) -> AgentIntent:
        q_lower = text.lower().strip()

        # ------------------------------------------------------------
        # 1. ESCALATION INTENT
        # ------------------------------------------------------------
        escalation_patterns = [
            r"\bescalat\w*\b",
            r"\b(?:send|forward|transfer)(?:\s+\w+)?\s+to\s+l2\b",
            r"\bl2(?:\s+support)?\b",
            r"\bneed\s+(?:an?\s+)?(?:engineer|human|agent)\b",
            r"\btalk\s+to\s+(?:an?\s+)?(?:human|engineer|specialist)\b",
            r"(?:حولني|تصعيد|مهندس|فريق الدعم|ابعتها ل l2)",
        ]
        if any(re.search(p, q_lower) for p in escalation_patterns):
            return AgentIntent.ESCALATION

        # ------------------------------------------------------------
        # 2. STATUS QUESTION
        # ------------------------------------------------------------
        status_keywords = [
            "status of",
            "ticket status",
            "is it solved",
            "any update",
            "حالة التذكرة",
            "الحالة",
            "اتحلت ولا لسه",
        ]
        if any(k in q_lower for k in status_keywords):
            return AgentIntent.STATUS_QUESTION

        # ------------------------------------------------------------
        # 3. IDENTIFICATION INTENT
        # ------------------------------------------------------------
        identification_keywords = [
            "where can i find",
            "where is the model",
            "where is model",
            "how to find model",
            "where to find the meter model",
            "where is the serial",
            "فين الموديل",
            "ازاي اعرف الموديل",
            "مكان الموديل",
            "اجيب الموديل منين",
            "فين نوع العداد",
        ]
        if any(k in q_lower for k in identification_keywords):
            return AgentIntent.IDENTIFICATION

        # ------------------------------------------------------------
        # 4. DIRECT ERROR EXPLANATION
        # ------------------------------------------------------------
        # Questions like "What is Error 70?", "What does error 96 mean?", "show error 0101", "ما هو خطأ 70؟", "يعني ايه error 70", "معناه ايه؟"
        error_explanation_patterns = [
            r"what\s+(?:is|does)\s+error",
            r"what\s+(?:is|does)\s+code",
            r"error\s*\d+\s*(?:mean|meaning|definition)",
            r"explain\s+(?:error|code)",
            r"(?:show|tell\s+me\s+about|display)\s+(?:error|code)\s*\d+",
            r"ما\s*(?:هو|معنى)\s*(?:خطأ|كود|error)",
            r"يعني\s*(?:ايه|إيه)\s*(?:error|خطأ|كود)",
            r"ماذا\s*يعني\s*(?:خطأ|كود|error)",
            r"معنى\s*(?:كود|خطأ|error)",
            r"كود\s*(?:الخطأ\s*)?\d+\s*معناه\s*(?:ايه|إيه)",
            r"الخطأ\s*\d+\s*معناه\s*(?:ايه|إيه)",
        ]
        for pattern in error_explanation_patterns:
            if re.search(pattern, q_lower):
                return AgentIntent.ERROR_EXPLANATION

        # Contextual error meaning question: "what does it mean?", "what does that mean?", "معناه ايه؟"
        if has_previous_context:
            contextual_meaning = [
                "what does it mean",
                "what does that mean",
                "what does this mean",
                "what is the meaning",
                "معناه ايه",
                "معناه إيه",
                "يعني ايه",
                "يعني إيه",
                "معناه",
            ]
            if any(k in q_lower for k in contextual_meaning) and len(text.split()) <= 5:
                return AgentIntent.ERROR_EXPLANATION

        # If the message is strictly an error code query like "Error 70?" or "What is 70?" or "Error 70" or "show error 0101"
        if re.search(r"^(?:what\s+is\s+|show\s+|explain\s+)?(?:error|code|كود|الخطأ)?\s*[:#-]?\s*\d+\??$", q_lower):
            return AgentIntent.ERROR_EXPLANATION

        # ------------------------------------------------------------
        # 5. FOLLOW-UP INTENT
        # ------------------------------------------------------------
        follow_up_keywords = [
            "same problem",
            "same issue",
            "still happening",
            "still not working",
            "problem is still",
            "that didn't work",
            "did not work",
            "checked the power",
            "i checked",
            "tried that",
            "what about",
            "what should i do",
            "what should we do",
            "what can i do",
            "what do i do",
            "how to fix",
            "how do i fix",
            "how can i fix",
            "how to solve",
            "what meter is this for",
            "what meter is that for",
            "which meter is this for",
            "is the meter broken",
            "is the meter damaged",
            "لسه المشكلة",
            "لسه المشكله",
            "نفس المشكلة",
            "نفس المشكله",
            "نفس العطل",
            "لسه مش شغال",
            "لسه مش شغالة",
            "جربت وما اشتغلش",
            "جربت ومنفعش",
            "فحصت الباور",
            "فحصت الكهربا",
            "أعمل ايه",
            "اعمل ايه",
            "أعمل إيه",
            "اعمل إيه",
            "إيه الحل",
            "ايه الحل",
            "ازاي أصلحها",
            "ازاي احلها",
            "طريقة الحل",
            "حلها ايه",
            "حلها إيه",
            "ده لأي عداد",
            "ده بتاع انهي عداد",
            "العداد بايظ",
            "العداد عطلان",
            "what is happening",
            "what's happening",
            "what is going on",
            "what's going on",
            "what happened",
            "what is the problem",
            "what's the problem",
            "what is the issue",
            "what's the issue",
            "what is wrong",
            "what's wrong",
            "ايه اللي بيحصل",
            "إيه اللي بيحصل",
            "ايه المشكلة",
            "إيه المشكلة",
            "ايه اللي حصل",
            "إيه اللي حصل",
        ]
        if any(k in q_lower for k in follow_up_keywords):
            return AgentIntent.FOLLOW_UP

        # If user answers a previous question directly (e.g. yes, no, or providing a field value when asked)
        if has_previous_context and last_question_field:
            if q_lower in ["yes", "no", "yeah", "yep", "نعم", "ايوه", "أيوه", "اه", "أه", "لا"]:
                return AgentIntent.FOLLOW_UP

        # ------------------------------------------------------------
        # 6. GENERAL QUESTION / GREETING / INFORMATIONAL QUERY
        # ------------------------------------------------------------
        general_keywords = [
            "can you help",
            "help me",
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "ممكن تساعدني",
            "ساعدني",
            "مرحبا",
            "اهلا",
            "أهلا",
            "السلام عليكم",
            "صباح الخير",
        ]
        if any(re.search(rf"(?:\b|^){re.escape(k)}(?:\b|$)", q_lower) for k in general_keywords) and len(text.split()) <= 4:
            return AgentIntent.GENERAL_QUESTION

        # General informational questions: e.g. "What is a smart meter?", "What is Vending?", "ما هو العداد الذكي؟", "ايه القراءات اللي العداد بيطلعها؟"
        general_q_patterns = [
            r"^(?:what\s+(?:is|are)|tell\s+me\s+about|can\s+you\s+explain|explain)\s+(?:a\s+|an\s+|the\s+)?([^\d\?]+)\??$",
            r"^(?:ما\s*(?:هو|هي)|ماهو|ماهي|معلومات\s*عن|كلمنا\s*عن|كلمني\s*عن|يعني\s*(?:ايه|إيه))\s+(?:نظام\s+|ال)?([^\d\?]+)\??$",
            r"^(?:what\s+(?:does|can|do))\s+.*?(?:mean|measure|do|use|support|provide|read|produce)\??$",
            r"^what\s+.*?(?:does|do|can|is|are|use|mean|produce|provide|read|show)\b.*?\??$",
            r"^which\s+.*?\??$",
            r"^(?:does|do|is|are)\s+.*?\??$",
            r"^how\s+(?:does|do|can|to|is)\s+.*?\??$",
            r"^can\s+(?:the\s+meter|it|[a-zA-Z0-9_-]+)\s+.*?\??$",
            r"what\s+does\s+(.+?)\s+mean\??$",
            r"^(?:هل\s+|كيف\s+)",
            r"^(?:ماذا\s*يقيس|ما\s*الذي\s*يقيسه|ما\s*هو\s*بروتوكول|أي\s*بروتوكول|ما\s*هي\s*أنظمة)\b",
            r"(?:يقيس|بيقيس)\s*(?:ايه|إيه|ماذا)",
            r"(?:هو\s+)?العداد\s+(?:بيقيس|يقيس)",
            r"^(?:ايه|إيه)\s+(?:هي\s+|هو\s+|ال)?(?:قراءات|وظائف|مواصفات|بروتوكول|أنظمة|قياسات|مميزات|طاقة|جهد|تيار|امكانيات|إمكانيات)\b",
            r"^(?:ايه|إيه)\s+.*?(?:بيقيس|يقيس|بيطلعه|بيطلعها|يطلعها|يسجل|بيسجل|يحسب|بيحسب)\b",
            r"^(?:هو\s+|هي\s+)?(?:العداد|الموديل|الجهاز)\s+.*?(?:بيقيس|يقيس|بيطلع|يطلع|بيطلعلي|يسجل|يدعم|بيستخدم|يستخدم|مواصفات)\b",
            r"^(?:ممكن\s+(?:اعرف|أعرف|توضح|تقولي|تفيدني))\s+.*?\??$",
        ]
        for gp in general_q_patterns:
            if re.search(gp, q_lower):
                # Ensure it is not an error code query, status query, or contextual situation query
                # Exclude explicit error code queries or problem reports, but allow model names with digits (e.g. MT174, ME514)
                if not re.search(r"(?:\b(?:error|code|خطأ|كود)\s*[:#\-]?\s*\d+\b|^\s*#?\d+\s*$|\b(?:happening|going\s+on|wrong|matter|مشكلة|عطلان|معطل|مش شغال)\b)", q_lower):
                    return AgentIntent.GENERAL_QUESTION

        # ------------------------------------------------------------
        # 7. TROUBLESHOOTING INTENT (Default for issues/errors/meters)
        # ------------------------------------------------------------
        trouble_keywords = [
            "not working", "isn't working", "is not working", "broken", "failed", "fails", "failing",
            "dead", "meter dead", "no power", "error", "problem", "issue", "cannot", "can't",
            "مش شغال", "مش شغالة", "عطلان", "معطل", "مشكلة", "عطل", "مش بيفتح",
            "بيطلع", "فشل", "تالف", "مكسور", "vending", "symbiot",
        ]
        if any(k in q_lower for k in trouble_keywords):
            return AgentIntent.TROUBLESHOOTING

        # If user has an active context and gives more info:
        if has_previous_context and last_intent in [
            AgentIntent.TROUBLESHOOTING.value,
            AgentIntent.FOLLOW_UP.value,
            AgentIntent.ERROR_EXPLANATION.value,
        ]:
            return AgentIntent.FOLLOW_UP

        return AgentIntent.OTHER
