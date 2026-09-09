import re
from typing import Dict, Any, List, Optional, Tuple


class FactExtractor:
    """
    Extracts structured case facts from natural language messages.
    Supports English, Arabic, Egyptian Arabic, and mixed technical phrases.
    Tolerates typos and informal language.
    """

    # ------------------------------------------------------------
    # ERROR CODE PATTERNS
    # ------------------------------------------------------------
    ERROR_CODE_PATTERNS = [
        # Explicit error/code prefixes (EN & AR) with optional "ال" and optional "code" / "الخطأ"
        r"(?:error|erorr|eror|errr|erro|irror|err|code|خطأ|خطا|الخطأ|الخطا|كود|الكود|إيرور|ايرور|ارور)\s*(?:code|الخطأ|الخطا)?\s*[:#\-]?\s*(\d+)\b",
        # "بيطلع 70" or "يعطي 70" or "shows 70" or "بيطلع Error 70"
        r"(?:بيطلع|بيعطي|يظهر|بيجيب|shows|giving|displays)\s*(?:error|erorr|eror|errr|خطأ|كود|الخطأ|الكود)?\s*[:#\-]?\s*(\d+)\b",
        # "error-70" or "err70" or "eror70" or "erorr70"
        r"\b(?:error|erorr|eror|errr|err)(\d+)\b",
    ]

    # ------------------------------------------------------------
    # METER MODEL PATTERNS
    # ------------------------------------------------------------
    METER_MODEL_PATTERNS = [
        r"\b(MT174(?:[-_ ]?[A-Za-z0-9]+)?)\b",
        r"\b(MT514(?:[-_ ]?[A-Za-z0-9]+)?)\b",
        r"\b(ME514(?:[-_ ]?[A-Za-z0-9]+)?)\b",
        r"\b(AM550)\b",
        r"\b(MT880)\b",
        r"\b(MT800)\b",
        r"\b(MT382)\b",
        r"\b(MW5[A-Za-z0-9_-]*)\b",
        r"\b(MV5[A-Za-z0-9_-]*)\b",
    ]

    # ------------------------------------------------------------
    # "I DON'T KNOW" EXPRESSIONS
    # ------------------------------------------------------------
    DONT_KNOW_PHRASES = [
        "don't know",
        "dont know",
        "do not know",
        "not sure",
        "no idea",
        "haven't checked",
        "cant tell",
        "can't tell",
        "cannot find",
        "مش عارف",
        "مش عارفه",
        "مش متأكد",
        "مش متاكد",
        "معرفش",
        "ما اعرف",
        "ما بعرف",
        "لا اعلم",
        "لا أعلم",
        "مش باين",
        "مش واضح",
        "مش لاقي",
    ]

    @classmethod
    def extract_facts(
        cls,
        text: str,
        last_question_field: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extract all identifiable facts and 'user does not know' indicators.
        Returns: (facts_dict, user_does_not_know_list)
        """
        facts: Dict[str, Any] = {}
        user_does_not_know: List[str] = []

        q_lower = text.lower().strip()

        # 1. Check for "I don't know"
        dont_know_detected, field_unknown = cls.extract_unknown_fields(
            text, last_question_field
        )
        if dont_know_detected:
            if field_unknown:
                user_does_not_know.extend(field_unknown)
            elif last_question_field:
                user_does_not_know.append(last_question_field)

        # 1b. Check for user frustration / request for no questions
        frustration_keywords = [
            "مش عايز أسئلة", "مش عايز اسئله", "مش عاوز أسئلة", "مش عاوز اسئله",
            "كفاية أسئلة", "كفاية اسئله", "بلاش أسئلة", "بلاش اسئله",
            "مش عايز أسئلة كتير", "مش عاوز أسئلة كتير",
            "stop asking questions", "no more questions", "don't ask questions",
            "dont ask questions", "don't ask so many questions", "dont ask so many questions",
            "too many questions", "enough questions"
        ]
        if any(k in q_lower for k in frustration_keywords):
            facts["user_frustrated"] = True

        # 2. Extract Error Code
        error_code = cls.extract_error_code(text, last_question_field)
        if error_code:
            facts["error_code"] = error_code

        # 3. Extract Meter Type
        meter_type = cls.extract_meter_type(text, last_question_field)
        if meter_type:
            facts["meter_type"] = meter_type

        # 4. Extract Meter Model
        meter_model = cls.extract_meter_model(text, last_question_field)
        if meter_model:
            facts["meter_model"] = meter_model

        # 5. Extract System
        system = cls.extract_system(text, last_question_field)
        if system:
            facts["system"] = system

        # 6. Extract Scenario
        scenario = cls.extract_scenario(text)
        if scenario:
            facts["scenario"] = scenario

        # 7. Extract Issue Description
        issue = cls.extract_issue_description(text)
        if issue:
            facts["issue"] = issue

        # 8. Detect Symptom Category & Specific Facts
        symptom_category = cls.detect_symptom_category(text)
        if symptom_category:
            facts["symptom_category"] = symptom_category

        display_symptom = cls.extract_display_symptom(text, last_question_field)
        if display_symptom:
            facts["display_symptom"] = display_symptom
            facts["symptom_category"] = "display"

        meter_responsiveness = cls.extract_meter_responsiveness(text)
        if meter_responsiveness:
            facts["meter_responsiveness"] = meter_responsiveness

        return facts, user_does_not_know

    @classmethod
    def extract_unknown_fields(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """Detect if the user expressed uncertainty and identify which field."""
        q_lower = text.lower()

        is_dont_know = any(phrase in q_lower for phrase in cls.DONT_KNOW_PHRASES)

        unknown_fields = []
        if is_dont_know:
            # Check if specific field was mentioned as unknown
            if any(w in q_lower for w in ["model", "موديل", "طراز", "نوع الموديل"]):
                unknown_fields.append("meter_model")
            if any(w in q_lower for w in ["type", "نوع العداد", "النوع", "كهربا ولا مية", "نوعه"]):
                unknown_fields.append("meter_type")
            if any(w in q_lower for w in ["system", "سيستم", "برنامج", "نظام"]):
                unknown_fields.append("system")
            if any(w in q_lower for w in ["error", "كود", "رقم الخطأ", "كود الخطأ"]):
                unknown_fields.append("error_code")
            if any(w in q_lower for w in ["anything", "أي حاجة", "اي حاجه", "أي حاجه عنه", "اي حاجه عنه", "لا شيء", "مش عارف حاجة", "مش عارف اي حاجة"]):
                unknown_fields.extend(["meter_model", "meter_type", "system"])

            # If user just said "don't know" and we previously asked about a specific field:
            if not unknown_fields and last_question_field:
                unknown_fields.append(last_question_field)

        return is_dont_know, unknown_fields

    @classmethod
    def extract_error_code(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Optional[str]:
        """Extract numeric error code, strictly preserving the technical identifier verbatim."""
        # Check standard patterns
        for pattern in cls.ERROR_CODE_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Direct answer check: e.g. user replies "70" or "Error 70" or "#70" or arbitrary numbers
        stripped = text.strip()
        if re.fullmatch(r"#?\d+", stripped):
            return stripped.lstrip("#")

        # If previous question was about error code and message contains a number:
        if last_question_field == "error_code":
            num_match = re.search(r"\b(\d+)\b", text)
            if num_match:
                return num_match.group(1).strip()

        return None

    @classmethod
    def extract_meter_type(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Optional[str]:
        """Extract meter type (Electric, Water, Ultrasonic)."""
        q_lower = text.lower()

        # Water checks first
        water_keywords = [
            "water meter",
            "water",
            "عداد مياه",
            "عداد ميه",
            "عداد المية",
            "عداد المياة",
            "مياه",
            "ميه",
        ]
        if any(w in q_lower for w in water_keywords):
            return "Water"

        # Ultrasonic checks
        if "ultrasonic" in q_lower or "التراسونيك" in q_lower:
            return "Ultrasonic"

        # Electric checks
        electric_keywords = [
            "electric meter",
            "electricity",
            "electric",
            "عداد كهرباء",
            "عداد الكهرباء",
            "عداد كهربا",
            "عداد الكهربا",
            "كهرباء",
            "كهربا",
        ]
        # Make sure "electric system" is not mistakenly classified as meter type alone
        # (Though meter type may still be Electric if specified)
        if any(w in q_lower for w in electric_keywords):
            return "Electric"

        # Contextual single word
        if last_question_field == "meter_type":
            if "electric" in q_lower or "كهربا" in q_lower:
                return "Electric"
            if "water" in q_lower or "مية" in q_lower:
                return "Water"

        return None

    @classmethod
    def extract_meter_model(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Optional[str]:
        """Extract meter model (MT514, ME514, AM550, etc.)."""
        for pattern in cls.METER_MODEL_PATTERNS:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                # Normalize spaces and dashes, e.g. "MT 514" -> "MT514"
                model_str = match.group(1).upper()
                model_str = re.sub(r"[\s_-]+", "", model_str)
                return model_str

        # Direct response to model question
        if last_question_field == "meter_model":
            # Match tokens like 514, mt514, mt174
            short_match = re.search(r"\b(mt\s*514|me\s*514|am\s*550|mt\s*880|mt\s*174)\b", text, re.IGNORECASE)
            if short_match:
                return re.sub(r"[\s_-]+", "", short_match.group(1).upper())

        return None

    @classmethod
    def extract_system(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Optional[str]:
        """Extract software/system name."""
        q_lower = text.lower()

        system_mapping = {
            "vending": ["vending", "فيندنج", "فيندينج", "الفيندنج"],
            "billing": ["billing", "بيلنج", "بيلينج", "البيلينج"],
            "symbiot": ["symbiot", "سيمبيوت", "السيمبيوت"],
            "meterverse": ["meterverse", "ميترفرس", "ميترفيرس"],
            "aqua": ["aqua", "اكوا", "أكوا"],
        }

        for sys_name, keywords in system_mapping.items():
            if any(k in q_lower for k in keywords):
                return sys_name.capitalize()

        # Electric system specifically
        electric_system_keywords = [
            "electric system",
            "electric software",
            "electric app",
            "electric application",
            "سيستم الكهربا",
            "سيستم الكهرباء",
            "نظام الكهرباء",
        ]
        if any(k in q_lower for k in electric_system_keywords):
            return "Electric"

        if last_question_field == "system":
            for sys_name, keywords in system_mapping.items():
                if any(k in q_lower for k in keywords):
                    return sys_name.capitalize()

        return None

    @classmethod
    def extract_scenario(cls, text: str) -> Optional[str]:
        """Extract scenario / trigger action."""
        q_lower = text.lower()

        # Account opening
        account_opening_keywords = [
            "open account",
            "opening account",
            "open the account",
            "open an account",
            "فتح حساب",
            "فتح الحساب",
            "بيفتح الحساب",
            "بيفتح حساب",
            "بيفتح account",
            "بيفتح الاكونت",
            "account opening",
        ]
        if any(k in q_lower for k in account_opening_keywords):
            return "account opening"

        # Card actions
        card_keywords = [
            "insert card",
            "pull out card",
            "inserting card",
            "reading card",
            "كارت العداد",
            "شحن الكارت",
            "وضع الكارت",
            "نزع الكارت",
            "سحب الكارت",
        ]
        if any(k in q_lower for k in card_keywords):
            return "card operation"

        # Temporal scenario indicator
        temporal_keywords = [
            "when ", "while ", "during ", "after ", "before ",
            "أثناء ", "لما ", "بعد ما ", "قبل ما ", "عند "
        ]
        for kw in temporal_keywords:
            if kw in q_lower:
                return text.strip()

        return None

    @classmethod
    def extract_issue_description(cls, text: str) -> Optional[str]:
        """Extract high-level problem statement."""
        q_lower = text.lower().strip()

        # Check if message is a question or follow-up:
        if any(q_lower.startswith(w) for w in ["what", "how", "why", "where", "is ", "does ", "أعمل", "اعمل", "معناه", "ازاي", "فين"]):
            return None

        # Exclude pure system location statements like "المشكلة في Vending", "the problem is in Vending"
        if re.search(r"(?:the\s+)?(?:problem|issue|عطل|ال?مشكلة)\s+(?:is\s+)?(?:in|في|بتحصل في)\s+\w+", q_lower):
            return None

        # Exclude statements reporting an error code like "بيطلع Error 70", "giving error 70", "it is error 70"
        if re.search(r"(?:error|eror|err|code|خطأ|خطا|الخطأ|الخطا|كود|الكود)\s*[:#\-]?\s*\d+", q_lower):
            return None
        if re.search(r"(?:بيطلع|بيعطي|يظهر|shows|giving)\s*(?:error|eror|كود)?\s*[:#\-]?\s*\d+", q_lower):
            return None

        # Common phrases:
        if any(k in q_lower for k in [
            "not working", "not work", "isn't working", "isnt working", "is not working",
            "doesn't work", "doesnt work", "does not work", "dont work", "don't work",
            "wont work", "won't work", "dead", "no power", "مش شغال", "مش شغالة",
            "مش شغال خالص", "فاشل", "عطلان", "معطل", "لا يعمل"
        ]):
            if any(m in q_lower for m in ["meter", "عداد", "متر"]):
                return "meter not working"
            return "not working"

        if any(k in q_lower for k in [
            "blank screen", "screen is blank", "display is blank", "display blank", "blank display",
            "screen is strange", "شاشة سودا", "الشاشة مطفية", "الشاشة لا تعمل", "شاشة", "الشاشة"
        ]):
            return "display issue / screen not working"

        if any(k in q_lower for k in ["cannot communicate", "cant communicate", "lost communication", "مشكلة اتصال", "الاتصال مش شغال", "مش بيقرأ"]):
            return "meter communication failure"

        if any(k in q_lower for k in ["broken", "مكسور", "محروق", "damage", "تالف"]):
            return "physical damage / broken hardware"

        if any(k in q_lower for k in ["cannot open", "can't open", "مش بيفتح"]):
            if "account" in q_lower or "حساب" in q_lower or "اكونت" in q_lower:
                return "account opening failure"

        # If text is descriptive (3+ words) and contains issue words
        words = text.split()
        if len(words) >= 3 and any(w in q_lower for w in ["error", "مشكلة", "issue", "problem", "fails", "failed", "عطل"]):
            return text.strip()

        return None

    @classmethod
    def detect_symptom_category(cls, text: str) -> Optional[str]:
        """
        Classifies open inquiries into specific symptom categories:
        - display: screen, lcd, display, blank, strange screen, broken screen
        - communication: cannot communicate, connection error, reading, optic, rs485
        - error_unspecified: reports an error or code but no numeric code was extracted
        - power: dead, no power, won't turn on, battery
        - general_vague: general not working, broken, etc.
        """
        q_lower = text.lower()

        # Check for DISPLAY issues first
        display_terms = [
            "screen", "display", "lcd", "blank screen", "screen is blank", "screen is strange",
            "weird screen", "broken screen", "flicker", "flickering", "شاشة", "الشاشة",
            "شاشه", "الشاشه", "مطفية", "مطفيه", "سودا", "سوداء", "مش واضحة", "مش باين"
        ]
        if any(w in q_lower for w in display_terms):
            return "display"

        # Check for COMMUNICATION issues
        comm_terms = [
            "communicate", "communication", "cannot read", "cant read", "connection",
            "disconnected", "connect", "port", "optical", "optic", "probe", "rs485",
            "rs232", "modem", "modbus", "hdlc", "اتصال", "الاتصال", "مش بيقرأ",
            "مش بيقرا", "مش بيتصل", "لا يوجد اتصال", "فصل اتصال"
        ]
        if any(w in q_lower for w in comm_terms):
            return "communication"

        # Check for POWER issues
        power_terms = [
            "dead", "no power", "wont turn on", "won't turn on", "doesnt turn on",
            "not turning on", "power failure", "blackout", "قاطع باور", "قاطع كهربا",
            "طافي", "مش شغال باور", "فاصل باور", "فاصل كهربا", "طافية"
        ]
        if any(w in q_lower for w in power_terms):
            return "power"

        # Check for ERROR_UNSPECIFIED (mentions error / code but no numeric code extracted)
        error_terms = [
            "gives an error", "shows an error", "gives error", "shows error", "error code",
            "there is an error", "an error appeared", "error message", "بيطلع ايرور",
            "بيطلع error", "بيجيب error", "بيطلع كود", "بيجيب كود", "في خطأ", "في كود",
            "بيطلع رقم", "بيظهر خطأ", "مكتوب error"
        ]
        if any(w in q_lower for w in error_terms):
            return "error_unspecified"

        # Check for GENERAL_VAGUE
        general_terms = [
            "not work", "not working", "isnt working", "isn't working", "doesn't work",
            "doesnt work", "wont work", "won't work", "problem", "issue", "مش شغال",
            "مش شغل", "مش شغالة", "مش شغاله", "عطلان", "معطل", "فيه مشكلة", "في مشكلة",
            "عندي مشكلة", "العداد بايظ", "العداد عطلان"
        ]
        if any(w in q_lower for w in general_terms):
            return "general_vague"

        return None

    @classmethod
    def extract_display_symptom(
        cls, text: str, last_question_field: Optional[str] = None
    ) -> Optional[str]:
        """Extract specific display symptom condition if explicitly stated."""
        q_lower = text.lower().strip()

        # Blank / Off checks
        blank_indicators = [
            "blank", "completely blank", "screen is blank", "display is blank",
            "display blank", "blank display", "screen blank", "black screen",
            "screen is off", "display is off", "screen is black", "display is black",
            "شاشة سودا", "شاشة سوداء", "الشاشة سودا", "الشاشة سوداء",
            "الشاشة مطفية", "شاشة مطفية", "الشاشة مطفيه", "شاشة مطفيه",
            "طافية", "طافيه", "الشاشة طافية", "شاشة طافية", "مطفية تماما", "مطفية خالص"
        ]
        if any(b in q_lower for b in blank_indicators):
            return "blank"

        # Direct short answer to display question
        if last_question_field in ["display_symptom", "screen", "general_symptom"]:
            if q_lower in ["blank", "completely blank", "it is blank", "it's blank", "black", "off", "مطفية", "مطفيه", "سودا", "سوداء", "طافية", "طافيه"]:
                return "blank"

        # Blinking / Flickering checks
        blinking_indicators = [
            "blinking", "flashing", "flicker", "flickering", "blink",
            "تومض", "بتنور وتطفي", "بتطفي وتنور", "وميض"
        ]
        if any(b in q_lower for b in blinking_indicators):
            return "blinking"

        # Unusual symbols
        symbols_indicators = [
            "unusual symbols", "strange symbols", "weird symbols", "garbled", "strange screen",
            "رموز غريبة", "رموز غير معتادة", "رموز عجيبة"
        ]
        if any(b in q_lower for b in symbols_indicators):
            return "unusual_symbols"

        # Broken
        broken_indicators = ["broken screen", "cracked screen", "شاشة مكسورة", "شاشه مكسوره"]
        if any(b in q_lower for b in broken_indicators):
            return "broken"

        # Showing readings / normal
        showing_indicators = [
            "showing readings", "showing numbers", "shows numbers", "normal screen",
            "شغالة وبتعرض قراءات", "عليها أرقام", "عليها ارقام"
        ]
        if any(b in q_lower for b in showing_indicators):
            return "showing_readings"

        return None

    @classmethod
    def extract_meter_responsiveness(cls, text: str) -> Optional[str]:
        """Extract explicit statements regarding meter button or operational response."""
        q_lower = text.lower().strip()
        no_response_indicators = [
            "no response", "does not respond", "doesn't respond", "not responding",
            "no button response", "buttons don't work", "buttons not working",
            "does not react", "doesn't react", "won't respond", "wont respond",
            "مش بيستجيب", "ما في استجابة", "مش بيرد", "الزرار مش شغال", "مش بيستجيب للزرار",
            "مبيستجيبش", "مفيش استجابة"
        ]
        if any(r in q_lower for r in no_response_indicators):
            return "no_response"

        responsive_indicators = [
            "it responds", "button works", "responds to button", "بيستجيب", "الزرار شغال"
        ]
        if any(r in q_lower for r in responsive_indicators):
            return "responsive"

        return None
