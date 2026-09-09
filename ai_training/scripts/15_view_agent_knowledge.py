"""
15_view_agent_knowledge.py
Inspect and display all knowledge chunks stored in ChromaDB that the ISKRA AI Agent can see.
Automatically exports the full knowledge base to a clean, searchable .txt file!

Usage:
  python ai_training/scripts/15_view_agent_knowledge.py                  # Exports & displays ALL 501 Core Technical Knowledge Chunks to .txt
  python ai_training/scripts/15_view_agent_knowledge.py --summary        # View summary metrics & breakdown tables only
  python ai_training/scripts/15_view_agent_knowledge.py --file "Error cpu.pdf" # View all chunks of a specific document
  python ai_training/scripts/15_view_agent_knowledge.py --model MT174    # View all chunks for a specific meter model
  python ai_training/scripts/15_view_agent_knowledge.py --type ERROR_REFERENCE # View error reference chunks
  python ai_training/scripts/15_view_agent_knowledge.py --search "Error 70"     # Test what the agent retrieves
  python ai_training/scripts/15_view_agent_knowledge.py --all            # Stream and view ALL 38,274 chunks (including trackers)
  python ai_training/scripts/15_view_agent_knowledge.py --out "custom.txt" # Specify custom output text file
"""

import sys
import os
import argparse
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter

# Windows console encoding safety
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import chromadb

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_training.agent.config import (
    VECTOR_STORE_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
)

DEFAULT_EXPORT_PATH = PROJECT_ROOT / "ai_training" / "agent_knowledge_export.txt"


def format_separator(title: str = "", char: str = "=", length: int = 80) -> str:
    if not title:
        return char * length
    prefix = f" {title} "
    total_padding = max(0, length - len(prefix))
    left = total_padding // 2
    right = total_padding - left
    return f"{char * left}{prefix}{char * right}"


def fetch_all_metadata_and_stats(collection) -> Dict[str, Any]:
    """
    Safely stream metadatas from ChromaDB in batches to prevent SQLite parameter limits.
    """
    total_count = collection.count()
    batch_size = 1000
    all_metadatas = []
    all_ids = []

    for offset in range(0, total_count, batch_size):
        batch = collection.get(
            limit=batch_size,
            offset=offset,
            include=["metadatas"]
        )
        batch_ids = batch.get("ids", [])
        batch_metas = batch.get("metadatas", [])
        all_ids.extend(batch_ids)
        all_metadatas.extend(batch_metas)

    # Compute breakdown statistics
    files_stats = defaultdict(lambda: {
        "chunks": 0,
        "meter_model": "UNKNOWN",
        "document_type": "OTHER",
        "is_tracker": False,
        "format": "UNKNOWN",
    })
    model_counts = Counter()
    doc_type_counts = Counter()
    tracker_chunks = 0
    technical_chunks = 0

    for meta in all_metadatas:
        if not meta:
            continue
        src = meta.get("source", "UNKNOWN")
        model = meta.get("meter_model", "UNKNOWN")
        doc_type = meta.get("document_type", "OTHER")
        is_tracker = meta.get("is_tracker", False)
        ext = meta.get("file_type", "unknown").upper()

        files_stats[src]["chunks"] += 1
        files_stats[src]["meter_model"] = model
        files_stats[src]["document_type"] = doc_type
        files_stats[src]["is_tracker"] = is_tracker
        files_stats[src]["format"] = ext

        model_counts[model] += 1
        doc_type_counts[doc_type] += 1
        if is_tracker:
            tracker_chunks += 1
        else:
            technical_chunks += 1

    return {
        "total_count": total_count,
        "files_stats": files_stats,
        "model_counts": model_counts,
        "doc_type_counts": doc_type_counts,
        "technical_chunks": technical_chunks,
        "tracker_chunks": tracker_chunks,
    }


