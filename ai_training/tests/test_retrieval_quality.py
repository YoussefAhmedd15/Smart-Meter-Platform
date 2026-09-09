# import unittest
# import re
# from ai_training.rag.retriever import HybridRetriever
# from ai_training.rag.reranker import EvidenceReranker
# from ai_training.agent.agent import L1Agent
# from ai_training.agent.models import AgentIntent


# class TestRetrievalQuality(unittest.TestCase):
#     """
#     Retrieval Quality & Grounding Verification Test Suite:
#     - Verifies expected source documents appear in top results.
#     - Verifies irrelevant meter models are penalized and isolated.
#     - Verifies tracker records do not outrank technical documentation.
#     - Verifies answers are strictly grounded in selected evidence.
#     - Verifies all 7 required evaluation cases.
#     """

#     @classmethod
#     def setUpClass(cls):
#         cls.retriever = HybridRetriever()
#         cls.reranker = EvidenceReranker()
#         cls.agent = L1Agent(retriever=cls.retriever)
#         cls.agent.response_generator.use_ollama = False

#     def setUp(self):
#         self.agent.reset()

#     # ============================================================
#     # TEST 1: Generic measurement question (no model specified)
#     # ============================================================
#     def test_01_generic_meter_measure_retrieval_and_isolation(self):
#         """
#         Case 1: "What can the meter measure?"
#         Expected:
#         - Retrieves authoritative technical documentation.
#         - Tracker chunks do NOT outrank technical documentation.
#         - Does NOT combine unrelated meter models (MT174 + ME514).
#         - Grounded answer does not contain unsupported measurements.
#         """
#         query = "What can the meter measure?"
#         evidence = self.retriever.search(query, top_k=3, isolate_models=True)

#         self.assertTrue(len(evidence) > 0, "Should retrieve at least one evidence chunk")
#         top_ev = evidence[0]
#         meta = top_ev.get("metadata", {})

#         # Document authority check: must be technical documentation (not tracker)
#         self.assertFalse(meta.get("is_tracker", False), "Top chunk must NOT be a tracker record")
#         auth_score = self.reranker.compute_authority_score(meta)
#         self.assertGreaterEqual(auth_score, 0.70, "Must be authoritative technical documentation")

#         # Model isolation check: all returned chunks must be from the same model family / document
#         models = [e.get("metadata", {}).get("meter_model") for e in evidence if e.get("metadata", {}).get("meter_model")]
#         if len(models) >= 2:
#             model_families = set(m.split("-")[0].upper() for m in models)
#             self.assertEqual(
#                 len(model_families), 1,
#                 f"Evidence chunks must NOT blend disjoint meter models: found {models}"
#             )

#         # Agent answer check
#         resp = self.agent.process_message(query)
#         self.assertIsNotNone(resp.text)
#         self.assertTrue(len(resp.text) > 20)

#         # Test G: Model scope clarification & ME514 evidence
#         resp_lower = resp.text.lower()
#         self.assertTrue(
#             "model-specific" in resp_lower or "not universal" in resp_lower or "rather than a single universal" in resp_lower,
#             "Must clarify that measurements are model-specific rather than universal across all models"
#         )
#         self.assertIn("me514", resp_lower, "Must reference ME514 as the supported evidence")
#         self.assertNotIn("mt174", resp_lower, "Must NOT blend MT174 into generic ME514 answer")

#     # ============================================================
#     # TEST 2: Model-specific question - MT174
#     # ============================================================
#     def test_02_mt174_measure_model_context_rule(self):
#         """
#         Case 2: "What can MT174 measure?"
#         Expected:
#         - MT174 evidence only/primarily.
#         - ME514 evidence is penalized and excluded.
#         - Answer reflects MT174 documentation.
#         """
#         query = "What can MT174 measure?"
#         evidence = self.retriever.search(query, top_k=2, isolate_models=True)

#         self.assertTrue(len(evidence) > 0)
#         top_m = evidence[0].get("metadata", {})
#         self.assertEqual(top_m.get("meter_model"), "MT174", "Top evidence must be from MT174")

#         # Ensure ME514 is not in results
#         for e in evidence:
#             m = e.get("metadata", {}).get("meter_model", "")
#             self.assertNotIn("ME514", m, "ME514 must be penalized when asking about MT174")

#         resp = self.agent.process_message(query)
#         self.assertIn("MT174", resp.text)
#         self.assertNotIn("ME514", resp.text)

