# import unittest
# import sys
# from pathlib import Path

# PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# AI_TRAINING_DIR = PROJECT_ROOT / "ai_training"
# for p in [str(PROJECT_ROOT), str(AI_TRAINING_DIR)]:
#     if p not in sys.path:
#         sys.path.insert(0, p)

# from ai_training.agent.agent import L1Agent
# from ai_training.agent.conversation import ConversationManager
# from ai_training.agent.normalizer import TextNormalizer
# from ai_training.agent.models import AgentIntent, AgentAction, CaseState


# class TestTypoHandling(unittest.TestCase):
#     """
#     Regression test suite for typo, spelling, grammar, informal language,
#     and mixed Arabic/English normalization.
#     """

#     def setUp(self):
#         self.agent = L1Agent()
#         self.manager = ConversationManager(agent=self.agent)

#     # ------------------------------------------------------------
#     # TEST A: erorr 70
#     # # ------------------------------------------------------------
#     # def test_A_erorr_70(self):
#     #     """User types 'erorr 70'; agent must normalize to Error 70 and retrieve verified definition."""
#     #     self.manager.start_new_case()
#     #     resp = self.manager.handle_message("erorr 70")
#     #     state = self.manager.get_case_state()

#     #     self.assertEqual(state["known_facts"].get("error_code"), "70")
#     #     self.assertIn("70 The lead seal button is not be pressed", resp.text)
#     #     self.assertNotIn("Did you mean", resp.text)
#     #     self.assertNotIn("correct your spelling", resp.text.lower())

#     # ------------------------------------------------------------
#     # TEST B: what does error 70 mwan
#     # ------------------------------------------------------------
#     # def test_B_what_does_error_70_mwan(self):
#     #     """User types 'what does error 70 mwan'; agent understands as 'what does Error 70 mean'."""
#     #     self.manager.start_new_case()
#     #     resp = self.manager.handle_message("what does error 70 mwan")
#     #     state = self.manager.get_case_state()

#     #     self.assertEqual(state["known_facts"].get("error_code"), "70")
#     #     self.assertEqual(state.get("intent"), AgentIntent.ERROR_EXPLANATION.value)
#     #     self.assertIn("70 The lead seal button is not be pressed", resp.text)

#     # ------------------------------------------------------------
#     # TEST C: meter not wokring
#     # ------------------------------------------------------------
#     def test_C_meter_not_wokring(self):
#         """User types 'meter not wokring'; agent extracts 'meter not working' without penalty."""
#         self.manager.start_new_case()
#         resp = self.manager.handle_message("meter not wokring")
#         state = self.manager.get_case_state()

#         self.assertIn(state["known_facts"].get("issue"), ["meter not working", "not working"])
#         self.assertEqual(resp.action, AgentAction.ASK_CLARIFICATION)

#     # ------------------------------------------------------------
#     # TEST D: the metter is dead
#     # ------------------------------------------------------------
#     def test_D_the_metter_is_dead(self):
#         """User types 'the metter is dead'; agent normalizes to 'the meter is dead' and troubleshoots."""
#         self.manager.start_new_case()
#         resp = self.manager.handle_message("the metter is dead")
#         state = self.manager.get_case_state()

#         self.assertIn(state["known_facts"].get("issue"), ["meter not working", "not working"])
#         self.assertIn(resp.action, [AgentAction.ASK_CLARIFICATION, AgentAction.ANSWER])

#     # ------------------------------------------------------------
#     # TEST E: العداد مش شغال وبيطلع erorr 70
#     # ------------------------------------------------------------
#     def test_E_arabic_with_english_typo(self):
#         """Mixed Arabic/English with typo: 'العداد مش شغال وبيطلع erorr 70'."""
#         self.manager.start_new_case()
#         resp = self.manager.handle_message("العداد مش شغال وبيطلع erorr 70")
#         state = self.manager.get_case_state()

#         self.assertEqual(state["known_facts"].get("error_code"), "70")
#         self.assertIn("70 The lead seal button is not be pressed", resp.text)
#         self.assertIn("الوثائق المعتمدة المتاحة", resp.text)

#     # ------------------------------------------------------------
#     # TEST F: whats happend now
#     # ------------------------------------------------------------
#     def test_F_whats_happend_now(self):
#         """User types 'whats happend now'; agent normalizes to follow-up inquiry."""
#         self.manager.start_new_case()
#         # Prime with an error
#         self.manager.handle_message("Error 70")
#         resp = self.manager.handle_message("whats happend now")
#         state = self.manager.get_case_state()

#         self.assertEqual(state.get("intent"), AgentIntent.FOLLOW_UP.value)
#         self.assertEqual(state["known_facts"].get("error_code"), "70")