def build_summary_text(stats: Dict[str, Any]) -> str:
    lines = []
    lines.append(format_separator("ISKRA AGENT VECTOR KNOWLEDGE BASE OVERVIEW"))
    lines.append(f"Export Timestamp  : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Vector Store Path : {VECTOR_STORE_DIR}")
    lines.append(f"Collection Name   : {COLLECTION_NAME}")
    lines.append(f"Embedding Model   : {EMBEDDING_MODEL}")
    lines.append(f"Total Chunks      : {stats['total_count']:,}")
    lines.append(f" - Core Technical Knowledge Chunks : {stats['technical_chunks']:,} (Manuals, Errors, Specs, Guides)")
    lines.append(f" - Field Support & Tracker Chunks  : {stats['tracker_chunks']:,} (SCDC & L1/L2 logs)")
    lines.append(format_separator())
    lines.append("")
    lines.append(format_separator("DOCUMENT INVENTORY & CHUNK DISTRIBUTION", "-"))
    lines.append(f"{'#':<3} | {'Source Document Filename':<42} | {'Format':<6} | {'Model':<10} | {'Type':<24} | {'Chunks':>6}")
    lines.append("-" * 102)

    sorted_files = sorted(stats["files_stats"].items(), key=lambda x: (x[1]["is_tracker"], x[0]))
    for idx, (filename, info) in enumerate(sorted_files, start=1):
        tracker_flag = " [TRACKER]" if info["is_tracker"] else ""
        type_display = (info["document_type"] + tracker_flag)[:24]
        lines.append(f"{idx:<3} | {filename:<42} | {info['format']:<6} | {info['meter_model']:<10} | {type_display:<24} | {info['chunks']:>6,}")

    lines.append("-" * 102)
    lines.append(f"{'TOTAL CHUNKS ACROSS ALL 20 FILES:':<91} {stats['total_count']:>6,}")
    lines.append("")
    lines.append(format_separator("CHUNKS BY METER MODEL", "-"))
    for model, cnt in stats["model_counts"].most_common():
        pct = (cnt / stats["total_count"]) * 100
        bar = "#" * int(pct // 4)
        lines.append(f"  * {model:<12} : {cnt:>6,} chunks ({pct:>5.1f}%) {bar}")

    lines.append("")
    lines.append(format_separator("CHUNKS BY DOCUMENT CATEGORY", "-"))
    for doc_type, cnt in stats["doc_type_counts"].most_common():
        pct = (cnt / stats["total_count"]) * 100
        bar = "#" * int(pct // 4)
        lines.append(f"  * {doc_type:<25} : {cnt:>6,} chunks ({pct:>5.1f}%) {bar}")
    lines.append(format_separator("", "-"))
    return "\n".join(lines)


def build_grouped_chunks_text(docs: List[str], metas: List[Dict[str, Any]], ids: List[str]) -> str:
    """Group and format chunks organized by source document into full text."""
    by_file = defaultdict(list)
    for chunk_id, doc, meta in zip(ids, docs, metas):
        src = meta.get("source", "UNKNOWN") if meta else "UNKNOWN"
        by_file[src].append((chunk_id, doc, meta))

    lines = []
    total_printed = len(docs)
    total_docs = len(by_file)
    lines.append(f"\nDisplaying {total_printed:,} chunks across {total_docs} document(s):\n")

    for doc_idx, (src_file, chunk_list) in enumerate(sorted(by_file.items()), start=1):
        first_meta = chunk_list[0][2] or {}
        model = first_meta.get("meter_model", "UNKNOWN")
        doc_type = first_meta.get("document_type", "OTHER")
        fmt = first_meta.get("file_type", "").upper()

        lines.append("\n" + "=" * 90)
        lines.append(f">>> DOCUMENT [{doc_idx}/{total_docs}]: {src_file} ({len(chunk_list)} chunks) | Model: {model} | Type: {doc_type} | Format: {fmt}")
        lines.append("=" * 90)

        for c_idx, (chunk_id, doc, meta) in enumerate(chunk_list, start=1):
            meta = meta or {}
            page = meta.get("page", "?")
            sheet = meta.get("sheet", "")
            loc = f"Page {page}" if not sheet else f"Sheet: {sheet}, Row {page}"

            lines.append(f"\n  --- [Chunk {c_idx}/{len(chunk_list)}] ID: {chunk_id} | {loc} ---")
            clean_doc = (doc or "").strip()
            for l in clean_doc.splitlines():
                lines.append(f"    {l}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="View & Export ISKRA AI Agent Vector Knowledge Base Content")
    parser.add_argument("--summary", action="store_true", help="Show summary metrics and document distribution tables only")
    parser.add_argument("--file", type=str, default="", help="Filter chunks by source document filename (substring match)")
    parser.add_argument("--model", type=str, default="", help="Filter chunks by meter model (e.g. MT174, ME514, MT514)")
    parser.add_argument("--type", type=str, default="", help="Filter chunks by document type (e.g. ERROR_REFERENCE, METER_MANUAL)")
    parser.add_argument("--search", type=str, default="", help="Run retrieval query to see what the agent retrieves")
    parser.add_argument("--all", action="store_true", help="Stream and export ALL 38,274 chunks (including tracker records)")
    parser.add_argument("--limit", type=int, default=None, help="Optional: limit number of chunks displayed")
    parser.add_argument("--out", "--output", type=str, default=str(DEFAULT_EXPORT_PATH), help=f"Path to save output .txt file (default: {DEFAULT_EXPORT_PATH})")
    parser.add_argument("--no-console-dump", action="store_true", help="Only export to .txt file without printing all chunks to terminal")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"[ERROR] Could not open collection '{COLLECTION_NAME}': {e}")
        sys.exit(1)

    # 1. Fetch metadata statistics
    stats = fetch_all_metadata_and_stats(collection)
    summary_text = build_summary_text(stats)
    print(summary_text)

    if args.summary:
        return

    # 2. Handle Semantic / Hybrid Agent Search
    if args.search:
        print("\n" + format_separator(f"AGENT RETRIEVAL SIMULATION: '{args.search}'"))
        try:
            from ai_training.rag.retriever import HybridRetriever
            retriever = HybridRetriever()
            top_k = args.limit or 10
            results = retriever.search(args.search, top_k=top_k)
            print(f"Retrieved {len(results)} chunks for query: '{args.search}'")
            search_lines = [summary_text, f"\nAGENT RETRIEVAL FOR: '{args.search}'\n"]
            for idx, r in enumerate(results, start=1):
                meta = r.get("metadata", {})
                block = [
                    "-" * 80,
                    f"[{idx}] Match Type: {r.get('evidence_type')} | Distance: {r.get('distance', 0.0):.4f}",
                    f"    Source    : {meta.get('source')} (Page {meta.get('page')})",
                    f"    Model     : {meta.get('meter_model')} | Type: {meta.get('document_type')}",
                ]
                if r.get("matched_line"):
                    block.append(f"    Exact Line: {r.get('matched_line')}")
                block.append("    Text      :")
                text = r.get("text", r.get("document", ""))
                for line in text.splitlines():
                    block.append(f"      {line}")
                formatted_block = "\n".join(block)
                print(formatted_block)
                search_lines.append(formatted_block)

            out_path = Path(args.out)
            out_path.write_text("\n".join(search_lines), encoding="utf-8")
            print(f"\n[OK] Retrieval simulation saved to: {out_path.resolve()}")
        except Exception as e:
            print(f"[ERROR] Agent retrieval test failed: {e}")
        return

    # 3. Knowledge Extraction & Export
    print("\n" + format_separator("EXPORTING KNOWLEDGE TO TEXT FILE"))

    all_docs = []
    all_metas = []
    all_ids = []

    if args.all:
        print("Gathering ALL 38,274 chunks across entire database (including Field Trackers)...")
        batch_size = 1000
        total_in_db = collection.count()
        for offset in range(0, total_in_db, batch_size):
            batch = collection.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
            for d, m, i in zip(batch.get("documents", []), batch.get("metadatas", []), batch.get("ids", [])):
                if args.model and m and m.get("meter_model") != args.model:
                    continue
                if args.type and m and m.get("document_type") != args.type:
                    continue
                if args.file and m and args.file.lower() not in (m.get("source", "").lower()):
                    continue
                all_docs.append(d)
                all_metas.append(m)
                all_ids.append(i)
                if args.limit and len(all_docs) >= args.limit:
                    break
            if args.limit and len(all_docs) >= args.limit:
                break
    else:
        # Default: Verified Core Technical Documentation Chunks (501 chunks)
        where_filter = {}
        if not args.file:
            where_filter["is_tracker"] = False
            print("Exporting ALL 501 Verified Core Technical Documentation Chunks (Pass --all to include 37k+ Tracker logs).")

        if args.model:
            where_filter["meter_model"] = args.model
            print(f"Filtering by meter model: {args.model}")

        if args.type:
            where_filter["document_type"] = args.type
            print(f"Filtering by document type: {args.type}")

        if where_filter:
            data = collection.get(where=where_filter, limit=args.limit, include=["documents", "metadatas"])
            all_docs = data.get("documents", [])
            all_metas = data.get("metadatas", [])
            all_ids = data.get("ids", [])
        elif args.file:
            batch_size = 1000
            total_in_db = collection.count()
            for offset in range(0, total_in_db, batch_size):
                batch = collection.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
                for d, m, i in zip(batch.get("documents", []), batch.get("metadatas", []), batch.get("ids", [])):
                    if m and args.file.lower() in (m.get("source", "").lower()):
                        all_docs.append(d)
                        all_metas.append(m)
                        all_ids.append(i)
                        if args.limit and len(all_docs) >= args.limit:
                            break
                if args.limit and len(all_docs) >= args.limit:
                    break
        else:
            data = collection.get(limit=args.limit, include=["documents", "metadatas"])
            all_docs = data.get("documents", [])
            all_metas = data.get("metadatas", [])
            all_ids = data.get("ids", [])

    # Format chunks text
    chunks_text = build_grouped_chunks_text(all_docs, all_metas, all_ids)

    # Write to .txt file
    out_path = Path(args.out)
    full_output_content = summary_text + "\n\n" + chunks_text + "\n\n" + format_separator("END OF KNOWLEDGE EXPORT")
    out_path.write_text(full_output_content, encoding="utf-8")

    size_kb = out_path.stat().st_size / 1024
    print(f"\n" + "=" * 80)
    print(f"SUCCESSFULLY EXPORTED TO: {out_path.resolve()}")
    print(f"Total Chunks Written    : {len(all_docs):,}")
    print(f"File Size               : {size_kb:.1f} KB")
    print(f"=" * 80)

    # If the user ran without --no-console-dump and with a small limit or filter, show in console
    if not args.no_console_dump and args.limit and args.limit <= 20:
        print(chunks_text)
    else:
        print(f"\n[NOTE] Because the knowledge base is large ({len(all_docs):,} chunks), it was written to:")
        print(f"       --> {out_path.resolve()}")
        print("       Open it in VS Code, Notepad, or your editor to search and read cleanly!")


if __name__ == "__main__":
    main()
