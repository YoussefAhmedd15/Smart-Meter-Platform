import re
from typing import List, Dict, Any, Optional, Tuple


class EvidenceReranker:
    """
    Reranks candidate knowledge base evidence using multi-factor evaluation:
    - Semantic similarity
    - Exact keyword / concept match
    - Document authority hierarchy
    - Meter model relevance & isolation
    - Tracker penalties for technical questions
    - Chunk coherence and completeness
    """

    AUTHORITY_WEIGHTS = {
        "TECHNICAL_SPECIFICATION": 1.00,
        "TECHNICAL_DESCRIPTION": 0.90,
        "METER_MANUAL": 0.80,
        "HARDWARE": 0.70,
        "COMMUNICATION": 0.60,
        "BROCHURE": 0.50,
        "ERROR_REFERENCE": 0.40,
        "TRACKER": 0.10,
        "L1_SUPPORT": 0.10,
        "L2_SUPPORT": 0.10,
        "HISTORICAL_RECORD": 0.10,
    }

    KNOWN_MODELS = [
        "MT174",
        "ME514",
        "MT514-CT",
        "MT514",
        "MT880",
        "AM550",
        "MT382",
        "ME382",
        "MT372",
    ]

    STOPWORDS = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "can", "could", "should",
        "would", "will", "tell", "explain", "about", "mean", "meaning", "define",
        "definition", "meter", "meters", "iskra", "iskraemeco", "application",
        "اي", "ايه", "ما", "هو", "هي", "ماذا", "هل", "عن", "في", "عداد", "العداد", "عدادات",
        "إسكرا", "اسكرا", "تطبيق", "نظام"
    }

    # Core concepts for technical capability questions
    MEASUREMENT_CONCEPTS = [
        "measure", "measurement", "measured", "measures", "measuring",
        "reading", "readings", "parameter", "parameters", "values", "value",
        "power", "voltage", "current", "energy", "demand", "phase",
        "active power", "reactive power", "apparent energy", "apparent power", "power factor",
        "unbalance", "average power", "mppul", "instantaneous",
        "يقيس", "قياس", "بيقيس", "قراءة", "قراءات", "القراءات", "طاقة", "جهد", "تيار", "قدرة", "استهلاك", "بيطلع", "يطلع", "بيسجل", "قيم"
    ]

    COMMUNICATION_CONCEPTS = [
        "protocol", "communication", "dlms", "cosem", "iec", "baud",
        "optical", "rs485", "port", "sms", "gprs", "modem", "interface", "اتصال", "بروتوكول", "واجهة"
    ]

    def detect_target_model(self, query: str) -> Optional[str]:
        """Detect if the user query explicitly mentions a meter model."""
        q_upper = query.upper()
        for model in sorted(self.KNOWN_MODELS, key=len, reverse=True):
            clean_model = model.replace("-", r"[\s\-_]?")
            pattern = rf"\b{clean_model}\b"
            if re.search(pattern, q_upper):
                return model
        return None

    def compute_authority_score(self, metadata: Dict[str, Any]) -> float:
        """
        Calculate document authority score according to the strict ISKRA hierarchy:
        1. Technical Specification (1.00)
        2. Technical Description (0.90)
        3. Meter Manual (0.80)
        4. Hardware documentation (0.70)
        5. Communication documentation (0.60)
        6. Brochure (0.50)
        7. Error Reference (0.40)
        8. L1/L2/Tracker records (0.10)
        """
        if metadata.get("is_tracker", False):
            return 0.10

        source = (metadata.get("source") or "").lower()
        doc_types_str = metadata.get("document_types") or metadata.get("document_type") or ""
        doc_types = [t.strip().upper() for t in doc_types_str.split(",") if t.strip()]

        if "technical specification" in source or "technical_specification" in source or "specs" in source:
            doc_types.append("TECHNICAL_SPECIFICATION")
        if "technical description" in source or "technical_description" in source:
            doc_types.append("TECHNICAL_DESCRIPTION")
        if "manual" in source or "mt174.pdf" in source or "me514.pdf" in source:
            doc_types.append("METER_MANUAL")
        if "installation" in source or "hardware" in source:
            doc_types.append("HARDWARE")
        if "tracker" in source or ".xlsx" in source or "l1" in source or "l2" in source:
            doc_types.append("TRACKER")

        best_score = 0.30
        for dt in doc_types:
            score = self.AUTHORITY_WEIGHTS.get(dt, 0.30)
            if score > best_score:
                best_score = score

        return best_score

    def compute_concept_match_score(self, text: str, query: str) -> float:
        """
        Evaluate concept matching against the user question.
        Rewards direct capability expressions like "meter measure...", "can measure...".
        """
        text_lower = text.lower()
        query_lower = query.lower()

        score = 0.0

        # Check measurement queries (English & Arabic)
        is_measurement_q = any(
            w in query_lower
            for w in [
                "measure", "measurement", "measuring", "measures", "reading", "readings",
                "parameter", "parameters", "quantities", "values", "produce", "instantaneous",
                "يقيس", "قياس", "بيقيس", "قراءة", "قراءات", "القراءات", "بيطلع", "يطلع", "بيطلعلي", "يسجل", "بيسجل", "قيم"
            ]
        )
        if is_measurement_q:
            # Exact capability expressions
            if any(p in text_lower for p in ["meter measure", "meters measure", "meter can measure"]):
                score += 0.55
            elif re.search(r"\bmeasures?\s+(?:each|the|all|total|voltage|active|current)\b", text_lower):
                score += 0.40
            elif any(p in text_lower for p in ["measurement function", "instantaneous parameters", "instantaneous values"]):
                score += 0.45
            elif any(w in text_lower for w in ["measure", "measuring", "measurement", "readings", "parameters"]):
                score += 0.25

            # Bonus for physical quantities and technical terms
            found_concepts = sum(1 for c in self.MEASUREMENT_CONCEPTS if c in text_lower)
            concept_bonus = min(found_concepts * 0.05, 0.40)
            score += concept_bonus

            return min(score, 1.0)

        # Check communication queries
        is_comm_q = any(w in query_lower for w in ["protocol", "communication", "اتصال", "بروتوكول"])
        if is_comm_q:
            found_concepts = sum(1 for c in self.COMMUNICATION_CONCEPTS if c in text_lower)
            return min(found_concepts * 0.15, 1.0)

        # Check specific technical terms like "vending"
        if "vending" in query_lower:
            if "vending" in text_lower:
                return 0.80
            return 0.0

        # General lexical overlap excluding stopwords
        q_tokens = [w for w in re.findall(r"\w+", query_lower) if len(w) > 2 and w not in self.STOPWORDS]
        if not q_tokens:
            return 0.0
        overlap = sum(1 for t in q_tokens if t in text_lower)
        return min(overlap / len(q_tokens), 1.0)

    def compute_model_alignment_score(self, chunk_model: Optional[str], target_model: Optional[str]) -> float:
        """
        Score model relevance:
        - If target_model specified: +1.0 for match, -1.0 for mismatch.
        - If no target_model: neutral (0.0).
        """
        if not target_model:
            return 0.0

        if not chunk_model:
            return 0.0

        chunk_m = chunk_model.upper().replace("-", "")
        target_m = target_model.upper().replace("-", "")

        if target_m in chunk_m or chunk_m in target_m:
            return 1.0
        else:
            return -1.0

    def compute_coherence_score(self, text: str) -> float:
        """Penalize tiny slide fragments and reward coherent descriptive paragraphs."""
        cleaned = text.strip()
        length = len(cleaned)
        if length < 40:
            return 0.10
        if length < 100:
            return 0.40
        if any(punct in cleaned for punct in [".", ";", ":", "\n"]):
            return 1.00
        return 0.70

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 3,
        isolate_models: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Reranks candidates and enforces model isolation so unrelated meter models
        are not blended together in the final selected evidence.
        """
        if not candidates:
            return []

        target_model = self.detect_target_model(query)
        scored_candidates = []

        is_technical_q = any(
            w in query.lower() for w in [
                "measure", "measurement", "protocol", "spec", "specification",
                "hardware", "wire", "voltage", "current", "energy", "يقيس", "قياس"
            ]
        )

        for item in candidates:
            meta = item.get("metadata", {})
            text = item.get("matched_line") or item.get("text") or item.get("document", "")

            # 1. Semantic Similarity
            dist = item.get("distance", 0.5)
            semantic_sim = max(0.0, 1.0 - (dist / 1.5))

            # Exact error matches get top priority
            if item.get("evidence_type") == "exact-error-code":
                scored_candidates.append({
                    **item,
                    "rerank_score": 2.0,
                    "authority_score": 1.0,
                    "concept_score": 1.0,
                    "semantic_sim": 1.0,
                    "target_model": target_model,
                })
                continue

            # 2. Authority Score
            authority_score = self.compute_authority_score(meta)

            # Tracker penalty for technical capability/spec questions
            if is_technical_q and meta.get("is_tracker", False):
                authority_score = 0.05

            # 3. Concept Match Score
            concept_score = self.compute_concept_match_score(text, query)

            # 4. Model Alignment Score
            chunk_model = meta.get("meter_model")
            model_score = self.compute_model_alignment_score(chunk_model, target_model)

            # 5. Coherence
            coherence = self.compute_coherence_score(text)

            # Multi-factor score
            final_score = (
                semantic_sim * 0.25
                + concept_score * 0.35
                + authority_score * 0.25
                + model_score * 0.10
                + coherence * 0.05
            )

            scored_candidates.append({
                **item,
                "rerank_score": final_score,
                "authority_score": authority_score,
                "concept_score": concept_score,
                "semantic_sim": semantic_sim,
                "target_model": target_model,
            })

        # Sort by rerank score descending
        scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        if not isolate_models or not scored_candidates:
            return scored_candidates[:top_k]

        # MODEL CONTEXT RULE: Enforce Model Isolation
        # If target model is specified, filter strictly to that model (or general chunks)
        if target_model:
            model_clean = target_model.upper().replace("-", "")
            filtered = []
            for item in scored_candidates:
                m = (item.get("metadata", {}).get("meter_model") or "").upper().replace("-", "")
                if not m or model_clean in m or m in model_clean:
                    filtered.append(item)
            return filtered[:top_k] if filtered else scored_candidates[:top_k]

        # If user did NOT specify a model (e.g. "What can the meter measure?"):
        # Select the single best-scoring source document / model family.
        # Do NOT merge MT174 + ME514 chunks into the same selected evidence!
        top_chunk = scored_candidates[0]
        top_source = top_chunk.get("metadata", {}).get("source")
        top_model = top_chunk.get("metadata", {}).get("meter_model")

        isolated_results = [top_chunk]
        for item in scored_candidates[1:]:
            item_source = item.get("metadata", {}).get("source")
            item_model = item.get("metadata", {}).get("meter_model")

            # Allow chunk if from the same document OR same model family
            if item_source == top_source:
                isolated_results.append(item)
            elif not top_model or not item_model:
                isolated_results.append(item)
            elif top_model.upper().split("-")[0] == item_model.upper().split("-")[0]:
                isolated_results.append(item)
            # Disjoint models (e.g. ME514 vs MT174) are strictly excluded!

            if len(isolated_results) >= top_k:
                break

        return isolated_results

    def classify_evidence_status(self, query: str, evidence: List[Dict[str, Any]]) -> str:
        """
        Classifies evidence state:
        - VERIFIED_ANSWER: Directly supports the requested claim from authoritative docs.
        - CONTEXT_AVAILABLE: Mentions related terms/logs without formal specification.
        - NOT_FOUND: No relevant evidence found.
        """
        if not evidence:
            return "NOT_FOUND"

        # Check error code queries (arbitrary digits, e.g. 70, 96, 0101, 0108)
        err_match = re.search(r"(?:error|خطأ|كود|eror|err)\s*[:#\-]?\s*(\d+)\b", query, flags=re.IGNORECASE)
        if not err_match and any(w in query.lower() for w in ["error", "code", "خطأ", "كود", "show"]):
            pure = re.search(r"\b(\d+)\b", query)
            if pure:
                err_match = pure

        if err_match:
            code = err_match.group(1).strip()
            norm_code = code.lstrip("0") or "0"
            has_exact = any(e.get("evidence_type") == "exact-error-code" and bool(e.get("matched_line")) for e in evidence)
            has_error_def = False
            for e in evidence:
                txt = (e.get("matched_line") or e.get("text") or "")
                if "\ufffd" in txt:
                    continue
                # Must be defined as an error code with descriptive words (at least 2 explanatory words)
                if re.search(rf"\b(?:error|err|code|كود|خطأ)\s*[:#\-]?\s*0*{norm_code}\b\s+[A-Za-z\u0600-\u06FF]{{2,}}", txt, re.IGNORECASE):
                    has_error_def = True
                    break
                if re.search(rf"(?:^|\n)\s*0*{norm_code}\s+[A-Za-z\u0600-\u06FF]{{2,}}", txt):
                    has_error_def = True
                    break
            if not has_exact and not has_error_def:
                return "NOT_FOUND"
            return "VERIFIED_ANSWER"

        top = evidence[0]
        score = top.get("rerank_score", 0.0)
        ev_type = top.get("evidence_type", "")
        meta = top.get("metadata", {})
        is_tracker = meta.get("is_tracker", False)

        if ev_type == "exact-error-code":
            return "VERIFIED_ANSWER"

        # Check for terms that only exist in tracker logs without formal definition (e.g. Vending)
        q_lower = query.lower()
        if "vending" in q_lower or any(t in q_lower for t in ["smart meter", "عداد ذكي", "العداد الذكي"]):
            return "CONTEXT_AVAILABLE"

        # If score is too low or only tracker for technical question
        if score < 0.28:
            return "NOT_FOUND"

        if is_tracker:
            return "CONTEXT_AVAILABLE"

        concept_score = top.get("concept_score", 0.0)
        semantic_sim = top.get("semantic_sim", 0.0)
        if concept_score >= 0.20 or (semantic_sim >= 0.55 and not is_tracker):
            return "VERIFIED_ANSWER"

        return "CONTEXT_AVAILABLE"