#     # ------------------------------------------------------------
#     # TEST G: Error 999 must NOT be converted to another code
#     # ------------------------------------------------------------
#     def test_G_unknown_error_999_preserved(self):
#         """Strict safety: Error 999 must remain 999 and NOT be hallucinated or converted."""
#         self.manager.start_new_case()
#         resp = self.manager.handle_message("Error 999")
#         state = self.manager.get_case_state()

#         self.assertEqual(state["known_facts"].get("error_code"), "999")
#         self.assertIn("999", resp.text)
#         self.assertNotIn("70", resp.text)
#         self.assertNotIn("96", resp.text)
#         self.assertIn("could not find Error 999", resp.text)

#     # ------------------------------------------------------------
#     # TEST H: MT999 must NOT be converted to MT514
#     # ------------------------------------------------------------
#     def test_H_unknown_model_MT999_preserved(self):
#         """Strict safety: MT999 must NOT be converted to MT514 or assumed supported."""
#         normalized = TextNormalizer.normalize("My meter is MT999.")
#         self.assertIn("MT999", normalized)
#         self.assertNotIn("MT514", normalized)

#         self.manager.start_new_case()
#         resp = self.manager.handle_message("My meter is MT999.")
#         state = self.manager.get_case_state()

#         # Model MT999 must not be converted to MT514
#         if state["known_facts"].get("meter_model"):
#             self.assertEqual(state["known_facts"].get("meter_model"), "MT999")

#     # ------------------------------------------------------------
#     # TEST I: Vending must remain Vending
#     # ------------------------------------------------------------
#     def test_I_vending_preserved(self):
#         """Technical term 'Vending' must be strictly preserved."""
#         normalized = TextNormalizer.normalize("What is Vending?")
#         self.assertIn("Vending", normalized)

#         self.manager.start_new_case()
#         resp = self.manager.handle_message("What is Vending?")
#         state = self.manager.get_case_state()

#         self.assertEqual(state.get("intent"), AgentIntent.GENERAL_QUESTION.value)
#         self.assertIn("Vending", resp.text)

#     # ------------------------------------------------------------
#     # TEST J: Contextual typo: Error 70 -> what does it mwan
#     # ------------------------------------------------------------
#     def test_J_contextual_typo(self):
#         """Turn 1: Error 70 -> Turn 2: 'what does it mwan'."""
#         self.manager.start_new_case()
#         self.manager.handle_message("Error 70")
#         resp2 = self.manager.handle_message("what does it mwan")
#         state2 = self.manager.get_case_state()

#         self.assertEqual(state2["known_facts"].get("error_code"), "70")
#         self.assertEqual(state2.get("intent"), AgentIntent.ERROR_EXPLANATION.value)
#         self.assertIn("70 The lead seal button is not be pressed", resp2.text)

#     # ------------------------------------------------------------
#     # TEST K: Mixed language typo: العداد مش شغال وبيطلع erorr 70
#     # ------------------------------------------------------------
#     def test_K_mixed_language_typo(self):
#         """Verify Arabic colloquial typo 'العداد مش شغل' normalizes to 'العداد مش شغال'."""
#         normalized = TextNormalizer.normalize("العداد مش شغل وبيطلع erorr 70")
#         self.assertIn("العداد مش شغال", normalized)
#         self.assertIn("Error 70", normalized)

#         self.manager.start_new_case()
#         resp = self.manager.handle_message("العداد مش شغل وبيطلع erorr 70")
#         state = self.manager.get_case_state()

#         self.assertEqual(state["known_facts"].get("error_code"), "70")
#         self.assertIn("70 The lead seal button is not be pressed", resp.text)

#     # ------------------------------------------------------------
#     # TEST L: Multiple typos in one message
#     # ------------------------------------------------------------
#     def test_L_multiple_typos_in_one_message(self):
#         """Message with multiple typos: 'the metter is not wokring and gives erorr 70 wat does it mwan'."""
#         raw = "the metter is not wokring and gives erorr 70 wat does it mwan"
#         normalized = TextNormalizer.normalize(raw)

#         self.assertIn("meter", normalized)
#         self.assertIn("working", normalized)
#         self.assertIn("Error 70", normalized)
#         self.assertIn("what", normalized)
#         self.assertIn("mean", normalized)

#         self.manager.start_new_case()
#         resp = self.manager.handle_message(raw)
#         state = self.manager.get_case_state()

#         self.assertEqual(state["known_facts"].get("error_code"), "70")
#         self.assertIn("70 The lead seal button is not be pressed", resp.text)
#         # Verify raw user text is preserved in history for audit
#         history = self.manager.agent.memory.history
#         self.assertEqual(history[0]["content"], raw)


# if __name__ == "__main__":
#     unittest.main()
