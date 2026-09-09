from pathlib import Path
import re
import json
import urllib.request
import urllib.error

import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VECTOR_STORE_DIR = (
    PROJECT_ROOT
    / "ai_training"
    / "vector_store"
)

COLLECTION_NAME = "iskra_knowledge"

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

OLLAMA_URL = "http://localhost:11434/api/generate"

OLLAMA_MODEL = "granite4.2:8b"

TOP_K = 5


# ============================================================
# INITIALIZATION
# ============================================================

print("=" * 70)
print("ISKRA SMART METER - L1 RAG ASSISTANT")
print("=" * 70)

print("\nLoading embedding model...")

model = SentenceTransformer(
    EMBEDDING_MODEL
)

print("Embedding model loaded.")


# ============================================================
# CHROMADB
# ============================================================

print("\nOpening ChromaDB...")

client = chromadb.PersistentClient(
    path=str(VECTOR_STORE_DIR)
)

collection = client.get_collection(
    name=COLLECTION_NAME
)

print(
    f"Collection : {COLLECTION_NAME}"
)

print(
    f"Documents  : {collection.count()}"
)


# ============================================================
# CASE STATE
# ============================================================

def create_case_state():

    return {
        "meter_type": None,
        "meter_model": None,
        "system": None,
        "error_code": None,
        "scenario": None,
        "issue_description": None,

        # New classification fields
        "issue_category": None,
        "classification_reason": None,
        "l1_status": None,
        "routing": None,
    }


case_state = create_case_state()


# ============================================================
# ERROR CODE EXTRACTION
# ============================================================

def extract_error_code(query: str):

    patterns = [
        r"error\s*(?:code)?\s*[:#-]?\s*(\d+)",
        r"code\s*[:#-]?\s*(\d+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            query,
            flags=re.IGNORECASE
        )

        if match:

            return match.group(1)

    return None


# ============================================================
# METER TYPE EXTRACTION
# ============================================================

def extract_meter_type(text: str):

    q = text.lower()

    electric_keywords = [
        "electric",
        "electricity",
        "electric meter",
        "عداد كهرباء",
        "كهرباء",
    ]

    water_keywords = [
        "water",
        "water meter",
        "عداد مياه",
        "مياه",
    ]

    if any(
        keyword in q
        for keyword in electric_keywords
    ):

        return "Electric"

    if any(
        keyword in q
        for keyword in water_keywords
    ):

        return "Water"

    return None


# ============================================================
# METER MODEL EXTRACTION
# ============================================================

