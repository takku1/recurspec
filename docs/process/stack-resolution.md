# Technology Resolution — the third-party-first gate

Every Contract Node passes this gate before it is specified or decomposed
further. It assigns a **decision class** and, for procured nodes, a concrete product.

Loop context: [contract-design.md](./contract-design.md) §3 ·
Module contract: [architecture/stack-resolver/SYSTEM.md](../architecture/stack-resolver/SYSTEM.md) ·
Worked example: [examples/identity-design.md](../examples/identity-design.md)

---

## The default is not BUILD

An agent asked to "implement login" will write a `users` table, a password column, and a
hashing call, because that is what implementing means. Nothing in a plain spec tree
stops it. This gate exists to make **BUILD the class that carries the burden of proof.**

> **Rule.** A node is BUILD only when it encodes something specific to your product that
> no vendor could know. Everything else is BUY, ADOPT, or WRAP.

Writing your own identity store is not a neutral choice with a cost in hours. It is a
choice to take on credential storage, breach liability, password reset flows, MFA, session
fixation, account enumeration, and every future compliance regime — permanently, with a
team of one. That trade is almost never correct, and it is made by default unless a gate
forbids it.

---

## Decision classes

| Class | You get | You own | Typical |
|-------|---------|---------|---------|
| **BUY** | A managed service behind an API | Configuration, the seam, the bill | Auth0, Clerk, Stripe, SendGrid, Algolia, Cloudflare |
| **ADOPT** | An OSS library or framework feature | Running it, upgrading it, its CVEs | NextAuth, Passport, Casbin, Postgres, OpenTelemetry |
| **WRAP** | A thin adapter of your own over a BUY/ADOPT | The adapter only — a file or two | `SessionAdapter` over an IdP's tokens |
| **BUILD** | Nothing; you write it | All of it, forever | Your domain rules, your pricing logic, your matching algorithm |
| **DEFER** | An open question | A research ticket | Anything the survey could not settle |

**WRAP is the most common real answer** and the one flat plans miss. Adopting Google
Identity does not eliminate work — it leaves you a small, well-bounded adapter that turns
a vendor token into your domain's `CurrentUser`. That adapter is a terminal BUILD-shaped
leaf, and it is also your swap point. Name it explicitly.

---

## The two questions that decide it

### 1. Is this a commodity or a differentiator?

| | Commodity | Differentiator |
|---|---|---|
| **Definition** | Every product in your category needs it and none competes on it | Why a customer picks you |
| **Examples** | Auth, email delivery, payments, search indexing, log aggregation, CDN, feature flags, error tracking | Your domain model, your ranking, your workflow, your pricing rules |
| **Resolution** | BUY / ADOPT | BUILD |

If you cannot name a way a user would notice you built it better, it is a commodity.
Build commodities and you spend your budget on the parts of the product that cannot
possibly win.

### 2. What does building it make you liable for?

Some modules carry obligations that transfer to a vendor when you buy them. This is
frequently the entire argument on its own.

| Module | Obligation you take on by building |
|-----------|-----------------------------------|
| Credential storage | Breach liability, hashing currency, MFA, rotation, enumeration defence |
| Card handling | PCI-DSS scope across your whole estate |
| Health / financial records | HIPAA / SOC2 / regional data residency |
| Email sending | Deliverability, SPF/DKIM/DMARC, blocklist reputation |

**Buying moves the obligation onto someone whose business is meeting it.** Weigh this
before hours.

---

## Scoring

When the answer is not obvious, score the alternatives. Six axes, 1–5:

| Axis | 1 | 5 |
|------|---|---|
| **Commodity depth** — how solved is this? | Novel; no real prior art | Utterly solved; many mature vendors |
| **Liability transfer** — what moves to the vendor? | Nothing | Major compliance/security burden |
| **Fit** — how much works out of the box? | <40% of requirements | ~everything |
| **Exit cost** (inverted: 5 = cheap to leave) | Proprietary, deeply coupled | Standard protocol, drop-in replacement |
| **Cost at 10× scale** (5 = still cheap) | Pricing becomes prohibitive | Flat or self-hosted |
| **Operational relief** | You still run/page for it | Vendor is on call |

