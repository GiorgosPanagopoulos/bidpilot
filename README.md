<div align="center">

<img src="https://raw.githubusercontent.com/GiorgosPanagopoulos/bidpilot/main/assets/bidpilot-logo.png" width="480" alt="BidPilot logo" />

<br/>

<strong>AI-Native Tender Intelligence for Suppliers</strong>

<em>Semantic matching, eligibility screening and cited bid drafting over public tenders</em>

<br/><br/>

<img src="https://raw.githubusercontent.com/GiorgosPanagopoulos/bidpilot/main/assets/bidpilot-graphical-abstract.png?v=2" width="900" alt="BidPilot architecture" />

</div>

---

<div align="center">

[![CI](https://github.com/GiorgosPanagopoulos/bidpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/GiorgosPanagopoulos/bidpilot/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.2-1C3C3C?style=for-the-badge)](https://python.langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-FF6B35?style=for-the-badge)](https://trychroma.com)
[![MongoDB Atlas](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://mongodb.com/atlas)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-FAB040?style=for-the-badge&logo=pre-commit&logoColor=black)](https://pre-commit.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

</div>

---

## Overview

BidPilot is a supplier-side tender intelligence backend. It ingests public tenders from TED (Tenders Electronic Daily), matches them to a company profile via a two-stage hybrid engine (semantic retrieval followed by explainable rule re-ranking), screens each match through a declarative eligibility engine, and runs a ReAct agent that reads the tender document (PDF), extracts structured requirements, analyses capability gaps, and drafts a cited technical proposal section by section. Phase 4 adds a second ingestion source (ΔΙΑΥΓΕΙΑ public contract awards) and an analytics layer: historical pricing per CPV, supplier win rates, and award trends. All draft output is marked `needs_review`: the API enforces a mandatory human-review gate and provides no auto-submit path.

Built on the same production architecture as ProcureAI: ContextVar multi-tenancy via the `X-Company-Id` header, custom exceptions with a global FastAPI handler, fire-and-forget Mongo audit logging, file-based versioned prompts with hot-reload via the `PromptLoader` singleton, and full CI (ruff, mypy, pytest).

---

## Features

| Feature | Description |
|---------|-------------|
| Tender Ingestion | Fetches and normalises TED eForms API v3 notices into a canonical `Tender` model with CPV codes, NUTS regions, budget, and deadline |
| TED Connector | Async `TEDSource` with configurable base URL, date-range fetch, and typed normalisation with graceful fallbacks |
| Shared Vector Corpus | ChromaDB persistent store holds all ingested tenders; every company profile queries against the single shared corpus |
| Hybrid Matcher | Two-stage pipeline: semantic cosine-distance retrieval (top-k) followed by rule re-ranking on CPV ratio, NUTS match, and budget feasibility |
| Explainable Reasons | Every `MatchResult` carries a `reasons[]` list so no match is silently promoted or dropped |
| Declarative Eligibility Engine | YAML-driven `EligibilityEngine` enforces financial capacity (hard), minimum lead days (hard), exclusion flag overlap (hard), and technical coverage (soft warning) |
| Hot-Reload Rules | `EligibilityEngine.reload()` re-reads `config/eligibility_rules.yaml` at runtime without a server restart |
| RAG Bid Drafting | ReAct agent (LangChain `create_react_agent` + `AgentExecutor`) reads an ingested tender PDF, extracts a structured `RequirementChecklist`, runs a `GapReport`, then drafts cited `BidDraftSection` objects via five specialised tools |
| Requirement Extraction | LLM-powered structured extraction of technical, financial, legal, administrative, and submission requirements, each with a `ProposalCitation` (locator + snippet) |
| Gap Analysis | Pure-logic matching of `RequirementChecklist` against `CompanyProfile` (capacity tags, turnover, exclusion flags); produces `GapReport` with `met/partial/unmet` per item and an overall `coverage_ratio` |
| Cited Proposal Sections | `draft_section` tool retrieves tender clauses and grounded company capabilities, then drafts prose with inline `[Locator]` citations; fabricated requirements are not permitted |
| Self-Check | `self_check` tool validates each drafted section against mandatory requirements and reports missing coverage |
| Human-in-the-Loop | `BidDraft.status` is always `needs_review`; the API response includes a mandatory-review notice; no auto-submit path exists |
| File-Based Versioned Prompts | `PromptLoader` singleton reads `prompts/{name}/{version}.txt` fresh on every call (hot-reloadable); used for all LLM instructions |
| Token and Cost Tracking | `TokenCostCallback` accumulates input/output tokens per agent run; `TokenUsage.cost_usd` computes cost from a per-model rate table |
| Multi-Tenancy | `X-Company-Id` header propagated to a Python `ContextVar`; all Mongo writes and audit events carry tenant identity |
| Fire-and-Forget Audit Log | Non-blocking `asyncio.ensure_future` writes every company, tender, match, and draft event to `audit_log` |
| Custom Exception Layer | Typed hierarchy with a single global FastAPI handler |
| APScheduler Cron | Daily auto-ingestion at 06:00 UTC (configurable via `INGEST_CRON`), also triggerable on-demand |
| Award Ingestion | Async `DiavgeiaSource` fetches contract-award decisions from the ΔΙΑΥΓΕΙΑ opendata API; normalises to a canonical `Award` model; `KimdisSource` stub raises `SourceUnavailableError` as a documented placeholder |
| Scheduled Award Sync | APScheduler runs `ingest_awards_pipeline` on the same cron as tender ingestion; also triggerable via `POST /awards/ingest` |
| Pricing Analytics | `compute_pricing_stats` returns min, max, mean, median, p25, p75 over `award_value` for any CPV/date scope; chart-ready JSON for Recharts |
| Supplier Win Rates | `compute_win_rates` aggregates awards per supplier, computes `win_share` against total scope, ranks by `awards_won`; supports `top_n` cap |
| Award Trends | `compute_trends` buckets awards by month, quarter, or year; returns `TrendSeries` with count, total, and mean per period |
| CI Pipeline | GitHub Actions: ruff lint, mypy type-check, pytest, gated on pushes and PRs to `main` |

---

## Architecture

```mermaid
graph TD
    subgraph Sources
        TED["TED eForms API v3"]
        DIAVGEIA["ΔΙΑΥΓΕΙΑ opendata API\naward/contract decisions"]
    end

    subgraph Ingestion
        SCHED["APScheduler\ncron: 06:00 UTC"]
        PIPE["ingest_pipeline\nfetch + normalize + embed"]
        AWARDS_PIPE["ingest_awards_pipeline\nfetch + normalize + upsert"]
        DOCPIPE["POST /tenders/{id}/ingest-doc\nfetch PDF + pypdf + chunk + embed"]
    end

    subgraph VectorStore
        CHROMA[("ChromaDB\nShared Corpus\ntenders collection")]
        TDOCS[("ChromaDB\nShared Corpus\ntender_docs collection")]
    end

    subgraph HybridMatcher["Hybrid Matcher"]
        SEM["query_tenders\nsemantic top-20"]
        RERANK["Rule Re-rank\nCPV + NUTS + budget"]
        ELIG["EligibilityEngine\nfinancial, deadline\nexclusion, technical"]
    end

    subgraph DraftingAgent["ReAct Drafting Agent"]
        TOOLS["Tools\nextract_requirements\nanalyze_gaps\nretrieve_clauses\ndraft_section\nself_check"]
        REACT["create_react_agent\nLangGraph prebuilt"]
        DRAFT["BidDraft\nstatus=needs_review"]
    end

    subgraph Analytics["Analytics Service (pure)"]
        PRICING["compute_pricing_stats\nmin/max/mean/median/p25/p75"]
        WINRATE["compute_win_rates\nawards_won + win_share"]
        TRENDS["compute_trends\nmonth/quarter/year buckets"]
    end

    subgraph Persistence
        MONGO[("MongoDB Atlas\ncompanies, tenders\nmatches, bid_drafts\nawards, audit_log")]
    end

    TED -->|async fetch| PIPE
    DIAVGEIA -->|async fetch| AWARDS_PIPE
    SCHED -->|triggers| PIPE
    SCHED -->|triggers| AWARDS_PIPE
    PIPE -->|upsert_tender_embedding| CHROMA
    PIPE -->|upsert_tender| MONGO
    AWARDS_PIPE -->|upsert_award| MONGO

    DOCPIPE -->|upsert_chunks| TDOCS

    PROFILE["CompanyProfile\nCPV, NUTS, turnover, tags"] -->|build_query| SEM
    SEM -->|cosine distance| CHROMA
    SEM --> RERANK
    RERANK --> ELIG
    ELIG --> RESULT["MatchResult\nscore + reasons + eligibility"]
    RESULT -->|upsert_match| MONGO

    TDOCS -->|RAG retrieval| TOOLS
    TOOLS --> REACT
    REACT --> DRAFT
    DRAFT -->|upsert_draft| MONGO

    MONGO -->|list_awards| PRICING
    MONGO -->|list_awards| WINRATE
    MONGO -->|list_awards| TRENDS

    ROUTERS["FastAPI Routers\n/companies /tenders /matches\n/drafts /awards /analytics"] --> PIPE
    ROUTERS --> AWARDS_PIPE
    ROUTERS --> PROFILE
    ROUTERS --> REACT
    RESULT --> ROUTERS
    DRAFT --> ROUTERS
    PRICING --> ROUTERS
    WINRATE --> ROUTERS
    TRENDS --> ROUTERS

    CTX["ContextVar Tenant\nX-Company-Id header"] -.->|cross-cutting| ROUTERS
    AUDIT["fire-and-forget\nAudit Log"] -.->|audit_log collection| MONGO
```

---

## Tech Stack

| Badge | Component | Role |
|-------|-----------|------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white) | **Python 3.12** | Runtime, async/await throughout |
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white) | **FastAPI 0.111** | REST API, dependency injection, lifespan hooks, global exception handler |
| ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge) | **LangChain + langchain-anthropic** | ReAct agent (`create_react_agent`), tool definitions, chat model interface |
| ![Anthropic](https://img.shields.io/badge/Anthropic_Claude-D97757?style=for-the-badge) | **Anthropic Claude** | LLM for requirement extraction, section drafting, and self-check (model configurable via `AGENT_MODEL`) |
| ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B35?style=for-the-badge) | **ChromaDB 0.5** | Persistent local vector store: `tenders` corpus for matching, `tender_docs` corpus for RAG drafting |
| ![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white) | **MongoDB Atlas + Motor 3** | Async document persistence: companies, tenders, matches, bid_drafts, audit log |
| ![APScheduler](https://img.shields.io/badge/APScheduler-3.10-808080?style=for-the-badge) | **APScheduler 3.10** | AsyncIOScheduler driving the cron-based tender ingestion pipeline |
| ![Pydantic](https://img.shields.io/badge/Pydantic_v2-E92063?style=for-the-badge&logo=pydantic&logoColor=white) | **Pydantic v2** | Data validation and typed settings via pydantic-settings |
| pypdf | **pypdf 4** | PDF text extraction for tender document ingestion |
| ![React](https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black) | **React 19** | UI runtime, concurrent rendering |
| ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white) | **TypeScript 5.7** | Strict end-to-end typing |
| ![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white) | **Vite 6** | Dev server and production bundler |
| ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white) | **Tailwind CSS v4** | Utility-first styling with `@theme` custom tokens |
| Zustand | **Zustand v5** | Lightweight state management (persist middleware for company profile) |
| Recharts | **Recharts v2** | BarChart / AreaChart for analytics |
| Framer Motion | **Framer Motion v11** | Page transitions and animated UI |
| Vitest | **Vitest + React Testing Library** | Component unit tests (16 tests) |

---

## Frontend

The `frontend/` directory is a standalone Vite + React 19 + TypeScript app that consumes the BidPilot REST API.

### Running locally

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to http://localhost:8000)
```

### Views

| View | Route | Description |
|------|-------|-------------|
| **Tender Feed** | `/` | Company profile panel, CPV/status filters, run-match button, match cards with score breakdown and eligibility badge |
| **Bid Workspace** | `/workspace` | Tender header, doc ingestion button, animated agent-working state, cited bid draft viewer with collapsible trace panel |
| **Analytics** | `/analytics` | Filter form (CPV, authority, date range, interval), pricing stats bar chart, supplier win rates horizontal chart, award trends area chart |

### Environment

```bash
VITE_API_BASE=http://localhost:8000   # default; override in .env.local
```

### Frontend CI

The `frontend` job in `.github/workflows/ci.yml` runs independently of the backend jobs:
`npm ci` → ESLint → `tsc --noEmit` → Vitest → `vite build`

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/GiorgosPanagopoulos/bidpilot.git
cd bidpilot

# 2. Create virtual environment (Python 3.12 required)
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install with dev extras
pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and MONGODB_URI at minimum

# 5. Run
uvicorn app.main:app --reload

# Interactive API docs: http://localhost:8000/docs
# Health check:        http://localhost:8000/health
```

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|:--------:|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude LLM | **Yes** | |
| `MONGODB_URI` | MongoDB Atlas connection string | **Yes** | |
| `MONGO_DB_NAME` | MongoDB database name | No | `bidpilot` |
| `CHROMA_PATH` | File system path for ChromaDB persistence | No | `./chroma_data` |
| `TED_API_BASE` | TED eForms API v3 base URL | No | `https://api.ted.europa.eu/v3` |
| `WEIGHT_SEMANTIC` | Semantic score weight in final match score | No | `0.6` |
| `WEIGHT_RULE` | Rule re-rank score weight in final match score | No | `0.4` |
| `MATCH_TOP_K` | Number of semantic candidates retrieved before rule re-ranking | No | `20` |
| `BUDGET_FEASIBILITY_FACTOR` | Multiplier on annual turnover for budget feasibility check | No | `2.0` |
| `INGEST_CRON` | Cron expression for scheduled automatic ingestion | No | `0 6 * * *` |
| `AGENT_MODEL` | Anthropic model for the drafting agent | No | `claude-sonnet-4-5` |
| `LOG_LEVEL` | Logging verbosity | No | `INFO` |

> Eligibility rule thresholds live in `config/eligibility_rules.yaml` and are reloaded at runtime via `EligibilityEngine.reload()`. Agent prompts live in `prompts/{name}/v1.txt` and are reloaded on every call via `PromptLoader`.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/companies` | Create or update a company profile |
| `GET` | `/companies/{company_id}` | Retrieve a company profile by ID |
| `POST` | `/tenders/ingest` | Trigger an on-demand TED ingestion run; returns `{"ingested": N}` (HTTP 202) |
| `GET` | `/tenders` | List persisted tenders, filterable by `status` and `cpv` |
| `POST` | `/tenders/{id}/ingest-doc` | Fetch the tender PDF from `raw_doc_uri`, extract text (pypdf), chunk, and embed into the `tender_docs` corpus (HTTP 202) |
| `POST` | `/matches/run` | Run the full hybrid matching pipeline for `company_id` |
| `GET` | `/matches` | Retrieve stored match results for `company_id`, sorted by score descending |
| `POST` | `/drafts/run` | Body `{company_id, tender_id}`: run the ReAct drafting agent and return a `BidDraft` (status `needs_review`, HTTP 201) |
| `GET` | `/drafts/{id}` | Retrieve a stored `BidDraft` by ID (tenant-scoped) |
| `GET` | `/drafts/{id}/trace` | Retrieve the ReAct reasoning trace (thought/action/observation steps) |
| `POST` | `/awards/ingest` | Manually trigger a ΔΙΑΥΓΕΙΑ award ingestion run; returns `{"ingested": N}` (HTTP 202) |
| `GET` | `/awards` | List persisted awards, filterable by `cpv`, `authority`, `supplier`, `supplier_vat`, `from`, `to` |
| `GET` | `/analytics/pricing` | Pricing stats (min/max/mean/median/p25/p75) for awards matching `cpv`, `from`, `to` |
| `GET` | `/analytics/win-rates` | Supplier win rates ranked by `awards_won`; supports `cpv`, `authority`, `from`, `to`, `top_n` |
| `GET` | `/analytics/trends` | Award trend series bucketed by `interval` (month/quarter/year); supports `cpv`, `authority`, `from`, `to` |
| `GET` | `/health` | Liveness probe |

All endpoints accept the optional `X-Company-Id` header for multi-tenant context propagation. Draft endpoints enforce that the result requires mandatory human review before any submission.

---

## Project Structure

```
bidpilot/
├── agent/
│   ├── executor.py             # run_drafting_agent: create_react_agent + AgentExecutor, trace builder
│   ├── prompt.py               # PromptLoader singleton (hot-reloadable file-based versioned prompts)
│   └── tools.py                # Five @tool functions: extract_requirements, analyze_gaps,
│                               #   retrieve_clauses, draft_section, self_check
├── llm/
│   ├── callbacks.py            # TokenCostCallback: accumulates input/output tokens per run
│   ├── clients.py              # get_drafting_llm(): ChatAnthropic factory (model from settings)
│   └── pricing.py              # TokenUsage dataclass with cost_usd computed from per-model rates
├── prompts/
│   ├── system/v1.txt           # ReAct system prompt (workflow instructions + tool format)
│   ├── requirement_extraction/v1.txt
│   ├── draft_section/v1.txt
│   └── self_check/v1.txt
├── app/
│   ├── main.py                 # FastAPI app factory, lifespan, router registration
│   ├── api/
│   │   ├── deps.py             # set_tenant dependency
│   │   └── routers/
│   │       ├── analytics.py    # GET /analytics/pricing, /win-rates, /trends
│   │       ├── awards.py       # POST /awards/ingest, GET /awards
│   │       ├── companies.py
│   │       ├── drafts.py       # POST /drafts/run, GET /drafts/{id}, GET /drafts/{id}/trace
│   │       ├── matches.py
│   │       └── tenders.py      # POST /tenders/ingest, GET /tenders, POST /tenders/{id}/ingest-doc
│   ├── core/
│   │   ├── context.py
│   │   ├── exceptions.py       # + DocumentParsingError, RequirementExtractionError,
│   │   │                       #   DraftingError, AwardIngestionError
│   │   ├── logging.py
│   │   └── settings.py         # + agent_model (AGENT_MODEL env var)
│   ├── ingestion/
│   │   ├── base.py
│   │   ├── diavgeia.py         # DiavgeiaSource (ΔΙΑΥΓΕΙΑ opendata) + KimdisSource stub
│   │   ├── doc_parser.py       # parse_pdf_to_chunks: pypdf extraction + paragraph chunking
│   │   ├── ted.py
│   │   └── scheduler.py        # + ingest_awards_pipeline, awards cron job
│   ├── matching/
│   │   ├── eligibility.py
│   │   └── matcher.py
│   ├── models/
│   │   ├── award.py            # RawAward, Award, PricingStats, SupplierWinRate,
│   │   │                       #   TrendPoint, TrendSeries
│   │   ├── company.py
│   │   ├── draft.py            # ProposalCitation, RequirementItem, RequirementChecklist,
│   │   │                       #   GapItem, GapReport, BidDraftSection, BidDraft
│   │   ├── match.py
│   │   └── tender.py
│   ├── repositories/
│   │   ├── audit.py
│   │   ├── awards.py           # upsert_award, list_awards (cpv/authority/supplier/date filters)
│   │   ├── companies.py
│   │   ├── drafts.py           # upsert_draft, get_draft, save_trace, get_trace
│   │   ├── matches.py
│   │   ├── mongo.py
│   │   └── tenders.py          # + get_tender
│   ├── services/
│   │   └── analytics.py        # compute_pricing_stats, compute_win_rates, compute_trends
│   └── vectorstore/
│       ├── chroma.py           # tenders corpus
│       └── tender_docs.py      # tender_docs corpus: upsert_chunks, query_tender_docs,
│                               #   get_all_tender_chunks, has_tender_docs
├── config/
│   └── eligibility_rules.yaml
├── tests/
│   ├── conftest.py
│   ├── test_diavgeia_normalize.py
│   ├── test_doc_ingest.py
│   ├── test_draft_pipeline.py
│   ├── test_eligibility.py
│   ├── test_gap_analysis.py
│   ├── test_ingest_audit.py
│   ├── test_matcher.py
│   ├── test_pricing_stats.py
│   ├── test_requirement_extraction.py
│   ├── test_self_check.py
│   ├── test_ted_normalize.py
│   ├── test_trends_monthly.py
│   └── test_win_rates.py
├── .env.example
├── .github/workflows/ci.yml
├── .pre-commit-config.yaml
└── pyproject.toml
```

---

## Roadmap

- Phase 1 - Ingestion + Hybrid Match MVP (Complete)
- Phase 2 - Eligibility Engine + CI (Complete)
- Phase 3 - RAG Bid Drafting (ReAct agent, requirement extraction, gap analysis, cited drafts) (Complete)
- Phase 4 - Award Analytics (ΔΙΑΥΓΕΙΑ ingestion, pricing stats, win rates, trend series) (Complete)
- Frontend - React 19 / TS / Vite / Tailwind v4 (Tender Feed + Bid Workspace + Analytics) (Complete)

---

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">
<strong>Built by <a href="https://github.com/GiorgosPanagopoulos">Georgios Panagopoulos</a></strong><br/>
<em>"I build things I'd trust with something that matters."</em>
<br/><br/>
<a href="https://github.com/GiorgosPanagopoulos"><img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white"/></a>
<a href="https://linkedin.com/in/georgios-panagopoulos-9253842ba"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white"/></a>
<br/><br/>
Powered by mass amounts of caffeine and mass amounts of curiosity
</div>
