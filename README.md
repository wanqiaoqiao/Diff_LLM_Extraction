[README_PACKAGE.md](https://github.com/user-attachments/files/28014601/README_PACKAGE.md)
# `ipsc-llm-doe`

A small Python package that turns stem-cell differentiation articles into a practical DOE.

It is built for the workflow you described:

1. Use an LLM to read full articles.
2. Extract the differentiation protocol article by article.
3. Select and summarize 10 relevant articles.
4. Reconstruct the stage-by-stage trajectory from `iPSC/hPSC` to the target lineage.
5. Aggregate time ranges, factors, concentrations, and markers.
6. Generate:
   - an `anchor protocol`
   - a first-pass `DOE`
   - the logic and evidence behind the synthesis

This package also supports a sixth signal layer:

7. `commercial_web_search` influence
   - use public commercial/manufacturing methods to bias the `anchor protocol`
   - but **deprioritize proprietary or under-described company factors in the first DOE**

## Why this extra commercial step exists

Academic papers optimize for biological insight and publishability.
Commercial programs often optimize for:
- manufacturability
- reproducibility
- scalability
- feeder-free or serum-free operation
- cryopreservation compatibility
- QC-friendly intermediate states

Those commercial/public signals can be very useful for the `anchor protocol`.
But they should not automatically dominate the first DOE, especially when the public description is proprietary, vague, or kit-based.

So the package uses this rule:

- `anchor protocol`: can be biased toward commercial/publicly repeated modules
- `DOE`: should mostly test explicit, academically repeated, factor-level variables

## Package structure

```text
src/ipsc_llm_doe/
  __init__.py
  cli.py
  llm_client.py
  models.py
  pipeline.py
  prompts.py
  render.py
  sources.py
  web_search.py
```

## The analysis path, step by step

### Step 1. Collect sources
Input can be:
- local PMC XML directory
- local article files
- PMCID
- URL

Implemented in:
- `sources.py`

This step:
- reads text from XML / HTML / TXT
- normalizes raw text
- creates candidate article objects

### Step 2. Add commercial/public method signals
Implemented in:
- `web_search.py`

This step is where you asked to include web search / company influence.

Current package behavior:
- stores explicit commercial/public method signals separately from academic article extraction
- keeps them auditable
- passes them into final synthesis as a separate evidence layer

Decision rule:
- if a company method is public, explicit, and also repeated in academic literature, it may influence both `anchor protocol` and `DOE`
- if a company method is proprietary or under-described, it may influence `anchor protocol` only and be marked as `deprioritized in DOE`

### Step 3. Rank article candidates
Implemented in:
- `sources.py`
- `pipeline.py`

This step scores candidates by:
- target-cell-type relevance
- pluripotent-cell relevance
- protocol-like wording
- optional commercial/manufacturing alignment

Important:
- academic relevance and commercial alignment are kept separate
- they are combined only for ranking

### Step 4. Use the LLM to extract each article
Implemented in:
- `llm_client.py`
- `prompts.py`
- `pipeline.py`

For each selected article, the package asks the model to extract:
- starting cell type
- final cell type
- every intermediate stage
- time windows
- basal medium
- factors
- concentrations
- markers
- evidence sentences
- protocol notes / uncertainty

This is the article-level extraction stage.

### Step 5. Synthesize the multi-article DOE
Implemented in:
- `pipeline.py`
- `prompts.py`

The package then sends the extracted article summaries plus the commercial/public method signals into a second LLM synthesis step.

The output must contain:
- consensus stage map
- factor and concentration ranges by stage
- recommended anchor protocol
- DOE
- logic and basis
- commercial-method influence rules

### Step 6. Render outputs
Implemented in:
- `render.py`

Outputs:
- machine-readable JSON
- human-readable TXT

The TXT is designed to match the style you have been using for:
- dopaminergic progenitors
- cardiomyocyte
- NK cell
- corneal epithelial cells
- pancreatic beta-cell

## Installation

From the project root:

```bash
cd "/Users/qiaoqiaowan/Desktop/iPSC/AI iPSC differentiation/literature/Protocol.io/ipsc_protocol_mvp"
source .venv/bin/activate
pip install -e .
```

## Required environment variable

```bash
export OPENAI_API_KEY="your_api_key_here"
```

Optional:

```bash
export OPENAI_MODEL="gpt-4.1-mini"
```

## Example usage

### Dopaminergic progenitors

```bash
ipsc-doe \
  --source "/Users/qiaoqiaowan/Desktop/iPSC/AI iPSC differentiation/literature/PMC/3/pmc_xml_batched" \
  --target-cell-type "dopaminergic progenitors" \
  --article-limit 10 \
  --output-dir "/Users/qiaoqiaowan/Desktop/iPSC/AI iPSC differentiation/literature/PMC/5/package_outputs" \
  --stem "dopaminergic_progenitor_doe"
```

### Pancreatic beta-like cells

```bash
ipsc-doe \
  --source "/Users/qiaoqiaowan/Desktop/iPSC/AI iPSC differentiation/literature/PMC/3/pmc_xml_batched" \
  --target-cell-type "pancreatic beta-cell" \
  --article-limit 10 \
  --output-dir "/Users/qiaoqiaowan/Desktop/iPSC/AI iPSC differentiation/literature/PMC/5/package_outputs" \
  --stem "pancreatic_beta_cell_doe"
```

## What gets saved

For each run:
- `*.json`
  - config
  - commercial signals
  - ranked candidates
  - per-article LLM extractions
  - final DOE summary
- `*.txt`
  - human-readable summary

## How commercial search influences the result

The package uses three explicit rules.

### 1. Commercial methods can bias the anchor protocol
Examples:
- company repeatedly uses a progenitor harvest state
- company repeatedly uses feeder-free manufacturing
- company repeatedly uses cluster maturation or maintenance-medium switch

These patterns are useful because they reflect manufacturability, not only academic optimization.

### 2. Proprietary or vague company factors are deprioritized in DOE
Examples:
- kit supplements with undisclosed composition
- proprietary maturation cocktails
- closed-formulation production media

These may appear in the `anchor protocol rationale`, but should not be first-pass DOE factors.

### 3. Public + repeated methods can enter both anchor and DOE
Examples:
- explicit DLL4-coated Notch presentation if publicly described and academically repeated
- explicit feeder-free stage modules repeated across papers and commercial materials
