# Verified agricultural reference documents

Put official agricultural publications here (ICAR, state agriculture departments, PJTSAU, or agricultural universities). Verify the issuing organization and crop relevance before indexing.

Copy manifest.example.json to manifest.json and add one record per file. Required metadata: document_title, issuing_organization, crop_category. Optional: publication_date and source_url. crop_category values must match the crop names displayed in the app after normalization (paddy, cotton, maize, chilli, turmeric, groundnut, soybean, red gram). Documents without metadata are skipped; a source is never assigned to a crop by guessing from its content.

From the project root, run:

    python -m rag.ingest

PDF pages are extracted with PyPDF, split into 1000-character chunks with 200-character overlap, embedded using sentence-transformers/all-MiniLM-L6-v2, and stored persistently in Chroma. Each indexed chunk stores title, issuing organization, crop, page, source URL, publication date, and filename. Keep a copy of the source publication and follow its license terms.

