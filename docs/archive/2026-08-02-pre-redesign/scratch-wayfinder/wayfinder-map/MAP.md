# Wayfinder Map — Recursive System Specification Engine

**Label:** `wayfinder:map`  
**Status:** Active Execution Frontier

## Destination
Build and verify the 4 core leaf components of the Recursive System Specification Engine (`SpecEngine`, `Reconciler`, `WayfinderConnector`, `ASTGatekeeper`) so the framework can self-heal and expand autonomously.

## Notes
- Skills required: `/recursive-spec`, `/reconcile-spec`, `/wayfinder`, `/tdd`, `/code-review`.
- All leaf tickets point directly to their target `SYSTEM.md` node URIs.

## Decisions so far
- [ADR-001: Adopted 4-component L1 architecture](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/SYSTEM.md) — Established SpecEngine, Reconciler, WayfinderConnector, and ASTGatekeeper.

## Open Frontier Tickets (Claimable)

- [ ] **[01-spec-engine]** Implement EARS Spec Engine Generator  
  - **Target Node:** [docs/architecture/SPEC_ENGINE/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/SPEC_ENGINE/SYSTEM.md)  
  - **Blocked By:** None (Ready to claim)

- [ ] **[02-reconciler]** Implement Multi-Signal Auto-Expander  
  - **Target Node:** [docs/architecture/RECONCILER/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/RECONCILER/SYSTEM.md)  
  - **Blocked By:** None (Ready to claim)

- [ ] **[03-wayfinder-connector]** Implement Ticket Publisher  
  - **Target Node:** [docs/architecture/WAYFINDER_CONNECTOR/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/WAYFINDER_CONNECTOR/SYSTEM.md)  
  - **Blocked By:** `01-spec-engine`

- [ ] **[04-ast-gatekeeper]** Implement Zero-Drift Checker  
  - **Target Node:** [docs/architecture/AST_GATEKEEPER/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/AST_GATEKEEPER/SYSTEM.md)  
  - **Blocked By:** `02-reconciler`

- [ ] **[05-measurement-harness]** Implement Branching Measurement Harness  
  - **Target Node:** [docs/architecture/MEASUREMENT_HARNESS/SYSTEM.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/docs/architecture/MEASUREMENT_HARNESS/SYSTEM.md)  
  - **Blocked By:** `04-ast-gatekeeper`
  - **Design Ref:** [DUAL_BACKCHANNEL_MEASUREMENT_LOOP.md](file:///C:/Users/dcarn/aiprojects/recursive-system-design/DUAL_BACKCHANNEL_MEASUREMENT_LOOP.md)

## Not yet specified (Fog of War)
- `/dual-loop` skill (Strategy Packet + Correction Packet protocol)
- `.measure/` baseline infrastructure + pre-commit measure gate
- Reconciler Signal D: Metric Drift → auto-spawn Wayfinder research tickets

## Out of scope
- Web-based GUI portal for non-dev spec editing (terminal & markdown-first rule).
