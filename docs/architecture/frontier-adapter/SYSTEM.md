# Frontier Adapter (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/WAYFINDER_CONNECTOR/SYSTEM.md`

## 1. System Intent & Responsibility

Publish frontier tickets for atomic leaves and Type B research/prototype gaps. Default tracker: local markdown under `.scratch/wayfinder-map/`. Keeps domain vocabulary in titles; links each ticket to a `SYSTEM.md` URI.

## 2. Sub-System Decomposition

**Atomic leaf (Phase 0).** Later: LocalMarkdownPublisher | GitHubAdapter | LinearAdapter — only if multi-tracker support is in open-work (remote webhook is deferred OW-15).

## 3. Interface Contracts

- **Inputs:** Leaf paths, ticket type (A implement / B research|prototype), blockers, domain terms from glossary.
- **Outputs:** MAP index entries, per-ticket files, optional remote issue IDs.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Connector SHALL use project domain vocabulary in issue titles (see [CONTEXT.md](../../../CONTEXT.md)).
  - `EvidenceStage:` Unknown
- **[Event-driven]** WHEN a new atomic leaf is created THE SYSTEM SHALL publish a corresponding frontier ticket. (blocked: OW-03 depends on OW-01)
  - `EvidenceStage:` Unknown
- **[Conditional]** IF the architectural boundary is unknown THEN THE SYSTEM SHALL emit a Type B ticket, not a false Type A implement ticket. (Wayfinder skill policy)
  - `EvidenceStage:` Unknown

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Default tracker is `.scratch/wayfinder-map/` (markdown-first).
- **ADR-002:** Incomplete product items stay in `ROADMAP.md`; trackers hold claimable build tickets only.

## 6. Leaf Execution & Test Seam

- **Implementation:** not yet built; planned seam `src/recurspec/frontier.py`.
- **Tests:** none yet; planned `tests/test_frontier.py`.
- **Open work:** OW-03; tracked as ROADMAP R-303 (deferred).

## 7. Measurement Seams

- **Primary metric:** `ticket_to_leaf_link_integrity` (every open ticket resolves to an existing `SYSTEM.md`)
- **Evaluation Gate / checks:** `modules/frontier-adapter/measure.sh`, `checks.sh`

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Fit gap. The core act (write a markdown ticket file linked to a
  `SYSTEM.md` URI) is trivial, but no existing tracker natively understands a Contract
  Tree; a thin adapter is unavoidable regardless of backend.
- **Selected:** Python standard library file I/O writing markdown under
  `.scratch/wayfinder-map/`, with the remote tracker (GitHub/Linear) as an optional adapter
  behind the same publish seam.
- **Standard / protocol:** none for the default local tracker; REST for optional remote
  adapters (GitHub Issues API, Linear API) — deferred (OW-15).
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | GitHub Issues as the only tracker | Forces every consumer repo onto GitHub and loses offline/local-first ticket creation before a remote exists. |
  | A dedicated issue-tracking library | The write path is one markdown file per ticket; a library adds weight for no real fit gap it closes. |

- **Fit gap:** trackers do not know what a `SYSTEM.md` URI or a Type A/B ticket
  distinction is; the adapter owns that mapping.
- **Seam:** `src/recurspec/frontier.py` (planned).
- **Exit cost:** LOW — the local markdown format is the source of truth; a remote adapter
  is additive, not a migration.
- **Cost model:** no service spend for the default local tracker; optional remote adapters
  cost whatever the chosen tracker charges.
- **Liability transferred:** none by default; ticket hosting if a remote adapter is enabled.
- **Operational owner:** us.
- **Failure mode:** a broken publish leaves a leaf without a ticket; caught by
  `ticket_to_leaf_link_integrity` in §7.
- **Open questions:** OW-03, OW-15 (remote webhook support).
