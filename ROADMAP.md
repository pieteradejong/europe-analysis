# ROADMAP — Demographic Analysis (Eurostat-first)

This roadmap focuses on **highly reliable, official** demographic inputs for Europe, starting with **Eurostat** at **EU27 + country level**. Religion-specific measures (including Islam) are treated as a separate layer because **Eurostat generally does not measure religion**.

## Principles

- **Official-first**: prefer Eurostat + national statistical offices (NSIs) for “hard” demography.
- **Reproducible ingestion**: every dataset has a stable identifier, ingestion config, and provenance metadata.
- **Projection-ready**: structure data to support cohort-component projections (age/sex cohorts + fertility + mortality + migration).
- **Separation of concerns**:
  - **Core demography**: age/sex/births/deaths/migration/nativity (Eurostat/NSIs).
  - **Religion layer**: country-specific census where available; otherwise high-quality surveys; always with uncertainty/scenarios.

## Track A — Eurostat core demography (Priority 1: acquire data)

### A1) Inventory & choose Eurostat datasets (minimum viable set)

Target metrics (Eurostat-first where possible):
- **Population size**: total population by country.
- **Age structure**: population by **age × sex** (baseline pyramid inputs).
- **Growth components**:
  - births (by mother age when available, for fertility),
  - deaths (age/sex mortality when available),
  - net migration / migration flows by age/sex (where available).
- **Nativity / migration proxies** (Eurostat-dependent):
  - population by **country of birth** and/or **citizenship**,
  - migration flows by **citizenship/country of birth** (where available).

Deliverables:
- A curated list of Eurostat dataset IDs we will ingest first (with links and notes on coverage).

### A2) Implement Eurostat acquisition (API crawler)

Deliverables:
- A Eurostat acquirer that can:
  - fetch dataset slices (country, year, age, sex),
  - handle paging/large responses,
  - rate limit and retry,
  - store raw responses + provenance.

Notes:
- Eurostat provides data through its dissemination services; ingestion should be config-driven so we can add datasets without new code.

### A3) Normalize into projection-friendly facts

Standardize into a consistent structure to support pyramids and projections:
- **Dimensions** (at minimum): `region_code` (country), `year`, `sex`, `age_min`, `age_max`, plus optional `citizenship`/`country_of_birth`.
- **Measures**: `population` (count), and for flows: `births`, `deaths`, `immigration`, `emigration` (depending on dataset).

Deliverables:
- Mapping rules per Eurostat dataset → standardized fields.
- Consistent age-band handling (single-year vs 5-year bands; open-ended 85+ style).

## Track B — Storage & provenance (Priority 2: store everything in DB)

### B1) Store “raw + normalized”

Design goals:
- Keep **raw snapshots** (source JSON/CSV payloads) for auditability.
- Store **normalized fact tables** for fast querying (pyramids, trends, projections).
- Track dataset provenance: dataset ID, query parameters, retrieval timestamp, license notes.

Deliverables:
- Schema extensions if needed to support:
  - dataset identifiers and dimensional metadata (sex/age definitions),
  - multiple measures (stock vs flow),
  - versioning by retrieval date.

## Track C — Visualizations (Demographic pyramids)

Once Track A+B have reliable baseline data:
- Generate demographic pyramids by:
  - country,
  - year,
  - optionally nativity proxy (country-of-birth/citizenship) where data supports it.
- Add trend views:
  - pyramid time slider,
  - population growth decomposition (births/deaths/net migration).

## Track D — Religion (including Islam) layer (later; not Eurostat-first)

Important: Eurostat generally does **not** provide religion affiliation. For religion-specific analysis, we will:

### D1) Country-by-country “official” religion sources

- Prefer **national censuses** where religion is asked and published.
- Capture metadata: question wording, nonresponse, reference year, geographic granularity.

### D2) Surveys for dynamics not in official registers

Use high-quality cross-national surveys only where necessary (estimates with uncertainty):
- religious switching / retention,
- intermarriage,
- identity transmission assumptions for projections.

### D3) Religion-linked projection metrics (scenario-based)

If projecting “Muslim population” or “Islam’s impact” demographics, focus on:
- cohort size by age/sex (baseline),
- fertility differentials (by nativity; religion where credibly measured),
- migration flows by origin (as proxy),
- switching/retention scenarios (explicit assumptions),
- intermarriage scenarios (explicit assumptions).

Deliverable:
- Scenario set (low/medium/high) with assumptions documented per country and data source quality.

## Near-term next steps (Eurostat-first, EU27 country level)

1. **Pick the first Eurostat dataset IDs** to ingest for:
   - population by age/sex,
   - births,
   - deaths,
   - migration flows,
   - country-of-birth/citizenship breakdowns (if available).
2. **Implement Eurostat acquisition** in the backend acquisition layer (config-driven).
3. **Define normalization mappings** per dataset into a unified pyramid/projection schema.
4. **Load into SQLite**, preserving raw payloads + provenance.
5. **Validate** with a small “known country” spot-check (one year, one country) against Eurostat UI totals.


