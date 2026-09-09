# from pathlib import Path
# import re

# import chromadb
# from sentence_transformers import SentenceTransformer


# # ============================================================
# # PATHS
# # ============================================================

# PROJECT_ROOT = Path(__file__).resolve().parents[2]

# VECTOR_STORE_DIR = (
#     PROJECT_ROOT
#     / "ai_training"
#     / "vector_store"
# )

# COLLECTION_NAME = "iskra_knowledge"

# EMBEDDING_MODEL = (
#     "sentence-transformers/"
#     "paraphrase-multilingual-MiniLM-L12-v2"
# )

# TOP_K = 5


# # ============================================================
# # INITIALIZATION
# # ============================================================

# print("=" * 60)
# print("ISKRA RAG - RETRIEVAL TEST")
# print("=" * 60)

# print("\nLoading embedding model...")

# model = SentenceTransformer(EMBEDDING_MODEL)

# print("Embedding model loaded.")

# print("\nOpening ChromaDB...")

# client = chromadb.PersistentClient(
#     path=str(VECTOR_STORE_DIR)
# )

# collection = client.get_collection(
#     name=COLLECTION_NAME
# )

# print(f"Collection: {COLLECTION_NAME}")
# print(f"Documents: {collection.count()}")


# # ============================================================
# # ERROR CODE DETECTION
# # ============================================================

# def extract_error_code(query: str):
#     """
#     Detect questions such as:

#     - What is error code 96?
#     - What does error 70 mean?
#     - MT514 error 96
#     - error: 70
#     - code 70
#     """

#     patterns = [
#         r"error\s*(?:code)?\s*[:#-]?\s*(\d+)",
#         r"code\s*[:#-]?\s*(\d+)",
#     ]

#     for pattern in patterns:
#         match = re.search(
#             pattern,
#             query,
#             flags=re.IGNORECASE
#         )

#         if match:
#             return match.group(1)

#     return None


# # ============================================================
# # VECTOR SEARCH
# # ============================================================

# def vector_search(query: str, top_k: int = TOP_K):

#     query_embedding = model.encode(
#         [query],
#         normalize_embeddings=True
#     ).tolist()

#     return collection.query(
#         query_embeddings=query_embedding,
#         n_results=top_k
#     )


# # ============================================================
# # DIRECT ERROR CODE SEARCH
# # ============================================================

# def direct_error_search(error_code: str):

#     """
#     Search for an exact Error Code inside the
#     knowledge-base chunks.

#     Examples:

#         70 The lead seal button is not be pressed

#         96 The firmware of old meter is too old

#     The search is line-based so that a number appearing
#     somewhere else in the document is not incorrectly
#     treated as an error code.
#     """

#     data = collection.get(
#         include=[
#             "documents",
#             "metadatas"
#         ]
#     )

#     documents = data.get(
#         "documents",
#         []
#     )

#     metadatas = data.get(
#         "metadatas",
#         []
#     )

#     matches = []

#     # --------------------------------------------------------
#     # Normalize error code
#     # --------------------------------------------------------

#     try:
#         error_number = int(error_code)
#     except ValueError:
#         return []

#     normalized_code = str(error_number)

#     # --------------------------------------------------------
#     # Patterns
#     # --------------------------------------------------------

#     # Pattern 1:
#     # 70 The lead seal button...
#     #
#     # 96 The firmware...
#     #
#     # 01 Data cannot...
#     exact_line_pattern = re.compile(
#         rf"(?m)^\s*0*{re.escape(normalized_code)}"
#         rf"(?:\s+|[.:)\-])",
#         flags=re.IGNORECASE
#     )

#     # Pattern 2:
#     # Error Code 70
#     #
#     # Error Code: 70
#     #
#     # Error Code - 70
#     explicit_error_pattern = re.compile(
#         rf"error\s+code\s*[:#\-]?\s*0*"
#         rf"{re.escape(normalized_code)}"
#         rf"(?:\s|$)",
#         flags=re.IGNORECASE
#     )

#     # --------------------------------------------------------
#     # Search every chunk
#     # --------------------------------------------------------

#     for document, metadata in zip(
#         documents,
#         metadatas
#     ):

#         if not document:
#             continue

#         # ----------------------------------------------------
#         # Exact line match
#         # ----------------------------------------------------

#         match = exact_line_pattern.search(
#             document
#         )

#         if match:

#             # Get the complete line containing
#             # the error code.
#             lines = document.splitlines()

#             matching_lines = []

#             for line in lines:

#                 if re.search(
#                     exact_line_pattern,
#                     line
#                 ):

#                     matching_lines.append(
#                         line.strip()
#                     )

#             matches.append(
#                 {
#                     "document": document,
#                     "metadata": metadata,
#                     "matched_line": (
#                         matching_lines[0]
#                         if matching_lines
#                         else ""
#                     ),
#                     "match_type": "exact-line",
#                 }
#             )

#             continue

#         # ----------------------------------------------------
#         # Explicit Error Code match
#         # ----------------------------------------------------

#         explicit_match = explicit_error_pattern.search(
#             document
#         )

