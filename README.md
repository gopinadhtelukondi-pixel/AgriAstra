# AgriAstra

Climate intelligence and multi-crop decision support built with Python 3.11 and Streamlit.

## Run locally

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    streamlit run app.py

Use Python 3.11 for local development and choose Python 3.11 in Streamlit Community Cloud's deployment settings. The first Chroma ingestion downloads the sentence-transformer model and can take several minutes.

## Implemented workflow

- Location search uses the Open-Meteo geocoder and requires explicit confirmation when there are multiple matches.
- Location lookup defaults to India and can be switched to a global search. English, Hindi, and Telugu labels and geocoder results are supported.
- Forecast requests return the next seven daily values for the selected coordinates and local timezone.
- Historical comparisons use ERA5 for consistency, matching forecast calendar dates over the previous five complete calendar years. Rainfall anomalies use a percent only when the baseline is at least 1 mm; smaller baselines display an absolute difference.
- Forecast, ERA5 reanalysis, optional NASA POWER history, and hypothetical scenarios stay separate. NASA POWER is an optional independent cross-check and is never averaged into the ERA5 baseline.
- The crop catalogue covers paddy, cotton, maize, chilli, turmeric, groundnut, soybean, and red gram. Growth stages vary by crop; custom crops receive no crop-specific thresholds.
- Climate exposure is descriptive. The app does not invent validated thresholds, risk scores, loss estimates, or yield predictions.
- OIDC sign-in protects the workspace. Farm profiles, forecast snapshots, assessments, advisories, and simulations are scoped to the identity provider's stable account subject in SQLite. Assessment history can be downloaded as CSV.
- API responses are cached in data/cache. A successful forecast response is fresh for 30 minutes and can be displayed stale for up to 12 hours after a request fails. Historical data is fresh for 24 hours and can be displayed stale for up to 24 days. The interface labels stale values and preserves the original retrieval timestamp. Missing values are never replaced with examples.
- A LangGraph multi-agent workflow uses a Supervisor Agent, Climate Context Agent, Crop Evidence Agent, Farmer Advisor Agent, and Safety Review Agent. Retrieval is filtered to the selected crop; the model only explains Python-computed climate indicators alongside retrieved references. Missing evidence or credentials produces a limitation message, not an invented answer.
- The advisor includes a clearly labeled example exchange. It responds in the selected interface language and avoids giving crop-specific advice without indexed, crop-matched references.

## Agricultural references and RAG

1. Place verified publications from ICAR, PJTSAU, state agricultural departments, or agricultural universities under rag/documents/.
2. Copy manifest.example.json to manifest.json and record each source's title, issuing organization, applicable crop categories, and any known publication date/source URL. Untagged documents are skipped; crop categories are not guessed.
3. Install requirements.txt and run:

       python -m rag.ingest

PDF pages are extracted with PyPDF, divided into 1000-character chunks with 200-character overlap, encoded with Hugging Face sentence-transformers/all-MiniLM-L6-v2, and stored in persistent Chroma. Retrieved sources retain title, organization, crop, page number, URL, and publication date. Review citations against the original publications before relying on advice. Keep source licensing terms in mind.

## Authentication and secrets

The preferred sign-in method is Streamlit OIDC. The OIDC subject is the account key; an optional email allowlist can restrict access. For local development without an OIDC client, set `[agriaastra] allow_local_auth = true`; users can create local accounts with passwords of at least 12 characters. Passwords are stored as salted PBKDF2 hashes. This local mode does not verify email and should not be used for public deployment. For production, set `allow_local_auth = false`, create an OIDC client (the example uses Google), and register the deployed app's `/oauth2callback` URL. Generate a unique random `cookie_secret` and put the client ID and secret in the hosting platform's secrets manager. Do not commit secrets.

The advisor uses GEMINI_API_KEY and optionally GEMINI_MODEL (defaults to gemini-3.8-flash). For Streamlit Community Cloud, add all keys and the `[auth]` block in the app's settings, not in source control. Example local secrets:

    GEMINI_API_KEY = "your-key"
    GEMINI_MODEL = "gemini-3.8-flash"
    # For local testing without OIDC, add:
    [agriaastra]
    allow_local_auth = true
    # For OIDC, instead configure the [auth] block from the example.

## Tests

Run the test suite with:

    python -m pytest

Tests cover climate baselines, missing values, geocoding ambiguity, forecast validation, crop-stage catalogues, simulation boundaries, and SQLite history.

## Deployment preparation

The app entry point is app.py and requirements.txt is at the project root. To publish on Streamlit Community Cloud, push the project to a GitHub repository, choose app.py as the entry point, select Python 3.11 in Advanced settings, configure Gemini and OIDC values in Cloud secrets, add the deployed callback URL to your identity provider, and deploy. Keep `.streamlit/secrets.toml`, local databases, and cache files out of source control.

SQLite stores per-user records on disk and works for a single-instance MVP. Local data is excluded from source control. Streamlit Community Cloud's filesystem can be ephemeral, so a public deployment needing durable history should switch the persistence adapter to a managed PostgreSQL service and configure encrypted backups before launch; authentication and user scoping are already in place.

## Data sources and limitations

- Open-Meteo Forecast API supplies the seven-day forecast.
- Open-Meteo Historical Archive supplies ERA5 reanalysis. It is an estimate, not an exact ground-station record, and it has a different model product and resolution from the forecast.
- NASA POWER Daily API supplies an optional comparison for PRECTOTCORR, T2M_MAX, and T2M_MIN. Its grid and UTC day boundaries differ; the app reports it separately.
- Gemini explains retrieved evidence. Python performs numerical calculations.
- No verified agricultural documents are bundled. Therefore the initial advisor has no crop guidance until the project owner supplies and indexes authorized sources.
- Internet access is required for geocoding and weather. Streamlit's local cache is not a durable history store in Community Cloud.

