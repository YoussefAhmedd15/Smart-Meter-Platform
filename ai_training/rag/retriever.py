import re
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from ..agent.config import (
    VECTOR_STORE_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    TOP_K,
)
from .evidence import deduplicate_evidence
from .exact_error import DirectErrorSearcher
from .reranker import EvidenceReranker


class HybridRetriever:
    """
    Singleton retriever for ISKRA knowledge base.
    Initializes SentenceTransformer, ChromaDB, and EvidenceReranker once to maintain fast response times.
    Combines exact error code lookup with multi-factor evidence reranking and model isolation.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(HybridRetriever, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, vector_store_dir: Optional[Path] = None, collection_name: str = COLLECTION_NAME):
        if getattr(self, "_initialized", False):
            return

        self.vector_store_dir = vector_store_dir or VECTOR_STORE_DIR
        self.collection_name = collection_name
        self.model = None
        self.client = None
        self.collection = None
        self.exact_searcher = None
        self.reranker = None
        self._tech_candidates: List[Dict[str, Any]] = []
        self.last_evidence_status: str = "NOT_FOUND"

        self._initialize_resources()
        self._initialized = True

    def _initialize_resources(self):
        """Load embedding model, ChromaDB collection, and technical candidates pool."""
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"[WARN] Failed to load SentenceTransformer: {e}")
            self.model = None

        self.reranker = EvidenceReranker()

        try:
            self.client = chromadb.PersistentClient(path=str(self.vector_store_dir))
            self.collection = self.client.get_collection(name=self.collection_name)
            self.exact_searcher = DirectErrorSearcher(self.collection)

            # Load technical documentation chunks into memory for instant multi-factor reranking
            tech_res = self.collection.get(where={"is_tracker": False}, include=["documents", "metadatas"])
            self._tech_candidates = [
                {
                    "document": d,
                    "metadata": m or {},
                    "distance": 0.5,
                    "evidence_type": "technical-manual",
                    "matched_line": "",
                    "text": d,
                }
                for d, m in zip(tech_res.get("documents", []), tech_res.get("metadatas", []))
            ]
        except Exception as e:
            print(f"[WARN] Failed to open ChromaDB collection: {e}")
            self.client = None
            self.collection = None
            self.exact_searcher = DirectErrorSearcher(None)
            self._tech_candidates = []

    def extract_error_code(self, query: str) -> Optional[str]:
        """Detect numeric error code patterns from query, preserving verbatim identifier."""
        patterns = [
            r"(?:error|erorr|eror|errr|erro|irror|err|code|خطأ|خطا|كود|إيرور|ايرور|ارور)\s*(?:code)?\s*[:#\-]?\s*(\d+)\b",
            r"(?:بيطلع|بيعطي|shows|giving)\s*(?:error|erorr|eror|خطأ|كود)?\s*[:#\-]?\s*(\d+)\b",
            r"\b(?:error|erorr|eror|errr|err)(\d+)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Check pure digits query like "70" or "#70" or "0101"
        stripped = query.strip()
        if re.fullmatch(r"#?\d+", stripped):
            return stripped.lstrip("#")

        return None

    def search(
        self,
        query: str,
        error_code: Optional[str] = None,
        top_k: int = TOP_K,
        isolate_models: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid retrieval:
        1. Exact error code search if an error code is detected or provided.
        2. Semantic vector search across chunks (including tracker logs if applicable).
        3. Multi-factor reranking with document authority, concept matching, and model isolation.
        4. Return top_k verified results with evidence status.
        """
        candidates: List[Dict[str, Any]] = []

        # Determine error code
        code_to_search = error_code or self.extract_error_code(query)

        # 1. Exact error code search
        if code_to_search and self.exact_searcher:
            exact_matches = self.exact_searcher.search(code_to_search)
            for m in exact_matches:
                candidates.append(
                    {
                        "document": m["document"],
                        "metadata": m.get("metadata", {}),
                        "distance": 0.0,
                        "evidence_type": "exact-error-code",
                        "matched_line": m.get("matched_line", ""),
                        "text": m.get("matched_line", m["document"]),
                    }
                )

        # 2. Vector search & technical documentation candidates
        if self.model and self.collection and query.strip():
            try:
                query_embedding = self.model.encode(
                    [query], normalize_embeddings=True
                ).tolist()

                # Broader search to capture relevant tracker logs or operational knowledge
                vector_res = self.collection.query(
                    query_embeddings=query_embedding,
                    n_results=top_k * 4,
                )
                docs = vector_res.get("documents", [[]])[0]
                metas = vector_res.get("metadatas", [[]])[0]
                dists = vector_res.get("distances", [[]])[0]

                for d, m, dist in zip(docs, metas, dists):
                    candidates.append(
                        {
                            "document": d,
                            "metadata": m or {},
                            "distance": float(dist) if dist is not None else 0.5,
                            "evidence_type": "vector",
                            "matched_line": "",
                            "text": d,
                        }
                    )
            except Exception as e:
                print(f"[WARN] Vector search error: {e}")

        # Add pre-indexed technical documentation chunks to ensure high-authority specs are considered
        if self._tech_candidates:
            candidates.extend(self._tech_candidates)

        # Deduplicate candidates across chunks
        deduped = deduplicate_evidence(candidates)

        # 3. Multi-Factor Reranking & Model Isolation
        reranked = self.reranker.rerank(
            query=query,
            candidates=deduped,
            top_k=top_k,
            isolate_models=isolate_models,
        )

        # 4. Classify evidence status
        status = self.reranker.classify_evidence_status(query, reranked)
        self.last_evidence_status = status

        if status == "NOT_FOUND" and self.extract_error_code(query):
            return []

        for item in reranked:
            item["evidence_status"] = status

        return reranked
