# Frontier Adapter (L1)

<!-- recurspec-contract: 1.0 -->

> Reference archive: `docs/archive/2026-08-02-pre-redesign/architecture/architecture/WAYFINDER_CONNECTOR/SYSTEM.md`

## 1. System Intent & Responsibility

Publish Research Frontier tickets for DEFER leaves and leaves that cite a ROADMAP
id. Default tracker: local markdown under `.recurspec/frontiers/` (generated runtime
state). Titles use CONTEXT.md vocabulary and each ticket links to a `SYSTEM.md` path.

## 2. Sub-System Decomposition

**Atomic leaf.** Local publication is the default; GitHub Issues is an optional
remote behind the same publish seam.

## 3. Interface Contracts

- **Inputs:** Contract Tree root; optional remote publisher.
- **Outputs:** MAP index, per-ticket markdown, optional remote issue URLs.

## 4. Invariants (EARS + Epistemic Stage)

- **[Ubiquitous]** The Adapter SHALL use project domain vocabulary in ticket titles (see [CONTEXT.md](../../../CONTEXT.md)).
  (`test_publish_writes_a_research_frontier_linked_to_the_contract`)
  - `EvidenceStage:` Sampled
- **[Event-driven]** WHEN a DEFER leaf or a leaf that cites a ROADMAP id is published THE SYSTEM SHALL write a Research Frontier ticket linked to that Contract Node.
  (`test_publish_writes_a_research_frontier_linked_to_the_contract`)
  - `EvidenceStage:` Sampled
- **[Conditional]** IF a ticket's Contract path no longer exists THEN THE SYSTEM SHALL report broken integrity rather than invent a replacement leaf.
  (`test_check_reports_a_ticket_whose_contract_is_gone`)
  - `EvidenceStage:` Sampled

## 5. Architectural Decisions (ADRs)

- **ADR-001:** Default tracker is `.recurspec/frontiers/` (generated, gitignored).
- **ADR-002:** Incomplete product items stay in `ROADMAP.md`; this adapter holds
  Research Frontier tickets only.

## 6. Leaf Execution & Test Seam

- **Implementation:** `src/recurspec/frontier.py`; CLI `recurspec frontier publish|check`.
- **Tests:** `tests/test_frontier.py`.
- **Roadmap:** R-303.

## 7. Measurement Seams

- **Primary metric:** `ticket_to_leaf_link_integrity` (every open ticket resolves to an existing `SYSTEM.md`)
- **Evaluation Gate / checks:** `modules/frontier-adapter/measure.sh`, `checks.sh`

## 8. Technology Resolution

- **Decision class:** BUILD
- **Justification:** Fit gap. The core act (write a markdown ticket file linked to a
  `SYSTEM.md` URI) is trivial, but no existing tracker natively understands a Contract
  Tree; a thin adapter is unavoidable regardless of backend.
- **Selected:** Python standard library file I/O writing markdown under
  `.recurspec/frontiers/`, with GitHub Issues as an optional adapter behind the same
  publish seam (`gh issue create`).
- **Standard / protocol:** none for the default local tracker; GitHub Issues via `gh`
  when `--remote github` is set.
- **Alternatives considered:**

  | Option | Why not |
  |---|---|
  | GitHub Issues as the only tracker | Forces every consumer repo onto GitHub and loses offline/local-first ticket creation before a remote exists. |
  | A dedicated issue-tracking library | The write path is one markdown file per ticket; a library adds weight for no real fit gap it closes. |

- **Fit gap:** trackers do not know what a `SYSTEM.md` URI or a Type A/B ticket
  distinction is; the adapter owns that mapping.
- **Seam:** `src/recurspec/frontier.py`.
- **Exit cost:** LOW — the local markdown format is the source of truth; a remote adapter
  is additive, not a migration.
- **Cost model:** no service spend for the default local tracker; optional remote adapters
  cost whatever the chosen tracker charges.
- **Liability transferred:** none by default; ticket hosting if a remote adapter is enabled.
- **Operational owner:** us.
- **Failure mode:** a broken publish leaves a leaf without a ticket; caught by
  `ticket_to_leaf_link_integrity` in §7.
- **Open questions:** none.
