from typing import List, Dict, Any


def deduplicate_evidence(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate evidence chunks resulting from chunk overlap or
    simultaneous vector and exact keyword retrieval.

    Preserves:
      - source
      - page
      - chunk
      - evidence_type
      - matched_line
      - text/document
    Prioritizes exact-match evidence over vector search.
    """
    unique_results: List[Dict[str, Any]] = []
    seen_keys = set()

    for item in results:
        metadata = item.get("metadata", {})
        source = metadata.get("source", "")
        page = metadata.get("page", "")
        chunk = metadata.get("chunk", "")
        matched_line = item.get("matched_line", "").strip()
        doc_text = item.get("document", item.get("text", "")).strip()

        # If an exact matched line exists, deduplicate on the line itself
        if matched_line:
            dedup_key = f"line:{matched_line.lower()}"
        else:
            # Otherwise deduplicate on source + page + chunk or signature text
            sig = doc_text[:120].lower().replace(" ", "")
            dedup_key = f"doc:{source}:{page}:{chunk}:{sig}"

        if dedup_key in seen_keys:
            continue

        seen_keys.add(dedup_key)
        unique_results.append(item)

    return unique_results
