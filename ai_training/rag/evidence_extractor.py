"""
ai_training/rag/evidence_extractor.py
EVIDENCE PASSAGE EXTRACTOR

Extracts the exact supporting passage from a retrieved chunk:
1. Detects section headers (e.g., "4.10 MPPUL alarm", "6.4 Measurement function", "2.8.1 Optical port...").
2. Identifies semantic concepts relevant to the user query and request type.
3. Discards leading fragments caused by chunk boundaries (e.g., "mit, at the same time...").
4. Discards trailing fragments belonging to subsequent sections.
5. Returns a coherent, grounded passage representing only the requested topic.
"""

import re
from typing import List, Optional, Tuple


# Regex pattern to identify section headers like "4.10 MPPUL alarm", "6.4 Measurement function",
# "2.8.1 Optical port according to IEC 62056-21", "1 Overview", "6 Functions", "(2) CPU Card error"
SECTION_HEADER_PATTERN = re.compile(
    r"(?:^|\n)\s*("
    r"(?:\d+(?:\.\d+)*|\(\d+\)|\d+\))\s+[A-Za-z\u0600-\u06FF][^\n]+"
    r"|Table\s+\d+[\-\d]*\s+[A-Za-z\u0600-\u06FF][^\n]+"
    r"|[A-Za-z\u0600-\u06FF][A-Za-z0-9\s\-_]{2,40}\s*(?:alarm|function|overview|specification|management|protocol|port|error)\b[^\n]*"
    r")",
    re.IGNORECASE,
)


def detect_request_type(query: str) -> str:
    """
    Classify user query into one of the supported request types:
    MEASUREMENT, ALARM, ERROR_MEANING, COMMUNICATION, DEFINITION,
    PROCEDURE, CAUSE, WHEN_IT_HAPPENS, SYMPTOMS, GENERAL_INFORMATION
    """
    q_lower = query.lower()

    # 1. Error meaning
    if re.search(r"\b(?:error|خطأ|كود|eror|err)\s*[:#\-]?\s*\d+\b", q_lower) or re.search(r"\b(?:error\s+code|كود\s+الخطأ)\b", q_lower):
        return "ERROR_MEANING"

    # 2. Procedure inquiry (how to fix, steps, resolve, repair)
    procedure_patterns = [
        r"\b(?:how\s+(?:to|do\s+i|can\s+i)\s+(?:fix|solve|repair|reset|operate|calibrate|configure|set\s+up|program|do)|what\s+should\s+i\s+do|what\s+do\s+i\s+do|what\s+can\s+i\s+do)\b",
        r"\b(?:procedure|steps|instructions|resolution|troubleshooting|configuration)\b",
        r"(?:طريقة\s+(?:حل|إصلاح|تصليح|تشغيل|معايرة|ريست|ضبط|برمجة|تهيئة)|كيفية\s+(?:حل|إصلاح|ضبط|برمجة|تهيئة)|ازاي\s+(?:أصلح|احل|اعمل|اضبط|أضبط|ابرمج)|إجراءات|خطوات|أعمل\s+ايه|اعمل\s+ايه|ايه\s+الحل)",
    ]
    if any(re.search(p, q_lower) for p in procedure_patterns):
        return "PROCEDURE"

    # 3. Cause inquiry (why, reason)
    cause_patterns = [
        r"\b(?:why\s+does|why\s+is|what\s+causes|reason\s+for|cause\s+of)\b",
        r"(?:لماذا|ليه|ما\s+سبب|أسباب|سبب\s+حدوث)",
    ]
    if any(re.search(p, q_lower) for p in cause_patterns):
        return "CAUSE"

    # 4. When it happens
    when_patterns = [
        r"\b(?:when\s+does|under\s+what\s+conditions|what\s+triggers)\b",
        r"(?:متى\s+يحدث|امتى\s+بيحصل|شروط\s+حدوث)",
    ]
    if any(re.search(p, q_lower) for p in when_patterns):
        return "WHEN_IT_HAPPENS"

    # 5. Symptoms
    symptom_patterns = [
        r"\b(?:symptoms|indications|how\s+do\s+i\s+know\s+if)\b",
        r"(?:أعراض|علامات|إزاي\s+أعرف)",
    ]
    if any(re.search(p, q_lower) for p in symptom_patterns):
        return "SYMPTOMS"

    # 6. Alarm
    alarm_patterns = [
        r"\b(?:alarm|unbalance|imbalance|mppul|relay\s+error)\b",
        r"(?:إنذار|انذار|عدم\s+اتزان|توازن|فازات|رمز\s+الإنذار)",
    ]
    if any(re.search(p, q_lower) for p in alarm_patterns):
        return "ALARM"

    # 7. Communication protocol / interface
    comm_patterns = [
        r"\b(?:protocol|communication|optical|rs485|baud|interface|iec\s*62056|mode\s*c|dlms|cosem)\b",
        r"(?:بروتوكول|اتصال|منفذ\s+ضوئي|بصرية|واجهة\s+اتصال)",
    ]
    if any(re.search(p, q_lower) for p in comm_patterns):
        return "COMMUNICATION"

    # 8. Measurement
    measure_patterns = [
        r"\b(?:measure|measurement|measuring|metering|readings?|parameters?|quantities|values?|voltage|current|active\s+power|power\s+factor|energy|instantaneous|produce)\b",
        r"(?:يقيس|قياس|بيقيس|القياسات|قراءة|قراءات|القراءات|كميات|قيم|الجهد|التيار|القدرة|الطاقة|بيطلع|يطلع|بيطلعلي|بيسجل|تسجيل)",
    ]
    if any(re.search(p, q_lower) for p in measure_patterns):
        return "MEASUREMENT"

    # 9. Definition / Concept inquiry
    def_patterns = [
        r"^(?:what\s+is|what\s+are|define|meaning\s+of|explain)\b",
        r"^(?:ما\s*(?:هو|هي)|ماهو|ماهي|معنى|ماذا\s+تعني|يعني\s*(?:ايه|إيه))\b",
    ]
    if any(re.search(p, q_lower) for p in def_patterns):
        return "DEFINITION"

    return "GENERAL_INFORMATION"