#         if explicit_match:

#             matches.append(
#                 {
#                     "document": document,
#                     "metadata": metadata,
#                     "matched_line": explicit_match.group(0),
#                     "match_type": "explicit-error-code",
#                 }
#             )

#     return matches


# # ============================================================
# # REMOVE DUPLICATES
# # ============================================================

# def remove_duplicate_results(results):

#     unique_results = []

#     seen = set()

#     for result in results:

#         matched_line = result.get("matched_line", "").strip()
#         document = result.get(
#             "document",
#             ""
#         )

#         if matched_line:
#             key = f"line:{matched_line.lower()}"
#         else:
#             key = f"doc:{document[:120].lower()}"

#         if key in seen:
#             continue

#         seen.add(key)

#         unique_results.append(
#             result
#         )

#     return unique_results


# # ============================================================
# # HYBRID SEARCH
# # ============================================================

# def search_knowledge(query: str):

#     # --------------------------------------------------------
#     # Vector Search
#     # --------------------------------------------------------

#     vector_results = vector_search(
#         query,
#         TOP_K
#     )

#     documents = vector_results.get(
#         "documents",
#         [[]]
#     )[0]

#     metadatas = vector_results.get(
#         "metadatas",
#         [[]]
#     )[0]

#     distances = vector_results.get(
#         "distances",
#         [[]]
#     )[0]

#     vector_result_list = []

#     for document, metadata, distance in zip(
#         documents,
#         metadatas,
#         distances
#     ):

#         vector_result_list.append(
#             {
#                 "document": document,
#                 "metadata": metadata,
#                 "distance": distance,
#                 "method": "vector",
#             }
#         )

#     # --------------------------------------------------------
#     # Error Code Detection
#     # --------------------------------------------------------

#     error_code = extract_error_code(
#         query
#     )

#     if error_code:

#         print(
#             f"\nDetected Error Code: {error_code}"
#         )

#         # ----------------------------------------------------
#         # Exact Search
#         # ----------------------------------------------------

#         exact_matches = direct_error_search(
#             error_code
#         )

#         exact_results = []

#         for match in exact_matches:

#             exact_results.append(
#                 {
#                     "document": match["document"],
#                     "metadata": match["metadata"],
#                     "distance": 0.0,
#                     "method": (
#                         "exact-error-code"
#                     ),
#                     "matched_line": match.get(
#                         "matched_line",
#                         ""
#                     ),
#                 }
#             )

#         # ----------------------------------------------------
#         # Exact results first
#         # ----------------------------------------------------

#         results = (
#             exact_results
#             + vector_result_list
#         )

#     else:

#         results = vector_result_list

#     # --------------------------------------------------------
#     # Remove duplicate documents
#     # --------------------------------------------------------

#     results = remove_duplicate_results(
#         results
#     )

#     # --------------------------------------------------------
#     # Return TOP_K
#     # --------------------------------------------------------

#     return results[:TOP_K]


# # ============================================================
# # PRINT RESULT
# # ============================================================

# def print_results(
#     query,
#     results
# ):

#     print("\n" + "=" * 60)

#     print(
#         f"QUESTION: {query}"
#     )

#     print("=" * 60)

#     if not results:

#         print(
#             "\nNo results found."
#         )

#         return

#     for index, result in enumerate(
#         results,
#         start=1
#     ):

#         document = result.get(
#             "document",
#             ""
#         )

#         metadata = result.get(
#             "metadata",
#             {}
#         )

#         method = result.get(
#             "method",
#             "unknown"
#         )

#         distance = result.get(
#             "distance",
#             0.0
#         )

#         print(
#             "\n" + "-" * 60
#         )

#         print(
#             f"RESULT #{index}"
#         )

#         print(
#             f"Method   : {method}"
#         )

#         print(
#             f"Source   : "
#             f"{metadata.get('source')}"
#         )

#         print(
#             f"Page     : "
#             f"{metadata.get('page')}"
#         )

#         print(
#             f"Chunk    : "
#             f"{metadata.get('chunk')}"
#         )

#         print(
#             f"Distance : "
#             f"{distance:.4f}"
#         )

#         # ----------------------------------------------------
#         # Show matched error line
#         # ----------------------------------------------------

#         matched_line = result.get(
#             "matched_line",
#             ""
#         )

#         if matched_line:

#             print(
#                 f"\nMatched Error : "
#                 f"{matched_line}"
#             )

#         print("\nContent:")

#         print(document)


# # ============================================================
# # MAIN
# # ============================================================

# def main():

#     query = input(
#         "\nEnter your question: "
#     ).strip()

#     if not query:

#         print(
#             "\nQuestion cannot be empty."
#         )

#         return

#     results = search_knowledge(
#         query
#     )

#     print_results(
#         query,
#         results
#     )

#     print(
#         "\n" + "=" * 60
#     )

#     print(
#         "HYBRID RETRIEVAL TEST COMPLETE"
#     )

#     print(
#         "=" * 60
#     )


# # ============================================================
# # ENTRY POINT
# # ============================================================

# if __name__ == "__main__":

#     main()