import unittest
from ai_training.agent.agent import L1Agent
from ai_training.agent.response import ResponseGenerator
from ai_training.agent.policy import (
    KnowledgePolicy,
    DOMAIN_TECHNICAL_COMPANY,
    DOMAIN_GENERAL_NON_TECHNICAL,
    MISSING_TECHNICAL_INFO_EN,
    MISSING_TECHNICAL_INFO_AR,
)
from ai_training.agent.models import AgentAction


class TestKnowledgePolicy(unittest.TestCase):
    """
    Test suite verifying strict enforcement of the
    TECHNICAL vs GENERAL KNOWLEDGE POLICY.
    """

    def setUp(self):
        # Use deterministic responses for fast, reproducible testing
        self.agent = L1Agent(response_generator=ResponseGenerator(use_ollama=False))

    def test_example_1_what_can_the_meter_measure(self):
        """
        Example 1:
        User: 'What can the meter measure?'
        Policy: Technical/company/product information -> Search KB -> KB ONLY.
        """
        resp = self.agent.process_message("What can the meter measure?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("verified iskra technical documentation", resp.text.lower())
        has_me514 = "me514" in resp.text.lower()
        has_mt174 = "mt174" in resp.text.lower()
        self.assertTrue(has_me514 ^ has_mt174, "Must answer strictly from a single model without blending (either ME514 or MT174, not both)")

    def test_example_2_what_does_login_mean(self):
        """
        Example 2:
        User: 'What does login mean?'
        Policy: General concept -> General knowledge is allowed.
        """
        resp = self.agent.process_message("What does login mean?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_GENERAL_NON_TECHNICAL)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("access", resp.text.lower())
        self.assertIn("password", resp.text.lower())

    def test_example_3_what_login_system_does_iskra_use(self):
        """
        Example 3:
        User: 'What login system does ISKRA use?'
        Policy: Context changes rule -> Company-specific -> KB ONLY.
        Not in KB -> Say not available in current ISKRA knowledge base.
        """
        resp = self.agent.process_message("What login system does ISKRA use?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("not available in the current iskra knowledge base", resp.text.lower())

    def test_example_4_what_is_tcp_ip(self):
        """
        Example 4:
        User: 'What is TCP/IP?'
        Policy: General networking concept -> General knowledge is allowed.
        """
        resp = self.agent.process_message("What is TCP/IP?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_GENERAL_NON_TECHNICAL)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("protocol", resp.text.lower())
        self.assertIn("network", resp.text.lower())

    def test_example_5_which_communication_protocol_does_mt174_use(self):
        """
        Example 5:
        User: 'Which communication protocol does MT174 use?'
        Policy: Technical/product-specific -> KB ONLY.
        """
        resp = self.agent.process_message("Which communication protocol does MT174 use?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("iec 62056-21", resp.text.lower())
        self.assertIn("mode c", resp.text.lower())

    def test_example_6_what_is_an_api(self):
        """
        Example 6:
        User: 'What is an API?'
        Policy: General concept -> General knowledge is allowed.
        """
        resp = self.agent.process_message("What is an API?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_GENERAL_NON_TECHNICAL)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("application programming interface", resp.text.lower())

    def test_example_7_which_api_does_the_iskra_application_use(self):
        """
        Example 7:
        User: 'Which API does the ISKRA application use?'
        Policy: Context changes rule -> Company/product-specific -> KB ONLY.
        Not in KB -> Say not available in current ISKRA knowledge base.
        """
        resp = self.agent.process_message("Which API does the ISKRA application use?")
        state = self.agent.get_state()
        self.assertEqual(state.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertEqual(resp.action, AgentAction.ANSWER)
        self.assertIn("not available in the current iskra knowledge base", resp.text.lower())

    def test_arabic_policy_examples(self):
        """
        Verify that policy applies equivalently in Arabic.
        """
        # Arabic technical inquiry (measurements)
        r1 = self.agent.process_message("ماذا يقيس العداد؟")
        s1 = self.agent.get_state()
        self.assertEqual(s1.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertTrue("الوثائق الفنية المعتمدة" in r1.text or "Voltage" in r1.text or "القياسات" in r1.text)

        # Arabic general inquiry (login)
        self.agent.reset()
        r2 = self.agent.process_message("يعني ايه login؟")
        s2 = self.agent.get_state()
        self.assertEqual(s2.question_domain, DOMAIN_GENERAL_NON_TECHNICAL)
        self.assertIn("تسجيل الدخول", r2.text)

        # Arabic company inquiry missing in KB
        self.agent.reset()
        r3 = self.agent.process_message("ما هو نظام تسجيل الدخول الخاص بإسكرا؟")
        s3 = self.agent.get_state()
        self.assertEqual(s3.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertIn("غير متوفرة في قاعدة معرفة إسكرا الحالية", r3.text)

        # Arabic general inquiry (API)
        self.agent.reset()
        r4 = self.agent.process_message("يعني ايه API؟")
        s4 = self.agent.get_state()
        self.assertEqual(s4.question_domain, DOMAIN_GENERAL_NON_TECHNICAL)
        self.assertIn("واجهة برمجة التطبيقات", r4.text)

        # Arabic company API inquiry missing in KB
        self.agent.reset()
        r5 = self.agent.process_message("ما هو الـ API المستخدم في تطبيق إسكرا؟")
        s5 = self.agent.get_state()
        self.assertEqual(s5.question_domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertIn("غير متوفرة في قاعدة معرفة إسكرا الحالية", r5.text)

    def test_rule_d_when_in_doubt_prefer_technical(self):
        """
        Rule D: When in doubt, prefer safer behavior (TECHNICAL_COMPANY).
        """
        domain, reason = KnowledgePolicy.classify_domain("How does the terminal relay connect?")
        self.assertEqual(domain, DOMAIN_TECHNICAL_COMPANY)
        self.assertIn("hardware", reason.lower())


if __name__ == "__main__":
    unittest.main()
