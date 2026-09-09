from typing import List, Dict, Any, Optional, Tuple
from .models import (
    CaseState,
    AgentIntent,
    AgentAction,
    AgentDecision,
    EvidenceItem,
)
from .config import ROUTING_MAP, DEFAULT_ROUTING
from .policy import DOMAIN_GENERAL_NON_TECHNICAL


class DecisionEngine:
    """
    Core deterministic L1 decision engine.
    Separates error meaning from resolution, classifies issues conservatively,
    decides agent actions without forcing a rigid questionnaire, and enforces
    at most one justified clarification question per turn.
    """

    def __init__(self, routing_map: Optional[Dict[str, str]] = None):
        self.routing_map = routing_map or ROUTING_MAP

    # ------------------------------------------------------------
    # 1. ISSUE CLASSIFICATION
    # ------------------------------------------------------------
    def classify_issue(
        self, state: CaseState, evidence: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Classifies issue into: Software, Hardware, Firmware, Communication, or Unknown.
        Evaluates context, messages, system name, and retrieved evidence.
        Never forces a classification if information is insufficient.
        """
        # Combine customer context text
        context_parts = [
            state.issue or "",
            state.scenario or "",
            state.system or "",
            state.last_user_message or "",
        ]
        context_str = " ".join(context_parts).lower()

        # Only check exact matched error lines from evidence, not broad vector noise
        exact_lines = [e.get("matched_line", "") for e in evidence if e.get("matched_line")]
        exact_str = " ".join(exact_lines).lower()
        eval_text = f"{context_str} {exact_str}".strip()

        # 1. Software checks (system names, accounts, vending, billing, apps)
        software_systems = ["vending", "billing", "symbiot", "meterverse", "aqua"]
        if (state.system and state.system.lower() in software_systems) or any(
            sys_name in context_str for sys_name in software_systems
        ):
            return "Software", f"Software system ({state.system or 'Application'}) involved."

        software_indicators = [
            "cannot open account", "open account", "account opening", "login",
            "software", "application error", "system error", "فتح حساب", "الاكونت",
            "برنامج", "السيستم", "سوفت وير", "database error"
        ]
        if any(w in context_str for w in software_indicators):
            return "Software", "Software operation or application workflow issue detected."

        # 2. Firmware checks
        firmware_indicators = [
            "firmware", "فيرموير", "سوفت وير العداد", "upgrade firmware",
            "flash firmware", "firmware version", "firmware too old"
        ]
        if any(w in eval_text for w in firmware_indicators):
            return "Firmware", "Firmware-related terms or evidence detected."

        # 3. Hardware checks
        hardware_indicators = [
            "broken", "damaged", "burned", "burnt", "power failure", "no power",
            "screen broken", "display broken", "lcd broken", "relay damaged",
            "battery failure", "physical", "تالف", "مكسور", "محروق", "باور",
            "شاشة مكسورة", "زرار مكسور", "button damaged", "physical damage"
        ]
        if any(w in eval_text for w in hardware_indicators):
            return "Hardware", "Physical or hardware component failure detected."

        if (
            (state.known_facts.get("display_symptom") == "blank" or getattr(state, "display_symptom", None) == "blank")
            and (state.known_facts.get("meter_responsiveness") == "no_response" or "not respond" in eval_text or "لا يستجيب" in eval_text)
        ):
            return "Hardware", "Meter display is blank and unresponsive to button input."

        # 4. Communication checks
        comm_indicators = [
            "communication", "communicate", "connection error", "rs485", "rs232",
            "modbus", "dlms", "cosem", "hdlc", "tcp connection", "not connected",
            "disconnected", "مشكلة اتصال", "الاتصال", "لا يوجد اتصال",
            "cannot read data", "lost communication"
        ]
        if any(w in eval_text for w in comm_indicators):
            return "Communication", "Communication/protocol failure detected."

        return "Unknown", "Insufficient evidence to classify category definitively."

    # ------------------------------------------------------------
    # 2. ROUTING
    # ------------------------------------------------------------
    def determine_routing(self, category: str) -> str:
        """Map category to support tier based on configured business rules."""
        return self.routing_map.get(category, DEFAULT_ROUTING)

    # ------------------------------------------------------------
    # 3. KNOWLEDGE & RESOLUTION STATUS
    # ------------------------------------------------------------
    def evaluate_knowledge_and_resolution(
        self, state: CaseState, evidence: List[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Evaluate Knowledge Status and Resolution Status.
        Crucial Rule: Knowing the meaning of an error does NOT mean the problem is resolved.
        """
        has_exact_error = any(
            e.get("evidence_type") == "exact-error-code" or bool(e.get("matched_line"))
            for e in evidence
        )
        has_any_evidence = len(evidence) > 0

        is_general_q = (state.intent == AgentIntent.GENERAL_QUESTION.value)

        # Knowledge Status
        if has_exact_error:
            knowledge_status = "Verified Knowledge Available"
        elif is_general_q:
            # For general questions, evaluate based on general evidence, not error code
            knowledge_status = "Verified Knowledge Available" if any(e.get("distance", 1.0) < 0.25 for e in evidence) else "No Verified Knowledge"
        elif state.error_code and not has_exact_error:
            # User explicitly provided an error code that was NOT found in verified docs!
            knowledge_status = "NOT_FOUND"
        elif has_any_evidence:
            knowledge_status = "Partial Knowledge"
        else:
            knowledge_status = "No Verified Knowledge"

        # Resolution Status
        # If knowledge explicitly contains troubleshooting instructions
        has_procedure = False
        for e in evidence:
            doc_text = e.get("document", "").lower()
            if any(p in doc_text for p in ["troubleshooting", "resolution", "step 1", "to fix", "حل المشكلة", "طريقة الحل"]):
                has_procedure = True
                break

        if has_procedure:
            resolution_status = "Troubleshooting Available"
        elif is_general_q:
            resolution_status = "Informational Query"
        elif has_exact_error or (state.error_code and not has_exact_error):
            # Meaning is verified (or unknown error), but resolution procedure is NOT in knowledge base!
            resolution_status = "Needs L2"
        elif state.issue_category in ["Software", "Hardware", "Firmware", "Communication"]:
            resolution_status = "Needs L2"
        else:
            resolution_status = "Needs More Information"

        return knowledge_status, resolution_status

    # ------------------------------------------------------------
    # 4. ACTION SELECTION
    # ------------------------------------------------------------
    def decide_action(
        self,
        state: CaseState,
        intent: AgentIntent,
        evidence: List[Dict[str, Any]],
        category: str,
    ) -> AgentDecision:
        """
        Decides next agent action:
        - ANSWER
        - ASK_CLARIFICATION
        - RETRIEVE_KNOWLEDGE
        - TROUBLESHOOT
        - ESCALATE
        - ACKNOWLEDGE
        """
        routing = self.determine_routing(category)
        knowledge_status, resolution_status = self.evaluate_knowledge_and_resolution(
            state, evidence
        )

        # --------------------------------------------------------
        # 0. USER IS FRUSTRATED / REQUESTED NO QUESTIONS
        # --------------------------------------------------------
        if state.user_frustrated:
            return AgentDecision(
                action=AgentAction.ESCALATE if resolution_status == "Needs L2" else AgentAction.ANSWER,
                reason="Customer expressed frustration or requested no questions. Providing direct guidance or escalation without questions.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # 0.1 GENERAL / NON-TECHNICAL CONCEPT QUERY (Policy Rule B)
        # --------------------------------------------------------
        if state.question_domain == DOMAIN_GENERAL_NON_TECHNICAL:
            return AgentDecision(
                action=AgentAction.ANSWER,
                reason="General non-technical conceptual query. Answer directly without meter questionnaire.",
                routing=routing,
                category="General",
                l1_status="General Knowledge",
                knowledge_status="General Knowledge",
            )

        # --------------------------------------------------------
        # A. USER REQUESTED ESCALATION
        # --------------------------------------------------------
        if intent == AgentIntent.ESCALATION:
            return AgentDecision(
                action=AgentAction.ESCALATE,
                reason="Customer requested escalation to L2.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # B. DIRECT ERROR EXPLANATION (e.g. "What is Error 70?", "Error 999")
        # --------------------------------------------------------
        if intent == AgentIntent.ERROR_EXPLANATION:
            # MUST answer immediately without asking any questions!
            return AgentDecision(
                action=AgentAction.ANSWER,
                reason="Direct error code explanation request.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # C. IDENTIFICATION QUESTION (e.g. "Where can I find the model?")
        # --------------------------------------------------------
        if intent == AgentIntent.IDENTIFICATION:
            return AgentDecision(
                action=AgentAction.ANSWER,
                reason="Customer asked where to identify meter information.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # D. GENERAL QUESTION / GREETING / INFORMATIONAL QUERY
        # --------------------------------------------------------
        if intent == AgentIntent.GENERAL_QUESTION:
            return AgentDecision(
                action=AgentAction.ANSWER,
                reason="General informational inquiry.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # E. EXACT ERROR FOUND IN TROUBLESHOOTING CASE
        # --------------------------------------------------------
        has_exact_error = any(
            e.get("evidence_type") == "exact-error-code" or bool(e.get("matched_line"))
            for e in evidence
        )
        if has_exact_error and state.error_code:
            # We have verified error meaning.
            # If no procedure exists in knowledge base, escalate or answer with verified meaning.
            return AgentDecision(
                action=AgentAction.ANSWER,
                reason="Verified error code identified. Presenting meaning and escalation recommendation.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # --------------------------------------------------------
        # F. CLARIFICATION QUESTION SELECTION (MAX ONE QUESTION)
        # --------------------------------------------------------
        # Only ask if genuinely necessary and justified by next action.
        # Check what the user DOES NOT KNOW so we never ask for it.
        unknown_fields = set(state.user_does_not_know)
        asked_fields = set(state.asked_topics)
        if state.last_question_field:
            asked_fields.add(state.last_question_field)

        # Identify what is already known vs what was asked or unknown
        known_facts = dict(state.known_facts)
        display_symptom = known_facts.get("display_symptom") or getattr(state, "display_symptom", None)
        meter_responsiveness = known_facts.get("meter_responsiveness")
        symptom_category = known_facts.get("symptom_category") or getattr(state, "symptom_category", None)

        if not display_symptom and state.last_user_message:
            from .extraction import FactExtractor
            display_symptom = FactExtractor.extract_display_symptom(state.last_user_message, state.last_question_field)
            if display_symptom:
                known_facts["display_symptom"] = display_symptom
                symptom_category = "display"

        if not symptom_category and state.last_user_message:
            from .extraction import FactExtractor
            symptom_category = FactExtractor.detect_symptom_category(state.last_user_message)

        if not meter_responsiveness and state.last_user_message:
            from .extraction import FactExtractor
            meter_responsiveness = FactExtractor.extract_meter_responsiveness(state.last_user_message)
            if meter_responsiveness:
                known_facts["meter_responsiveness"] = meter_responsiveness

        # If user provided no error code and problem needs clarification:
        if not state.error_code:
            # 1. Display symptom
            if symptom_category == "display":
                # If display symptom condition is ALREADY explicitly known (e.g. blank, blinking):
                # DO NOT ask whether the screen is blank again!
                if display_symptom:
                    # Request ONLY genuinely missing, materially useful next information:
                    # For a blank screen, whether the meter responds to button operation or shows signs of power
                    if "meter_responsiveness" not in unknown_fields and "meter_responsiveness" not in asked_fields and not meter_responsiveness:
                        return AgentDecision(
                            action=AgentAction.ASK_CLARIFICATION,
                            reason=f"Display condition is known ({display_symptom}). Requesting missing meter operational responsiveness.",
                            question_field="meter_responsiveness",
                            routing="L2 Hardware" if category == "Unknown" else routing,
                            category="Hardware" if category == "Unknown" else category,
                            l1_status=resolution_status,
                            knowledge_status=knowledge_status,
                        )
                    # If responsiveness is already evaluated/known, no further question is required.
                    # Escalate according to existing evidence/routing logic:
                    return AgentDecision(
                        action=AgentAction.ESCALATE,
                        reason="Display issue evaluated and no verified L1 troubleshooting exists in documentation. Case requires hardware support.",
                        routing="L2 Hardware",
                        category="Hardware",
                        l1_status="Needs L2",
                        knowledge_status=knowledge_status,
                    )
                elif "display_symptom" not in unknown_fields and "display_symptom" not in asked_fields:
                    return AgentDecision(
                        action=AgentAction.ASK_CLARIFICATION,
                        reason="Customer reported a display/screen issue, requesting display details.",
                        question_field="display_symptom",
                        routing=routing,
                        category=category,
                        l1_status=resolution_status,
                        knowledge_status=knowledge_status,
                    )

            # 2. Communication symptom (e.g. "meter cannot communicate")
            if symptom_category == "communication" and "communication_symptom" not in unknown_fields and "communication_symptom" not in asked_fields:
                return AgentDecision(
                    action=AgentAction.ASK_CLARIFICATION,
                    reason="Customer reported a communication issue, requesting interface or error details.",
                    question_field="communication_symptom",
                    routing=routing,
                    category=category,
                    l1_status=resolution_status,
                    knowledge_status=knowledge_status,
                )

            # 3. Unspecified error symptom (e.g. "meter shows an error", "العداد بيطلع error")
            if symptom_category == "error_unspecified" and "error_code" not in unknown_fields and "error_code" not in asked_fields:
                return AgentDecision(
                    action=AgentAction.ASK_CLARIFICATION,
                    reason="Customer stated an error is displayed without code, asking for exact error code.",
                    question_field="error_code",
                    routing=routing,
                    category=category,
                    l1_status=resolution_status,
                    knowledge_status=knowledge_status,
                )

            # 4. Power symptom (e.g. "meter is dead", "no power")
            if symptom_category == "power" and "power_symptom" not in unknown_fields and "power_symptom" not in asked_fields:
                return AgentDecision(
                    action=AgentAction.ASK_CLARIFICATION,
                    reason="Customer reported power failure, requesting power/LED status.",
                    question_field="power_symptom",
                    routing=routing,
                    category=category,
                    l1_status=resolution_status,
                    knowledge_status=knowledge_status,
                )

            # 5. General vague symptom (e.g. "meter not work", "العداد مش شغال")
            if not state.scenario and not display_symptom and symptom_category not in ["display", "communication", "power", "error_unspecified"] and "general_symptom" not in unknown_fields and "general_symptom" not in asked_fields and "error_code" not in asked_fields:
                return AgentDecision(
                    action=AgentAction.ASK_CLARIFICATION,
                    reason="Initial inquiry lacks specific symptom details, asking for clarification.",
                    question_field="general_symptom",
                    routing=routing,
                    category=category,
                    l1_status=resolution_status,
                    knowledge_status=knowledge_status,
                )

        # If we have an issue with Vending or account opening but no error code and user hasn't said error code is unknown:
        if state.system and not state.error_code and "error_code" not in unknown_fields and "error_code" not in asked_fields:
            return AgentDecision(
                action=AgentAction.ASK_CLARIFICATION,
                reason="System is known, checking if an error code or message appeared.",
                question_field="error_code",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # If we have an error code, system, or issue, but no verified resolution procedure in docs:
        if resolution_status == "Needs L2":
            return AgentDecision(
                action=AgentAction.ESCALATE,
                reason="No verified L1 resolution procedure in documentation. Case requires L2.",
                routing=routing,
                category=category,
                l1_status=resolution_status,
                knowledge_status=knowledge_status,
            )

        # Default to ANSWER based on available evidence or safe assistance
        return AgentDecision(
            action=AgentAction.ANSWER,
            reason="Providing assistance based on available facts.",
            routing=routing,
            category=category,
            l1_status=resolution_status,
            knowledge_status=knowledge_status,
        )
