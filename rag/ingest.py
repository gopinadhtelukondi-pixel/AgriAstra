"""Ingest verified PDF/text sources into Chroma with crop and citation metadata.

Add entries to manifest.json. Documents without explicit crop_category metadata are skipped;
this prevents accidental cross-crop retrieval.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCUMENTS = ROOT / "documents"
MANIFEST = DOCUMENTS / "manifest.json"
VECTOR_DIR = ROOT / "chroma_db"
COLLECTION = "agricultural_references"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def ingest():
    try:
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from pypdf import PdfReader
    except ImportError as exc:
        raise SystemExit("Install the RAG dependencies from requirements.txt before ingestion.") from exc

    if not MANIFEST.exists():
        raise SystemExit("Create rag/documents/manifest.json first. See rag/documents/README.md.")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )
    store = Chroma(collection_name=COLLECTION, persist_directory=str(VECTOR_DIR), embedding_function=embedder)
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    docs = []
    for file_path in sorted(DOCUMENTS.iterdir()):
        if file_path.suffix.lower() not in {".pdf", ".txt", ".md"}:
            continue
        meta = manifest.get(file_path.name)
        if not meta:
            print(f"Skipped {file_path.name}: no manifest metadata.")
            continue
        categories = [str(item).strip().casefold() for item in meta.get("crop_category", []) if str(item).strip()]
        if not categories or not meta.get("document_title") or not meta.get("issuing_organization"):
            print(f"Skipped {file_path.name}: title, organization and crop_category are required.")
            continue
        pages = []
        if file_path.suffix.lower() == ".pdf":
            for page_number, page in enumerate(PdfReader(str(file_path)).pages, 1):
                pages.append((page.extract_text() or "", page_number))
        else:
            pages.append((file_path.read_text(encoding="utf-8", errors="ignore"), meta.get("page_number", "n/a")))
        for text, page_number in pages:
            if not text.strip():
                continue
            for chunk in splitter.split_text(text):
                for crop in categories:
                    chunk_meta = {
                        "document_title": str(meta["document_title"]),
                        "issuing_organization": str(meta["issuing_organization"]),
                        "crop_category": crop,
                        "page_number": str(page_number),
                        "source_url": str(meta.get("source_url", "")),
                        "publication_date": str(meta.get("publication_date", "")),
                        "source_file": file_path.name,
                        "region": str(meta.get("region", "")),
                    }
                    docs.append(Document(page_content=chunk, metadata=chunk_meta))
    if not docs:
        print("No eligible source chunks found.")
        return 0
    # Replace previous chunks for each ingested source file.
    collection = store._collection
    source_files = sorted({doc.metadata["source_file"] for doc in docs})
    for file_name in source_files:
        found = collection.get(where={"source_file": file_name}, include=["metadatas"])
        if found.get("ids"):
            collection.delete(ids=found["ids"])
    ids = []
    for doc in docs:
        identity = "|".join((doc.metadata["source_file"], doc.metadata["crop_category"], doc.metadata["page_number"], doc.page_content))
        ids.append(hashlib.sha256(identity.encode("utf-8")).hexdigest())
    store.add_documents(docs, ids=ids)
    print(f"Indexed {len(docs)} chunks from {len(source_files)} source files in {VECTOR_DIR}.")
    return len(docs)


if __name__ == "__main__":
    ingest()

