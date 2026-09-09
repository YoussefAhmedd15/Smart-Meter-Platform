"""
Test Suite: Conversational Clarification & Known Fact Retention
Validates that:
1. Explicit user statements (such as 'the display is blank') are stored as known facts.
2. The agent never asks the user to repeat, restate, or confirm already known facts.
3. The agent asks at most one genuinely useful next question requesting only missing information,
   or provides direct escalation/answering if no further information is required.
4. Preserves exact error code retrieval, unknown error handling, safety, and routing.
"""

import unittest
import sys
from pathlib import Path

# Add project root and ai_training to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
AI_TRAINING_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_TRAINING_DIR.parent

for p in [str(PROJECT_ROOT), str(AI_TRAINING_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ai_training.agent.agent import L1Agent
from ai_training.agent.models import AgentIntent, AgentAction
from ai_training.agent.response import ResponseGenerator
from ai_training.rag.retriever import HybridRetriever


class TestClarificationBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = HybridRetriever()

    def setUp(self):
        self.agent = L1Agent(
            retriever=self.retriever,
            response_generator=ResponseGenerator(use_ollama=False),
        )

    # ------------------------------------------------------------
    # Test 1: Vague initial symptom
    # User: "my meter not work"
    # Expected: clarification asking for a useful symptom.
    # ------------------------------------------------------------
    def test_01_vague_symptom_clarification(self):
        resp = self.agent.process_message("my meter not work")
        state = self.agent.get_state()

        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertEqual(state.issue, "meter not working")
        self.assertEqual(state.last_question_field, "general_symptom")
        self.assertLessEqual(resp.text.count("?"), 1)
        self.assertTrue(
            "symptom" in resp.text.lower()
            or "what" in resp.text.lower()
            or "display" in resp.text.lower()
        )

    # ------------------------------------------------------------
    # Test 2: User explicitly provides symptom
    # User: "my meter not work" -> Agent asks for symptom
    # User: "the display is blank"
    # Expected:
    # - display blank is stored as known fact
    # - agent does NOT ask whether the display is blank again
    # - asks at most one genuinely useful next question OR gives appropriate next action
    # ------------------------------------------------------------
    def test_02_explicit_fact_no_redundant_question(self):
        # Turn 1
        r1 = self.agent.process_message("my meter not work")
        self.assertEqual(r1.action, AgentAction.ASK_CLARIFICATION)

        # Turn 2: Explicit fact provided
        r2 = self.agent.process_message("the display is blank")
        state2 = self.agent.get_state()

        # Fact is stored in known_facts and state
        self.assertEqual(state2.known_facts.get("display_symptom"), "blank")
        self.assertEqual(state2.display_symptom, "blank")
        self.assertEqual(state2.symptom_category, "display")

        # MUST NOT ask if screen/display is blank:
        lower_resp = r2.text.lower()
        self.assertNotIn("is it completely blank", lower_resp)
        self.assertNotIn("is the screen blank", lower_resp)
        self.assertNotIn("is the display blank", lower_resp)
        self.assertNotIn("is it blank", lower_resp)

        # Must ask at most one genuinely useful next question (e.g. meter responsiveness / buttons)
        # OR give appropriate next action:
        self.assertLessEqual(r2.text.count("?"), 1)
        self.assertTrue(
            "respond" in lower_resp
            or "button" in lower_resp
            or "operate" in lower_resp
            or "hardware" in lower_resp
            or "support" in lower_resp
            or r2.action in [AgentAction.ASK_CLARIFICATION, AgentAction.ESCALATE]
        )

        # Turn 3: User answers responsiveness
        r3 = self.agent.process_message("it does not respond to any buttons")
        state3 = self.agent.get_state()
        self.assertEqual(state3.known_facts.get("meter_responsiveness"), "no_response")
        # No further questions needed; escalates to L2 Hardware
        self.assertNotIn("?", r3.text)
        self.assertIn("Hardware", state3.issue_category)
        self.assertEqual(state3.routing, "L2 Hardware")

    # ------------------------------------------------------------
    # Test 2b: Arabic equivalent
    # Turn 1: "العداد مش شغال"
    # Turn 2: "الشاشة مطفية"
    # ------------------------------------------------------------
    def test_02b_arabic_explicit_display_blank(self):
        self.agent.process_message("العداد مش شغال")
        r2 = self.agent.process_message("الشاشة مطفية")
        state2 = self.agent.get_state()

        self.assertEqual(state2.known_facts.get("display_symptom"), "blank")
        self.assertEqual(state2.display_symptom, "blank")

        # Agent must not ask whether the screen is مطفية
        self.assertNotIn("هل هي مطفأة تماماً", r2.text)
        self.assertNotIn("هل الشاشة مطفية", r2.text)
        # Asks useful next question in Arabic
        self.assertTrue("يستجيب" in r2.text or "زر" in r2.text or "الدعم" in r2.text)

    # ------------------------------------------------------------
    # Test 3: Unspecified error symptom
    # User: "it shows an error"
    # Expected: existing behavior remains; ask for error code/message
    # ------------------------------------------------------------
    def test_03_unspecified_error_asks_for_code(self):
        r1 = self.agent.process_message("meter not work")
        r2 = self.agent.process_message("it shows an error")
        state2 = self.agent.get_state()

        self.assertEqual(r2.action, AgentAction.ASK_CLARIFICATION)
        self.assertEqual(state2.last_question_field, "error_code")
        self.assertTrue(
            "code" in r2.text.lower()
            or "error" in r2.text.lower()
            or "message" in r2.text.lower()
        )

    # ------------------------------------------------------------
    # Test 4: Exact error code retrieval
    # User: "70"
    # Expected: existing exact Error 70 retrieval remains unchanged;
    # verified evidence remains unchanged.
    # ------------------------------------------------------------
    def test_04_exact_error_70_remains_unchanged(self):
        self.agent.process_message("meter not work")
        self.agent.process_message("it shows an error")
        r3 = self.agent.process_message("70")
        state3 = self.agent.get_state()

        self.assertEqual(state3.error_code, "70")
        self.assertEqual(r3.action, AgentAction.ANSWER)
        self.assertTrue(len(state3.evidence) > 0)
        top_ev = state3.evidence[0]
        self.assertEqual(top_ev.get("evidence_type"), "exact-error-code")
        self.assertIn("lead seal button", top_ev.get("matched_line", "").lower())
        self.assertIn("lead seal button", r3.text.lower())

    # ------------------------------------------------------------
    # Test 5: Unknown error code
    # User: unknown error code ("Error 999")
    # Expected: existing NOT_FOUND behavior remains, no invented
    # troubleshooting, existing escalation/routing remains.
    # ------------------------------------------------------------
    def test_05_unknown_error_not_found(self):
        resp = self.agent.process_message("Error 999")
        state = self.agent.get_state()

        self.assertEqual(state.error_code, "999")
        self.assertEqual(state.knowledge_status, "NOT_FOUND")
        self.assertIn("could not find Error 999", resp.text)
        self.assertNotIn("press the button for 10 seconds", resp.text.lower())
        self.assertNotIn("replace the meter", resp.text.lower())
        self.assertTrue(
            "routing" in resp.text.lower()
            or "support" in resp.text.lower()
            or "escalat" in resp.text.lower()
        )


if __name__ == "__main__":
    unittest.main()
