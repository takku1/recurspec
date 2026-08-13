# Worked example — "Login and user accounts"

One line from a flat plan, run through the [decomposition loop](../process/contract-design.md)
and the [technology resolution gate](../process/stack-resolution.md).

> **Vendor facts below are illustrative of the decision's _shape_, not a current market
> survey.** Plans, limits, and versions change. The RESEARCH phase requires verifying
> them against live documentation at decision time — the same no-fabrication rule that
> governs [research/foundations.md](../research/foundations.md) applies to §8 entries.

---

## Before

```
- Login and user accounts
```

An implementing agent handed this writes a `users` table, a `password_hash` column, and a
bcrypt call. That output is defensible against the line as written — which is the point.
The line is the defect.

## After

```
Identity & Access                     [mixed]  -> SPLIT
├── Identity Verification             BUY      -> TERMINAL
├── Session Management                WRAP     -> TERMINAL
├── Authorization Policy              [mixed]  -> SPLIT
│   ├── Policy Evaluation             ADOPT    -> TERMINAL
│   └── Role & Permission Model       BUILD    -> TERMINAL
├── Account Lifecycle                 [mixed]  -> SPLIT
│   ├── Recovery & Verification       BUY      -> TERMINAL (delegated)
│   └── Deletion & Export             BUILD    -> TERMINAL
└── Auth Audit Trail                  ADOPT    -> TERMINAL
```

Depth 3, seven terminal nodes, **two of them genuinely custom** — and those two encode
your product's rules, not "what is a password".

---

## Why it split where it did

The parent `Identity & Access` is not uniform: verifying a human is a solved commodity,
while deciding what a `regional_manager` may approve is specific to your business. The
**fault line between BUY and BUILD is the interface**, so that is where the node splits.
Same logic one level down: policy *evaluation* is a solved algorithm (ADOPT), policy
*content* is yours (BUILD).

---

## L2 · Identity Verification

**Responsibility:** Prove a visitor controls an identity. Does **not** own what that
identity may do, or how the session persists.

**Invariants**

- **[Ubiquitous]** The system SHALL NOT store user passwords in any form.
  `EvidenceStage:` Observed — enforced by absence of a credential column
- **[Event-driven]** WHEN identity verification succeeds THE SYSTEM SHALL receive a
  signed OIDC ID token carrying a stable subject identifier.
  `EvidenceStage:` Observed
- **[Conditional]** IF the IdP is unreachable THEN THE SYSTEM SHALL fail closed and
  surface a retry, never fall back to a local credential path.
  `EvidenceStage:` Unknown — needs a failure-injection test

```markdown
## 8. Technology Resolution

- Decision class: BUY
- Selected: Google Identity Platform (OIDC), Google + email-link providers
- Standard / protocol: OIDC / OAuth 2.1  <- any compliant IdP substitutes
- Alternatives considered:
  | Option | Why not |
  |--------|---------|
  | Auth0 / Okta | Strong fit; per-MAU cost rises faster at our projected scale |
  | Clerk | Excellent DX, ships UI; more opinionated about session shape than we want |
  | Keycloak (self-host) | Full control, no per-user cost — but we then operate an HA IdP |
  | Custom users table | Rejected on liability: credential storage, MFA, reset, enumeration |
- Fit gap: no domain roles; no session shape; no GDPR deletion of OUR data
           -> generates the sibling nodes
- Seam: `src/auth/idp_adapter.*` — the ONLY module allowed to import the vendor SDK
- Exit cost: LOW — OIDC-standard; swap = new issuer config + re-map claims,
             provided no vendor type escapes the adapter
- Cost model: free tier to ~50k MAU; ~$0.00x/MAU beyond.
              Re-open if MAU > 500k or per-MAU pricing changes
- Liability transferred: credential storage, hashing currency, MFA, breach exposure,
                         account-enumeration defence, reset-token security
- Operational owner: vendor
- Failure mode: IdP outage = no new logins. Existing sessions survive to expiry
                (see Session Management). Fail closed; status-page link on error.
- Open questions: none
```

**Terminal because procured.** We do not spec OIDC internals, JWT signing, or key
rotation. Google owns those. Specifying them would be writing documentation for someone
else's product.

---

## L2 · Session Management

**Responsibility:** Turn a verified identity into a `CurrentUser` that persists across
requests, and end it on demand.

This is the WRAP that flat plans miss. Buying identity did not remove this work — it
bounded it to an adapter.

**Invariants**

- **[Ubiquitous]** The system SHALL derive session state only from a validated IdP token.
  `EvidenceStage:` Observed
- **[State-driven]** WHILE a session is active THE SYSTEM SHALL re-validate the token
  signature and expiry on every authenticated request.
  `EvidenceStage:` Observed
- **[Event-driven]** WHEN a user signs out THE SYSTEM SHALL revoke the refresh token at
  the IdP, not merely clear the local cookie.
  `EvidenceStage:` Unknown — OW candidate