def split_sections(text: str) -> List[Tuple[str, str]]:
    """
    Split chunk text into a list of (header, section_content) tuples.
    If text starts before the first header, the initial fragment has an empty header.
    """
    matches = list(SECTION_HEADER_PATTERN.finditer(text))
    if not matches:
        return [("", text.strip())]

    sections = []
    # Any text before the first section header is treated as a leading fragment
    first_start = matches[0].start()
    if first_start > 0:
        leading_text = text[:first_start].strip()
        if leading_text:
            sections.append(("", leading_text))

    for i, m in enumerate(matches):
        header = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append((header, content))

    return sections


def clean_leading_fragment(text: str) -> str:
    """
    Remove leading fragmented sentences caused by chunking boundaries
    (e.g., words starting with lowercase, mid-sentence punctuation like 'mit, at the same time...').
    """
    lines = text.split("\n")
    cleaned_lines = []
    found_clean_start = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if not found_clean_start:
            # Check if this line looks like a mid-sentence chunk boundary
            # e.g., starts with lowercase letter or punctuation
            if stripped[0].islower() and not stripped.startswith(("http", "www")):
                continue
            # e.g., trailing words like "mit, at the same time"
            if re.match(r"^[a-z]{1,5}[,\.]\s+", stripped):
                continue
            found_clean_start = True

        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines) if cleaned_lines else text.strip()


def extract_relevant_passage(
    chunk_text: str,
    query: str,
    request_type: str = "GENERAL",
) -> str:
    """
    Extract the most relevant passage from chunk_text for the given query and request_type.
    Strips leading and trailing noise from unrelated sections.
    """
    if not chunk_text:
        return ""

    q_lower = query.lower()
    sections = split_sections(chunk_text)

    # Keywords from query (excluding generic stopwords)
    stopwords = {
        "what", "which", "does", "the", "and", "for", "with", "this", "that", "how",
        "can", "are", "tell", "about", "explain", "meaning", "meter", "iskra",
        "ما", "هو", "هي", "ماذا", "هل", "عن", "في", "العداد", "عداد", "إسكرا"
    }
    raw_tokens = re.findall(r"\b[A-Za-z0-9\u0600-\u06FF\-_]{2,}\b", q_lower)
    query_keywords = [t for t in raw_tokens if t not in stopwords]

    # Specific semantic concepts by request type
    if request_type == "ALARM" or "alarm" in q_lower or "unbalance" in q_lower:
        priority_concepts = ["unbalance", "mppul", "alarm", "power unbalance", "relay", "إنذار", "اتزان"]
    elif request_type == "MEASUREMENT" or any(w in q_lower for w in ["measure", "يقيس", "قياس", "بيقيس"]):
        priority_concepts = ["measure", "measurement", "metering", "voltage", "current", "active", "power", "energy", "instantaneous", "demand"]
    elif request_type == "COMMUNICATION" or any(w in q_lower for w in ["protocol", "communication", "اتصال", "بروتوكول"]):
        priority_concepts = ["protocol", "iec", "62056", "mode c", "optical", "rs485", "communication", "baud"]
    elif request_type == "ERROR_MEANING" or "error" in q_lower or "خطأ" in q_lower:
        priority_concepts = ["error", "code", "cpu", "fault", "خطأ", "كود"]
    else:
        priority_concepts = query_keywords

    # 1. First, check if any section header or content strongly matches query priority concepts
    best_section = None
    best_score = -1.0

    for header, content in sections:
        combined = f"{header}\n{content}".lower()
        score = 0.0

        # High reward for header match
        h_lower = header.lower()
        for kw in query_keywords:
            if kw in h_lower:
                score += 3.0
            elif kw in combined:
                score += 1.0

        for pc in priority_concepts:
            if pc in h_lower:
                score += 4.0
            elif pc in combined:
                score += 1.5

        # Penalize empty header (leading fragments)
        if not header:
            score -= 2.0

        if score > best_score:
            best_score = score
            best_section = (header, content)

    # 2. If a matching section was found and has a positive score, use it
    if best_section and best_score > 0:
        header, content = best_section
        clean_content = clean_leading_fragment(content)
        # Limit content to the relevant paragraph or first 3-4 sentences if very long
        paragraphs = [p.strip() for p in clean_content.split("\n\n") if p.strip()]
        if paragraphs:
            # Pick paragraph matching keywords
            matching_paras = [p for p in paragraphs if any(k in p.lower() for k in query_keywords or priority_concepts)]
            selected_body = "\n\n".join(matching_paras[:2]) if matching_paras else paragraphs[0]
        else:
            selected_body = clean_content

        if header:
            return f"{header}\n{selected_body}".strip()
        return selected_body.strip()

    # 3. Fallback: locate specific sentences containing the keywords in chunk
    cleaned_chunk = clean_leading_fragment(chunk_text)
    lines = [l.strip() for l in cleaned_chunk.split("\n") if l.strip()]
    matching_lines = []
    for line in lines:
        l_lower = line.lower()
        if any(k in l_lower for k in query_keywords or priority_concepts):
            matching_lines.append(line)

    if matching_lines:
        return "\n".join(matching_lines[:4])

    return cleaned_chunk[:300]
