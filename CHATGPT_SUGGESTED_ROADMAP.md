# Product Requirements Document (PRD)

## Product Name

German Industrial Capacity & Production Tracker (GICPT)

## Owner

Product: Pieter de Jong
Engineering: Pieter de Jong
Status: Draft v1.0

---

## 1. Executive Summary

The German Industrial Capacity & Production Tracker (GICPT) is a data-driven analytical application designed to monitor the real industrial health of Germany as a leading indicator for European economic wellbeing.

Germany sits upstream of Europe’s manufacturing base, export engine, labor markets, and fiscal stability. Sustained changes in German industrial output, capacity utilization, and energy-adjusted production reliably precede broader European slowdowns or recoveries by 1–2 quarters.

This product focuses on **physical production reality**, not sentiment, politics, or market narratives.

---

## 2. Problem Statement

Existing macro dashboards and economic tools suffer from three core problems:

1. Over-reliance on sentiment surveys and financial market proxies
2. Excessive indicator sprawl that obscures signal
3. Failure to distinguish cyclical recessions from structural deindustrialization

As a result, policymakers, analysts, and informed individuals often recognize European downturns too late.

There is no focused, opinionated tool that:

* Centers Germany explicitly
* Tracks industrial capacity, not just output
* Incorporates energy constraints post-2022
* Produces actionable regime-level signals

---

## 3. Goals & Objectives

### Primary Goals

* Detect early signs of European industrial stress via German data
* Distinguish temporary downturns from permanent capacity loss
* Provide a small set of high-signal indicators with clear interpretation

### Secondary Goals

* Enable historical comparison across industrial regimes
* Support expansion into composite indices and nowcasting
* Serve as a foundation for EU-wide industrial exposure analysis

---

## 4. Non-Goals

This product explicitly does NOT aim to:

* Predict equity markets
* Provide political or policy commentary
* Act as a general-purpose macroeconomic dashboard
* Track survey-based confidence indicators

---

## 5. Target Users

### Primary Users

* Technically literate analysts
* Engineers and researchers interested in real-economy signals
* Policymakers and policy-adjacent professionals

### Secondary Users

* Journalists covering European economics
* Advanced individual investors
* Academics and students

Users are assumed to be comfortable with charts, YoY comparisons, and regime-based reasoning.

---

## 6. Key User Questions

The application should enable users to answer:

1. Is German industry expanding, stagnating, or contracting?
2. Is capacity underutilized or constrained?
3. Are orders collapsing ahead of production?
4. Is industrial capacity being permanently destroyed?
5. Which sectors are driving weakness?
6. Is labor stress building beneath the surface?

---

## 7. Core Metrics (MVP Scope)

### 7.1 Industrial Production (Primary Indicator)

* Metric: Manufacturing output (excluding construction)
* View: YoY % change
* Frequency: Monthly
* Source: Destatis / Eurostat

Interpretation rules:

* Sustained YoY contraction → Europe-wide slowdown likely
* Flat output + rising costs → margin compression

---

### 7.2 Capacity Utilization

* Metric: Manufacturing capacity utilization (%)
* Frequency: Quarterly
* Source: Destatis / ECB

Threshold logic:

* < 78% → Structural weakness
* 80–83% → Normal range
* > 85% → Bottlenecks / overheating

---

### 7.3 New Manufacturing Orders

* Metrics:

  * Domestic orders
  * Foreign orders
* Frequency: Monthly
* Source: Destatis

Derived signals:

* Orders ↓ faster than production → layoffs risk
* Production ↓ faster than orders → inventory clearing

---

### 7.4 Energy-Adjusted Industrial Activity

Post-2022, energy use is a first-class constraint.

Metrics:

* Industrial electricity consumption
* Industrial gas consumption
* Output of energy-intensive sectors

Interpretation:

* Output stable + energy use falling → deindustrialization risk

---

### 7.5 Sectoral Output Decomposition

#### Tier 1 (Systemic Sectors)

* Automotive
* Machinery & capital goods
* Chemicals

Rule:
If automotive + machinery are weak simultaneously, European growth is structurally constrained.

#### Tier 2 (Cyclical Signals)

* Electrical equipment
* Metals
* Construction materials

---

### 7.6 Labor Market Stress (Lagging Confirmation)

Metrics:

* Kurzarbeit participation
* Hours worked

Note:
Germany hoards labor; unemployment is a lagging indicator.

---

## 8. MVP Dashboard Requirements

The initial dashboard must display:

1. Industrial Production (YoY trend)
2. Manufacturing Orders (Domestic vs Foreign)
3. Capacity Utilization vs thresholds
4. Industrial Energy Consumption trend
5. Tier 1 sector output comparison
6. Kurzarbeit participation trend

Each metric must include:

* Short textual interpretation
* Threshold-based highlighting

---

## 9. Regime Classification (Phase 2)

The system will support regime labeling:

* Expansion
* Late-cycle slowdown
* Cyclical recession
* Structural deindustrialization

Regimes are determined by multi-indicator agreement, not single prints.

---

## 10. German Industrial Stress Index (Phase 3)

A composite index combining:

* Production momentum
* Orders momentum
* Capacity utilization deviation
* Energy usage delta
* Tier 1 sector weakness
* Labor stress proxy

Output:

* Continuous score
* Green / Yellow / Red classification

---

## 11. Data Requirements

* Official statistical sources only
* Transparent revisions handling
* YoY normalization by default
* Historical backfill to at least 2000

---

## 12. UX & Presentation Principles

* Minimalist, information-dense layout
* Emphasis on trends, not point estimates
* Clear annotation of structural vs cyclical signals
* Avoid clutter and excessive interactivity

---

## 13. Success Metrics

The product is successful if it:

* Flags downturns before mainstream European indicators
* Avoids false positives from sentiment noise
* Is understandable without economic commentary
* Becomes a reference framework for industrial analysis

---

## 14. Risks & Mitigations

### Risk: Overfitting historical cycles

Mitigation: Emphasize regime logic over numeric precision

### Risk: Data revisions

Mitigation: Track first-release vs revised data

### Risk: Energy data availability

Mitigation: Use proxies and sector-level confirmation

---

## 15. Future Extensions

* EU country exposure mapping
* Germany vs US / China industrial cycle comparison
* Nowcasting using partial-month indicators
* API access for external research tools

---

End of PRD.
