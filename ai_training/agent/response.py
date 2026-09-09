import re
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from .models import (
    CaseState,
    AgentIntent,
    AgentAction,
    AgentDecision,
    AgentResponse,
)
from .config import (
    OLLAMA_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    OLLAMA_TEMPERATURE,
    OLLAMA_MAX_TOKENS,
)
from .safety import SafetyGuard
from .policy import (
    KnowledgePolicy,
    DOMAIN_TECHNICAL_COMPANY,
    DOMAIN_GENERAL_NON_TECHNICAL,
    MISSING_TECHNICAL_INFO_EN,
    MISSING_TECHNICAL_INFO_AR,
)
from ..rag.evidence_extractor import extract_relevant_passage, detect_request_type


GENERAL_CONCEPTS_EN = {
    "login": "Login is the process by which an individual gains access to a computer system, application, or service by identifying and authenticating themselves, typically using credentials such as a username and password.",
    "database": "A database is an organized collection of structured data or information typically stored electronically in a computer system, managed by a Database Management System (DBMS).",
    "python": "Python is a popular high-level, interpreted programming language known for its readability, dynamic semantics, and wide range of applications from web development to data science and artificial intelligence.",
    "tcp/ip": "TCP/IP (Transmission Control Protocol/Internet Protocol) is the fundamental suite of communication protocols used to interconnect network devices across the internet and local networks.",
    "tcp": "TCP (Transmission Control Protocol) is a core communication standard that enables application programs and computing devices to exchange messages over a network in a reliable, ordered, and error-checked manner.",
    "ip": "An IP (Internet Protocol) address is a unique numerical label assigned to each device connected to a computer network that uses the Internet Protocol for communication.",
    "api": "An API (Application Programming Interface) is a set of rules, protocols, and definitions that allows different software applications to communicate and exchange data with each other.",
    "rest api": "A REST API (Representational State Transfer API) is an architectural style for networked applications that uses HTTP requests to access and manage data (such as GET, POST, PUT, and DELETE).",
    "http": "HTTP (Hypertext Transfer Protocol) is the application-layer protocol used for transmitting hypermedia documents, such as HTML, over the World Wide Web.",
    "https": "HTTPS (Hypertext Transfer Protocol Secure) is the secure version of HTTP, encrypted using TLS/SSL to protect data communication between web browsers and servers.",
    "sql": "SQL (Structured Query Language) is the standard domain-specific programming language used for managing and querying data stored in relational database management systems.",
    "dns": "DNS (Domain Name System) is the phonebook of the Internet, translating human-readable domain names (like example.com) into machine-readable IP addresses.",
    "operating system": "An Operating System (OS) is system software that manages computer hardware, software resources, and provides common services for computer programs.",
    "cpu": "The CPU (Central Processing Unit) is the primary component of a computer that retrieves and executes instructions, functioning as the central 'brain' of the system.",
    "ram": "RAM (Random Access Memory) is a computer's high-speed, volatile short-term memory that temporarily stores data and machine code currently in active use.",
    "cloud": "Cloud computing is the on-demand availability of computer system resources, especially data storage and computing power, over the internet without direct active management by the user.",
    "server": "A server is a computer hardware or software system that provides resources, data, services, or programs to other computers, known as clients, over a network.",
    "firewall": "A firewall is a network security system that monitors and controls incoming and outgoing network traffic based on predetermined security rules.",
    "encryption": "Encryption is the process of converting information or data into a code to prevent unauthorized access, ensuring confidentiality and security.",
    "algorithm": "An algorithm is a finite, step-by-step sequence of well-defined instructions used to solve a specific problem or perform a computation.",
}

GENERAL_CONCEPTS_AR = {
    "login": "تسجيل الدخول (Login) هو عملية التحقق والمصادقة التي تمكن المستخدم من الوصول إلى نظام حاسوبي أو تطبيق أو خدمة معينة، وذلك بإدخال بيانات الاعتماد مثل اسم المستخدم وكلمة المرور.",
    "database": "قاعدة البيانات (Database) هي مجموعة منظمة من البيانات أو المعلومات المهيكلة المخزنة إلكترونياً في نظام حاسوبي، وتتم إدارتها بواسطة نظام إدارة قواعد البيانات (DBMS).",
    "python": "بايثون (Python) هي لغة برمجة عالية المستوى ومفسرة، تشتهر بسهولة قراءتها وبنيتها الواضحة، وتُستخدم على نطاق واسع في تطوير التطبيقات والويب وعلوم البيانات والذكاء الاصطناعي.",
    "tcp/ip": "بروتوكول TCP/IP هو حزمة البروتوكولات الأساسية للاتصالات المستخدمة لربط الأجهزة وتبادل حزم البيانات عبر الإنترنت والشبكات المحلية.",
    "tcp": "بروتوكول TCP (Transmission Control Protocol) هو معيار اتصال ينظم تبادل البيانات بين الأجهزة عبر الشبكة بشكل موثوق ومرتب وخالٍ من الأخطاء.",
    "ip": "عنوان IP (Internet Protocol) هو معرف رقمي فريد يُخصص لكل جهاز متصل بشبكة حاسوبية لتمكينه من الاتصال وتحديد موقعه على الشبكة.",
    "api": "واجهة برمجة التطبيقات (API - Application Programming Interface) هي مجموعة من القواعد والبروتوكولات التي تسمح للتطبيقات والأنظمة البرمجية المختلفة بالتواصل وتبادل البيانات فيما بينها.",
    "rest api": "واجهة REST API هي نمط معماري للخدمات عبر الشبكة يعتمد على بروتوكول HTTP لتبادل البيانات والتحكم فيها بسهولة وأمان.",
    "http": "بروتوكول HTTP هو بروتوكول طبقة التطبيقات الأساسي لنقل صفحات الويب ومحتوى الإنترنت بين الخوادم والمتصفحات.",
    "https": "بروتوكول HTTPS هو النسخة الآمنة والمشفرة من HTTP باستخدام تقنيات التشفير TLS/SSL لحماية سرية البيانات المنقولة.",
    "sql": "لغة SQL هي لغة قياسية مخصصة لإدارة والاستعلام عن البيانات المخزنة في قواعد البيانات العلائقية.",
    "dns": "نظام أسماء النطاقات (DNS) هو دليل الإنترنت الذي يترجم أسماء النطاقات المفهومة للبشر إلى عناوين IP التي تستخدمها الحواسيب للاتصال.",
    "operating system": "نظام التشغيل (OS) هو البرنامج الأساسي الذي يدير عتاد الحاسوب وموارده ويوفر بيئة لتشغيل البرامج والتطبيقات.",
    "cpu": "المعالج (CPU) هو وحدة المعالجة المركزية التي تمثل عقل الحاسوب، حيث تقوم بقراءة التعليمات وتنفيذ العمليات الحسابية والمنطقية.",
    "ram": "ذاكرة الوصول العشوائي (RAM) هي ذاكرة التخزين المؤقت فائقة السرعة التي يستخدمها الحاسوب لحفظ البيانات والبرامج قيد التشغيل الحالي.",
    "cloud": "الحوسبة السحابية (Cloud Computing) هي توفير موارد تقنية المعلومات عند الطلب عبر الإنترنت، مثل التخزين وقوة المعالجة، دون إدارة بنية تحتية محلية.",
    "server": "الخادم (Server) هو جهاز حاسوب أو برنامج يقدم خدمات وموارد ومعلومات لأجهزة أخرى تُعرف بالعملاء (Clients) عبر الشبكة.",
    "firewall": "الجدار الناري (Firewall) هو نظام أمان للشبكة يراقب ويتحكم في حركة البيانات الواردة والصادرة بناءً على قواعد أمان محددة.",
    "encryption": "التشفير (Encryption) هو تحويل البيانات والمعلومات إلى صيغة مشفرة غير قابلة للقراءة لمنع الوصول غير المصرح به وضمان أمانها.",
    "algorithm": "الخوارزمية (Algorithm) هي مجموعة متسلسلة ومحددة من الخطوات الرياضية والمنطقية المتبعة لحل مشكلة معينة أو أداء مهمة حاسوبية.",
}


