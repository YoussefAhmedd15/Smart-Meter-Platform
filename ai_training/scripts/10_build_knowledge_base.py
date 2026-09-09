from pathlib import Path
import re

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

KNOWLEDGE_DIR = PROJECT_ROOT / "ai_training" / "data" / "knowledge"
VECTOR_STORE_DIR = PROJECT_ROOT / "ai_training" / "vector_store"


# ============================================================
# SETTINGS
# ============================================================

COLLECTION_NAME = "iskra_knowledge"

# Lightweight multilingual embedding model.
# Good starting point for local RAG.
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_pdf_pages(pdf_path: Path):
    """Extract text while preserving page numbers."""

    reader = PdfReader(str(pdf_path))

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        text = text.strip()

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:
    """Normalize extracted PDF text."""

    text = text.replace("\x00", " ")

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Reduce excessive empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# CHUNKING
# ============================================================

def create_chunks(text: str):
    """
    Split text into overlapping chunks.

    We use character-based chunking for the first version
    to keep the pipeline simple and stable.
    """

    text = clean_text(text)

    if not text:
        return []

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(start + CHUNK_SIZE, text_length)

        # Try to end at a natural boundary
        if end < text_length:

            candidates = [
                text.rfind("\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("。", start, end),
                text.rfind(";", start, end),
            ]

            best_boundary = max(candidates)

            if best_boundary > start + (CHUNK_SIZE // 2):
                end = best_boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        next_start = end - CHUNK_OVERLAP

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# ============================================================
# BUILD DOCUMENTS
# ============================================================

def build_documents():
    """Read all PDFs and convert them into RAG documents."""

    pdf_files = sorted(KNOWLEDGE_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {KNOWLEDGE_DIR}"
        )

    documents = []
    metadatas = []
    ids = []

    total_chunks = 0

    for pdf_path in pdf_files:

        print(f"\nProcessing: {pdf_path.name}")

        pages = extract_pdf_pages(pdf_path)

        print(f"  Pages extracted: {len(pages)}")

        for page_data in pages:

            page_number = page_data["page"]
            text = clean_text(page_data["text"])

            chunks = create_chunks(text)

            for chunk_index, chunk in enumerate(chunks):

                document_id = (
                    f"{pdf_path.stem}"
                    f"_page_{page_number}"
                    f"_chunk_{chunk_index}"
                )

                documents.append(chunk)

                metadatas.append(
                    {
                        "source": pdf_path.name,
                        "file_type": "pdf",
                        "page": page_number,
                        "chunk": chunk_index,
                    }
                )

                ids.append(document_id)

                total_chunks += 1

    print(f"\nTotal documents/chunks: {total_chunks}")

    return documents, metadatas, ids


# ============================================================
# CHROMA DATABASE
# ============================================================

def build_vector_database(documents, metadatas, ids):

    print("\nLoading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    print("Embedding model loaded.")

    print("\nOpening ChromaDB...")

    client = chromadb.PersistentClient(
        path=str(VECTOR_STORE_DIR)
    )

    # Rebuild the collection cleanly.
    # This prevents duplicate chunks when the script is rerun.
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Deleted old collection: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "ISKRA Smart Meter Knowledge Base"
        },
    )

    print("\nCreating embeddings...")

    embeddings = model.encode(
        documents,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embeddings = embeddings.tolist()

    print("Embeddings created.")

    print("\nAdding documents to ChromaDB...")

    # Add in batches
    batch_size = 100

    for start in range(0, len(documents), batch_size):

        end = min(start + batch_size, len(documents))

        collection.add(
            ids=ids[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
            embeddings=embeddings[start:end],
        )

        print(
            f"Added {end}/{len(documents)} chunks"
        )

    print("\nVector database created successfully.")

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Documents: {collection.count()}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("ISKRA KNOWLEDGE BASE BUILDER")
    print("=" * 60)

    print(f"\nKnowledge directory:")
    print(KNOWLEDGE_DIR)

    print(f"\nVector store:")
    print(VECTOR_STORE_DIR)

    documents, metadatas, ids = build_documents()

    if not documents:
        raise RuntimeError(
            "No usable text was extracted from the knowledge files."
        )

    build_vector_database(
        documents,
        metadatas,
        ids,
    )

    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()