Rough reading: **≥22 → BUY** · **15–21 → ADOPT** (usually self-host the OSS option) ·
**≤14 → BUILD**, and record why in §8.

Scores are a thinking aid, not an oracle. A single 1 on liability transfer for something
like credential storage should override a high total.

---

## Anti-lock-in: prefer things that speak a standard

Exit cost is the axis teams underweight, and it is controllable by *what you pick*, not
just *whether you buy*.

> **Rule.** Where a standard exists, prefer an option that speaks it, and put your WRAP
> adapter on the standard — not on the vendor's proprietary extensions.

| Capability | Standard to prefer | Effect |
|------------|-------------------|--------|
| Identity | OIDC / OAuth 2.1 | Any compliant IdP is a config change |
| Email | SMTP | Provider swap is credentials |
| Object storage | S3-compatible API | Many vendors, including self-hosted MinIO |
| Telemetry | OpenTelemetry | Backend is a collector endpoint |
| Relational data | SQL + a migration tool | Portable across engines |
| Payments | *(no real standard)* | Accept the lock-in consciously; isolate hard behind a seam |

A proprietary API is not disqualifying — Stripe is worth it — but it must be a *conscious*
entry in §8 with the exit cost written down, not a discovery made two years later.

**The seam is the insurance.** The WRAP adapter is the only place vendor types are
allowed to appear. When vendor objects leak into your domain layer, exit cost silently
goes from LOW to HIGH regardless of how standard the protocol was.

---

## When BUILD really is right

The gate is a bias, not a prohibition. BUILD when:

- **It is your differentiator.** The thing customers buy.
- **The fit gap is fatal.** Vendors cover <40% and the remainder is the hard part.
- **Cost inverts at your scale.** Per-seat or per-event pricing that becomes untenable,
  with a credible internal alternative. Model it; do not assume it.
- **The dependency is a liability.** Unmaintained, single-maintainer, hostile licence, or
  a vendor whose failure would take you down with no fallback.
- **It is genuinely trivial and stable.** A 30-line utility with no security surface beats
  a transitive dependency tree. Small, boring, and *finished* is a real category.

Record the reason in §8. A BUILD without a recorded justification is the failure mode
this gate exists to catch.

---

## §8 Technology Resolution — required fields

Every terminal node carries this. It is what replaces `- Login and user accounts`.

```markdown
## 8. Technology Resolution

- **Decision class:** BUY | ADOPT | WRAP | BUILD | DEFER
- **Selected:** <product / library, pinned version or plan tier>
- **Standard / protocol:** <OIDC, SMTP, S3, none>
- **Alternatives considered:**
  | Option | Why not |
  |--------|---------|
  | <name> | <specific reason — cost, fit gap, licence, maturity> |
- **Fit gap:** <what it does NOT cover — this is where child nodes come from>
- **Seam:** `<path to the adapter/module that isolates it>`
- **Adapter namespace:** `<directory whose code growth belongs to this WRAP>`
- **Exit cost:** LOW | MEDIUM | HIGH — <what swapping would actually require>
- **Cost model:** <pricing at expected scale; the number that would change the decision>
- **Liability transferred:** <compliance/security obligations moved to the vendor>
- **Operational owner:** vendor | us
- **Failure mode:** <what happens when it is down, and the fallback>
- **Open questions:** <R-nnn / Wayfinder ticket, or "none">
```

**Fit gap is the field that drives recursion.** What the vendor does not cover is
precisely the set of child nodes — that is how "Google Identity handles verification"
generates "…so we still own session shape, roles, and deletion."

---

## Review triggers

A §8 entry is a claim about the world, and the world moves. Re-open a resolution when:

| Trigger | Signal |
|---------|--------|
| Pinned version no longer matches the lockfile | Structural Feedback code drift |
| Vendor pricing/tier changes, or scale crosses the modelled point | Cost model invalidated |
| Dependency unmaintained, or a CVE with no upstream fix | Liability inverted |
| Fit gap grew — you keep writing workarounds around the vendor | Adapter bloat; the WRAP is becoming a BUILD |

The last one is the quiet failure: a WRAP that grows past its seam has silently become a
custom implementation with a vendor bill attached. Treat adapter growth as a bloat signal
like any other.