#     # ============================================================
#     # TEST 3: Model-specific question - ME514 (Test B)
#     # ============================================================
#     def test_03_me514_measure_model_context_rule(self):
#         """
#         Test B: "What can ME514 measure?"
#         Expected:
#         - ME514 evidence only/primarily.
#         - MT174 evidence is penalized and excluded.
#         - Synthesizes Section 6.1 (active energy) and Section 6.4 (voltage, current, active power, power factor, instantaneous).
#         - Must NOT contain unrelated MT174-specific claims.
#         """
#         query = "What can ME514 measure?"
#         evidence = self.retriever.search(query, top_k=5, isolate_models=True)

#         self.assertTrue(len(evidence) > 0)
#         top_m = evidence[0].get("metadata", {})
#         self.assertIn("ME514", top_m.get("meter_model", ""), "Top evidence must be from ME514")

#         # Ensure MT174 is not in results
#         for e in evidence:
#             m = e.get("metadata", {}).get("meter_model", "")
#             self.assertNotIn("MT174", m, "MT174 must be penalized when asking about ME514")

#         resp = self.agent.process_message(query)
#         resp_lower = resp.text.lower()
#         self.assertIn("me514", resp_lower)
#         self.assertNotIn("mt174", resp_lower)

#         # Multi-chunk synthesis checks across Section 6.1 and Section 6.4
#         self.assertIn("active energy", resp_lower)
#         self.assertIn("voltage", resp_lower)
#         self.assertIn("current", resp_lower)
#         self.assertIn("active power", resp_lower)
#         self.assertIn("power factor", resp_lower)

#     # ============================================================
#     # TEST 4: Exact error code explanation - Error 70 (Test D)
#     # ============================================================
#     def test_04_error_70_exact_evidence(self):
#         """
#         Test D: "What does Error 70 mean?"
#         Expected:
#         - Exact Error 70 evidence is retrieved.
#         - Status is VERIFIED_ANSWER.
#         - Answer quotes the exact verified definition without unrelated fragment text.
#         """
#         query = "What does Error 70 mean?"
#         evidence = self.retriever.search(query, top_k=2)

#         self.assertTrue(len(evidence) > 0)
#         self.assertEqual(self.retriever.last_evidence_status, "VERIFIED_ANSWER")

#         resp = self.agent.process_message(query)
#         self.assertIn("The lead seal button is not be pressed", resp.text)
#         self.assertNotIn("mit, at the same time", resp.text)

#     # ============================================================
#     # TEST 4b: Exact error code explanation - Error 96 (Test E)
#     # ============================================================
#     def test_04b_error_96_exact_evidence(self):
#         """
#         Test E: "What does Error 96 mean?"
#         Expected:
#         - Exact Error 96 evidence is retrieved.
#         - Status is VERIFIED_ANSWER.
#         - Answer quotes the exact verified definition ("The firmware of old meter is too old").
#         - Must NOT contain unrelated fragment text.
#         """
#         query = "What does Error 96 mean?"
#         evidence = self.retriever.search(query, top_k=2)

#         self.assertTrue(len(evidence) > 0)
#         self.assertEqual(self.retriever.last_evidence_status, "VERIFIED_ANSWER")

#         resp = self.agent.process_message(query)
#         self.assertIn("The firmware of old meter is too old", resp.text)
#         self.assertNotIn("mit, at the same time", resp.text)

#     # ============================================================
#     # TEST 5: Context-available query - Vending (Test C)
#     # ============================================================
#     def test_05_vending_context_available(self):
#         """
#         Test C: "What is Vending?"
#         Expected:
#         - Status is CONTEXT_AVAILABLE.
#         - Explicitly distinguishes operational context from formal technical definition.
#         """
#         query = "What is Vending?"
#         evidence = self.retriever.search(query, top_k=2)
#         status = self.retriever.last_evidence_status

#         self.assertEqual(status, "CONTEXT_AVAILABLE", "Vending should be classified as CONTEXT_AVAILABLE")

#         resp = self.agent.process_message(query)
#         resp_lower = resp.text.lower()
#         self.assertIn("vending", resp_lower)
#         self.assertTrue(
#             "card/token" in resp_lower or "prepayment software" in resp_lower or "operational" in resp_lower,
#             "Must explain operational context (card/token workflows or prepayment software)"
#         )
#         self.assertTrue(
#             "does not contain a formal" in resp_lower or "no formal" in resp_lower,
#             "Must state that KB does not contain a formal technical definition"
#         )

#     # ============================================================
#     # TEST 6: Non-existent error code - Error 999 (Test F)
#     # ============================================================
#     def test_06_error_999_zero_hallucination(self):
#         """
#         Test F: "What is Error 999?"
#         Expected:
#         - Status is NOT_FOUND.
#         - No hallucination: clearly informs the user that Error 999 is not in verified documentation.
#         - Does NOT match 999.99 kW or other unrelated numbers.
#         """
#         query = "What is Error 999?"
#         evidence = self.retriever.search(query, top_k=2)
#         status = self.retriever.last_evidence_status

