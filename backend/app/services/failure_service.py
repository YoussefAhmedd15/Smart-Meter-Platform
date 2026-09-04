import difflib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..db.models import FailureRecord, Meter


class FailureIntelligenceService:

    def __init__(self, db: Session):
        self.db = db

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculates normalized string similarity ratio between 0.0 and 1.0."""
        if not text1 or not text2:
            return 0.0
        return round(difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio(), 4)

    def find_similar_failures(self, failure_id: int, top_k: int = 5) -> List[dict]:
        target = self.db.query(FailureRecord).filter(FailureRecord.id == failure_id).first()
        if not target:
            return []

        all_failures = (
            self.db.query(FailureRecord)
            .filter(FailureRecord.id != failure_id)
            .all()
        )

        similar_results = []
        for past in all_failures:
            # Deterministic scoring components
            type_match = 1.0 if past.error_type == target.error_type else 0.2
            case_match = 1.0 if past.test_case == target.test_case else 0.4
            fw_match = 1.0 if past.firmware_version == target.firmware_version else 0.6
            text_sim = self.calculate_text_similarity(past.error_message, target.error_message)

            # Combined weighted score
            similarity = round(
                (0.35 * text_sim) + (0.25 * type_match) + (0.25 * case_match) + (0.15 * fw_match),
                4
            )

            # Assign confidence tier
            if similarity >= 0.85:
                confidence = "HIGH"
            elif similarity >= 0.60:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            similar_results.append({
                "failure_id": past.id,
                "similarity_score": round(similarity * 100, 1),
                "confidence": confidence,
                "firmware_version": past.firmware_version,
                "test_case": past.test_case,
                "error_type": past.error_type,
                "error_message": past.error_message,
                "root_cause": past.root_cause or "Communication handshake timeout under high optical baudrate.",
                "solution": past.solution or "Verify optical probe alignment, reset parity to EVEN, or decrease initial baud rate to 300.",
                "created_at": past.created_at.isoformat() if past.created_at else None,
            })

        # Sort by similarity descending
        similar_results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_results[:top_k]

    def analyze_failure(self, failure_id: int) -> dict:
        target = self.db.query(FailureRecord).filter(FailureRecord.id == failure_id).first()
        if not target:
            return {"error": "Failure record not found"}

        similar = self.find_similar_failures(failure_id, top_k=3)
        
        best_match = similar[0] if similar else None
        
        return {
            "target_failure": {
                "id": target.id,
                "meter_id": target.meter_id,
                "firmware_version": target.firmware_version,
                "test_case": target.test_case,
                "error_type": target.error_type,
                "error_message": target.error_message,
                "severity": target.severity,
                "timestamp": target.created_at.isoformat() if target.created_at else None,
            },
            "best_match": best_match,
            "similar_failures": similar,
            "ai_summary": (
                f"Failure '{target.test_case}' ({target.error_type}) evaluated against database history. "
                + (f"Matched prior incident #{best_match['failure_id']} with {best_match['similarity_score']}% similarity." if best_match else "No prior identical failure detected.")
            )
        }