def extract_meter_model(text: str):

    patterns = [
        r"\bME514(?:[-_ ]?[A-Za-z0-9]+)?\b",
        r"\bMT514(?:[-_ ]?[A-Za-z0-9]+)?\b",
        r"\bAM550\b",
        r"\bMT880\b",
        r"\bMT800\b",
        r"\bMW5[A-Za-z0-9_-]*\b",
        r"\bMV5[A-Za-z0-9_-]*\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:

            return match.group(0).upper()

    return None


# ============================================================
# SYSTEM EXTRACTION
# ============================================================

def extract_system(text: str):
    """
    Extract the software/system involved.

    Electric alone means meter type.
    It does NOT mean Electric system.
    """

    q = text.lower()

    systems = {
        "billing": "Billing",
        "symbiot": "Symbiot",
        "vending": "Vending",
        "meterverse": "MeterVerse",
        "aqua": "Aqua",
    }

    for keyword, system_name in systems.items():

        if keyword in q:

            return system_name

    electric_system_patterns = [
        "electric system",
        "electric software",
        "electric application",
        "electric app",
        "in electric system",
        "on electric system",
    ]

    for pattern in electric_system_patterns:

        if pattern in q:

            return "Electric"

    return None


# ============================================================
# ISSUE CLASSIFICATION
# ============================================================

def classify_issue():

    """
    Conservative rule-based issue classification.

    Categories:
        Software
        Hardware
        Firmware
        Communication
        Unknown

    IMPORTANT:
    This function does not invent a category when
    there is insufficient evidence.
    """

    text_parts = [
        case_state.get("issue_description") or "",
        case_state.get("scenario") or "",
        case_state.get("system") or "",
    ]

    text = " ".join(
        text_parts
    ).lower()

    # --------------------------------------------------------
    # Firmware
    # --------------------------------------------------------

    firmware_keywords = [
        "firmware",
        "firmware update",
        "firmware upgrade",
        "firmware version",
        "flash firmware",
        "old firmware",
        "firmware issue",
        "firmware error",
        "سوفت وير العداد",
        "فيرموير",
    ]

    if any(
        keyword in text
        for keyword in firmware_keywords
    ):

        return (
            "Firmware",
            "Firmware-related evidence was found in the case."
        )

    # --------------------------------------------------------
    # Communication
    # --------------------------------------------------------

    communication_keywords = [
        "communication",
        "communicate",
        "communication error",
        "communication failed",
        "cannot communicate",
        "no communication",
        "connection error",
        "connection failed",
        "not connected",
        "disconnect",
        "disconnected",
        "rs485",
        "rs232",
        "modbus",
        "dlms",
        "hdlc",
        "tcp connection",
        "serial communication",
        "data cannot be read",
        "cannot read data",
        "لا يوجد اتصال",
        "مشكلة اتصال",
        "الاتصال",
    ]

    if any(
        keyword in text
        for keyword in communication_keywords
    ):

        return (
            "Communication",
            "Communication-related evidence was found in the case."
        )

    # --------------------------------------------------------
    # Hardware
    # --------------------------------------------------------

    hardware_keywords = [
        "hardware",
        "display broken",
        "screen broken",
        "lcd broken",
        "relay damaged",
        "relay failure",
        "button damaged",
        "button not working",
        "physical damage",
        "burned",
        "burnt",
        "broken",
        "damaged",
        "not powering",
        "power failure",
        "power supply",
        "no power",
        "battery problem",
        "battery failure",
        "sensor damaged",
        "physical problem",
        "damage",
        "هاردوير",
        "تلف",
        "مكسور",
        "محروق",
        "باور",
    ]

    if any(
        keyword in text
        for keyword in hardware_keywords
    ):

        return (
            "Hardware",
            "Hardware-related evidence was found in the case."
        )

    # --------------------------------------------------------
    # Software
    # --------------------------------------------------------

    software_keywords = [
        "software",
        "application",
        "app",
        "system error",
        "system issue",
        "software error",
        "software issue",
        "cannot open account",
        "open account",
        "account opening",
        "billing",
        "symbiot",
        "vending",
        "meterverse",
        "aqua",
        "electric system",
        "software problem",
        "program",
        "application error",
        "login",
        "authentication",
        "screen error",
        "button not responding",
        "cannot save",
        "cannot send",
        "cannot create",
        "cannot update",
        "سوفت وير",
        "برنامج",
        "سيستم",
        "النظام",
    ]

    if any(
        keyword in text
        for keyword in software_keywords
    ):

        return (
            "Software",
            "Software/system-related evidence was found in the case."
        )

    # --------------------------------------------------------
    # Unknown
    # --------------------------------------------------------

    return (
        "Unknown",
        "The available case information is insufficient to classify the issue."
    )


# ============================================================
# ROUTING
# ============================================================

def determine_routing(category):

    routing_map = {
        "Software": "L2 Software",
        "Hardware": "L2 Hardware",
        "Firmware": "L2 Firmware",
        "Communication": "L2 Software",
        "Unknown": "L1 Review",
    }

    return routing_map.get(
        category,
        "L1 Review"
    )


# ============================================================
# L1 DECISION
# ============================================================

def determine_l1_status(
    category,
    exact_error_found
):

    # Exact verified error code means L1 has
    # verified knowledge about the error.
    if exact_error_found:

        return "Knowledge Available"

    # Unknown category cannot be safely resolved.
    if category == "Unknown":

        return "Insufficient Information"

    # For now, classification alone does not
    # mean that L1 has a verified solution.
    return "Needs Knowledge Check"


# ============================================================
# UPDATE CLASSIFICATION
# ============================================================

def update_classification():

    category, reason = classify_issue()

    case_state["issue_category"] = category

    case_state["classification_reason"] = reason

    case_state["routing"] = determine_routing(
        category
    )


# ============================================================
# UPDATE CASE STATE
# ============================================================

def update_case_state(
    question: str
):

    global case_state

    # --------------------------------------------------------
    # Meter Type
    # --------------------------------------------------------

    meter_type = extract_meter_type(
        question
    )

    if meter_type:

        case_state["meter_type"] = meter_type

    # --------------------------------------------------------
    # Meter Model
    # --------------------------------------------------------

    meter_model = extract_meter_model(
        question
    )

    if meter_model:

        case_state["meter_model"] = meter_model

    # --------------------------------------------------------
    # System
    # --------------------------------------------------------

    system = extract_system(
        question
    )

    if system:

        case_state["system"] = system

    # --------------------------------------------------------
    # Error Code
    # --------------------------------------------------------

    error_code = extract_error_code(
        question
    )

    if error_code:

        case_state["error_code"] = error_code

    # --------------------------------------------------------
    # Scenario
    # --------------------------------------------------------

    scenario_keywords = [
        "when",
        "during",
        "while",
        "after",
        "before",
        "happens",
        "started",
        "occurred",
        "issue started",
        "أثناء",
        "بعد",
        "قبل",
        "لما",
        "بدأ",
        "حصل",
    ]

    q = question.lower()

    if any(
        keyword in q
        for keyword in scenario_keywords
    ):

        case_state["scenario"] = question

    # --------------------------------------------------------
    # Issue Description
    # --------------------------------------------------------

    if (
        not case_state["issue_description"]
        and len(question.split()) >= 3
    ):

        case_state["issue_description"] = question


# ============================================================
# GET MISSING CASE INFORMATION
# ============================================================

def get_missing_information():

    missing = []

    if not case_state["meter_type"]:

        missing.append(
            "Meter type: Is it Electric or Water?"
        )

    if not case_state["meter_model"]:

        missing.append(
            "Meter model: What is the meter model?"
        )

    if not case_state["system"]:

        missing.append(
            "Software/System: Which system is involved? "
            "For example: Billing, Symbiot, Vending, "
            "MeterVerse, Aqua, Electric, or another system."
        )

    if not case_state["error_code"]:

        missing.append(
            "Error code/message: Is there any error code "
            "or message displayed?"
        )

    if not case_state["scenario"]:

        missing.append(
            "Scenario: What were you doing when "
            "the issue occurred?"
        )

    return missing


# ============================================================
# DISPLAY CASE STATE
# ============================================================

def print_case_state():

    print(
        "\n" + "=" * 70
    )

    print(
        "CASE INFORMATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Meter Type    : "
        f"{case_state['meter_type'] or 'Not provided'}"
    )

    print(
        f"Meter Model   : "
        f"{case_state['meter_model'] or 'Not provided'}"
    )

    print(
        f"System        : "
        f"{case_state['system'] or 'Not provided'}"
    )

    print(
        f"Error Code    : "
        f"{case_state['error_code'] or 'Not provided'}"
    )

    print(
        f"Scenario      : "
        f"{case_state['scenario'] or 'Not provided'}"
    )

    print(
        f"Issue         : "
        f"{case_state['issue_description'] or 'Not provided'}"
    )


# ============================================================
# DISPLAY CLASSIFICATION
# ============================================================

def print_classification():

    print(
        "\n" + "=" * 70
    )

    print(
        "ISSUE CLASSIFICATION"
    )

    print(
        "=" * 70
    )

    print(
        f"Category : "
        f"{case_state['issue_category']}"
    )

    print(
        f"Reason   : "
        f"{case_state['classification_reason']}"
    )

    print(
        f"Routing  : "
        f"{case_state['routing']}"
    )


# ============================================================
# VECTOR SEARCH
# ============================================================

def vector_search(
    query: str,
    top_k: int = TOP_K
):

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]

    output = []

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        output.append(
            {
                "document": document,
                "metadata": metadata,
                "distance": distance,
                "method": "vector",
            }
        )

    return output