#         self.assertEqual(status, "NOT_FOUND", "Error 999 must have status NOT_FOUND")
#         self.assertEqual(len(evidence), 0, "No evidence chunks should be returned for non-existent error")

#         resp = self.agent.process_message(query)
#         self.assertTrue(
#             "not found" in resp.text.lower() or "could not find" in resp.text.lower(),
#             "Agent must state that Error 999 was not found in verified documentation"
#         )
#         self.assertNotIn("999.99", resp.text, "Must not match 999.99 kW")

#     # ============================================================
#     # TEST 7: Arabic measurement query (Test H)
#     # ============================================================
#     def test_07_arabic_measurement_query_retrieval(self):
#         """
#         Test H: "هو العداد بيقيس ايه؟"
#         Expected:
#         - Same grounded behavior as "What can the meter measure?".
#         - Clarifies model scope in Arabic (ME514).
#         - Does NOT blend disjoint meter models.
#         - Responds in Arabic with strictly grounded measurement claims.
#         """
#         query = "هو العداد بيقيس ايه؟"
#         evidence = self.retriever.search(query, top_k=5, isolate_models=True)

#         self.assertTrue(len(evidence) > 0)
#         top_ev = evidence[0]
#         meta = top_ev.get("metadata", {})
#         self.assertFalse(meta.get("is_tracker", False), "Must not be a tracker chunk")

#         resp = self.agent.process_message(query)
#         self.assertEqual(resp.action.value, "ANSWER")
#         self.assertTrue("تختلف بحسب موديل العداد" in resp.text or "ليست قائمة موحدة" in resp.text)
#         self.assertIn("ME514", resp.text)
#         self.assertTrue(any(c in resp.text for c in ["الجهد", "التيار", "القدرة", "الطاقة"]))

#     # ============================================================
#     # TEST 8: Document Authority Hierarchy
#     # ============================================================
#     def test_08_document_authority_hierarchy(self):
#         """
#         Verifies the strict authority hierarchy:
#         Technical Specification (1.00) > Technical Description (0.90) >
#         Meter Manual (0.80) > Hardware (0.70) > Communication (0.60) >
#         Brochure (0.50) > Error Reference (0.40) > Tracker (0.10).
#         """
#         spec_score = self.reranker.compute_authority_score({"document_types": "TECHNICAL_SPECIFICATION", "is_tracker": False})
#         desc_score = self.reranker.compute_authority_score({"document_types": "TECHNICAL_DESCRIPTION", "is_tracker": False})
#         manual_score = self.reranker.compute_authority_score({"document_types": "METER_MANUAL", "is_tracker": False})
#         hw_score = self.reranker.compute_authority_score({"document_types": "HARDWARE", "is_tracker": False})
#         comm_score = self.reranker.compute_authority_score({"document_types": "COMMUNICATION", "is_tracker": False})
#         brochure_score = self.reranker.compute_authority_score({"document_types": "BROCHURE", "is_tracker": False})
#         err_score = self.reranker.compute_authority_score({"document_types": "ERROR_REFERENCE", "is_tracker": False})
#         tracker_score = self.reranker.compute_authority_score({"document_types": "TRACKER", "is_tracker": True})

#         self.assertEqual(spec_score, 1.00)
#         self.assertEqual(desc_score, 0.90)
#         self.assertEqual(manual_score, 0.80)
#         self.assertEqual(hw_score, 0.70)
#         self.assertEqual(comm_score, 0.60)
#         self.assertEqual(brochure_score, 0.50)
#         self.assertEqual(err_score, 0.40)
#         self.assertEqual(tracker_score, 0.10)

#         # Confirm strict monotonicity
#         self.assertGreater(spec_score, desc_score)
#         self.assertGreater(desc_score, manual_score)
#         self.assertGreater(manual_score, hw_score)
#         self.assertGreater(hw_score, comm_score)
#         self.assertGreater(comm_score, brochure_score)
#         self.assertGreater(brochure_score, err_score)
#         self.assertGreater(err_score, tracker_score)

#     # ============================================================
#     # TEST 9: Grounding Verification strips unsupported claims
#     # ============================================================
#     def test_09_grounding_verification_strips_unsupported_claims(self):
#         """
#         Verifies that _verify_grounding strips technical measurement claims
#         (e.g. voltage, current, reactive energy) when not supported by evidence.
#         """
#         # Simulated evidence containing only average power and unbalance
#         evidence = [{
#             "text": "Meter measure each phase average power. If the maximum phase deducts the minimum one exceeded the power unbalance limit...",
#             "metadata": {"source": "MT514-CT_Technical Description pdf.pdf", "is_tracker": False}
#         }]

