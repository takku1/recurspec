---
name: wayfinder
description: Plan a huge chunk of work — more than one agent session can hold — as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
disable-model-invocation: true
---

A loose idea has arrived — too big for one agent session, and wrapped in fog: the way from here to the **destination** isn't visible yet. Wayfinding is about finding that way, not charging at the destination. This skill charts the way as a **shared map** on the repo's issue tracker, then works its **decision tickets** — questions whose resolution is a decision, not slices of a build to execute — one at a time until the route is clear.

## The Map

The map is a single issue or local markdown file (`.scratch/wayfinder-map/MAP.md`), labelled `wayfinder:map` — the canonical artifact. Its tickets are child issues or frontier files.

### Map Structure

```markdown
## Destination

<what reaching the end of this map looks like — the spec, decision, or change this effort is finding its way to.>

## Notes

<domain; skills every session should consult; standing preferences for this effort>

## Decisions so far

- [<closed ticket title>](link) — <one-line gist of the answer>

## Not yet specified (Fog of War)

## Out of scope
```

## Ticket Types & Frontier Types

- **Type A Frontier (Concealed Architecture / Task):** Architecture is specified; implementation or verified task.
- **Type B Frontier (Open Research / Prototype):** Behavior/boundary unknown; requires `/research` or `/prototype` before locking spec.
- **Grilling (HITL):** Decision interview via `/grilling` or `/domain-modeling`.
- **Task (AFK/HITL):** Concrete work unblocking a decision.

## RSS Integration Rule

When Back-Channel B (Empirical Reconciliation) detects a metric regression or an unknown component boundary, Wayfinder automatically emits a Type B `research` or `prototype` ticket to clear the fog before implementation resumes.
