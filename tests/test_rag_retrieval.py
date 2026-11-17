from pathlib import Path

import rag.retriever as retriever


def test_retrieval_filter_is_exactly_selected_crop(monkeypatch, tmp_path):
    monkeypatch.setattr(retriever, "VECTOR_DIR", tmp_path)
    (tmp_path / "chroma.sqlite3").touch()
    class FakeStore:
        def similarity_search_with_score(self, question, k, filter):
            assert question == "rain"
            assert k == 5
            assert filter == {"crop_category": "cotton"}
            return []
    monkeypatch.setattr(retriever, "_vectorstore", lambda: FakeStore())
    assert retriever.retrieve("rain", "Cotton") == []

