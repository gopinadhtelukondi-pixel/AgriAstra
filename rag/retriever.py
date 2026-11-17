"""Crop-filtered Chroma retrieval using local Hugging Face sentence embeddings."""
import os
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VECTOR_DIR = Path(os.getenv("AGRIASTRA_CHROMA_DIR", str(ROOT / "chroma_db")))
COLLECTION = "agricultural_references"
EMBEDDING_MODEL = os.getenv("AGRIASTRA_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def _vectorstore():
    try:
        from langchain_chroma import Chroma
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError("Install the RAG requirements from requirements.txt to enable document retrieval.") from exc
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, model_kwargs={"device": "cpu"})
    return Chroma(
        collection_name=COLLECTION,
        persist_directory=str(VECTOR_DIR),
        embedding_function=embeddings,
    )


def has_index():
    """Return whether the persistent Chroma index exists on disk."""
    return (VECTOR_DIR / "chroma.sqlite3").is_file()


def retrieve(question, crop, k=5, region=None):
    """Retrieve only chunks explicitly tagged for the selected crop."""
    docs_scores = []
    if has_index():
        store = _vectorstore()
        docs_scores = store.similarity_search_with_score(question, k=k, filter={"crop_category": crop.casefold()})
    results = []
    for document, score in docs_scores:
        meta = document.metadata
        source_region = str(meta.get("region", "")).casefold()
        if source_region and region and source_region not in str(region).casefold():
            continue
        results.append({
            "text": document.page_content,
            "distance": float(score),
            "title": meta.get("document_title", meta.get("source_file", "Agricultural reference")),
            "organization": meta.get("issuing_organization", "Organization not recorded"),
            "crop": meta.get("crop_category", crop),
            "page": meta.get("page_number", "n/a"),
            "source_url": meta.get("source_url", ""),
            "publication_date": meta.get("publication_date", ""),
            "source_file": meta.get("source_file", ""),
        })
    if results:
        return results
    return _local_text_references(question, crop, k, region)


def _local_text_references(question, crop, k, region=None):
    """Use explicitly tagged bundled Markdown/text guides before Chroma is built."""
    documents_dir = ROOT / "documents"
    manifest_path = documents_dir / "manifest.json"
    if not manifest_path.is_file():
        return []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    terms = set(re.findall(r"[a-z0-9]+", question.casefold()))
    results = []
    for filename, metadata in manifest.items():
        categories = [str(value).strip().casefold() for value in metadata.get("crop_category", [])]
        if crop.casefold() not in categories or Path(filename).suffix.casefold() not in {".md", ".txt"}:
            continue
        source_region = str(metadata.get("region", "")).casefold()
        if source_region and (not region or source_region not in str(region).casefold()):
            continue
        source_path = documents_dir / filename
        try:
            content = source_path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if not content:
            continue
        doc_terms = set(re.findall(r"[a-z0-9]+", content.casefold()))
        overlap = len(terms & doc_terms)
        results.append({
            "text": content,
            "distance": float(1 / (1 + overlap)),
            "title": metadata.get("document_title", filename),
            "organization": metadata.get("issuing_organization", "Organization not recorded"),
            "crop": crop,
            "page": "n/a",
            "source_url": metadata.get("source_url", ""),
            "publication_date": metadata.get("publication_date", ""),
            "source_file": filename,
            "region": source_region,
        })
    results.sort(key=lambda item: item["distance"])
    return results[:k]