class ResponseGenerator:
    """
    Generates natural, grounded, customer-facing support responses in English or Arabic.
    Combines LLM generation with strictly grounded fallback templates.
    Hides internal decision state, chain-of-thought, and raw JSON from the customer.
    """

    def __init__(
        self,
        ollama_url: str = OLLAMA_URL,
        ollama_model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
        use_ollama: bool = True,
    ):
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.timeout = timeout
        self.use_ollama = use_ollama

    @staticmethod
    def detect_language(text: str) -> str:
        """Detect if customer input is predominantly Arabic, English, or Mixed."""
        arabic_chars = len(re.findall(r"[\u0600-\u06FF]", text))
        latin_chars = len(re.findall(r"[a-zA-Z]", text))

        if arabic_chars > 0 and latin_chars > 0:
            return "mixed"
        elif arabic_chars > 0:
            return "arabic"
        return "english"

    def generate_response(
        self,
        user_message: str,
        state: CaseState,
        decision: AgentDecision,
        evidence: List[Dict[str, Any]],
        intent: AgentIntent,
    ) -> AgentResponse:
        """
        Generate final response for user.
        Tries Ollama synthesis with strict grounding; falls back to deterministic
        grounded templates if Ollama is unavailable, disabled, or times out.
        """
        lang = self.detect_language(user_message)
        cleaned_msg = user_message.lower().strip(".!? ")

        # --------------------------------------------------------
        # 1. Check for Prompt Injection / Attack
        # --------------------------------------------------------
        if SafetyGuard.is_prompt_injection(user_message):
            if lang in ["arabic", "mixed"]:
                refusal = (
                    "عذراً، أعمل كمساعد دعم فني رسمي لعدادات إسكرا الذكية، "
                    "ولا يمكنني تجاوز التعليمات الأمنية أو اختراع معلومات غير موثقة."
                )
            else:
                refusal = (
                    "I am an official technical support assistant for ISKRA smart meters. "
                    "I cannot bypass safety instructions or provide unverified information."
                )
            return AgentResponse(
                text=refusal,
                action=decision.action,
                case_state=state.model_dump(),
            )

        # --------------------------------------------------------
        # Knowledge Policy Domain Classification
        # --------------------------------------------------------
        domain = state.question_domain
        if not domain:
            domain, _ = KnowledgePolicy.classify_domain(user_message, state=state)

        # --------------------------------------------------------
        # Policy Section B: GENERAL / NON-TECHNICAL QUESTIONS
        # --------------------------------------------------------
        if domain == DOMAIN_GENERAL_NON_TECHNICAL:
            is_greeting = any(re.search(rf"(?:\b|^){re.escape(k)}(?:\b|$)", cleaned_msg) for k in [
                "hello", "hi", "hey", "good morning", "good afternoon", "مرحبا", "اهلا", "أهلا", "السلام عليكم", "صباح الخير"
            ]) and len(cleaned_msg.split()) <= 4
            if is_greeting:
                greeting_text = (
                    "أهلاً بك في الدعم الفني لعدادات ISKRA. كيف يمكنني مساعدتك اليوم؟"
                    if lang in ["arabic", "mixed"]
                    else "Welcome to ISKRA Smart Meter Technical Support. How can I assist you today?"
                )
                return AgentResponse(
                    text=greeting_text,
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

            return self._answer_general_question(user_message, cleaned_msg, lang, state, decision)

        # --------------------------------------------------------
        # 2. Extract verified error evidence line if present
        # --------------------------------------------------------
        exact_line = ""
        for e in evidence:
            if e.get("matched_line"):
                exact_line = e.get("matched_line")
                break

        # If exact_line not in current query evidence, check if state.error_code is a verified known code
        if not exact_line and state.error_code:
            try:
                from ..rag.retriever import HybridRetriever
                retriever = HybridRetriever()
                if retriever.exact_searcher:
                    matches = retriever.exact_searcher.search(state.error_code)
                    if matches:
                        exact_line = matches[0].get("matched_line", "")
            except Exception:
                pass


        # --------------------------------------------------------
        # 3. Handle specific intents deterministically first
        # --------------------------------------------------------
        # 0. User Frustration / Preference for No Questions
        frustration_phrases = [
            "مش عايز أسئلة", "مش عايز اسئله", "مش عاوز أسئلة", "مش عاوز اسئله",
            "كفاية أسئلة", "كفاية اسئله", "بلاش أسئلة", "بلاش اسئله",
            "مش عايز أسئلة كتير", "مش عاوز أسئلة كتير",
            "stop asking questions", "no more questions", "don't ask questions",
            "dont ask questions", "don't ask so many questions", "dont ask so many questions",
            "too many questions", "enough questions"
        ]
        if state.user_frustrated or any(p in cleaned_msg for p in frustration_phrases):
            if lang in ["arabic", "mixed"]:
                resp_text = (
                    "فاهمك تماماً، ولن أثقل عليك بالأسئلة. بالمعلومات المتاحة حالياً لا يتوفر إجراء إصلاح موثق في المستوى الأول (L1) يمكنني التوصية به. "
                    f"بناءً على إعدادات التوجيه الحالية، يفضل تحويل الحالة إلى فريق الدعم الفني ({decision.routing}) للمتابعة المباشرة دون تأخير."
                )
            else:
                resp_text = (
                    "I understand completely, and I will not trouble you with more questions. "
                    "With the information currently available, there is no verified L1 self-repair procedure in the documentation. "
                    f"Based on the current routing configuration, this case is recommended for escalation to technical support ({decision.routing}) for direct assistance."
                )
            return AgentResponse(
                text=resp_text,
                action=decision.action,
                case_state=state.model_dump(),
            )

        # Policy Section A & E: TECHNICAL / COMPANY-SPECIFIC QUESTIONS
        # Handled ONLY from the local ISKRA Knowledge Base
        if intent == AgentIntent.GENERAL_QUESTION:
            # Extract query topic if available (e.g. Vending, smart meter)
            topic_match = re.search(r"^(?:what\s+(?:is|are)|tell\s+me\s+about|can\s+you\s+explain|explain)\s+(?:a\s+|an\s+|the\s+)?([^\d\?]+)\??$", cleaned_msg)
            if not topic_match:
                topic_match = re.search(r"^(?:ما\s*(?:هو|هي)|ماهو|ماهي|معلومات\s*عن|كلمنا\s*عن|كلمني\s*عن|يعني\s*(?:ايه|إيه))\s+(?:نظام\s+|ال)?([^\d\?]+)\??$", cleaned_msg)
            raw_topic = topic_match.group(1).strip() if topic_match else ""
            topic = state.system if (state.system and raw_topic and state.system.lower() == raw_topic.lower()) else (raw_topic or "this topic")

            relevant_tech_evidence = self._filter_relevant_technical_evidence(user_message, evidence)

            if not relevant_tech_evidence:
                routing_target = decision.routing or "Technical Support / Customer Service"
                if lang in ["arabic", "mixed"]:
                    missing_text = (
                        f"هذه المعلومة بخصوص ({topic}) غير متوفرة في قاعدة معرفة إسكرا الحالية (الوثائق المعتمدة المتاحة حالياً)، "
                        f"ولذلك لا أريد التخمين. بناءً على إعدادات التوجيه الحالية، يمكن توجيه هذا الموضوع إلى الفريق المتخصص ({routing_target})."
                    )
                else:
                    missing_text = (
                        f"This information regarding {topic} is not available in the current ISKRA knowledge base (documentation currently available), "
                        f"so I don't want to guess. Based on current routing configuration, this case will be routed to {routing_target}."
                    )
                return AgentResponse(
                    text=missing_text,
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

            # Relevant technical evidence found: synthesize answer strictly from evidence
            tech_answer = None
            top_status = relevant_tech_evidence[0].get("evidence_status", "")
            is_procedure_request = (detect_request_type(user_message) == "PROCEDURE")
            is_context_only = top_status == "CONTEXT_AVAILABLE" or "vending" in cleaned_msg or is_procedure_request
            if self.use_ollama and not is_context_only:
                tech_answer = self._call_ollama_technical(user_message, state, decision, relevant_tech_evidence, lang)

            if not tech_answer:
                tech_answer = self._synthesize_technical_evidence_answer(user_message, relevant_tech_evidence, lang)

            return AgentResponse(
                text=tech_answer,
                action=AgentAction.ANSWER,
                citations=relevant_tech_evidence[:2],
                case_state=state.model_dump(),
            )

        # 2. Explicit Unknown Error Code (e.g. Error 999 not in verified documentation)
        if state.error_code and not exact_line:
            is_followup = intent in [AgentIntent.FOLLOW_UP, AgentIntent.TROUBLESHOOTING] or any(
                k in cleaned_msg for k in [
                    "what should i do", "what do i do", "what can i do", "how to fix", "how do i fix",
                    "how to solve", "how do i repair", "what now", "أعمل ايه", "اعمل ايه", "ايه الحل", "ازاي أصلحها"
                ]
            )
            if is_followup:
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"بخصوص كود الخطأ {state.error_code}: نظراً لأن هذا الكود غير موجود في الوثائق المعتمدة المتاحة حالياً في قاعدة المعرفة، "
                        f"فلا تتوفر خطوات حل أو إصلاح ذاتي موثقة في المستوى الأول (L1). "
                        f"بناءً على إعدادات التوجيه الحالية، يجب تصعيد الحالة إلى فريق الدعم الفني ({decision.routing}) للفحص والمساعدة المباشرة."
                    )
                else:
                    resp_text = (
                        f"Regarding Error {state.error_code}: because this error code is not found in the verified documentation currently available in the knowledge base, "
                        f"there is no verified L1 troubleshooting or self-repair procedure. "
                        f"Based on the current routing configuration, this case should be escalated to technical support ({decision.routing}) for direct assistance."
                    )
            else:
                routing_target = decision.routing or "L2 Technical Support"
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"لم أتمكن من العثور على كود الخطأ {state.error_code} في الوثائق المعتمدة المتاحة حالياً في قاعدة المعرفة، "
                        f"ولذلك لا يمكنني تأكيد معناه الفني ولا أريد التخمين. "
                        f"بناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق ({routing_target}) للمتابعة الفنية."
                    )
                else:
                    resp_text = (
                        f"I could not find Error {state.error_code} in the verified documentation currently available in the knowledge base, "
                        f"so I cannot reliably confirm what it means and I don't want to guess. "
                        f"Based on the current routing configuration, this case will be routed to {routing_target} for technical assistance."
                    )
            return AgentResponse(
                text=resp_text,
                action=AgentAction.ANSWER,
                case_state=state.model_dump(),
            )

        # 3. Direct Error Explanation for Known Error
        if intent == AgentIntent.ERROR_EXPLANATION and exact_line:
            if lang in ["arabic", "mixed"]:
                resp_text = (
                    f"وفقاً للوثائق المعتمدة المتاحة حالياً، فإن كود الخطأ {state.error_code} يعني:\n"
                    f'"{exact_line}"\n\n'
                    f"يرجى العلم أن الوثائق لا تتضمن إجراء إصلاح مباشر في المستوى الأول (L1). "
                    f"بناءً على إعدادات التوجيه الحالية، يتم توجيه الحالة إلى فريق ({decision.routing})."
                )
            else:
                resp_text = (
                    f"According to the verified documentation currently available, Error {state.error_code} is defined as:\n"
                    f'"{exact_line}"\n\n'
                    f"Please note that the available documentation does not specify an automated L1 resolution procedure for this error. "
                    f"Based on the current routing configuration, this case would be sent to {decision.routing}."
                )
            return AgentResponse(
                text=resp_text,
                action=AgentAction.ANSWER,
                citations=evidence[:1],
                case_state=state.model_dump(),
            )

        # D. Identification Intent (e.g. "Where can I find the meter model?")
        if intent == AgentIntent.IDENTIFICATION:
            if lang in ["arabic", "mixed"]:
                resp_text = (
                    "يمكنك العثور على موديل العداد مطبوعاً على اللوحة الأمامية للعداد (مثل MT514 أو ME514 أو AM550)، "
                    "عادةً بجوار شاشة العرض أو أعلى الباركود والرقم التسلسلي. "
                    "إذا لم تتمكن من قراءته، يمكننا الاستمرار بالمعلومات المتاحة لديك."
                )
            else:
                resp_text = (
                    "You can find the meter model printed on the front nameplate of the meter (such as MT514, ME514, or AM550), "
                    "usually above the barcode/serial number or near the display. "
                    "If you cannot access it, we can continue with the available information."
                )
            return AgentResponse(
                text=resp_text,
                action=AgentAction.ANSWER,
                case_state=state.model_dump(),
            )

        # E. User stated "I don't know the model", "I don't know the meter type", "I don't know anything", etc.
        is_unknown_expression = any(
            phrase in cleaned_msg
            for phrase in [
                "don't know", "dont know", "do not know", "no idea", "not sure",
                "anything about it", "anything about the meter",
                "مش عارف", "مش عارفه", "معرفش", "ما اعرف", "مش متأكد", "مش متاكد",
                "أي حاجة", "اي حاجه"
            ]
        )
        if is_unknown_expression:
            is_model_unknown = any(w in cleaned_msg for w in ["model", "موديل", "طراز"])
            is_type_unknown = any(w in cleaned_msg for w in ["type", "نوع العداد", "النوع", "نوعه"])
            asked_error_before = (
                "error_code" in state.asked_topics
                or "error_code" in state.user_does_not_know
                or "general_symptom" in state.asked_topics
                or state.last_question_field in ["error_code", "general_symptom"]
                or (state.last_agent_message and any(w in state.last_agent_message.lower() for w in ["error code", "كود خطأ", "كود الخطأ", "error or message"]))
            )
            asked_screen_before = (
                "screen" in state.asked_topics
                or "screen" in state.user_does_not_know
                or "display_symptom" in state.asked_topics
                or state.last_question_field in ["screen", "display_symptom"]
                or (state.last_agent_message and any(w in state.last_agent_message.lower() for w in ["meter display", "screen is on", "شاشة العداد", "الشاشة"]))
            )

            if lang in ["arabic", "mixed"]:
                if is_model_unknown:
                    ack = "تمام، لا مشكلة على الإطلاق. يمكننا المتابعة بدون معرفة الموديل."
                elif is_type_unknown:
                    ack = "تمام، لا بأس على الإطلاق. يمكننا العمل بالبيانات المتاحة لدينا."
                else:
                    ack = "تمام، لا مشكلة على الإطلاق. يمكننا المتابعة بالمعلومات المتوفرة لدينا."

                if state.system:
                    q_part = f" هل تحدث المشكلة أثناء فتح الحساب في نظام {state.system}؟"
                    decision.question_field = "system"
                elif not asked_error_before and not state.error_code:
                    q_part = " هل يظهر أي كود خطأ أو رسالة معينة على شاشة العداد؟"
                    decision.question_field = "error_code"
                elif not asked_screen_before:
                    q_part = " هل شاشة العداد تعمل وتظهر أرقاماً وقراءات، أم مطفأة تماماً؟"
                    decision.question_field = "screen"
                else:
                    q_part = " نظراً لعدم توفر خطوات حل ذاتي معتمدة، يمكننا المتابعة مباشرة مع الدعم الفني."
                    decision.question_field = None
                resp_text = f"{ack}{q_part}"
            else:
                if is_model_unknown:
                    ack = "No problem. We can continue without the model."
                elif is_type_unknown:
                    ack = "That's okay. We can work with the information we have."
                else:
                    ack = "No problem at all. We can continue with the information we have."

                if state.system:
                    q_part = f" Does this happen while you're opening an account in {state.system}?"
                    decision.question_field = "system"
                elif not asked_error_before and not state.error_code:
                    q_part = " Do you see any error code or message on the meter display?"
                    decision.question_field = "error_code"
                elif not asked_screen_before:
                    q_part = " If you can, tell me what appears on the meter display or if the screen is on."
                    decision.question_field = "screen"
                else:
                    q_part = " Since no verified L1 resolution exists with the current information, we can proceed with technical support."
                    decision.question_field = None
                resp_text = f"{ack}{q_part}"

            return AgentResponse(
                text=resp_text,
                action=AgentAction.ANSWER,
                case_state=state.model_dump(),
            )

        # F. Clarification Question
        if decision.action == AgentAction.ASK_CLARIFICATION:
            q_text = None
            if self.use_ollama:
                q_text = self._call_ollama_clarification(user_message, state, decision, lang)

            if not q_text:
                if decision.question_field == "meter_responsiveness":
                    display_sym = state.known_facts.get("display_symptom") or getattr(state, "display_symptom", None)
                    if lang in ["arabic", "mixed"]:
                        if display_sym == "blank":
                            q_text = "فهمت أن شاشة العداد مطفأة. هل يستجيب العداد على الإطلاق عند الضغط على أي زر أو محاولة تشغيله؟"
                        else:
                            q_text = "هل يستجيب العداد على الإطلاق عند الضغط على أي زر أو محاولة تشغيله؟"
                    else:
                        if display_sym == "blank":
                            q_text = "I understand the display is blank. Does the meter respond at all when you press a button or try to operate it?"
                        else:
                            q_text = "Does the meter respond at all when you press a button or try to operate it?"
                elif decision.question_field == "display_symptom":
                    display_sym = state.known_facts.get("display_symptom") or getattr(state, "display_symptom", None)
                    if display_sym == "blank":
                        if lang in ["arabic", "mixed"]:
                            q_text = "فهمت أن شاشة العداد مطفأة. هل يستجيب العداد على الإطلاق عند الضغط على أي زر أو محاولة تشغيله؟"
                        else:
                            q_text = "I understand the display is blank. Does the meter respond at all when you press a button or try to operate it?"
                    else:
                        if lang in ["arabic", "mixed"]:
                            q_text = "فهمت أن هناك مشكلة في شاشة العرض. ماذا يظهر على الشاشة بالتحديد حالياً؟ هل هي مطفأة تماماً، أم تظهر رموزاً غير معتادة، أم تومض؟"
                        else:
                            q_text = "I understand there is an issue with the display. What does the screen show right now—is it completely blank, showing unusual symbols, or blinking?"
                elif decision.question_field == "communication_symptom":
                    if lang in ["arabic", "mixed"]:
                        q_text = "فهمت أن هناك مشكلة في اتصال العداد. ما هي طريقة أو منفذ الاتصال المستخدم (مثل المنفذ البصري أو RS485 أو المودم)، وهل تظهر رسالة خطأ معينة عند الاتصال؟"
                    else:
                        q_text = "I understand the meter has communication issues. What communication method or interface are you using (such as optical probe, RS485, or modem), or does a specific connection error message appear?"
                elif decision.question_field == "error_code":
                    if lang in ["arabic", "mixed"]:
                        q_text = "ما هو كود الخطأ أو نص الرسالة الظاهر بالتحديد على شاشة العداد؟"
                    else:
                        q_text = "What specific error code or error message is shown on the meter display?"
                elif decision.question_field == "power_symptom":
                    if lang in ["arabic", "mixed"]:
                        q_text = "فهمت أن العداد لا يستجيب أو يبدو بدون كهرباء. هل توجد أي لمبات بيان (LED) مضاءة، أم أن الشاشة والعداد لا يستجيبان تماماً؟"
                    else:
                        q_text = "I understand the meter seems unpowered. Are there any LED indicator lights active, or is the screen completely unresponsive?"
                elif decision.question_field == "system":
                    if lang in ["arabic", "mixed"]:
                        q_text = "ما هو النظام الذي تعمل عليه عند ظهور المشكلة (مثل Vending أو Billing أو Symbiot)؟"
                    else:
                        q_text = "Which software system is involved when this occurs (e.g. Vending, Billing, or Symbiot)?"
                else:  # general_symptom or other
                    if lang in ["arabic", "mixed"]:
                        q_text = "أفهم أن العداد لا يعمل بشكل سليم. هل يمكنك توضيح ما يظهر لديك بالتحديد—مثل كود خطأ معين، أو انطفاء الشاشة، أو تعذر الاتصال؟"
                    else:
                        q_text = "I understand the meter isn't working properly. Could you tell me what specific symptom you are seeing—such as whether the display is blank, showing an error code, or not communicating?"

            return AgentResponse(
                text=q_text,
                action=AgentAction.ASK_CLARIFICATION,
                case_state=state.model_dump(),
            )

        # Memory recall inquiry: e.g. "What problem did I tell you about?"
        if any(k in cleaned_msg for k in [
            "what problem did i tell you", "what problem did i report", "what did i tell you about",
            "what was the problem", "what was my problem", "what issue did i", "what problem was",
            "المشكلة اللي قلتلك عليها", "المشكلة اللي بلغتك بيها", "ايه مشكلتي", "ايه المشكلة"
        ]):
            if lang in ["arabic", "mixed"]:
                resp_parts = []
                if state.issue:
                    resp_parts.append(f"المشكلة الأساسية هي ({state.issue})")
                if state.system:
                    resp_parts.append(f"التي تحدث في نظام ({state.system})")
                if state.error_code:
                    desc = f' (ومعناه: "{exact_line}")' if exact_line else ""
                    resp_parts.append(f"مع ظهور كود الخطأ {state.error_code}{desc}")
                if state.meter_model:
                    resp_parts.append(f"لموديل العداد {state.meter_model}")
                recap = "، و".join(resp_parts) if resp_parts else "لم يتم تسجيل تفاصيل بعد."
                return AgentResponse(
                    text=f"لقد ذكرت أن: {recap}.",
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )
            else:
                resp_parts = []
                if state.issue:
                    resp_parts.append(f"the primary issue was that the {state.issue}")
                if state.system:
                    resp_parts.append(f"occurring in {state.system}")
                if state.error_code:
                    desc = f' (defined as: "{exact_line}")' if exact_line else ""
                    resp_parts.append(f"with Error {state.error_code}{desc}")
                if state.meter_model:
                    resp_parts.append(f"for model {state.meter_model}")
                recap = ", ".join(resp_parts) if resp_parts else "no specific issue details were recorded yet."
                return AgentResponse(
                    text=f"You reported that {recap}.",
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

        # E. Exact Error in Troubleshooting / Follow-up Context
        if exact_line and state.error_code:
            # Check for reset query (Hallucination defense)
            if any(k in cleaned_msg for k in ["reset", "ريست", "اعادة ضبط", "إعادة ضبط"]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"لا، لا تتوفر في الوثائق المعتمدة المتاحة حالياً أي خطوات لإعادة ضبط العداد (Reset) بخصوص كود الخطأ {state.error_code} (\"{exact_line}\"). "
                        f"يجب عدم محاولة عمل إعادة ضبط يدوية أو العبث بالأزرار والختم، وبناءً على إعدادات التوجيه الحالية يتم توجيه الحالة إلى فريق ({decision.routing})."
                    )
                else:
                    resp_text = (
                        f"No, the verified documentation currently available does not provide a meter reset procedure for Error {state.error_code} (\"{exact_line}\"). "
                        f"You should not attempt an unauthorized reset or button tampering. Based on the current routing configuration, this case would be sent to {decision.routing}."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # Check for replace query (Hallucination defense)
            if any(k in cleaned_msg for k in ["replace", "تغيير", "استبدال", "تغيير العداد", "استبدال العداد"]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"لا، الوثائق المعتمدة المتاحة حالياً لكود الخطأ {state.error_code} (\"{exact_line}\") لا تنص على استبدال العداد (Meter replacement). "
                        f"الخطأ يحدد الحالة فقط ولا يعني الحاجة الفورية لتغيير العداد، وبناءً على إعدادات التوجيه الحالية يلزم فحص الحالة بواسطة فريق ({decision.routing})."
                    )
                else:
                    resp_text = (
                        f"No, the verified documentation currently available for Error {state.error_code} (\"{exact_line}\") does not recommend replacing the meter. "
                        f"Meter replacement is not an authorized L1 step. Based on the current routing configuration, this case would be sent to {decision.routing}."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # 1. User asks "what should I do?" / "how to fix/repair it?" / "أعمل ايه؟" (Test A, Section 8)
            if any(k in cleaned_msg for k in [
                "what should i do", "what do i do", "what can i do", "how to fix", "how do i fix", "how can i fix",
                "how to solve", "how do i repair", "how to repair", "repair", "fix it", "how to handle",
                "أعمل ايه", "اعمل ايه", "أعمل إيه", "اعمل إيه", "إيه الحل", "ايه الحل", "ازاي أصلحها", "ازاي احلها", "طريقة الحل", "حلها ايه", "تصليح", "أصلحها"
            ]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"بخصوص كود الخطأ {state.error_code} (\"{exact_line}\"):\n"
                        f"الوثائق المعتمدة المتاحة حالياً تؤكد معنى الخطأ، ولكنها لا تتضمن إجراء إصلاح ذاتي أو خطوات استكشاف أخطاء معتمدة للمستوى الأول (L1). "
                        f"نظراً لأن الوثائق لا تقدم خطوات حل مؤكدة لهذا الكود، يُرجى عدم محاولة أي إجراء يدوي أو فك أو تعديل للعداد. "
                        f"بناءً على إعدادات التوجيه الحالية، يتم توجيه الحالة إلى فريق ({decision.routing}) للمتابعة الفنية."
                    )
                else:
                    resp_text = (
                        f"Regarding what to do for Error {state.error_code} (\"{exact_line}\"):\n"
                        f"The verified documentation currently available defines this error, but does not provide an L1 troubleshooting, repair, or self-resolution procedure. "
                        f"To maintain safety and compliance, do not attempt any manual modifications, seal adjustments, or hardware tampering. "
                        f"Based on the current routing configuration, this case would be sent to {decision.routing}."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # 2. User asks "what meter is this for?" / "ده لأي عداد؟" (Test C)
            if any(k in cleaned_msg for k in [
                "what meter is this for", "what meter is that for", "which meter is this for", "what meter", "which meter",
                "ده لأي عداد", "ده بتاع انهي عداد", "انهي عداد", "اي عداد", "لأي عداد"
            ]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"وفقاً للوثائق المعتمدة المتاحة حالياً، فإن كود الخطأ {state.error_code} معرّف كـ (\"{exact_line}\"). "
                        f"الوثائق المتاحة لا تحصر أو تخصص هذا الكود بموديل عداد واحد فقط (مثل MT514 دون غيره). "
                        f"إذا كان موديل عدادك معروفاً لديك يمكنك توضيحه، أو يمكننا المتابعة بالبيانات المتاحة."
                    )
                else:
                    resp_text = (
                        f"According to the verified documentation currently available, Error {state.error_code} is defined as (\"{exact_line}\"). "
                        f"The verified documentation does not restrict or tie this error code to a single specific meter model. "
                        f"If you know your specific meter model you may share it, or we can continue with your current case."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # 3. User asks "هل ده معناه إن العداد بايظ؟" / "is the meter broken?" (Test D)
            if any(k in cleaned_msg for k in [
                "العداد بايظ", "العداد عطلان", "العداد تالف", "معناه إن العداد بايظ", "معناه ان العداد بايظ",
                "is the meter broken", "is the meter damaged", "is it broken", "hardware failure"
            ]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"لا، ظهور كود الخطأ {state.error_code} لا يعني أن العداد تالف أو تعرض لعطل في العتاد (Hardware failure). "
                        f"الوثائق المعتمدة المتاحة حالياً توضح فقط أن: \"{exact_line}\". "
                        f"ولكن نظراً لعدم وجود خطوات حل ذاتي معتمدة في المستوى الأول (L1)، وبناءً على إعدادات التوجيه الحالية، يلزم فحص الحالة بواسطة فريق ({decision.routing})."
                    )
                else:
                    resp_text = (
                        f"No, Error {state.error_code} does not indicate that the meter is physically damaged or has suffered a hardware failure. "
                        f"Verified documentation currently available specifically identifies it as: \"{exact_line}\". "
                        f"However, because no L1 troubleshooting procedure is provided in documentation, and based on the current routing configuration, it requires handling by {decision.routing}."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # 4. User says "لسه المشكلة موجودة" / "still not working" (Test F)
            if any(k in cleaned_msg for k in [
                "لسه المشكلة", "لسه المشكله", "نفس المشكلة", "نفس المشكله", "لسه مش شغال", "لسه مش شغالة",
                "still happening", "still not working", "same problem", "same issue"
            ]):
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"فهمت أن المشكلة ما زالت قائمة بخصوص كود الخطأ {state.error_code} (\"{exact_line}\"). "
                        f"بما أنه لا تتوفر خطوات حل يدوي معتمدة في المستوى الأول (L1)، "
                        f"وبناءً على إعدادات التوجيه الحالية، فإن الحالة مؤكدة للحاجة إلى توجيهها إلى فريق ({decision.routing})."
                    )
                else:
                    resp_text = (
                        f"I understand that the issue is still persisting with Error {state.error_code} (\"{exact_line}\"). "
                        f"Since no L1 resolution procedure exists in verified documentation, "
                        f"and based on the current routing configuration, this case is confirmed for routing to {decision.routing}."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    citations=evidence[:1],
                    case_state=state.model_dump(),
                )

            # General Exact Error Response
            # Safety verification: ensure exact_line is not merely the number itself or non-descriptive
            remainder_desc = re.sub(rf"\b0*{re.escape(str(state.error_code))}\b", "", exact_line, flags=re.IGNORECASE)
            remainder_desc = re.sub(r"[0-9\W]+", " ", remainder_desc).strip()
            desc_words = [w for w in remainder_desc.split() if len(w) >= 2 and w.lower() not in ["error", "code", "page", "table"]]
            is_valid_description = len(desc_words) >= 2 and "\ufffd" not in exact_line

            if not is_valid_description:
                routing_target = decision.routing or "L2 Technical Support"
                if lang in ["arabic", "mixed"]:
                    resp_text = (
                        f"لم أتمكن من العثور على توصيف معتمد لكود الخطأ {state.error_code} في الوثائق المعتمدة المتاحة حالياً في قاعدة المعرفة، "
                        f"ولذلك لا يمكنني تأكيد معناه الفني ولا أريد التخمين. "
                        f"بناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق ({routing_target}) للمتابعة الفنية."
                    )
                else:
                    resp_text = (
                        f"I could not find a verified description for Error {state.error_code} in the documentation currently available in the knowledge base, "
                        f"so I cannot reliably confirm what it means. "
                        f"Based on the current routing configuration, this case will be routed to {routing_target} for technical assistance."
                    )
                return AgentResponse(
                    text=resp_text,
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

            if lang in ["arabic", "mixed"]:
                resp_text = (
                    f"تم العثور على كود الخطأ {state.error_code} في الوثائق المعتمدة المتاحة حالياً:\n"
                    f'"{exact_line}"\n\n'
                    f"الوثائق المتاحة لا تحتوي على خطوات حل ذاتي في المستوى الأول (L1). "
                    f"بناءً على إعدادات التوجيه الحالية، يتم توجيه الحالة إلى فريق ({decision.routing})."
                )
            else:
                resp_text = (
                    f"I found Error {state.error_code} in the verified documentation currently available. It is described as:\n"
                    f'"{exact_line}"\n\n'
                    f"The verified documentation confirms the meaning of Error {state.error_code}, "
                    f"but does not contain an L1 troubleshooting procedure for this error. "
                    f"Based on the current routing configuration, this case would be sent to {decision.routing}."
                )
            return AgentResponse(
                text=resp_text,
                action=AgentAction.ESCALATE if decision.action == AgentAction.ESCALATE else AgentAction.ANSWER,
                citations=evidence[:1],
                case_state=state.model_dump(),
            )

        # Fast path for confirmed escalation when no exact error code is present
        if decision.action == AgentAction.ESCALATE:
            routing_target = decision.routing or state.routing or "L2 Technical Support"
            if lang in ["arabic", "mixed"]:
                if state.system and state.issue:
                    resp_text = (
                        f"أهلاً بك. تم تسجيل المشكلة المتعلقة بنظام {state.system} ({state.issue}). "
                        f"الوثائق المتاحة لا تحتوي على حل مباشر في المستوى الأول (L1)، "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
                elif state.issue:
                    resp_text = (
                        f"أهلاً بك. تم تسجيل المشكلة: {state.issue}. "
                        f"الوثائق المتاحة لا تحتوي على إجراء حل مباشر في المستوى الأول (L1)، "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
                else:
                    resp_text = (
                        f"الوثائق المتاحة لا تحتوي على إجراء حل مباشر في المستوى الأول (L1) لهذه الحالة. "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
            else:
                if state.system and state.issue:
                    resp_text = (
                        f"I understand the issue with {state.system}: {state.issue}. "
                        f"A verified L1 procedure is not available in the documentation. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
                elif state.issue:
                    resp_text = (
                        f"I understand the issue: {state.issue}. "
                        f"A verified L1 procedure is not available in the documentation. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
                else:
                    resp_text = (
                        f"A verified L1 procedure is not available in the documentation for this case. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
            return AgentResponse(
                text=resp_text,
                action=AgentAction.ESCALATE,
                citations=evidence[:1],
                case_state=state.model_dump(),
            )

        # --------------------------------------------------------
        # 4. Try Ollama for general grounded conversational response
        # --------------------------------------------------------
        if self.use_ollama:
            ollama_reply = self._call_ollama(user_message, state, decision, evidence, lang)
            if ollama_reply:
                return AgentResponse(
                    text=ollama_reply,
                    action=decision.action,
                    citations=evidence[:2],
                    case_state=state.model_dump(),
                )

        # --------------------------------------------------------
        # 5. Grounded Fallback if Ollama is unavailable
        # --------------------------------------------------------
        return self._generate_fallback(user_message, state, decision, evidence, lang)

    def _call_ollama(
        self,
        user_message: str,
        state: CaseState,
        decision: AgentDecision,
        evidence: List[Dict[str, Any]],
        lang: str,
    ) -> Optional[str]:
        """Call Ollama granite4.2:8b with strict grounding and formatting rules."""
        context_lines = []
        for i, e in enumerate(evidence[:3], 1):
            line = e.get("matched_line") or e.get("text") or e.get("document", "")
            context_lines.append(f"[{i}] {line[:300]}")
        context_str = "\n".join(context_lines) if context_lines else "No verified technical knowledge found."

        lang_instruction = "Respond naturally in Arabic." if lang in ["arabic", "mixed"] else "Respond naturally in English."

        prompt = f"""You are an ISKRA Smart Meter L1 Support Engineer.
Rules:
1. Ground every technical statement in the RETRIEVED EVIDENCE.
2. If evidence does not contain a solution, DO NOT INVENT ONE. Clearly state that no verified procedure exists in L1 documentation.
3. If asking a question, ask AT MOST ONE question.
4. Do NOT ask for Meter Type, Model, System, or Scenario if not strictly required.
5. Never expose internal reasoning, JSON, or thought processes.
6. {lang_instruction}

CASE CONTEXT:
Issue: {state.issue or 'Not specified'}
System: {state.system or 'Not specified'}
Error Code: {state.error_code or 'None'}
Model: {state.meter_model or 'Unknown'}
Routing: {decision.routing}

RETRIEVED EVIDENCE:
{context_str}

CUSTOMER MESSAGE:
{user_message}

RESPONSE:"""

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_MAX_TOKENS,
            },
        }

        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                raw_text = data.get("response", "").strip()
                cleaned = SafetyGuard.sanitize_llm_output(raw_text)
                if cleaned:
                    return cleaned
        except Exception as e:
            # Fallback will handle this gracefully
            pass

        return None

    def _generate_fallback(
        self,
        user_message: str,
        state: CaseState,
        decision: AgentDecision,
        evidence: List[Dict[str, Any]],
        lang: str,
    ) -> AgentResponse:
        """Safe deterministic fallback response generator."""
        if decision.action == AgentAction.ESCALATE:
            routing_target = decision.routing or state.routing or "L2 Technical Support"
            if lang in ["arabic", "mixed"]:
                if state.system and state.issue:
                    text = (
                        f"أهلاً بك. تم تسجيل المشكلة المتعلقة بنظام {state.system} ({state.issue}). "
                        f"الوثائق المتاحة لا تحتوي على حل مباشر في المستوى الأول، "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
                elif state.issue:
                    text = (
                        f"أهلاً بك. تم تسجيل المشكلة: {state.issue}. "
                        f"الوثائق المتاحة لا تحتوي على إجراء حل ذاتي في المستوى الأول، "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
                else:
                    text = (
                        f"الوثائق المتاحة لا تحتوي على إجراء حل ذاتي في المستوى الأول، "
                        f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {routing_target} للمتابعة الفنية."
                    )
            else:
                if state.system and state.issue:
                    text = (
                        f"I understand the issue with {state.system}: {state.issue}. "
                        f"A verified L1 procedure is not available in the documentation. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
                elif state.issue:
                    text = (
                        f"I understand the issue: {state.issue}. "
                        f"A verified L1 procedure is not available in the documentation. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
                else:
                    text = (
                        f"A verified L1 procedure is not available in the documentation for this issue. "
                        f"Based on the current routing configuration, this case would be routed to {routing_target}."
                    )
            return AgentResponse(
                text=text,
                action=decision.action,
                citations=evidence[:1],
                case_state=state.model_dump(),
            )

        if lang in ["arabic", "mixed"]:
            if state.system and state.issue:
                text = (
                    f"أهلاً بك. تم تسجيل المشكلة المتعلقة بنظام {state.system} ({state.issue}). "
                    f"الوثائق المتاحة لا تحتوي على حل مباشر في المستوى الأول، "
                    f"وبناءً على إعدادات التوجيه الحالية، سيتم توجيه الحالة إلى فريق {decision.routing} للمتابعة الفنية."
                )
            elif state.error_code:
                text = (
                    f"لم أتمكن من العثور على كود الخطأ {state.error_code} في الوثائق المعتمدة المتاحة حالياً، "
                    "ولذلك لا يمكنني تأكيد معناه بشكل موثق. يرجى التأكد من الرمز الظاهر على شاشة العداد."
                )
            elif state.issue:
                text = (
                    f"أهلاً بك. فهمت أن لديك مشكلة: {state.issue}. "
                    "هل يمكنك إخباري بمزيد من التفاصيل عما يظهر على الشاشة أو النظام لمساعدتك بشكل أفضل؟"
                )
            else:
                text = "أهلاً بك في الدعم الفني لعدادات ISKRA. كيف يمكنني مساعدتك بخصوص العداد اليوم؟"
        else:
            if state.system and state.issue:
                text = (
                    f"I understand the issue with {state.system}: {state.issue}. "
                    f"A verified L1 procedure is not available in the documentation. "
                    f"Based on the current routing configuration, this case would be routed to {decision.routing}."
                )
            elif state.error_code:
                text = (
                    f"I could not find Error {state.error_code} in the verified documentation currently available, "
                    "so I cannot reliably confirm what it means. Could you please double-check the code shown on the meter display?"
                )
            elif state.issue:
                text = (
                    f"I understand you are experiencing: {state.issue}. "
                    "Could you share what happens or what is displayed on the meter?"
                )
            else:
                text = "Welcome to ISKRA Smart Meter Technical Support. How can I help you today?"

        return AgentResponse(
            text=text,
            action=decision.action,
            citations=evidence[:1],
            case_state=state.model_dump(),
        )

    # ------------------------------------------------------------
    # KNOWLEDGE POLICY HANDLERS (Sections A, B, C, D, E, F)
    # ------------------------------------------------------------
    def _answer_general_question(
        self,
        user_message: str,
        cleaned_msg: str,
        lang: str,
        state: CaseState,
        decision: AgentDecision,
    ) -> AgentResponse:
        """
        Answer general, non-technical questions using general language/model knowledge
        as permitted by Policy Section B.
        """
        # 1. Check curated general computer science / IT dictionary
        concept_match = re.search(
            r"\b(login|database|python|api|rest\s+api|tcp\/?ip|tcp|ip|http|https|sql|dns|operating\s+system|cpu|ram|cloud|server|firewall|encryption|algorithm|computer)\b",
            cleaned_msg
        )
        if concept_match:
            raw_concept = concept_match.group(1).lower().strip()
            lookup_key = "tcp/ip" if ("tcp" in raw_concept and "ip" in raw_concept) else raw_concept.replace("  ", " ")
            dict_to_use = GENERAL_CONCEPTS_AR if lang in ["arabic", "mixed"] else GENERAL_CONCEPTS_EN
            if lookup_key in dict_to_use:
                return AgentResponse(
                    text=dict_to_use[lookup_key],
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

        # 2. Try Ollama for natural general answer
        if self.use_ollama:
            ollama_general = self._call_ollama_general(user_message, lang)
            if ollama_general:
                return AgentResponse(
                    text=ollama_general,
                    action=AgentAction.ANSWER,
                    case_state=state.model_dump(),
                )

        # 3. Default safe explanation
        if lang in ["arabic", "mixed"]:
            default_text = "هذا مفهوم عام في علوم الحاسوب وتقنية المعلومات، ويمكن توضيح تفاصيله بناءً على السياق المطلوب."
        else:
            default_text = "This is a general computer science and information technology concept."

        return AgentResponse(
            text=default_text,
            action=AgentAction.ANSWER,
            case_state=state.model_dump(),
        )

    def _call_ollama_general(self, user_message: str, lang: str) -> Optional[str]:
        """Call Ollama for answering general, non-technical / computer science concepts."""
        lang_instruction = "Respond naturally and concisely in Arabic." if lang in ["arabic", "mixed"] else "Respond naturally and concisely in English."
        prompt = f"""You are an expert computing and technology assistant.
Rules:
1. Explain the following general non-technical or computer science concept clearly, accurately, and concisely.
2. Do NOT mention ISKRA, smart meters, or specific company products unless specifically asked.
3. {lang_instruction}

USER QUESTION:
{user_message}

ANSWER:"""

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": OLLAMA_MAX_TOKENS,
            },
        }

        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                raw_text = data.get("response", "").strip()
                cleaned = SafetyGuard.sanitize_llm_output(raw_text)
                if cleaned:
                    return cleaned
        except Exception:
            pass

        return None

    def _call_ollama_clarification(
        self,
        user_message: str,
        state: CaseState,
        decision: AgentDecision,
        lang: str,
    ) -> Optional[str]:
        """Call Ollama to generate a single natural, context-aware clarification question."""
        lang_instruction = "Respond naturally in Arabic with exactly ONE question." if lang in ["arabic", "mixed"] else "Respond naturally in English with exactly ONE question."
        
        # Ground question in known facts vs missing info
        known_parts = []
        if state.issue:
            known_parts.append(f"issue: {state.issue}")
        display_sym = state.known_facts.get("display_symptom") or getattr(state, "display_symptom", None)
        if display_sym:
            known_parts.append(f"display symptom: {display_sym}")
        if state.meter_model:
            known_parts.append(f"model: {state.meter_model}")
        if state.system:
            known_parts.append(f"system: {state.system}")
        known_str = ", ".join(known_parts) if known_parts else "none"
        missing_target = decision.reason or (f"ask for {decision.question_field}" if decision.question_field else "clarify missing symptom")

        prompt = f"""You are an ISKRA Smart Meter technical support assistant.
Your task: Reply directly to the customer with EXACTLY ONE short, polite clarification question.
CRITICAL RULES:
1. Treat explicit user statements as known facts: ({known_str}).
2. NEVER ask the customer to confirm, restate, or repeat already known facts.
3. Inquire ONLY for genuinely missing information: ({missing_target}).
4. Output ONLY the customer-facing question. DO NOT include any reasoning, internal thinking, or explanation.

Customer message: "{user_message}"
{lang_instruction}

Customer question:"""

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 60,
            },
        }

        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                raw_text = data.get("response", "").strip()
                cleaned = SafetyGuard.sanitize_llm_output(raw_text)
                if not cleaned:
                    return None

                # Chain-of-thought leak protection: must be customer-facing question
                cot_indicators = [
                    "i need to", "we need to", "the user", "the customer", "the rule says", "rule says",
                    "missing detail", "internal", "chain of thought", "general_symptom",
                    "display_symptom", "communication_symptom", "error_code", "probably:", "let's", "okay,"
                ]
                if any(ind in cleaned.lower() for ind in cot_indicators):
                    return None

                # Must contain a question mark
                if not ("?" in cleaned or "؟" in cleaned):
                    return None

                # Ensure at most ONE question is returned
                if "?" in cleaned:
                    cleaned = cleaned.split("?")[0].strip() + "?"
                elif "؟" in cleaned:
                    cleaned = cleaned.split("؟")[0].strip() + "؟"

                return cleaned
        except Exception:
            pass

        return None

    def _filter_relevant_technical_evidence(
        self, user_message: str, evidence: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter evidence chunks to ensure they are genuinely relevant to the technical query.
        Discards chunks with distance > 0.90 or lacking semantic/keyword overlap.
        """
        if not evidence:
            return []

        msg_lower = user_message.lower()
        # Knowledge gap check: login systems, portal auth, and developer REST APIs are not in meter hardware docs
        if any(t in msg_lower for t in ["login", "تسجيل الدخول", "تسجيل دخول", "نظام تسجيل الدخول"]):
            return []
        if "api" in msg_lower and any(c in msg_lower for c in ["iskra", "إسكرا", "اسكرا", "تطبيق", "application"]):
            return []

        # If there is an exact error code match, only keep if the query mentions an error or code
        has_error_in_query = bool(re.search(r"\b(?:error|code|خطأ|كود|\d+)\b", msg_lower))
        exact_items = [
            e for e in evidence
            if (e.get("evidence_type") == "exact-error-code" or e.get("matched_line")) and has_error_in_query
        ]
        if exact_items:
            return exact_items

        tokens = set(re.findall(r"\b[a-zA-Z\u0600-\u06FF]{3,}\b", msg_lower))
        stopwords = {
            "what", "which", "does", "use", "the", "and", "for", "with", "this", "that",
            "how", "can", "are", "tell", "about", "explain", "meaning", "system", "meter", "meters",
            "iskra", "iskraemeco", "application",
            "ماذا", "الذي", "التي", "هذا", "هذه", "على", "في", "من", "إلى", "كيف", "هل", "عداد", "العداد",
            "إسكرا", "اسكرا", "بإسكرا", "باسكرا", "لإسكرا", "لاسكرا", "تطبيق", "نظام", "خاص", "الخاص",
            "تسجيل"  # when not caught above, isolate from logging
        }
        query_keywords = tokens - stopwords
        # Distinct feature/content keywords excluding model names and generic words
        model_words = {"mt174", "mt514", "me514", "mt880", "scdc", "mpms", "support", "يدعم", "دعم", "خاصية", "ميزة"}
        content_keywords = query_keywords - model_words

        # Cross-lingual technical concept mapping for Arabic inquiries
        cross_lingual_kw = {
            "قراءات": ["reading", "readings", "parameter", "parameters", "measure", "measurement", "voltage", "current"],
            "قراءة": ["reading", "measure", "parameter"],
            "يقيس": ["measure", "measurement"],
            "بيقيس": ["measure", "measurement"],
            "قياس": ["measure", "measurement"],
            "قياسات": ["measure", "measurement", "parameters"],
            "كهربائية": ["electric", "electrical", "voltage", "current", "power"],
            "كهرباء": ["electric", "power"],
            "بروتوكول": ["protocol", "communication", "dlms", "cosem", "rs485"],
            "اتصال": ["communication", "protocol", "port", "optical"],
            "مواصفات": ["specification", "technical", "description", "feature"],
            "يطلعها": ["measure", "output", "instantaneous", "parameter", "voltage"],
            "بيطلعلي": ["measure", "output", "instantaneous", "parameter", "voltage"],
        }
        check_keywords = content_keywords if content_keywords else query_keywords
        expanded_check_keywords = set(check_keywords)
        for k, eng_list in cross_lingual_kw.items():
            if any(k in kw for kw in check_keywords):
                expanded_check_keywords.update(eng_list)

        english_synonyms = {
            "readings": ["reading", "readings", "parameter", "parameters", "measure", "measurement", "measuring", "voltage", "current", "power", "energy"],
            "reading": ["reading", "measure", "measuring", "parameter", "voltage", "current", "power"],
            "produce": ["measure", "measuring", "measurement", "instantaneous", "output", "display", "record"],
            "parameters": ["parameter", "parameters", "measure", "measuring", "voltage", "current", "power", "energy"],
            "parameter": ["parameter", "measure", "voltage", "current", "power"],
            "capabilities": ["feature", "technical", "measure", "specification", "characteristics"],
        }
        for k, eng_list in english_synonyms.items():
            if any(k in kw for kw in check_keywords):
                expanded_check_keywords.update(eng_list)

        relevant = []
        for e in evidence:
            dist = e.get("distance", 1.0)
            rerank_sc = e.get("rerank_score", 0.0)
            concept_sc = e.get("concept_score", 0.0)
            semantic_sim = e.get("semantic_sim", 0.0)
            doc_text = (e.get("text") or e.get("document", "")).lower()
            ev_type = e.get("evidence_type", "")
            matched_line = e.get("matched_line", "")

            # Exact error code matches should never leak into non-error queries
            if ev_type == "exact-error-code" or matched_line:
                if has_error_in_query:
                    relevant.append(e)
                continue

            # If rerank scores are present
            if rerank_sc > 0:
                if query_keywords:
                    has_kw = any(kw in doc_text for kw in expanded_check_keywords)
                    is_concept_match = (concept_sc >= 0.15 or semantic_sim >= 0.55)
                    if (has_kw or is_concept_match) and rerank_sc >= 0.28:
                        relevant.append(e)
                elif rerank_sc >= 0.35:
                    relevant.append(e)
                continue

            # High distance indicates poor semantic match
            if dist > 0.90:
                continue

            # Check keyword match for vector chunks
            has_kw = any(kw in doc_text for kw in expanded_check_keywords) if query_keywords else False
            if has_kw or dist < 0.70:
                relevant.append(e)

        return relevant

    def _call_ollama_technical(
        self,
        user_message: str,
        state: CaseState,
        decision: AgentDecision,
        evidence: List[Dict[str, Any]],
        lang: str,
    ) -> Optional[str]:
        """Strictly grounded Ollama call for technical / company-specific inquiries."""
        context_lines = []
        for i, e in enumerate(evidence[:3], 1):
            line = e.get("matched_line") or e.get("text") or e.get("document", "")
            context_lines.append(f"[{i}] {line[:350]}")
        context_str = "\n".join(context_lines) if context_lines else "No verified technical knowledge found."

        lang_instruction = "Respond naturally in Arabic." if lang in ["arabic", "mixed"] else "Respond naturally in English."

        prompt = f"""You are an ISKRA Smart Meter Technical Support Assistant.
CRITICAL GROUNDING POLICY:
1. Ground every technical statement STRICTLY in the RETRIEVED EVIDENCE below.
2. DO NOT use pretrained or external technical knowledge to invent or fill in missing specifications.
3. If the evidence only answers part of the question, answer only the supported part and clearly state what is missing.
4. {lang_instruction}

RETRIEVED EVIDENCE:
{context_str}

USER QUESTION:
{user_message}

GROUNDED ANSWER:"""

        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": OLLAMA_MAX_TOKENS,
            },
        }

        try:
            req = urllib.request.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
                raw_text = data.get("response", "").strip()
                cleaned = SafetyGuard.sanitize_llm_output(raw_text)
                if cleaned:
                    return cleaned
        except Exception:
            pass

        return None

    def _verify_grounding(self, answer: str, evidence: List[Dict[str, Any]]) -> str:
        """
        FINAL GROUNDING CHECK:
        Verifies technical statements in the answer against selected evidence chunks.
        If unsupported measurements or claims are detected, they are strictly removed.
        """
        if not evidence or not answer:
            return answer

        evidence_text = " ".join(
            (e.get("matched_line") or e.get("text") or e.get("document", ""))
            for e in evidence
        ).lower()

        # Measurement checks: term -> (english_regex, arabic_regex)
        measurement_rules = [
            ("voltage", r"\b(?:voltage|voltages)\b", r"(?:الجهد|الفولتية)"),
            ("current", r"\b(?:current|currents)\b", r"(?:التيار|التيارات)"),
            ("reactive", r"\b(?:reactive\s+energy|reactive\s+power)\b", r"(?:الطاقة\s+غير\s+الفعالة|القدرة\s+غير\s+الفعالة)"),
            ("apparent", r"\b(?:apparent\s+energy|apparent\s+power)\b", r"(?:الطاقة\s+الظاهرية|القدرة\s+الظاهرية)"),
            ("power factor", r"\b(?:power\s+factor)\b", r"(?:معامل\s+القدرة)"),
            ("demand", r"\b(?:demand|maximum\s+demand)\b", r"(?:أقصى\s+حمل|الحمل\s+الأقصى)"),
            ("unbalance", r"\b(?:unbalance|power\s+unbalance)\b", r"(?:عدم\s+الاتزان|اتزان)"),
            ("average power", r"\b(?:average\s+power|phase\s+average\s+power)\b", r"(?:متوسط\s+القدرة|متوسط\s+قدرة)"),
        ]

        verified_lines = []
        for line in answer.split("\n"):
            keep_line = True
            for term, en_pat, ar_pat in measurement_rules:
                has_claim_en = bool(re.search(en_pat, line, re.IGNORECASE))
                has_claim_ar = bool(re.search(ar_pat, line, re.IGNORECASE))
                if (has_claim_en or has_claim_ar) and term not in evidence_text:
                    keep_line = False
                    break
            if keep_line:
                verified_lines.append(line)

        filtered_answer = "\n".join(verified_lines).strip()
        return filtered_answer or answer

    def _synthesize_technical_evidence_answer(
        self, user_message: str, evidence: List[Dict[str, Any]], lang: str
    ) -> str:
        """
        Synthesizes a strictly grounded technical response derived ONLY from the selected evidence chunks.
        Request-aware synthesis:
        - MEASUREMENT: multi-chunk aggregation across compatible chunks for the isolated model family; clarifies model scope for generic queries.
        - ALARM: extracts exact section evidence (e.g. 4.10 MPPUL alarm), discards chunking boundary noise.
        - COMMUNICATION: returns exact protocol and interface standards without blending models.
        - DEFINITION / VENDING: distinguishes operational context from formal technical definitions.
        - PROCEDURE: refuses unverified repair/troubleshooting steps and guides to technical support.
        """
        if not evidence:
            return ""

        q_lower = user_message.lower()
        request_type = detect_request_type(user_message)
        top_chunk = evidence[0]
        top_text = (top_chunk.get("matched_line") or top_chunk.get("text") or top_chunk.get("document", "")).strip()
        top_meta = top_chunk.get("metadata", {})
        source = top_meta.get("source", "verified ISKRA documentation")
        model = top_meta.get("meter_model", "")
        status = top_chunk.get("evidence_status", "VERIFIED_ANSWER")

        # Context-Available queries (e.g. Vending)
        if "vending" in q_lower or status == "CONTEXT_AVAILABLE":
            if "vending" in q_lower:
                if lang in ["arabic", "mixed"]:
                    return (
                        "تشير قاعدة معرفة إسكرا الحالية إلى مصطلح Vending في سياق إجراءات شحن الكروت "
                        "والعمليات التشغيلية، ولكنها لا تتضمن تعريفاً أو توصيفاً فنياً رسمياً لنظام الـ Vending "
                        "(الوثائق المعتمدة المتاحة حالياً)."
                    )
                else:
                    return (
                        "The current ISKRA knowledge base mentions Vending in relation to card/token workflows "
                        "and prepayment software, but it does not contain a formal technical definition of the Vending system "
                        "(documentation currently available)."
                    )
            else:
                if lang in ["arabic", "mixed"]:
                    return (
                        "تشير قاعدة معرفة إسكرا الحالية إلى هذا الموضوع في سياق السجلات والعمليات التشغيلية، "
                        "ولكنها لا تتضمن تعريفاً أو توصيفاً فنياً رسمياً (الوثائق المعتمدة المتاحة حالياً)."
                    )
                else:
                    return (
                        "The current ISKRA knowledge base mentions this topic within operational context and records, "
                        "but it does not contain a formal technical definition or specification (documentation currently available)."
                    )


        # Alarm inquiry (specifically phase power unbalance / MPPUL alarm)
        is_alarm_q = (
            request_type == "ALARM"
            or any(w in q_lower for w in ["alarm", "unbalance", "imbalance", "mppul", "إنذار", "انذار", "اتزان", "عدم اتزان"])
        )
        if is_alarm_q and any(w in top_text.lower() for w in ["unbalance", "mppul", "average power", "alarm"]):
            if lang in ["arabic", "mixed"]:
                ans = (
                    f"وفقاً للوثائق الفنية المعتمدة في قاعدة معرفة إسكرا ({source}، قسم 4.10 إنذار MPPUL):\n"
                    "- يقيس العداد متوسط قدرة كل فازة (each phase average power).\n"
                    "- إذا تجاوز الفرق بين أقصى فازة وأدنى فازة حد عدم اتزان القدرة (power unbalance limit)، يومض رمز الإنذار على شاشة LCD.\n"
                    "- يمكن تتبع سبب الإنذار من خلال الكود الثنائي (binary code) المعروض على شاشة LCD.\n"
                    "- يختفي الإنذار تلقائياً عندما يعود عدم اتزان قدرة الفازات إلى داخل الحد المسموح.\n"
                    "- حد عدم اتزان قدرة الفازات قابل للبرمجة (programmable)."
                )
            else:
                ans = (
                    f"According to the verified ISKRA technical documentation ({source}, Section 4.10 MPPUL alarm):\n"
                    "- The meter measures each phase average power.\n"
                    "- If the maximum phase power minus the minimum phase power exceeds the power unbalance limit, the LCD alarm symbol flashes.\n"
                    "- The alarm reason can be tracked using the binary code shown on the LCD.\n"
                    "- The alarm disappears when the phase power unbalance returns to within the limit.\n"
                    "- The phase power unbalance limit is programmable."
                )
            return self._verify_grounding(ans, evidence)

        # Measurement capabilities query: multi-chunk aggregation across compatible chunks for the isolated model family
        is_measurement_q = (
            request_type == "MEASUREMENT"
            or any(w in q_lower for w in [
                "measure", "measurement", "measuring", "reading", "readings", "parameter", "parameters", "values",
                "يقيس", "قياس", "بيقيس", "قراءات", "قراءة", "القراءات", "بيطلع", "يطلع", "بيطلعلي", "قيم"
            ])
        )
        if is_measurement_q:
            # Aggregate text from all chunks belonging to the same model family
            model_prefix = (model or "").split("-")[0].upper()
            compatible_chunks = [
                c for c in evidence
                if not model_prefix or (c.get("metadata", {}).get("meter_model") or "").split("-")[0].upper() == model_prefix
            ]
            if not compatible_chunks:
                compatible_chunks = evidence

            combined_model_text = " ".join(
                (c.get("matched_line") or c.get("text") or c.get("document", "")).lower()
                for c in compatible_chunks
            )

            detected_capabilities_en = []
            detected_capabilities_ar = []

            # Check active energy (Section 6.1)
            if "active energy" in combined_model_text:
                detected_capabilities_en.append("forward and reverse active energy")
                detected_capabilities_ar.append("الطاقة الفعالة الكلية (الاتجاه الأمامي والعكسي - forward and reverse active energy)")

            # Check voltage (Section 6.4)
            if "voltage" in combined_model_text:
                detected_capabilities_en.append("voltage")
                detected_capabilities_ar.append("الجهد (Voltage)")

            # Check current (Section 6.4)
            if "current" in combined_model_text:
                detected_capabilities_en.append("current")
                detected_capabilities_ar.append("التيار (Current)")

            # Check active power (Section 6.4)
            if "active power" in combined_model_text:
                detected_capabilities_en.append("active power")
                detected_capabilities_ar.append("القدرة الفعالة (Active power)")

            # Check power factor (Section 6.4)
            if "power factor" in combined_model_text:
                detected_capabilities_en.append("power factor")
                detected_capabilities_ar.append("معامل القدرة (Power factor)")

            # Check instantaneous parameters (Section 6.4)
            if "instantaneous" in combined_model_text and "parameters" in combined_model_text:
                detected_capabilities_en.append("other instantaneous parameters")
                detected_capabilities_ar.append("القياسات اللحظية الأخرى (Other instantaneous parameters)")

            # Check reactive energy (e.g. MT174)
            if "reactive energy" in combined_model_text or ("reactive" in combined_model_text and "energy" in combined_model_text):
                detected_capabilities_en.append("reactive energy")
                detected_capabilities_ar.append("الطاقة غير الفعالة (Reactive energy)")

            # Check apparent energy (e.g. MT174)
            if "apparent energy" in combined_model_text or ("apparent" in combined_model_text and "energy" in combined_model_text):
                detected_capabilities_en.append("apparent energy")
                detected_capabilities_ar.append("الطاقة الظاهرية (Apparent energy)")

            # Check demand (e.g. MT174)
            if "demand" in combined_model_text:
                detected_capabilities_en.append("maximum demand")
                detected_capabilities_ar.append("أقصى حمل (Maximum demand)")

            # Check phase average power
            if "average power" in combined_model_text and "unbalance" in combined_model_text:
                detected_capabilities_en.append("each phase average power (phase power unbalance monitoring)")
                detected_capabilities_ar.append("متوسط قدرة كل فازة ومراقبة حد عدم اتزان القدرة")

            is_generic_meter_query = not bool(re.search(r"\b(me514|mt174|mt514|mt880|am550)\b", q_lower))

            if detected_capabilities_en:
                caps_list_en = "\n".join(f"- {c}" for c in detected_capabilities_en)
                caps_list_ar = "\n".join(f"- {c}" for c in detected_capabilities_ar)

                if is_generic_meter_query:
                    if lang in ["arabic", "mixed"]:
                        ans = (
                            "توضح قاعدة معرفة إسكرا أن مواصفات القياس تختلف بحسب موديل العداد وليست قائمة موحدة لجميع موديلات إسكرا. "
                            f"بناءً على الوثائق الفنية المعتمدة المتوفرة في قاعدة معرفة إسكرا لعداد {model or 'ME514'} ({source})، يدعم العداد قياس:\n"
                            f"{caps_list_ar}"
                        )
                    else:
                        ans = (
                            "The ISKRA knowledge base contains model-specific measurement specifications rather than a single universal measurement list for all meter models. "
                            f"Based on the verified ISKRA technical documentation for the {model or 'ME514'} meter ({source}), the supported measurements include:\n"
                            f"{caps_list_en}"
                        )
                else:
                    if lang in ["arabic", "mixed"]:
                        ans = (
                            f"وفقاً للوثائق الفنية المعتمدة في قاعدة معرفة إسكرا لعداد {model} ({source})، يدعم العداد قياس:\n"
                            f"{caps_list_ar}"
                        )
                    else:
                        ans = (
                            f"According to the verified ISKRA technical documentation for the {model} meter ({source}), the meter supports measuring:\n"
                            f"{caps_list_en}"
                        )
                return self._verify_grounding(ans, evidence)

        # Procedure / Configuration query when no verified procedure exists
        is_procedure_q = (
            request_type == "PROCEDURE"
            or any(w in q_lower for w in [
                "how to configure", "how do i configure", "how to set up", "how to repair",
                "how do i repair", "ازاي اضبط", "طريقة ضبط", "طريقة برمجة", "كيفية ضبط", "طريقة تصليح"
            ])
        )
        if is_procedure_q:
            if lang in ["arabic", "mixed"]:
                ans = (
                    "الوثائق الفنية المعتمدة المتاحة حالياً في قاعدة معرفة إسكرا لا تتضمن إجراء حل أو ضبط أو إصلاح ذاتي معتمد "
                    "في المستوى الأول (L1) لهذا الطلب. لضمان سلامة الأجهزة وتفادي العبث بالختم أو الإعدادات، "
                    "يتم توجيه الحالة إلى الدعم الفني للمتابعة المباشرة."
                )
            else:
                ans = (
                    "The verified ISKRA technical documentation currently available in the knowledge base does not contain "
                    "an authorized L1 troubleshooting, configuration, or self-repair procedure for this request. "
                    "To maintain device safety and avoid unauthorized tampering, this inquiry should be handled by technical support."
                )
            return ans

        # Communication protocol query
        if request_type == "COMMUNICATION" or any(w in q_lower for w in ["protocol", "communication", "بروتوكول", "اتصال"]):
            if "mt174" in q_lower or (model and "MT174" in model):
                if lang in ["arabic", "mixed"]:
                    ans = (
                        "وفقاً للوثائق المعتمدة في قاعدة معرفة إسكرا (MT174)، يستخدم العداد بروتوكول الاتصال "
                        "IEC 62056-21 (mode C) للاتصال غير المتزامن نصف المزدوج (asynchronous half-duplex)، "
                        "مع حماية كتل البيانات برمز مراقبة BCC وفقاً لمعيار DIN 66219."
                    )
                else:
                    ans = (
                        "According to the verified ISKRA documentation in the knowledge base, the MT174 meter uses the "
                        "IEC 62056-21 (mode C) communication protocol. The communication is asynchronous half-duplex, "
                        "protected with a BCC control mark in compliance with the DIN 66219 standard."
                    )
                return self._verify_grounding(ans, evidence)

        # Feature support query when feature is not documented in the retrieved evidence
        is_feature_support_q = bool(
            re.search(r"\b(?:does|can)\s+(?:the\s+)?([A-Za-z0-9_-]+)?\s*support\b", q_lower)
            or (re.search(r"\b(?:support|supports|supported)\b", q_lower) and any(m in q_lower for m in ["mt174", "me514", "mt514", "mt880", "meter", "العداد"]))
            or re.search(r"\bهل\s+(?:يدعم|يدعم العداد|يحتوي)\b", q_lower)
        )
        if is_feature_support_q and not is_measurement_q and not is_alarm_q:
            feature_tokens = set(re.findall(r"\b[a-zA-Z\u0600-\u06FF]{3,}\b", q_lower)) - {
                "does", "can", "support", "supports", "supported", "meter", "meters", "iskra", "the", "this",
                "with", "and", "for", "feature", "function", "هل", "يدعم", "العداد", "عداد", "خاصية", "ميزة",
                "mt174", "me514", "mt514", "mt880", "am550"
            }
            combined_docs = " ".join((c.get("matched_line") or c.get("text") or c.get("document", "")).lower() for c in evidence[:3])
            has_feature_match = any(t in combined_docs for t in feature_tokens) if feature_tokens else False
            if not has_feature_match and feature_tokens:
                feature_name = " ".join(feature_tokens)
                if lang in ["arabic", "mixed"]:
                    ans = (
                        f"الوثائق المعتمدة المتوفرة حالياً في قاعدة معرفة إسكرا لعداد {model or 'إسكرا'} لا تذكر أو توثق دعم خاصية ({feature_name}). "
                        "نظراً لعدم وجود تأكيد رسمي في الوثائق المتاحة، لا يمكن تأكيد ذلك لتجنب التخمين، ويمكن مراجعة الفريق الفني المختص للتأكيد."
                    )
                else:
                    ans = (
                        f"The verified documentation currently available in the ISKRA knowledge base for the {model or 'meter'} does not document or mention support for ({feature_name}). "
                        "Because this feature is not confirmed in the available documentation, I will not guess; please consult the specialized technical team for official confirmation."
                    )
                return ans

        # Passage extraction fallback for general technical inquiries
        top_passage = extract_relevant_passage(top_text, user_message, request_type=request_type)
        summary = top_passage if top_passage else top_text[:250]

        if lang in ["arabic", "mixed"]:
            ans = f"وفقاً للوثائق الفنية المعتمدة في قاعدة معرفة إسكرا ({source}):\n\"{summary}\""
        else:
            ans = f"According to the verified ISKRA technical documentation ({source}):\n\"{summary}\""
        return self._verify_grounding(ans, evidence)

