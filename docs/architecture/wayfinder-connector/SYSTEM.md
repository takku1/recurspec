# Wayfinder Connector (L1)

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/WAYFINDER_CONNECTOR/SYSTEM.md`

## 1. System Intent & Responsibility

Publish frontier tickets for atomic leaves and Type B research/prototype gaps. Default tracker: local markdown under `.scratch/wayfinder-map/`. Keeps domain vocabulary in titles; links each ticket to a `SYSTEM.md` URI.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: LocalMarkdownPublisher | GitHubAdapter | LinearAdapter — only if multi-tracker support is in open-work (remote webhook is deferred OW-15).

## 3. Interface Contracts

| | |
|--|--|
| **Inputs** | Leaf paths, ticket type (A implement / B research|prototype), blockers, domain terms from glossary |
| **Outputs** | MAP index entries, per-ticket files, optional remote issue IDs |

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Connector SHALL use project domain vocabulary in issue titles (see [glossary.md](../../glossary.md)).  
  - `EvidenceStage:` Observed
- **[Event-driven]** WHEN a new atomic leaf is created THE SYSTEM SHALL publish a corresponding frontier ticket.  
  - `EvidenceStage:` Sampled · *Blocked:* OW-03 depends on OW-01
- **[Conditional]** IF the architectural boundary is unknown THEN THE SYSTEM SHALL emit a Type B ticket, not a false Type A implement ticket.  
  - `EvidenceStage:` Observed (Wayfinder skill policy)

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Default tracker is `.scratch/wayfinder-map/` (markdown-first).
- **ADR-002:** Incomplete process items stay in `docs/open-work.md`; Wayfinder holds claimable build tickets only.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/wayfinder_connector/publisher.py`
- **Tests:** `tests/test_wayfinder_connector.py`
- **Open work:** OW-03

## 7. Measurement Seams

- **Primary metric:** `ticket_to_leaf_link_integrity` (every open ticket resolves to an existing `SYSTEM.md`)
- **Harness / checks:** `components/wayfinder-connector/measure.sh`, `checks.sh`
