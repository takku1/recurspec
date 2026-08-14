# R-204: agent-runtime survey for the Worker Pool `RuntimeCall` seam

**Status:** survey complete (2026-08-14). Implemented as
`messages_runtime()` over optional `anthropic==0.122.0`, not as a Claude Agent
SDK wrap. The first-pass recommendation below (WRAP `claude-agent-sdk` with
`disallowed_tools`) was rejected at resolve time: the product's default
toolset is Read/Write/Edit/Bash, `allowed_tools` does not remove tools, and a
deny-list of every filesystem tool is a WRAP that fights the SDK. The Worker
Pool invariant is packet-only; that is a Messages/Completions call.

**Implemented class:** ADOPT the official Messages client as an optional extra;
WRAP it as `RuntimeCall`. Claude Agent SDK and OpenAI Agents SDK remain
documented rejections.

**Capability surveyed:** run one isolated agent turn given only a packet; return a
structured body plus `tokens_in`, `tokens_out`, and latency ms. The worker must not
receive a filesystem path or `tree_root`.

**Non-goals (owned elsewhere):** Recurspec dispatch policy (Worker Pool already
implements budget, tier routing, maker ≠ checker, concurrency), job-store scheduling,
context-packer, and Candidate worktree sandboxing (Evaluation Gate).

**Seam this survey must fit:**

```python
RuntimeCall = Callable[[packet, phase: str, tier: str], RuntimeResponse]
RuntimeResponse = (body, tokens_in, tokens_out, ms)
```

as declared in [`src/recurspec/spec_runner/workers.py`](../../src/recurspec/spec_runner/workers.py)
and [worker-pool/SYSTEM.md](../architecture/spec-runner/worker-pool/SYSTEM.md).