#         # Draft answer containing both supported and unsupported claims
#         draft_answer = (
#             "According to the documentation, the meter supports:\n"
#             "- each phase average power (monitoring phase power unbalance against programmable limits).\n"
#             "- voltage and current.\n"
#             "- reactive energy and apparent energy."
#         )

#         verified = self.agent.response_generator._verify_grounding(draft_answer, evidence)

#         self.assertIn("each phase average power", verified)
#         self.assertNotIn("voltage and current", verified, "Unsupported voltage/current must be stripped")
#         self.assertNotIn("reactive energy", verified, "Unsupported reactive energy must be stripped")

#     # ============================================================
#     # TEST 10: MPPUL Alarm Passage Extraction (Test A)
#     # ============================================================
#     def test_10_mppul_alarm_extraction(self):
#         """
#         Test A: "What is the phase power unbalance alarm?"
#         Expected:
#         - Extracts actual 4.10 MPPUL alarm evidence.
#         - Must contain: MPPUL, phase average power, power unbalance limit, LCD alarm symbol.
#         - Must NOT contain: "mit, at the same time".
#         - Does NOT invent repair or diagnostic procedures.
#         """
#         query = "What is the phase power unbalance alarm?"
#         evidence = self.retriever.search(query, top_k=2)

#         self.assertTrue(len(evidence) > 0)
#         self.assertEqual(self.retriever.last_evidence_status, "VERIFIED_ANSWER")

#         resp = self.agent.process_message(query)
#         resp_lower = resp.text.lower()

#         # Required semantic concepts
#         self.assertIn("mppul", resp_lower)
#         self.assertIn("phase average power", resp_lower)
#         self.assertIn("power unbalance limit", resp_lower)
#         self.assertIn("lcd alarm symbol", resp_lower)

#         # Discarded fragment noise check
#         self.assertNotIn("mit, at the same time", resp_lower)
#         self.assertNotIn("mit, at the same", resp_lower)

#     # ============================================================
#     # TEST 11: Communication Protocol MT174 (Test I)
#     # ============================================================
#     def test_11_communication_protocol_mt174(self):
#         """
#         Test I: "What communication protocol does MT174 use?"
#         Expected:
#         - Returns MT174 communication evidence (IEC 62056-21 mode C).
#         - Does NOT mix unrelated models (e.g. ME514).
#         """
#         query = "What communication protocol does MT174 use?"
#         evidence = self.retriever.search(query, top_k=2, isolate_models=True)

#         self.assertTrue(len(evidence) > 0)
#         top_m = evidence[0].get("metadata", {})
#         self.assertEqual(top_m.get("meter_model"), "MT174")

#         resp = self.agent.process_message(query)
#         resp_lower = resp.text.lower()
#         self.assertIn("mt174", resp_lower)
#         self.assertIn("iec 62056-21", resp_lower)
#         self.assertIn("mode c", resp_lower)
#         self.assertNotIn("me514", resp_lower)

#     # ============================================================
#     # TEST 12: Procedure Grounding Refusal (Test J)
#     # ============================================================
#     def test_12_procedure_grounding_refusal(self):
#         """
#         Test J: Ask for a procedure when no documented procedure exists.
#         Expected:
#         - Agent does NOT invent a procedure.
#         - States that no procedure/information is available in documentation.
#         """
#         query = "What is the procedure to calibrate the ME514 meter?"
#         resp = self.agent.process_message(query)
#         resp_lower = resp.text.lower()

#         self.assertTrue(
#             "does not contain" in resp_lower or "not available" in resp_lower or "no authorized" in resp_lower or "does not provide" in resp_lower,
#             "Agent must state that procedure/information is not available in the knowledge base"
#         )
#         # Verify no invented steps
#         self.assertNotIn("step 1", resp_lower)
#         self.assertNotIn("press button", resp_lower)
#         self.assertNotIn("unscrew", resp_lower)

#         # Also test repair procedure refusal for an error code
#         query2 = "How do I repair Error 70?"
#         resp2 = self.agent.process_message(query2)
#         resp2_lower = resp2.text.lower()
#         self.assertTrue(
#             "does not provide" in resp2_lower or "not available" in resp2_lower,
#             "Agent must not invent an L1 repair procedure"
#         )
#         self.assertIn("l1 review", resp2_lower)



# if __name__ == "__main__":
#     unittest.main()