# ============================================================
# EXACT ERROR SEARCH
# ============================================================

def direct_error_search(
    error_code: str
):

    data = collection.get(
        include=[
            "documents",
            "metadatas"
        ]
    )

    documents = data.get(
        "documents",
        []
    )

    metadatas = data.get(
        "metadatas",
        []
    )

    matches = []

    try:

        error_number = int(
            error_code
        )

    except ValueError:

        return []

    normalized_code = str(
        error_number
    )

    exact_line_pattern = re.compile(
        rf"(?m)^\s*0*"
        rf"{re.escape(normalized_code)}"
        rf"(?:\s+|[.:)\-])",
        flags=re.IGNORECASE
    )

    explicit_error_pattern = re.compile(
        rf"error\s+code\s*[:#\-]?\s*0*"
        rf"{re.escape(normalized_code)}"
        rf"(?:\s|$)",
        flags=re.IGNORECASE
    )

    for document, metadata in zip(
        documents,
        metadatas
    ):

        if not document:

            continue

        # ----------------------------------------------------
        # Exact line search
        # ----------------------------------------------------

        match = exact_line_pattern.search(
            document
        )

        if match:

            lines = document.splitlines()

            matching_lines = []

            for line in lines:

                if re.search(
                    exact_line_pattern,
                    line
                ):

                    matching_lines.append(
                        line.strip()
                    )

            matches.append(
                {
                    "document": document,
                    "metadata": metadata,
                    "matched_line": (
                        matching_lines[0]
                        if matching_lines
                        else ""
                    ),
                }
            )

            continue

        # ----------------------------------------------------
        # Explicit Error Code search
        # ----------------------------------------------------

        match = explicit_error_pattern.search(
            document
        )

        if match:

            matches.append(
                {
                    "document": document,
                    "metadata": metadata,
                    "matched_line": match.group(0),
                }
            )

    return matches


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(
    results
):

    unique = []

    seen = set()

    for result in results:

        matched_line = result.get("matched_line", "").strip()
        document = result.get(
            "document",
            ""
        )

        if matched_line:
            key = f"line:{matched_line.lower()}"
        else:
            key = f"doc:{document[:120].lower()}"

        if key in seen:

            continue

        seen.add(key)

        unique.append(
            result
        )

    return unique