**Method:** first-party product docs, PyPI project pages, GitHub license files, and
vendor API/pricing pages only. Blog posts and secondary summaries were not used as
evidence. Unstable facts that could not be pinned are listed under
[What I could not verify](#what-i-could-not-verify).

---

## 1. Capability

The Worker Pool already owns Recurspec-specific policy. R-204 needs a **production
adapter** that, for one injected call:

1. Accepts a packet (the only worker-visible input) plus phase and tier strings.
2. Runs an isolated session: no carry-over from sibling nodes unless Recurspec
   explicitly resumes.
3. May execute a tool-use loop inside that session (RESEARCH / SPECIFY turns need
   tools; FRAME / CHECK may not).
4. Returns a structured body the Contract Engine can validate, not free prose that
   needs a second model call to parse.
5. Returns actual `tokens_in` and `tokens_out` (Worker Pool budget rule is token-sum
   based).
6. Returns wall-clock `ms` for `wall_clock_per_node_p95`.
7. Never receives a `tree_root` or filesystem path through the call signature.

The adapter is a **procurement seam**, not a second scheduler. Anything that owns
graph state, job readiness, or multi-agent roles is a fit-gap against job-store and
the Runner (see Worker Pool §8 alternatives).

---

## 2. Direct answers

### Does a "Claude Agent SDK" exist as an installable Python package?

**Yes.** Official product name: **Claude Agent SDK** (Python). Official PyPI name:
`claude-agent-sdk`. Latest version verified on 2026-08-14: **0.2.138**, uploaded
**2026-08-13**. Source: [https://pypi.org/project/claude-agent-sdk/](https://pypi.org/project/claude-agent-sdk/).

First-party docs: [https://code.claude.com/docs/en/agent-sdk/overview](https://code.claude.com/docs/en/agent-sdk/overview)
and [https://code.claude.com/docs/en/agent-sdk/python](https://code.claude.com/docs/en/agent-sdk/python).

The predecessor package `claude-code-sdk` **0.0.25** (uploaded 2025-09-29) is marked
**DEPRECATED** on PyPI and tells installers to migrate to `claude-agent-sdk`:
[https://pypi.org/project/claude-code-sdk/](https://pypi.org/project/claude-code-sdk/).

License of the current SDK, from the PyPI page and the overview docs: use is governed
by [Anthropic's Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms),
except where a bundled component has its own LICENSE file. This is **not** an MIT
grant for the SDK itself.

### Is MCP a runtime or a tool protocol? Can it replace an SDK here?

**MCP is a tool/context protocol, not an agent runtime.** The 2026-07-28 specification
defines it as an open protocol that standardizes how LLM *applications* connect to
external data sources and tools (hosts / clients / servers over JSON-RPC). It does
not run a model, count tokens, time a turn, or return `RuntimeResponse`. Sources:
[https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro](https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro)
and [https://modelcontextprotocol.io/specification/2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28).

The official Python implementation is the `mcp` package, latest verified **2.0.0**
(uploaded 2026-07-28, MIT): [https://pypi.org/project/mcp/](https://pypi.org/project/mcp/).
That SDK builds MCP servers and clients. It does not replace `RuntimeCall`.

MCP can sit **inside** a selected runtime as the tool bus (Claude Agent SDK and
OpenAI Agents SDK both document MCP integration). It cannot be the runtime.

---

## 3. Alternatives table

| Candidate | Official name | PyPI / equivalent | Latest verified | Date | License | Prompt/packet | Tool-use loop | Token usage | Isolated session | Latency ms | Fit gap vs `RuntimeCall` | Rebuild by hand? | Pricing (first-party) | Maintenance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | Claude Agent SDK | `claude-agent-sdk` | 0.2.138 | 2026-08-13 [PyPI](https://pypi.org/project/claude-agent-sdk/) | Anthropic Commercial ToS ([PyPI](https://pypi.org/project/claude-agent-sdk/), [overview](https://code.claude.com/docs/en/agent-sdk/overview)) | Yes: `query(prompt=...)` ([Python ref](https://code.claude.com/docs/en/agent-sdk/python)) | Yes: SDK runs the Claude Code agent loop ([overview](https://code.claude.com/docs/en/agent-sdk/overview)) | Yes: `ResultMessage.usage` / `model_usage` ([cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)) | Yes: each `query()` is a new session by default; `resume` / `ClaudeSDKClient` are opt-in ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)) | No first-party field; adapter must time the call | Default tools are filesystem (Read/Write/Bash); `cwd` is a path; settings load from disk unless `setting_sources=[]` ([features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)); no `ms` field; Recurspec phases/tiers unknown to the SDK | No for the loop. Yes for packet mapping, budget/tier, FS deny, session isolation flags, local timer | SDK itself: no list price. Inference billed at Claude API rates (e.g. Sonnet 5 $2 / $10 per MTok) ([platform pricing](https://platform.claude.com/docs/en/about-claude/pricing)). Consumer Claude Code plans are a different product ([claude.com/pricing](https://claude.com/pricing)) | Daily-class: 0.2.138 on 2026-08-13, 0.2.137 on 2026-08-12 ([PyPI history](https://pypi.org/project/claude-agent-sdk/#history)) |
| B | OpenAI Agents SDK | `openai-agents` | 0.20.0 | 2026-08-11 [PyPI](https://pypi.org/project/openai-agents/) | MIT ([LICENSE](https://github.com/openai/openai-agents-python/blob/main/LICENSE)) | Yes: `Runner.run(agent, input)` ([docs](https://openai.github.io/openai-agents-python/)) | Yes: built-in loop until the task completes ([docs](https://openai.github.io/openai-agents-python/)) | Yes: `result.context_wrapper.usage.input_tokens` / `output_tokens` ([usage](https://openai.github.io/openai-agents-python/usage/)) | Yes: omit `session` for a one-shot run; `Session` is opt-in ([usage](https://openai.github.io/openai-agents-python/usage/)) | No first-party field; adapter must time the call | Default path is not filesystem-bound (`Agent` vs `SandboxAgent`). Still does not know Recurspec phases/tiers/budget. Structured body needs `output_type` on the last agent. `final_output` typed as `Any` ([results](https://openai.github.io/openai-agents-python/results/)) | No for the loop. Yes for packet mapping, budget/tier, local timer | SDK: no list price. Model inference: **UNVERIFIED** here (OpenAI pricing URL redirected; not copied from memory) | Active: 0.20.0 on 2026-08-11, 0.19.4 on 2026-08-05 ([PyPI history](https://pypi.org/project/openai-agents/#history)) |
| C | Google Agent Development Kit | `google-adk` | 2.7.0 | 2026-08-13 [PyPI](https://pypi.org/project/google-adk/) | Apache 2.0 ([PyPI](https://pypi.org/project/google-adk/)) | Yes: `Agent(...)` plus a runner/CLI | Yes: workflow runtime with loops, retry, HITL ([PyPI](https://pypi.org/project/google-adk/)) | UNVERIFIED as a first-class `tokens_in`/`tokens_out` pair on a one-shot result object from the pages fetched | Session objects exist (2.0 notes a session-schema break) ([PyPI](https://pypi.org/project/google-adk/)) | UNVERIFIED | Owns a graph workflow runtime — the same class of control-flow collision Worker Pool §8 recorded against LangGraph. Optimized for Gemini; extra deploy surface (Cloud Run / Vertex Agent Engine) | Would rebuild Recurspec's "one stateless packet→result" mapping and still import a second scheduler | Library: no list price. Gemini / Vertex inference: **UNVERIFIED** (not fetched from a first-party price table in this survey) | Active: 2.7.0 on 2026-08-13, 2.6.3 on 2026-08-07 ([PyPI](https://pypi.org/project/google-adk/)) |
| D | Claude Managed Agents | Hosted REST product (not a PyPI runtime) | n/a (API product) | Docs current as of fetch; public beta noted 2026-04-08 ([release notes](https://platform.claude.com/docs/en/release-notes/overview)) | Anthropic commercial (platform) | Yes: session + events ([overview](https://platform.claude.com/docs/en/managed-agents/overview)) | Yes: Anthropic runs the harness | Token billing stated ([pricing](https://platform.claude.com/docs/en/about-claude/pricing#claude-managed-agents-pricing)) | Yes: Anthropic-managed or self-hosted sandbox ([quickstart](https://platform.claude.com/docs/en/managed-agents/quickstart)) | Session runtime is billed; per-call `ms` for Recurspec telemetry is not the product's unit | BUY-shaped hosted control plane. Recurspec already isolates Candidates in worktrees; a remote sandbox plus session IDs is a second isolation model. Worker would still need a WRAP to hide paths | No for the loop. Yes for a REST adapter, auth, event stream, and mapping to `RuntimeResponse` | Tokens at model rates **plus** $0.08 per session-hour while `running`; web search $10 / 1,000 ([pricing](https://platform.claude.com/docs/en/about-claude/pricing#claude-managed-agents-pricing), [claude.com/pricing](https://claude.com/pricing)) | First-party product; budget-on-session added 2026-08-07 ([release notes](https://platform.claude.com/docs/en/release-notes/overview)) |
| E | LangGraph | `langgraph` | 1.2.11 | 2026-08-11 [PyPI](https://pypi.org/project/langgraph/) | MIT ([PyPI](https://pypi.org/project/langgraph/)) | Indirect: you build a graph and invoke it | Yes, plus durable state, HITL, persistence ([PyPI](https://pypi.org/project/langgraph/)) | Via the model provider, not a Recurspec-shaped return | Checkpoints / threads — persistent by design | UNVERIFIED as a first-class field | **Owns graph state and control flow** — exactly what job-store and the Runner own. Worker Pool §8 already rejected this | Would mean two schedulers | Library free (MIT). LangSmith hosted extras: **UNVERIFIED** (not fetched) | Active: 1.2.11 on 2026-08-11 ([PyPI](https://pypi.org/project/langgraph/)) |
| F | CrewAI | `crewai` | 1.15.16 | 2026-08-14 [PyPI](https://pypi.org/project/crewai/) | MIT ([PyPI](https://pypi.org/project/crewai/)) | Crew/task YAML + `kickoff(inputs=...)` | Yes, via Crews/Flows | UNVERIFIED as `tokens_in`/`tokens_out` on a one-shot result | Role/crew conversation, not a stateless packet function | UNVERIFIED | Role and conversation abstractions Worker Pool §8 does not want. Optional AMP control plane is a separate product | Yes for reducing a Crew down to `RuntimeCall` | OSS MIT. AMP / Control Plane commercial pricing: **UNVERIFIED** | Very active: 1.15.16 on 2026-08-14 ([PyPI](https://pypi.org/project/crewai/)) |
| G | AutoGen AgentChat | `autogen-agentchat` | 0.7.5 | 2025-09-30 [PyPI](https://pypi.org/project/autogen-agentchat/) | CC BY 4.0 on repo `LICENSE` ([GitHub](https://github.com/microsoft/autogen/blob/main/LICENSE)) | Conversational agents / teams | Yes (multi-agent chat) | UNVERIFIED from pages fetched | Conversation-centric, not one-shot packet isolation | UNVERIFIED | Same role/conversation mismatch as CrewAI. Last stable PyPI release is ~10 months old as of this survey | Yes to flatten teams into `RuntimeCall` | Library: no list price. Model inference depends on the configured client | Last PyPI 0.7.5 on 2025-09-30 — stale relative to A/B/C |
| H | Anthropic Messages API + `anthropic` SDK | `anthropic` | 0.122.0 | 2026-08-13 [PyPI](https://pypi.org/project/anthropic/) | MIT ([PyPI](https://pypi.org/project/anthropic/)) | Yes: `messages.create(...)` | **No** — you implement the tool loop ([overview comparison](https://code.claude.com/docs/en/agent-sdk/overview); [Messages API](https://platform.claude.com/docs/en/api/messages)) | Yes: response `usage.input_tokens` / `output_tokens` ([Messages API](https://platform.claude.com/docs/en/api/messages)) | Stateless per request; you hold history | Adapter-timed | Worker Pool §8: "cheapest to start, then rebuilds tool-use, retry, and session isolation by hand" | **Yes** — loop, retry, isolation | Sonnet 5 $2 / $10 per MTok; Haiku 4.5 $1 / $5; Opus 5 $5 / $25 ([platform pricing](https://platform.claude.com/docs/en/about-claude/pricing)) | Active: 0.122.0 on 2026-08-13 |
| I | xAI official SDK | `xai-sdk` | 1.18.0 | 2026-08-13 [PyPI](https://pypi.org/project/xai-sdk/) | Apache-2.0 ([PyPI](https://pypi.org/project/xai-sdk/)) | Yes: `client.chat.create(...)` | Function calling and **server-side** agentic tools (web / X / code) are documented; a Recurspec-owned client tool loop is still yours ([PyPI](https://pypi.org/project/xai-sdk/)) | Telemetry can export token usage; first-class `tokens_in`/`tokens_out` on a one-shot agent result: treat as **partial** | Chat objects hold history in-process; API is described as stateless | Adapter-timed | Same family as H: HTTP/gRPC client, not an isolated agent-turn runtime | **Yes** for a local tool loop matching Recurspec tools | grok-4.6: $2 / $6 per 1M tokens below 200k prompt ($4 / $12 at/above) ([docs.x.ai/docs/models](https://docs.x.ai/docs/models)) | Active: 1.18.0 on 2026-08-13 |
| J | MCP Python SDK | `mcp` | 2.0.0 | 2026-07-28 [PyPI](https://pypi.org/project/mcp/) | MIT ([PyPI](https://pypi.org/project/mcp/)) | No — servers expose tools/resources/prompts | No — hosts still run the model loop | No | n/a | n/a | Protocol, not a runtime. Cannot implement `RuntimeCall` | Would still need A, B, or H underneath | None for the protocol | 2.0.0 on 2026-07-28 (spec-aligned) |

Deprecated / do-not-select: `claude-code-sdk` 0.0.25 ([PyPI](https://pypi.org/project/claude-code-sdk/)).

---

## 4. Family notes

### 4.1 Managed vendor SDKs

**Claude Agent SDK** is the first-party library that runs the Claude Code harness
in-process. Official docs contrast it with (1) the Messages/`anthropic` Client SDK,
where *you* implement the tool loop, and (2) Claude Managed Agents, a hosted REST
product ([overview](https://code.claude.com/docs/en/agent-sdk/overview)).

Capabilities that map onto `RuntimeCall`:

- `query(prompt=..., options=ClaudeAgentOptions(...))` takes a string (or streamed
  dicts), not a tree path ([Python ref](https://code.claude.com/docs/en/agent-sdk/python)).
- The SDK runs the agent loop, including built-in tools, hooks, MCP, and
  structured JSON Schema output after tool use
  ([structured outputs](https://code.claude.com/docs/en/agent-sdk/structured-outputs)).
- `ResultMessage` carries `usage` and `model_usage` with input/output token
  counts ([cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).
- Default `query()` creates a new session; isolation is the documented default
  ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)).
- `max_turns` and `max_budget_usd` exist, but Recurspec's budget is
  `max_tokens_per_node` in tokens, so the pool still enforces that after the call.

Fit gaps the WRAP must close:

- **Filesystem gravity.** Default Claude Code tools include Read, Write, Edit, Bash
  ([PyPI](https://pypi.org/project/claude-agent-sdk/)). `cwd` is a path. Official
  docs warn: do not rely on default `query()` options for multi-tenant isolation;
  pass `setting_sources=[]` and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
  ([features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)).
  Recurspec's invariant is stronger: the *worker* never sees a path. The adapter
  must deny filesystem tools (or only allow in-process MCP tools that operate on
  the packet) and must not forward `tree_root`.
- **No `ms` field.** Latency is Recurspec's to measure around the await.
- **Commercial ToS** on the SDK, plus a ~88–100 MB wheel that bundles the Claude
  Code CLI ([PyPI files](https://pypi.org/project/claude-agent-sdk/#files)).
- Recurspec phase/tier strings are unknown to the SDK; the adapter maps `tier`
  onto `model`.

**OpenAI Agents SDK** is the other first-party "runs the loop for you" library.
`Agent` + `Runner.run` is packet-shaped; filesystem appears only if you choose
`SandboxAgent` ([docs](https://openai.github.io/openai-agents-python/),
[PyPI](https://pypi.org/project/openai-agents/)). Usage is aggregated on
`context_wrapper.usage`. MIT license. Provider-agnostic claim is first-party
("100+ other LLMs" on PyPI) but Recurspec should treat non-OpenAI token accuracy
as adapter-tested, not assumed ([usage](https://openai.github.io/openai-agents-python/usage/)).

**Google ADK** (`google-adk` 2.7.0, Apache 2.0) is a real first-party product
([https://adk.dev/](https://adk.dev/), [PyPI](https://pypi.org/project/google-adk/)).
It is a workflow/graph framework, not a one-shot `RuntimeCall`. Same structural
objection as LangGraph.

**Claude Managed Agents** is a BUY-shaped hosted harness with token + $0.08/session-hour
billing ([pricing](https://platform.claude.com/docs/en/about-claude/pricing#claude-managed-agents-pricing)).
Useful later if Recurspec wants Anthropic to own the sandbox. It is the wrong
shape for an injected local callable behind a pool that already isolates
Candidates in worktrees.

### 4.2 OSS agent-session libraries

LangGraph, CrewAI, and AutoGen are real, recently-or-formerly maintained, and
explicitly considered in Worker Pool §8. Nothing in this survey overturns that
rejection: they add a second control plane (graph / crew / team) Recurspec already
owns. AutoGen's last verified PyPI release is 2025-09-30, and the repository
`LICENSE` on `main` is CC BY 4.0
([https://github.com/microsoft/autogen/blob/main/LICENSE](https://github.com/microsoft/autogen/blob/main/LICENSE))
— not treated here as Apache-2.0 despite common secondary claims.

### 4.3 Framework-native / raw HTTP

`anthropic` 0.122.0 (MIT, 2026-08-13) and `xai-sdk` 1.18.0 (Apache-2.0, 2026-08-13)
are the correct *clients* if Recurspec ever BUILD-s the loop. Official Claude docs
state that using the Client SDK means *you* implement the tool loop
([overview](https://code.claude.com/docs/en/agent-sdk/overview)). That is the
commodity test Worker Pool §8 already failed for raw HTTP.

xAI documents function calling and server-side agentic tools; that is still not
an isolated Recurspec turn runtime ([PyPI](https://pypi.org/project/xai-sdk/)).

Latency `ms` is never a vendor field in this family; the adapter times the call.

### 4.4 Standard protocol (MCP)

See [Direct answers](#is-mcp-a-runtime-or-a-tool-protocol-can-it-replace-an-sdk-here).
Select MCP as the **tool protocol** the WRAP may speak. Do not select MCP as the
runtime.

---

## 5. Scoring and recommended decision class

Axes from [stack-resolution.md](../process/stack-resolution.md) (1–5). Scores are
a thinking aid. Worker Pool policy stays BUILD; this table is **only** the
R-204 runtime behind `RuntimeCall`.

| Option | Commodity | Liability transfer | Fit | Exit (5=cheap) | Cost @10× | Ops relief | Total | Reading |
|---|---|---|---|---|---|---|---|---|
| WRAP `claude-agent-sdk` | 5 | 2 | 4 | 3 | 3 | 3 | **20** | ADOPT-range product; WRAP because Recurspec already owns dispatch |
| WRAP `openai-agents` | 5 | 3 | 4 | 4 | 3 | 3 | **22** | Close second; MIT; slightly less FS gravity |
| BUY Claude Managed Agents | 5 | 4 | 2 | 2 | 3 | 4 | **20** | Hosted sandbox is a different isolation model |
| ADOPT `google-adk` / `langgraph` | 5 | 2 | 2 | 3 | 4 | 2 | **18** | Second scheduler |
| BUILD on `anthropic` / `xai-sdk` | 5 | 1 | 2 | 5 | 3 | 1 | **17** | Rebuilds the commodity loop |
| MCP as the runtime | 5 | 1 | 1 | 5 | 5 | 1 | **18** | Wrong layer |

**Recommended class: WRAP.**

**Selected product (research recommendation, not a pin until implementation):**
Claude Agent SDK, PyPI `claude-agent-sdk==0.2.138` (verified 2026-08-14 on
[PyPI](https://pypi.org/project/claude-agent-sdk/)).

**Why WRAP, not ADOPT/BUY/BUILD:**

- The commodity (agent tool-use loop + session + token usage + structured output)
  is solved by a first-party SDK. BUILD of that loop is what Worker Pool §8
  already rejected.
- Recurspec-specific policy (phase→tier, token budget refusal, maker ≠ checker,
  concurrency) stays in `WorkerPool`. The SDK must not own those.
- The adapter is the swap point: `RuntimeCall` stays the only vendor-facing type.
  Exit cost stays LOW if the next runtime implements the same callable.
- BUY (Managed Agents) adds session-hour billing and a remote sandbox Recurspec
  does not need for this seam.

**Why Claude Agent SDK over OpenAI Agents SDK (close second):**

- Worker Pool source comments already named this product as the intended runtime
  pending a live pin (`workers.py` module docstring). This survey supplies that pin.
- First-party structured outputs *after* a multi-turn tool loop
  ([docs](https://code.claude.com/docs/en/agent-sdk/structured-outputs)) match
  Worker Pool ADR-003 (structured results, not prose).
- Token accounting is documented at result and per-model grain
  ([cost tracking](https://code.claude.com/docs/en/agent-sdk/cost-tracking)).

OpenAI Agents SDK remains the documented fallback if Commercial ToS or the
bundled CLI wheel is unacceptable. That is a WRAP of `openai-agents==0.20.0`,
not a redesign of the seam.

**Adapter obligations (fit gap Recurspec still owns):**

1. Map `packet` → prompt (and optional `output_format` schema). Never pass
   `tree_root` or a Candidate path into `cwd` / `add_dirs`.
2. Isolate: `query()` one-shot; do not set `continue_conversation` or `resume`
   unless Recurspec later defines a resume packet. Set `setting_sources=[]` and
   `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`
   ([features](https://code.claude.com/docs/en/agent-sdk/claude-code-features)).
3. Deny filesystem tools (`disallowed_tools` for Read/Write/Edit/Bash/Glob/Grep
   unless a later design explicitly allows packet-local tools).
4. Map `tier` → model id (cheap vs capable). Do not let the SDK pick a project
   default from disk.
5. Read `tokens_in` / `tokens_out` from `ResultMessage.usage` (and `model_usage`
   if subagents are enabled — default should be no subagents).
6. Measure `ms` with a monotonic clock around the await.
7. Translate SDK errors into Worker Pool `tool_error` / `refused`.
8. Document the control-plane / execution-plane split as
   [foundations.md §12](./foundations.md#12-sandboxed-agent-execution-references)
   requires: the adapter does not verify the bundled CLI image.

**Cost model (inference, not the library):**

- Claude Sonnet 5: $2 input / $10 output per million tokens
  ([https://platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing)).
- Claude Haiku 4.5: $1 / $5 per MTok (same page) — candidate cheap-tier model.
- Claude Opus 5: $5 / $25 per MTok (same page).
- Prompt-cache multipliers and web-search $10 / 1,000 searches are on that page
  if the adapter enables those tools.
- The `claude-agent-sdk` wheel itself has no separate list price on PyPI.

---

## 6. What I could not verify

- **OpenAI API token prices** as of this survey. `https://platform.openai.com/docs/pricing`
  redirected to `https://developers.openai.com/api/docs/pricing` and was not
  fetched successfully. Do not pin GPT prices from memory.
- **Google Gemini / Vertex token prices** for ADK-backed runs. Not fetched from a
  first-party price table.
- **Whether `ResultMessage.usage` in Python always exposes integer
  `input_tokens` / `output_tokens` keys** vs a dict that also needs cache fields
  summed. The cost-tracking page documents both per-step `message.usage` and
  result-level `usage` / `model_usage`; an implementor must read the live
  dataclass in `claude-agent-sdk` 0.2.138 rather than invent a mapping.
- **Whether Python `query()` can suppress all disk session transcripts.**
  TypeScript has `persistSession: false`; Python is documented to use
  `CLAUDE_CODE_SKIP_PROMPT_HISTORY` instead
  ([sessions](https://code.claude.com/docs/en/agent-sdk/sessions)). Behavior of
  that env var on Windows was not executed in this survey.
- **Exact SPDX classification of `claude-agent-sdk`.** PyPI states Commercial ToS;
  whether any file inside the wheel is MIT (as the deprecated `claude-code-sdk`
  was) was not audited file-by-file.
- **AutoGen package license on PyPI metadata** vs the GitHub `LICENSE` (CC BY 4.0).
  Only the GitHub file was read. Do not claim Apache-2.0 for AutoGen from this note.
- **CrewAI AMP / Control Plane prices.** The OSS package is MIT; commercial AMP
  pricing was not on the PyPI page.
- **LangSmith Deployment prices.**
- **Whether xAI server-side agentic tools return Recurspec-shaped token totals
  without extra telemetry setup.**
- **Runtime measurement of any SDK** (latency, token honesty, isolation). This
  survey is documentary (`Observed` / citation-backed). It is not `Measured`.
- **A ratified standard for sandboxing coding-agent loops.** Same gap as
  [foundations.md §12](./foundations.md#12-sandboxed-agent-execution-references).

---

## 7. Sources (primary)

1. Worker Pool contract: [docs/architecture/spec-runner/worker-pool/SYSTEM.md](../architecture/spec-runner/worker-pool/SYSTEM.md)
2. Seam implementation: [src/recurspec/spec_runner/workers.py](../../src/recurspec/spec_runner/workers.py)
3. Decision-class process: [docs/process/stack-resolution.md](../process/stack-resolution.md)
4. Claude Agent SDK PyPI: https://pypi.org/project/claude-agent-sdk/
5. Claude Agent SDK overview: https://code.claude.com/docs/en/agent-sdk/overview
6. Claude Agent SDK Python reference: https://code.claude.com/docs/en/agent-sdk/python
7. Claude Agent SDK sessions: https://code.claude.com/docs/en/agent-sdk/sessions
8. Claude Agent SDK cost tracking: https://code.claude.com/docs/en/agent-sdk/cost-tracking
9. Claude Agent SDK structured outputs: https://code.claude.com/docs/en/agent-sdk/structured-outputs
10. Claude Agent SDK filesystem settings: https://code.claude.com/docs/en/agent-sdk/claude-code-features
11. Deprecated Claude Code SDK: https://pypi.org/project/claude-code-sdk/
12. Anthropic Commercial Terms: https://www.anthropic.com/legal/commercial-terms
13. Anthropic Messages API: https://platform.claude.com/docs/en/api/messages
14. Anthropic Python client: https://pypi.org/project/anthropic/
15. Anthropic platform pricing: https://platform.claude.com/docs/en/about-claude/pricing
16. Claude consumer/API pricing portal: https://claude.com/pricing
17. Claude Managed Agents overview: https://platform.claude.com/docs/en/managed-agents/overview
18. Claude Managed Agents quickstart: https://platform.claude.com/docs/en/managed-agents/quickstart
19. Claude Platform release notes: https://platform.claude.com/docs/en/release-notes/overview
20. OpenAI Agents SDK PyPI: https://pypi.org/project/openai-agents/
21. OpenAI Agents SDK docs: https://openai.github.io/openai-agents-python/
22. OpenAI Agents SDK usage: https://openai.github.io/openai-agents-python/usage/
23. OpenAI Agents SDK results: https://openai.github.io/openai-agents-python/results/
24. OpenAI Agents SDK license: https://github.com/openai/openai-agents-python/blob/main/LICENSE
25. Google ADK PyPI: https://pypi.org/project/google-adk/
26. Google ADK site: https://adk.dev/
27. LangGraph PyPI: https://pypi.org/project/langgraph/
28. CrewAI PyPI: https://pypi.org/project/crewai/
29. AutoGen AgentChat PyPI: https://pypi.org/project/autogen-agentchat/
30. AutoGen license file: https://github.com/microsoft/autogen/blob/main/LICENSE
31. xAI SDK PyPI: https://pypi.org/project/xai-sdk/
32. xAI model pricing: https://docs.x.ai/docs/models
33. MCP intro: https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro
34. MCP specification 2026-07-28: https://modelcontextprotocol.io/specification/2026-07-28
35. MCP Python SDK PyPI: https://pypi.org/project/mcp/