```markdown
## 8. Technology Resolution

- Decision class: WRAP (over BUY: Identity Verification; ADOPT: framework middleware)
- Selected: framework session middleware + httpOnly/SameSite=Lax/Secure cookie;
            custom `SessionAdapter` mapping ID-token claims -> domain `CurrentUser`
- Standard / protocol: OIDC claims; RFC 6265 cookies
- Alternatives considered:
  | Option | Why not |
  |--------|---------|
  | Vendor-hosted session SDK | Couples our domain user to vendor types; raises exit cost |
  | Server-side session store (Redis) | Extra infrastructure we do not yet need; revisit at multi-region |
  | Raw JWT in localStorage | XSS-exfiltratable; rejected on security |
- Fit gap: none remaining at this level
- Seam: `src/auth/session_adapter.*` (+ `CurrentUser` domain type)
- Exit cost: LOW — the adapter IS the swap point
- Cost model: none (our code)
- Liability transferred: none — this is ours
- Operational owner: us
- Failure mode: token invalid/expired -> treat as anonymous, redirect to sign-in.
                Never fail open to a partially-authenticated state.
- Open questions: refresh-token rotation strategy -> Wayfinder Type B
```

**Terminal because atomic build.** One session, one test seam. Watch it for growth: an
adapter that keeps accreting logic has become a BUILD wearing a WRAP's label.

---

## L3 · Policy Evaluation

**Responsibility:** Given a subject, action, and resource, return permit or deny.

```markdown
## 8. Technology Resolution

- Decision class: ADOPT
- Selected: Casbin (RBAC model), self-hosted in-process
- Standard / protocol: none formal; Casbin model/policy files are portable-ish
- Alternatives considered:
  | Option | Why not |
  |--------|---------|
  | Open Policy Agent | More powerful (Rego), heavier: sidecar + new language to learn |
  | Hand-rolled `if user.role == "admin"` | The reinvention this gate exists to prevent: unauditable, untestable, scattered |
  | Vendor RBAC (in IdP) | Ties domain authorization to the IdP; raises exit cost sharply |
- Fit gap: ships no policy CONTENT -> generates the Role & Permission Model sibling
- Seam: `src/authz/policy_engine.*`
- Exit cost: MEDIUM — swapping engines means re-expressing policies; the decision
             POINT stays put because callers only see `can(subject, action, resource)`
- Cost model: OSS, no licence cost; upgrade/CVE burden is ours
- Liability transferred: none
- Operational owner: us
- Failure mode: engine load error -> deny all (fail closed), alert
- Open questions: none
```

Note the deliberate split: keeping evaluation separate from policy content means the
*algorithm* is adopted and only the *rules* are written — and the rules become data with
a single enforcement point, rather than conditionals scattered across handlers.

---

## L3 · Role & Permission Model

**Responsibility:** Define the roles, permissions, and resource ownership rules of *this
product*.

```markdown
## 8. Technology Resolution

- Decision class: BUILD
- Justification: differentiator. No vendor can know that a regional_manager may approve
  refunds under $500 only within their own region. This IS the domain.
- Selected: Casbin policy files under version control + a domain `Permission` enum
- Alternatives considered:
  | Option | Why not |
  |--------|---------|
  | Vendor role management UI | Roles become vendor state, untestable in CI, undiffable in review |
  | Permissions as free-text strings | No compile-time safety; typos become silent grants |
- Fit gap: n/a (custom by intent)
- Seam: `src/authz/roles.*`, `policies/*.csv`
- Exit cost: n/a
- Cost model: our engineering time
- Liability transferred: none — we own correctness here, so it needs the heaviest tests
- Operational owner: us
- Failure mode: an over-permissive rule is a security incident
                -> policy changes require review + a deny-by-default test suite
- Open questions: does the model need per-resource ACLs, or do roles suffice? -> Type B
```

**This is the node that deserved the effort all along** — and a flat plan would have
buried it under "login" while an agent spent its budget re-implementing password hashing.

---

## L3 · Recovery & Verification · L3 · Deletion & Export · L2 · Auth Audit Trail

Abbreviated — same structure:

| Node | Class | Selected | Key point |
|------|-------|----------|-----------|
| **Recovery & Verification** | BUY | Delegated entirely to the IdP's flows | We hold no credentials, so we have nothing to reset. Buying verification bought recovery for free — a downstream saving the flat plan cannot see |
| **Deletion & Export** | BUILD | Custom job spanning our datastores + IdP delete API | **Nobody can buy this**: only we know every place a user's data lives. Legal obligation (GDPR Art. 15/17) with real deadlines |
| **Auth Audit Trail** | ADOPT | OpenTelemetry -> our existing collector | Standard protocol, backend is a config change. Do not invent a bespoke audit log |

`Deletion & Export` is the sharpest illustration of the gate. It looks like generic
plumbing, so a flat plan omits it entirely — but it is unbuyable *and* legally mandatory,
which is exactly the profile of work that surfaces late and hurts.

---

## What the decomposition bought

| | Flat line | Decomposed |
|---|---|---|
| Nodes | 1 | 7 terminal |
| Custom code | "all of login" | 2 nodes + 1 thin adapter |
| Credential liability | ours | vendor's |
| Where the effort lands | password hashing | roles, permissions, and deletion |
| Vendor swap | "rewrite auth" | re-point one adapter (exit cost LOW, recorded) |
| GDPR deletion | not on the plan | a specified node with an owner |

The naive reading of "login" produces a `users` table and misses deletion, audit, and the
role model entirely. Those omissions are not caught by testing — the tests pass, because
the tests were written against the same flat line.

---

## Running it yourself

```
/recurspec         # route the goal through specification and later execution phases
/recurspec     # run the gate on one existing node, or re-open a stale §8
```

Then claim leaves from `.scratch/wayfinder-map/MAP.md` and implement via
[`/recurspec`](../../src/recurspec/skill/SKILL.md).
