import re
from typing import List, Dict, Any, Optional


class DirectErrorSearcher:
    """
    Performs deterministic, line-based search for exact error codes
    in the ISKRA smart meter documentation chunks.
    Ensures numbers appearing elsewhere in text are not falsely matched as errors.
    """

    def __init__(self, collection=None):
        self.collection = collection
        self._cached_documents = None
        self._cached_metadatas = None

    def _ensure_cache(self):
        if self._cached_documents is None and self.collection is not None:
            try:
                # Load verified technical and error documentation chunks (is_tracker == False)
                # Official error definitions and specifications are in technical docs (501 chunks)
                data = self.collection.get(where={"is_tracker": False}, include=["documents", "metadatas"])
                self._cached_documents = data.get("documents", [])
                self._cached_metadatas = data.get("metadatas", [])
            except Exception as e:
                # Fallback to safe batched retrieval
                docs = []
                metas = []
                batch_size = 500
                total = self.collection.count()
                for offset in range(0, min(total, 2000), batch_size):
                    batch = self.collection.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
                    docs.extend(batch.get("documents", []))
                    metas.extend(batch.get("metadatas", []))
                self._cached_documents = docs
                self._cached_metadatas = metas

    def search(self, error_code: str) -> List[Dict[str, Any]]:
        """
        Search for exact error code in the knowledge chunks.
        Returns matching records with matched_line, metadata, and evidence_type.
        """
        if not error_code:
            return []

        try:
            error_number = int(str(error_code).strip().lstrip("#"))
        except ValueError:
            return []

        normalized_code = str(error_number)

        # Pattern 1: Beginning of line error code (e.g. "70 The lead seal button...", "96 The firmware...")
        exact_line_pattern = re.compile(
            rf"(?m)^\s*0*{re.escape(normalized_code)}(?:\s+|[.:)\-]|$)",
            flags=re.IGNORECASE,
        )

        # Pattern 2: Explicit error code phrase (e.g. "Error Code 70", "Error: 70")
        explicit_error_pattern = re.compile(
            rf"error\s+code\s*[:#\-]?\s*0*{re.escape(normalized_code)}(?:\s|$)",
            flags=re.IGNORECASE,
        )

        self._ensure_cache()
        if not self._cached_documents:
            return []

        matches = []

        for document, metadata in zip(self._cached_documents, self._cached_metadatas):
            if not document:
                continue

            # Exact line match check
            if exact_line_pattern.search(document):
                lines = [l.strip() for l in document.splitlines() if l.strip()]
                for idx, line in enumerate(lines):
                    if exact_line_pattern.search(line):
                        clean_line = line.strip()
                        # Avoid pure page number lines like "13 | Page"
                        if "|" in clean_line and "page" in clean_line.lower():
                            continue
                        # If clean_line lacks descriptive words, check adjacent lines (forward or backward for RTL tables):
                        if not re.search(r"[a-zA-Z\u0600-\u06FF]{2,}", clean_line):
                            found_adj = False
                            for offset in [1, 2]:
                                if idx + offset < len(lines):
                                    adj = lines[idx + offset].strip()
                                    if re.search(r"[a-zA-Z\u0600-\u06FF]{2,}", adj):
                                        clean_line = f"{clean_line} {adj}"
                                        found_adj = True
                                        break
                            if not found_adj:
                                prev_parts = []
                                for offset in [1, 2, 3]:
                                    if idx - offset >= 0:
                                        adj = lines[idx - offset].strip()
                                        if re.search(r"[a-zA-Z\u0600-\u06FF]{2,}", adj):
                                            prev_parts.insert(0, adj)
                                        elif prev_parts:
                                            break
                                if prev_parts:
                                    clean_line = f"{clean_line} {' '.join(prev_parts)}"

                        # A verified error definition MUST contain descriptive words explaining the error,
                        # not merely the error code number itself or table column numbers.
                        if "\ufffd" in clean_line:
                            continue
                        remainder = re.sub(rf"\b0*{re.escape(normalized_code)}\b", "", clean_line, flags=re.IGNORECASE)
                        remainder = re.sub(r"[0-9\W]+", " ", remainder).strip()
                        desc_words = [w for w in remainder.split() if len(w) >= 2 and w.lower() not in ["error", "code", "page", "table"]]
                        if len(desc_words) >= 2:
                            matches.append(
                                {
                                    "document": document,
                                    "text": clean_line,
                                    "matched_line": clean_line,
                                    "metadata": metadata,
                                    "evidence_type": "exact-error-code",
                                    "distance": 0.0,
                                }
                            )

            # Explicit pattern check
            elif explicit_error_pattern.search(document):
                lines = [l.strip() for l in document.splitlines() if l.strip()]
                for line in lines:
                    if explicit_error_pattern.search(line):
                        clean_line = line.strip()
                        if "\ufffd" in clean_line:
                            continue
                        remainder = re.sub(rf"\b0*{re.escape(normalized_code)}\b", "", clean_line, flags=re.IGNORECASE)
                        remainder = re.sub(r"[0-9\W]+", " ", remainder).strip()
                        desc_words = [w for w in remainder.split() if len(w) >= 2 and w.lower() not in ["error", "code", "page", "table"]]
                        if len(desc_words) >= 2:
                            matches.append(
                                {
                                    "document": document,
                                    "text": clean_line,
                                    "matched_line": clean_line,
                                    "metadata": metadata,
                                    "evidence_type": "exact-error-code",
                                    "distance": 0.0,
                                }
                            )

        def _match_quality(m):
            line = m.get("matched_line", "")
            score = 0
            if "\ufffd" in line:
                score -= 30
            if not re.search(r"[a-zA-Z\u0600-\u06FF]{3,}", line):
                score -= 40
            error_terms = ["error", "fault", "alarm", "failure", "button", "seal", "card", "firmware", "threshold", "cancel", "relay", "press"]
            if any(t in line.lower() for t in error_terms):
                score += 25
            score += min(len(line), 50)
            return score

        matches.sort(key=_match_quality, reverse=True)
        return matches
