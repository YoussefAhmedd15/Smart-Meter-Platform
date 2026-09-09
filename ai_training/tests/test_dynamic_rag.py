import unittest
from ai_training.agent.agent import L1Agent
from ai_training.agent.models import AgentIntent, AgentAction
from ai_training.agent.policy import DOMAIN_TECHNICAL_COMPANY, DOMAIN_GENERAL_NON_TECHNICAL


class TestDynamicConversationalRAG(unittest.TestCase):
    """
    Comprehensive test suite for the dynamic conversational RAG ISKRA agent.
    Validates dynamic understanding, single-question clarifications, arbitrary error codes,
    knowledge gap protection, and multi-turn state preservation.
    """

    def setUp(self):
        self.agent = L1Agent()

    def test_01_vague_symptom_meter_not_work(self):
        """
        Vague symptom: 'meter not work'
        Must ask AT MOST ONE clarification question tailored to symptom without assuming error code.
        """
        resp = self.agent.process_message("meter not work")
        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        # Must not contain multiple question marks
        self.assertLessEqual(resp.text.count("?"), 1)
        # Must not hallucinate an error code or assume communication failure
        self.assertNotIn("70", resp.text)
        self.assertNotIn("Error 70", resp.text)
        # Must not expose chain of thought
        self.assertNotIn("chain of thought", resp.text.lower())
        self.assertNotIn("the rule says", resp.text.lower())

    def test_02_vague_symptom_arabic(self):
        """
        Vague symptom in Egyptian Arabic: 'العداد مش شغال'
        Must clarify in Arabic with at most one question.
        """
        resp = self.agent.process_message("العداد مش شغال")
        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertLessEqual(resp.text.count("؟") + resp.text.count("?"), 1)
        # Arabic response
        self.assertTrue(any(w in resp.text for w in ["الشاشة", "كود", "المشكلة", "توضيح", "العداد"]))

    def test_03_display_symptom(self):
        """
        Display symptom: 'meter screen is blank'
        Clarification must focus on display/screen.
        """
        resp = self.agent.process_message("meter screen is blank")
        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertTrue(any(w in resp.text.lower() for w in ["screen", "display", "blank", "symbols"]))

    def test_04_communication_symptom(self):
        """
        Communication symptom: 'meter cannot communicate'
        Clarification must focus on communication interface or error.
        """
        resp = self.agent.process_message("meter cannot communicate")
        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertTrue(any(w in resp.text.lower() for w in ["communication", "interface", "port", "optical", "rs485", "modem"]))

    def test_05_unspecified_error_symptom(self):
        """
        Unspecified error: 'meter shows an error'
        Clarification must ask for the specific error code or message.
        """
        resp = self.agent.process_message("meter shows an error")
        self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertTrue(any(w in resp.text.lower() for w in ["code", "message", "display", "error"]))

    def test_06_exact_error_70(self):
        """
        Exact verified error: 'meter shows error 70'
        Answers directly with Error 70 definition from verified documentation.
        """
        resp = self.agent.process_message("meter shows error 70")
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("lead seal", resp.text.lower())
        self.assertIn("70", resp.text)

    def test_07_arbitrary_unseen_error_code(self):
        """
        Arbitrary unseen error code: 'meter shows error 383333456789'
        Must be preserved exactly as 383333456789, classified as TECHNICAL_COMPANY,
        not found in KB, and routed to specialist without hallucinating.
        """
        resp = self.agent.process_message("meter shows error 383333456789")
        state = self.agent.get_state()
        self.assertEqual(state.error_code, "383333456789")
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertEqual(state.knowledge_status, "NOT_FOUND")
        self.assertIn("383333456789", resp.text)
        # Must not guess Error 70 or 96
        self.assertNotIn("lead seal", resp.text.lower())
        self.assertNotIn("flash memory", resp.text.lower())

    def test_08_undocumented_feature_inquiry(self):
        """
        Undocumented feature inquiry: 'Does MT174 support quantum telemetry?'
        Must identify knowledge gap and route to specialist without hallucinating.
        """
        resp = self.agent.process_message("Does MT174 support quantum telemetry?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertTrue(
            "not available in the current iskra knowledge base" in resp.text.lower()
            or "documentation currently available" in resp.text.lower()
        )
        self.assertNotIn("yes, mt174 supports quantum", resp.text.lower())

    def test_09_undocumented_procedure_inquiry(self):
        """
        Undocumented procedure: 'How do I configure remote optical baud rate?'
        Must not invent configuration steps.
        """
        resp = self.agent.process_message("How do I configure remote optical baud rate?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        # Either reports not available or provides verified citations without invented steps
        self.assertTrue(
            "not available in the current iskra knowledge base" in resp.text.lower()
            or "documentation currently available" in resp.text.lower()
            or state.l1_status == "Needs L2"
        )

    def test_10_mixed_language_and_typos(self):
        """
        Mixed Arabic/English with typos: 'العداد بيطلع erorr 70 wat does it mean'
        Normalizes typo, identifies Error 70, and answers from KB.
        """
        resp = self.agent.process_message("العداد بيطلع erorr 70 wat does it mean")
        state = self.agent.get_state()
        self.assertEqual(state.error_code, "70")
        self.assertIn("lead seal", resp.text.lower())

    def test_11_multi_turn_dynamic_conversation(self):
        """
        Multi-turn dynamic troubleshooting:
        Turn 1: 'meter not work' -> dynamic clarification.
        Turn 2: 'it shows an error' -> asks for error code.
        Turn 3: '70' -> answers Error 70 from verified documentation.
        """
        r1 = self.agent.process_message("meter not work")
        self.assertEqual(r1.action, AgentAction.ASK_CLARIFICATION)

        r2 = self.agent.process_message("it shows an error")
        self.assertEqual(r2.action, AgentAction.ASK_CLARIFICATION)
        self.assertTrue("code" in r2.text.lower() or "error" in r2.text.lower())

        r3 = self.agent.process_message("70")
        state3 = self.agent.get_state()
        self.assertEqual(state3.error_code, "70")
        self.assertEqual(r3.action, AgentAction.ANSWER)
        self.assertIn("lead seal", r3.text.lower())

    def test_12_frustrated_customer_escalation(self):
        """
        Customer expresses frustration: 'I am so angry, stop asking questions and just help me!'
        Must not ask any questionnaire questions.
        """
        resp = self.agent.process_message("I am so angry, stop asking questions and just help me!")
        self.assertNotEqual(resp.action, AgentAction.ASK_CLARIFICATION)
        self.assertNotIn("?", resp.text)


if __name__ == "__main__":
    unittest.main()
