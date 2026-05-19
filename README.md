# iPSC Protocol MVP

Minimal local pipeline for collecting, structuring, and querying iPSC differentiation protocols from `protocols.io`.

## What it does

This MVP can:

- search/fetch public `protocols.io` protocols when API/runtime access works
- fall back to local JSON/HTML/TXT files when live API access is unavailable
- save raw protocol snapshots to `data/raw/`
- normalize protocol text into sections and ordered steps
- extract first-pass structured fields using regex and curated dictionaries
- store normalized results in SQLite
- export CSV/JSON for inspection
- query protocols by target cell type from the command line
- expose an API that reads articles with an LLM and synthesizes a stage-wise DOE for protocol optimization

## Project structure

```text
ipsc_protocol_mvp/
  README.md
  requirements.txt
  .env.example
  main.py
  api_server.py
  llm_protocol_doe.py
  config.py
  db.py
  schemas.py
  protocolsio_client.py
  parser.py
  extractor.py
  normalize.py
  query.py
  seed_keywords.py
  collection_targets.py
  dictionaries.py
  exports/
  data/
    raw/
      local_seed/
    processed/
```

## Install

Use Python 3.11.

```bash
cd "/Users/qiaoqiaowan/Desktop/创业/AI iPSC differentiation/Protocol.io/ipsc_protocol_mvp"
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment setup

Copy `.env.example` into `.env` or export environment variables manually.

Relevant variables:

- `PROTOCOLSIO_API_TOKEN`: optional API token
- `PROTOCOLSIO_SEARCH_URL`: best-effort search endpoint
- `PROTOCOLSIO_PROTOCOL_URL_TEMPLATE`: best-effort detail endpoint
- `SPECIES_DEFAULT`: fallback species
- `LOG_LEVEL`: logging level
- `OPENAI_API_KEY`: required for the LLM DOE API
- `OPENAI_MODEL`: optional override, default `gpt-4.1-mini`
- `PMC_XML_DIR`: optional local PMC XML directory used for `PMC1234567` lookup

Example:

```bash
export OPENAI_API_KEY="your-key"
export PMC_XML_DIR="/Users/qiaoqiaowan/Desktop/创业/AI iPSC differentiation/PMC/3/pmc_xml_batched"
```

## Run the pipeline

### 1. Ingest

Auto mode tries API first, then local files:

```bash
python main.py ingest
```

Force local mode:

```bash
python main.py ingest --mode local
python main.py ingest --mode local --cell-type cardiomyocyte
```

### 2. Parse

```bash
python main.py parse
```

### 3. Extract

```bash
python main.py extract
```

### 4. Export

```bash
python main.py export
```

Outputs:

- `exports/protocols_export.csv`
- `exports/protocols_export.json`
- `exports/protocol_review.csv`

### 5. Collections

```bash
python main.py collections
```

This exports `exports/target_collection_manifest.json` with the four prioritized cell types:

- `cardiomyocyte`
- `dopaminergic neuron`
- `hepatocyte`
- `NK cell`

Each collection is configured with a target of about 100 protocols and a curated keyword list for future ingestion.

### 6. Query

```bash
python main.py query --cell-type cardiomyocyte
python main.py query --cell-type dopaminergic
```

## LLM DOE API

Start the API server:

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

Open the built-in frontend:

- `http://127.0.0.1:8000/`

### Endpoints

- `GET /`
- `GET /health`
- `POST /analyze-protocol-doe`

### Request body

```json
{
  "sources": [
    "/Users/qiaoqiaowan/Desktop/创业/AI iPSC differentiation/PMC/3/pmc_xml_batched",
    "PMC11251028",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC11256493/"
  ],
  "target_cell_type": "cardiomyocyte",
  "article_limit": 10,
  "start_cell_type_hint": "iPSC",
  "max_candidate_files": 5000,
  "max_chars_per_article": 22000,
  "save_json_path": "/tmp/cardiomyocyte_doe.json"
}
```

### Example curl

```bash
curl -X POST http://127.0.0.1:8000/analyze-protocol-doe \
  -H 'Content-Type: application/json' \
  -d '{
    "sources": ["/Users/qiaoqiaowan/Desktop/创业/AI iPSC differentiation/PMC/3/pmc_xml_batched"],
    "target_cell_type": "cardiomyocyte",
    "article_limit": 10,
    "start_cell_type_hint": "iPSC",
    "save_json_path": "/tmp/cardiomyocyte_doe.json"
  }'
```

### What the API returns

The JSON response contains:

- `selection_summary`: which candidate articles were scanned and selected
- `article_extractions`: per-article LLM extraction of stage timeline, media, factors, concentrations, markers, and evidence
- `doe_synthesis`: consensus intermediate-stage map, factor/concentration ranges, recommended anchor protocol, DOE screening factors, and the logic behind the summary

## Mock demo input

A small offline demo protocol is included in:

- `data/raw/local_seed/mock_ipsc_cardiomyocyte_protocol.json`

This lets the full pipeline run even without live API access.

## Database schema

### `protocols`

- `id`
- `source`
- `source_protocol_id`
- `title`
- `abstract`
- `source_url`
- `species`
- `start_cell_type`
- `target_cell_type`
- `raw_text`
- `created_at`

### `stages`

- `id`
- `protocol_id`
- `stage_order`
- `stage_name`
- `intermediate_cell_type`
- `start_day`
- `end_day`
- `basal_medium`
- `matrix`
- `notes`

### `factors`

- `id`
- `stage_id`
- `name`
- `normalized_name`
- `concentration_value`
- `concentration_text`
- `unit`
- `role`

## Extraction behavior

This MVP uses regex plus curated dictionaries for:

- factor synonyms
- cell type synonyms
- basal media
- matrices/coatings
- time expressions
- concentration expressions

Stage inference is conservative:

- if a day range is clear, it is stored
- if a factor and concentration are clear, they are stored
- if the signal is weak, fields stay null

The DOE API is different:

- it reads full article text from URLs, local files, directories, or PMCIDs
- it ranks candidate articles for the requested target cell type
- it uses an LLM to extract protocol trajectories per article
- it runs a second LLM synthesis step to generate a consensus DOE and preserve the underlying logic

## Known limitations

- `protocols.io` API/search payload shapes may vary, so live ingestion is best-effort only
- the parser is intentionally simple and may miss complex nested sections
- factor extraction links concentrations to the local step, not always to the exact reagent mention
- target cell type inference is conservative and dictionary-driven
- the DOE API requires `OPENAI_API_KEY`
- if you pass a very large directory, candidate scanning can take time
- some article URLs may block scraping or provide only partial content

## Future improvements

- add confidence scoring per article and per stage in the DOE API
- support cached article text snapshots to reduce repeat API cost
- add a CSV export endpoint for DOE factor matrices
- add unit tests and a small fixture set