# ============================================================
# HYBRID RETRIEVAL
# ============================================================

def retrieve_knowledge(
    query: str
):

    vector_results = vector_search(
        query,
        TOP_K
    )

    error_code = extract_error_code(
        query
    )

    exact_results = []

    if error_code:

        exact_matches = direct_error_search(
            error_code
        )

        for match in exact_matches:

            exact_results.append(
                {
                    "document": match["document"],
                    "metadata": match["metadata"],
                    "distance": 0.0,
                    "method": "exact-error-code",
                    "matched_line": match.get(
                        "matched_line",
                        ""
                    ),
                }
            )

    results = (
        exact_results
        + vector_results
    )

    results = remove_duplicates(
        results
    )

    return results[:TOP_K]


# ============================================================
# BUILD CONTEXT FOR OLLAMA
# ============================================================

def build_context(
    results
):

    if not results:

        return (
            "No relevant knowledge was retrieved."
        )

    context_parts = []

    for index, result in enumerate(
        results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        source = metadata.get(
            "source",
            "Unknown source"
        )

        page = metadata.get(
            "page",
            "Unknown page"
        )

        chunk = metadata.get(
            "chunk",
            "Unknown chunk"
        )

        document = result.get(
            "document",
            ""
        )

        matched_line = result.get(
            "matched_line",
            ""
        )

        if matched_line:

            evidence_text = (
                f"Exact match: {matched_line}"
            )

        else:

            evidence_text = document

        context_parts.append(
            f"""
[EVIDENCE {index}]
Source: {source}
Page: {page}
Chunk: {chunk}

{evidence_text}
"""
        )

    return "\n".join(
        context_parts
    )


# ============================================================
# CALL OLLAMA
# ============================================================

def ask_ollama(
    question: str,
    context: str
):

    prompt = f"""
You are an ISKRA L1 technical support assistant.

RULES:

1. Answer ONLY from the retrieved evidence.
2. Never invent information.
3. Never assume the meter model.
4. Never assume the meter type.
5. Never assume the software/system.
6. Never invent error codes.
7. Never invent troubleshooting procedures.
8. Never invent root causes.
9. If information is missing, clearly say what information is missing.
10. If the evidence is insufficient to solve the issue, do not guess.
11. If an exact error code is found, give only its meaning from the evidence.
12. Keep the answer short and practical.
13. Do not explain your reasoning.
14. Do not think aloud.
15. Answer in the same language as the user.

CASE INFORMATION:

Meter Type: {case_state["meter_type"]}
Meter Model: {case_state["meter_model"]}
System: {case_state["system"]}
Error Code: {case_state["error_code"]}
Scenario: {case_state["scenario"]}
Issue Description: {case_state["issue_description"]}
Issue Category: {case_state["issue_category"]}
Routing: {case_state["routing"]}

RETRIEVED EVIDENCE:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "think": False,

        "options": {
            "temperature": 0,
            "num_predict": 150
        }
    }

    data = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            response_data = json.loads(
                response.read().decode(
                    "utf-8"
                )
            )

            answer = response_data.get(
                "response",
                ""
            ).strip()

            if not answer:

                return (
                    "The model returned an empty response."
                )

            return answer

    except urllib.error.URLError as error:

        return (
            "ERROR: Could not connect to Ollama.\n"
            f"Details: {error}"
        )

    except Exception as error:

        return (
            "ERROR while calling Ollama.\n"
            f"Details: {error}"
        )


# ============================================================
# DISPLAY RETRIEVED EVIDENCE
# ============================================================

def print_evidence(
    results
):

    print(
        "\n" + "=" * 70
    )

    print(
        "RETRIEVED EVIDENCE"
    )

    print(
        "=" * 70
    )

    if not results:

        print(
            "\nNo relevant evidence found."
        )

        return

    for index, result in enumerate(
        results,
        start=1
    ):

        metadata = result.get(
            "metadata",
            {}
        )

        print(
            f"\n[{index}] "
            f"{result.get('method')}"
        )

        print(
            f"Source : "
            f"{metadata.get('source')}"
        )

        print(
            f"Page   : "
            f"{metadata.get('page')}"
        )

        print(
            f"Chunk  : "
            f"{metadata.get('chunk')}"
        )

        matched_line = result.get(
            "matched_line",
            ""
        )

        if matched_line:

            print(
                f"Match  : "
                f"{matched_line}"
            )


# ============================================================
# RESET CASE
# ============================================================

def reset_case():

    global case_state

    case_state = create_case_state()

    print(
        "\nNew case started."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nType your ISKRA support question."
    )

    print(
        "Commands:"
    )

    print(
        "  exit  -> Close"
    )

    print(
        "  reset -> Start a new case"
    )

    while True:

        print(
            "\n" + "-" * 70
        )

        question = input(
            "\nYou: "
        ).strip()

        if not question:

            continue

        if question.lower() in {
            "exit",
            "quit",
            "q"
        }:

            print(
                "\nGoodbye."
            )

            break

        if question.lower() == "reset":

            reset_case()

            continue

        # ----------------------------------------------------
        # UPDATE CASE STATE
        # ----------------------------------------------------

        update_case_state(
            question
        )

        # ----------------------------------------------------
        # PROCESS WITH AVAILABLE FACTS (NON-BLOCKING)
        # ----------------------------------------------------

        update_classification()

        print_case_state()

        print_classification()

        # ----------------------------------------------------
        # RETRIEVE KNOWLEDGE
        # ----------------------------------------------------

        results = retrieve_knowledge(
            question
        )

        # ----------------------------------------------------
        # DISPLAY EVIDENCE
        # ----------------------------------------------------

        print_evidence(
            results
        )

        # ----------------------------------------------------
        # CHECK EXACT ERROR CODE
        # ----------------------------------------------------

        error_code = case_state.get(
            "error_code"
        )

        exact_matches = []

        if error_code:

            exact_matches = direct_error_search(
                error_code
            )

        # ----------------------------------------------------
        # L1 STATUS
        # ----------------------------------------------------

        case_state["l1_status"] = determine_l1_status(
            case_state["issue_category"],
            bool(exact_matches)
        )

        print(
            "\n" + "=" * 70
        )

        print(
            "L1 DECISION"
        )

        print(
            "=" * 70
        )

        print(
            f"Status  : "
            f"{case_state['l1_status']}"
        )

        print(
            f"Routing : "
            f"{case_state['routing']}"
        )

        # ----------------------------------------------------
        # EXACT ERROR CODE ANSWER
        # ----------------------------------------------------

        if exact_matches:

            matched_line = (
                exact_matches[0]
                .get(
                    "matched_line",
                    ""
                )
            )

            if matched_line:

                print(
                    "\n" + "=" * 70
                )

                print(
                    "ISKRA L1 ASSISTANT"
                )

                print(
                    "=" * 70
                )

                print(
                    "\nVerified Error Code:"
                )

                print(
                    matched_line
                )

                print(
                    f"\nL1 Status: "
                    f"{case_state['l1_status']}"
                )

                print(
                    f"Routing: "
                    f"{case_state['routing']}"
                )

                continue

        # ----------------------------------------------------
        # UNKNOWN CLASSIFICATION
        # ----------------------------------------------------

        if case_state["issue_category"] == "Unknown":

            print(
                "\nISKRA L1 cannot safely classify this issue "
                "from the available information."
            )

            print(
                "More technical information is required."
            )

            continue

        # ----------------------------------------------------
        # BUILD CONTEXT
        # ----------------------------------------------------

        context = build_context(
            results
        )

        # ----------------------------------------------------
        # ASK OLLAMA
        # ----------------------------------------------------

        print(
            "\n" + "=" * 70
        )

        print(
            "ISKRA L1 ASSISTANT"
        )

        print(
            "=" * 70
        )

        print(
            "\nThinking..."
        )

        answer = ask_ollama(
            question,
            context
        )

        # ----------------------------------------------------
        # DISPLAY ANSWER
        # ----------------------------------------------------

        print(
            "\nAnswer:"
        )

        print(
            answer
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()