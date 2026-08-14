# Technology Resolution

Answer, for one module: **what will actually implement this?** Produces a §8
Technology Resolution block backed by a real survey.

Use when:

- A Contract Node says what a module *does* but not what it *is built from*.
- Someone is about to write code for a problem that may already be solved.
- A §8 has gone stale (version drift, pricing change, vendor unmaintained).
- You want a second opinion on a build-vs-buy call already made.

For a whole tree, use `/recurspec` — it runs this gate at every node. After resolving,
run `recurspec stack check` on the repository.

---

## 1. Frame the capability

State the responsibility as a **capability**, not an implementation. "Prove a visitor
controls an identity", not "users table". Add explicit non-goals and the constraints that
bound the choice:

- expected scale (and the scale that would change the answer)
- compliance regime (PII, PCI, HIPAA, residency)
- existing stack and languages
- budget shape — is engineering time or vendor spend the scarcer resource?

## 2. Survey — does this already exist?

Find **at least two real alternatives** across these families:

| Family | Look for |
|--------|----------|
| Managed service | Vendors whose whole business is this capability |
| OSS library | Mature, maintained, permissively licensed |
| Framework-native | Something your existing framework already ships |
| Standard protocol | An interop standard that keeps you portable |

For each: current version or plan tier, licence, maintenance signals, and **what it does
not cover**.

> **Verify against live documentation.** Use `/research` or fetch current docs — do not
> rely on recall for versions, pricing, or feature coverage. Never invent a vendor, a
> version number, or a price. If the survey cannot be completed, resolve **DEFER** and
> record it as a Research Frontier in `ROADMAP.md` rather than guessing.

## 3. Score, if it is not obvious

Six axes, 1–5:

| Axis | 1 | 5 |
|------|---|---|
| Commodity depth | Novel, no prior art | Utterly solved |
| Liability transfer | Nothing moves | Major compliance burden moves |
| Fit out of the box | <40% of requirements | ~everything |
| Exit cost (inverted) | Proprietary, deeply coupled | Standard protocol, drop-in |
| Cost at 10× scale | Prohibitive | Flat or self-hosted |
| Operational relief | You still get paged | Vendor is on call |

**≥22 → BUY** · **15–21 → ADOPT** · **≤14 → BUILD**.

A guide, not an oracle: a single 1 on liability transfer for something like credential
storage overrides a high total.

## 4. Resolve

| Class | When |
|-------|------|
| **BUY** | Commodity with real liability transfer or heavy operational load |
| **ADOPT** | Commodity you can run cheaply; no meaningful liability to transfer |
| **WRAP** | Almost always alongside BUY/ADOPT — the adapter fitting it to your domain |
| **BUILD** | Differentiator · fatal fit gap · cost inverts · dependency is a liability · genuinely trivial and stable |
| **DEFER** | Survey incomplete → Research Frontier |

**BUILD requires a recorded justification** naming which condition applies. The other
classes need no defence beyond the block itself.

Do not forget the **WRAP**. Buying a capability rarely removes all work — it bounds it to
an adapter. Name that adapter; it is both a terminal build node and your swap point.

## 5. Emit

```markdown
## 8. Technology Resolution

- **Decision class:** BUY | ADOPT | WRAP | BUILD | DEFER
- **Justification:** <BUILD only — which of the five conditions applies>
- **Selected:** <product / library, pinned version or plan tier>
- **Standard / protocol:** <OIDC, SMTP, S3, OTel, none>
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | <name> | <specific reason — not "worse"> |
- **Fit gap:** <what it does NOT cover>
- **Seam:** `<path to the module isolating it>`
- **Exit cost:** LOW | MEDIUM | HIGH — <what swapping requires>
- **Cost model:** <pricing at expected scale; the number that would flip the decision>
- **Liability transferred:** <obligations moved to the vendor>
- **Operational owner:** vendor | us
- **Failure mode:** <behaviour when down, and the fallback>
- **Open questions:** <OW-nn / ticket, or "none">
```

Write it into the node's `SYSTEM.md`. Keep the alternatives table permanently — it is what
stops the same debate recurring.

---

## Two things to flag back

**The fit gap generates children.** What the vendor does not cover is precisely the set of
sibling nodes. If the gap is substantial, say so — the module probably needs
decomposing via `/recurspec`, split at the boundary between what is bought and what
remains.

**A growing adapter is a bloat signal.** If the WRAP keeps accreting logic, it has quietly
become a custom implementation with a vendor bill attached. Re-open the resolution rather
than letting the seam erode.
