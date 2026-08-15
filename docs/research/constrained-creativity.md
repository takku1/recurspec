# Constrained creativity: literature survey and applicability to Recurspec

This document investigates a specific design hypothesis: that deliberately imposed
constraints (a strict ruleset, a bounded conceptual space, a formal contract) can
increase the quality or novelty of creative output rather than suppress it, and asks
whether that literature suggests concrete changes to Recurspec's architecture — the
Contract Tree, EARS invariants, Technology Resolution decision rules, the
Architect/Implementor split, and the Evaluation Gate.

It follows the evidence policy already established in
[foundations.md](./foundations.md): cite original research, state only what the
cited source actually establishes, and label a Recurspec-specific application as a
**design inference** when the source motivates it but does not evaluate that
mechanism. This document adds one more discipline specific to its subject: several
of the strongest-sounding claims in the popular "constraints breed creativity"
narrative (the jam study above all) are weaker, contested, or reversed once traced
to their primary source, and that is reported here rather than smoothed over.

Nothing in this document is a claim that Recurspec's own mechanisms have been
validated by any cited source. Every "Recurspec design inference" below is an
untested hypothesis about applicability, not a result.

## 1. Constraint-driven creativity in game design theory

Salen and Zimmerman's *Rules of Play* argues that "meaningful play" — the designer's
target outcome — emerges from the interaction between players and a system of rules,
and that discernible, integrated consequences of an action are what make play
meaningful at all. Rules are the mechanism that makes actions have legible
consequences; an unruled space does not produce meaningful play merely by being
unconstrained. See [Salen & Zimmerman, *Rules of Play: Game Design Fundamentals*, MIT
Press, 2004](https://mitpress.mit.edu/9780262240451/rules-of-play/) (ISBN
978-0262240451).

Bogost's *Persuasive Games* coins "procedural rhetoric": the claim that a
rule-based, executable system can make an argument about how a domain works through
the processes and constraints it enforces, not only through text or images. The
rules are not incidental to the game's expressive content; they are its primary
expressive medium. See [Bogost, *Persuasive Games: The Expressive Power of
Videogames*, MIT Press, 2007](https://mitpress.mit.edu/9780262514880/persuasive-games/)
(ISBN 978-0262514880).

Lai and Vecchi trace a direct lineage of "formalized creativity" across five
constraint-driven creative movements — Global Game Jam, Lars von Trier's Dogma '95
film manifesto, the 4k/64k demo scene, the OuBaPo constrained-comics movement, and
Japanese collaborative renga poetry — arguing (via Moeran's six constraint types:
material, temporal, spatial, social, representational, economic) that all five share
a structure: multiple participants producing an artifact under deliberately imposed
formal limits, valuing process as much as product. This is a comparative historical
and theoretical analysis, not a controlled experiment. See [Lai & Vecchi, "Formal
Constraints and Creativity: Connecting Game Jams, Dogma '95, the Demo Scene, OuBaPo,
and Renga poets," *Games and Culture*, 20(8), 963-983,
2025](https://doi.org/10.1177/15554120241233865).

Kultima, Alha, and Nummenmaa's qualitative interview study of the Survival Mode 2016
Global Game Jam site (experienced developers, an added thematic constraint on top of
the standard jam theme, and infrastructure limits from a remote Lapland venue) found
practitioners describing constraints as having *both* a liberating and a restricting
effect on the same creative process, not a uniformly positive one. See [Kultima,
Alha, & Nummenmaa, "Design Constraints in Game Design: Case: Survival Mode Game Jam
2016," Proc. Int'l Conf. on Game Jams, Hackathons, and Game Creation Events, ACM,
22-29, 2016](https://doi.org/10.1145/2897167.2897174). A companion study of jam
*organisers* similarly found some organisers treat the jam theme as a rigid
constraint and others as flexible/negotiable — i.e., practitioners disagree about
how tightly a constraint should bind even within the same event format. See [Falk,
Biskjaer, Halskov, & Kultima, "How Organisers Understand and Promote Participants'
Creativity in Game Jams," Proc. 6th Int'l Conf. on Game Jams, Hackathons and Game
Creation Events, ACM, 12-21, 2021](https://doi.org/10.1145/3472688.3472690).

**What this supports:** across game design theory and a cluster of empirical/
historical case studies from other constrained-art movements, a rule system that
gives actions legible, bounded consequences is treated as a precondition for
meaningful creative work, not an obstacle to it — but practitioners themselves report
the same constraint as sometimes liberating and sometimes simply restricting,
depending on how it is applied.

**What this does not support:** none of these sources is a controlled experiment
showing that *more* rules produce *better* output monotonically, or that any
particular ruleset design is optimal. Rules of Play and Persuasive Games are
theoretical/design texts; Lai & Vecchi is a comparative historical argument; the
Kultima/Alha and Falk et al. studies are qualitative and explicitly report a mixed,
double-edged effect rather than a clean "constraints help" finding.

**Recurspec design inference:** the Contract Tree's EARS invariants and interface
definitions function like Bogost's procedural rhetoric and Salen & Zimmerman's rule
system for the Implementor — they are what make a Candidate's actions have legible,
checkable consequences (pass/fail against the Evaluation Gate) rather than
unconstrained code that only "looks" plausible. This is a real structural analogy,
not a metaphor stretch: a Contract Node without invariants is exactly Salen &
Zimmerman's unruled space, where "meaningful" outcomes (in Recurspec's terms,
verifiable ones) cannot be distinguished from arbitrary ones. The Kultima/Alha
finding that the *same* constraint reads as liberating or restricting depending on
delivery is the more actionable half of this section: it suggests a Contract Node's
invariants should be reviewed not just for correctness but for whether the
Implementor experiences them as generative scaffolding (this is the shape a correct
answer takes) versus arbitrary red tape (this rule serves no verification purpose).
Recurspec has no mechanism today that distinguishes these two failure-adjacent
states of a Contract Node — that is a concrete gap, not currently a concrete fix.

## 2. Boden's typology of creativity and its computational formalization

Boden's *The Creative Mind* distinguishes three kinds of creativity relative to a
"conceptual space" (the set of ideas reachable under a domain's implicit rules):
**combinational** creativity (novel combinations of familiar ideas), **exploratory**
creativity (generating new ideas by traversing the interior and boundary of an
existing conceptual space without changing its rules), and **transformational**
creativity (altering the space's own generative rules so that previously
unreachable ideas become reachable). See [Boden, *The Creative Mind: Myths and
Mechanisms*, 2nd ed., Routledge,
2004](https://www.routledge.com/The-Creative-Mind-Myths-and-Mechanisms/Boden/p/book/9780415314534)
(ISBN 978-0415314534; 1st ed. 1990).

Wiggins formalizes this into a computational-creativity framework: a creative system
is defined by a universe of possible concepts, a (typically much smaller) set of
rules defining which concepts are currently "in" the conceptual space, a set of
traversal rules for searching within that space, and — for transformational
creativity — rules for changing the rules that define the space itself. See
[Wiggins, "A Preliminary Framework for Description, Analysis and Comparison of
Creative Systems," *Knowledge-Based Systems*, 19(7), 449-458,
2006](https://doi.org/10.1016/j.knosys.2006.04.009).

Ritchie proposes empirical, largely domain-independent criteria for judging whether
a generative system's output should be called "creative" — centered on novelty and
quality relative to the space of things the system's ruleset makes reachable, and on
how *typical* a result is of the inspiring examples versus how far it departs from
them. See [Ritchie, "Some Empirical Criteria for Attributing Creativity to a
Computer Program," *Minds and Machines*, 17(1), 67-99,
2007](https://doi.org/10.1007/s11023-007-9066-2).

**What this supports:** creativity researchers treat "constrained" and "creative" as
compatible, not opposed, for two of Boden's three categories: exploratory creativity
is *defined* as creative search inside a bounded space, and Wiggins's framework
formally requires an explicit, finite ruleset before a system's behavior can even be
evaluated for creativity at all.

**What this does not support: **neither source claims exploratory creativity is
"as good as" or interchangeable with transformational creativity — Boden is explicit
that transformational creativity (changing the rules) is the deeper, rarer kind, and
that a system permanently confined to one fixed conceptual space cannot produce it.
Tightening a ruleset can only ever purchase more exploratory creativity; it cannot
purchase transformational creativity, and an over-tightened space can foreclose it.

**Recurspec design inference:** this is the closest thing in the reviewed literature
to a load-bearing structural mapping, and it also names Recurspec's central risk
precisely. A Contract Node's invariants and its Technology Resolution decision
define Boden's "conceptual space" for the Implementor: the Evaluation Gate rewards
exploratory creativity (novel Candidates that satisfy the existing space) and has no
mechanism for transformational creativity (a Candidate that reveals the space itself
is wrong). Recurspec already has a named mechanism for exactly this — **Structural
Feedback**, where implementation shape and the Contract Tree disagree, and
**Research Frontier**, an uncertainty that must be resolved before a node can be
completed — so this section's actionable contribution is not "add a new mechanism"
but "treat Structural Feedback explicitly as the system's transformational-creativity
channel, and audit whether it is actually reachable in practice." A Candidate that
is REVERTed by the Evaluation Gate because it violates an invariant is exploratory
failure; a Candidate that is *correct in a way the Contract Node's invariants did not
anticipate* is transformational signal, and the two are easy to conflate under a
binary KEEP/REVERT gate. Whether the Evaluation Gate currently distinguishes "wrong"
from "right but the space was wrong" is a concrete, checkable question against the
existing `src/recurspec/evaluation.py` gate logic, not answered by this literature
review.

## 3. Functional fixedness and design fixation

Duncker's classic "candle problem" experiment found that when a box of tacks was
presented as a closed container (holding tacks), few participants thought to empty
it and use the box itself as a candle-holder; when the same tacks were presented
loose beside an empty box, almost all participants solved the problem. The box's
established function as "a container" fixed subjects' perception of what it could
be. See [Duncker, "On Problem Solving" (trans. L. S. Lees), *Psychological
Monographs*, 58(5), 1945] (originally *Zur Psychologie des produktiven Denkens*,
Springer, 1935); summarized in the [Wikipedia overview of the candle
problem](https://en.wikipedia.org/wiki/Candle_problem), used here only as a pointer
to the primary study, not as the citation itself.

Jansson and Smith's design-fixation experiments found that engineering students
given an example solution to a design problem — even one explicitly flagged as
flawed — reliably reproduced features of that example in their own designs at a
higher rate than a control group given no example, and did so without recognizing
it. See [Jansson & Smith, "Design Fixation," *Design Studies*, 12(1), 3-11,
1991](https://doi.org/10.1016/0142-694X(91)90003-F).

A related mechanism: Hallihan, Cheong, and Shu's protocol-analysis study of novice
designers doing biomimetic design found confirmation bias operating *during* concept
generation — designers disproportionately interpreted ambiguous or disconfirming
information as supporting their initial idea, reinforcing whatever direction they
started in. See [Hallihan, Cheong, & Shu, "Confirmation and Cognitive Bias in Design
Cognition," Proc. ASME 2012 IDETC/CIE, Vol. 7,
2012](https://asmedigitalcollection.asme.org/IDETC-CIE/proceedings-abstract/IDETC-CIE2012/913/253634).

**What this supports:** a prior example or a fixed frame measurably narrows
subsequent search, and this happens below conscious awareness — it is not a matter
of the subjects trying and failing to think outside the frame, they typically do not
notice the frame is there. This is a robust, frequently-replicated experimental
result (candle problem) plus a directly design-relevant follow-on (Jansson & Smith).

**What this does not support:** none of these studies is about *rule-based*
constraints (an explicit invariant a person can read and reason about); they are
about *implicit, unstated* framing from a prior example or an object's habitual use.
Explicit constraints (Section 1-2's subject) and implicit fixation (this section's
subject) are related but not identical phenomena, and the literature does not show
that one substitutes for or prevents the other. An explicit rule can coexist with,
or even amplify, fixation on how that rule has previously been satisfied.

**Recurspec design inference:** this is a genuine risk to a specific Recurspec
mechanism — the **Best Known State** and any worked example an Architect provides
alongside a Contract Node. Jansson & Smith's finding maps almost exactly onto
Recurspec's shape: the Best Known State is precisely "an example solution provided
with a design problem," and their result predicts an Implementor's next Candidate
will disproportionately resemble it even where a materially different approach
would satisfy the invariants better — including reproducing a flaw the Best Known
State happens to have. This is concrete and testable: instrument Candidates
generated with versus without visibility into the current Best Known State's
implementation (not just its metric vector) and compare solution diversity, the same
ablation shape Recurspec already uses elsewhere (see foundations.md §11's
repair-memory ablation precedent). It also argues for a specific, checkable design
question: does the Implementor's context expose the Best Known State's *code*, or
only its *metric vector and pass/fail status*? If the former, Recurspec may be
manufacturing design fixation by construction on every repair cycle, independent of
how well-specified the invariants are.

## 4. Choice overload / "paradox of choice" — a claim that does not survive contact with its own follow-up literature

Iyengar and Lepper's field experiment at an upscale grocery store alternated a
tasting display of 6 versus 24 jam varieties. The 24-jam display attracted more
browsers but converted roughly ten times fewer of them into buyers (about 3% versus
about 30%), and a companion lab study found participants who chose from a smaller
set of essay topics wrote better essays and reported more satisfaction. See [Iyengar
& Lepper, "When Choice Is Demotivating: Can One Desire Too Much of a Good Thing?"
*Journal of Personality and Social Psychology*, 79(6), 995-1006,
2000](https://doi.org/10.1037/0022-3514.79.6.995).

This result does not replicate as a general phenomenon. Scheibehenne, Greifeneder,
and Todd's meta-analysis pooled 63 conditions from 50 published and unpublished
experiments (N = 5,036) testing the choice-overload hypothesis and found a mean
effect size indistinguishable from zero, with large unexplained variance between
studies; the authors state they could not identify sufficient conditions under which
more choice reliably reduces satisfaction or motivation. See [Scheibehenne,
Greifeneder, & Todd, "Can There Ever Be Too Many Options? A Meta-Analytic Review of
Choice Overload," *Journal of Consumer Research*, 37(3), 409-425,
2010](https://doi.org/10.1086/651235).

**What this supports:** under some circumstances, in some populations, a smaller
choice set can increase conversion, satisfaction, or output quality relative to a
larger one — the phenomenon is real in specific settings and the original jam study
is a genuine, published, peer-reviewed field experiment, not a myth invented later.

**What this does not support:** "more choice is demotivating" as a general,
reliable psychological law. This is the single largest gap between the popular
version of "constraints help creativity" (which frequently cites the jam study as if
it were settled) and what the primary literature — including a large, rigorous
meta-analysis by researchers who took the hypothesis seriously — actually
establishes. Citing the jam study alone, without Scheibehenne et al.'s correction,
would be exactly the kind of overreach foundations.md's evidence policy exists to
prevent.

**Recurspec design inference:** this section counsels *against* a plausible-sounding
but unsupported justification, which is itself the useful finding. It would be easy
to justify Technology Resolution's fixed five-way decision class
(`BUY`/`ADOPT`/`WRAP`/`BUILD`/`DEFER`, per CONTEXT.md) as "fewer options reduce
decision paralysis, per the choice-overload literature." That justification should
not be made: the meta-analysis found no reliable effect of set size on decision
quality or satisfaction, across a much larger and more rigorous evidence base than
the original study. Technology Resolution's fixed taxonomy may still be a good
design — it plausibly earns its keep on other grounds entirely, e.g. that five
categories are exhaustive and each has a distinct downstream evaluation path — but
those are architectural and legibility arguments, not decision-psychology ones, and
the two should not be conflated in the skill's own documentation
(`src/recurspec/skill/references/resolve.md`) or in `resolve-stack`'s design
rationale if either currently gestures at "reduces choice overload."

## 5. Constraint satisfaction in generative/computational creativity systems

Wiggins's framework (Section 2) treats every generative creative system as, in
effect, a constraint-satisfaction problem: a universe of possible artifacts, a rule
set carving out the currently reachable subset, and a search procedure over that
subset. Ritchie's evaluation criteria (Section 2) then ask, of any output that
satisfies the constraints: is it novel relative to the inspiring set, and is it of
acceptable quality — two axes that are independent of mere constraint-satisfaction,
since a system can satisfy all constraints and still produce typical, low-value
output.

**What this supports:** in computational-creativity research, "satisfies the
constraints" and "is creative" are explicitly treated as different questions — a
generator that always produces valid-but-boring output within a legal space is
constraint-satisfying without being creative by Ritchie's criteria.

**What this does not support:** neither source is empirical evidence that adding
more constraints to a generative system *increases* the novelty or quality of what
survives; they supply vocabulary for evaluating creative output, not a causal
mechanism for producing it.

**Recurspec design inference:** this is the most direct, mechanical parallel to the
Evaluation Gate in the whole survey, and also exposes the sharpest gap. The
Evaluation Gate today (per CONTEXT.md) decides `KEEP`/`REVERT`/`ESCALATE` from
correctness checks, metric comparison, telemetry honesty, and bounded retries — this
is pure constraint satisfaction in Wiggins's sense (does the Candidate stay inside
the legal space). Recurspec has no equivalent of Ritchie's novelty/quality axes: two
Candidates that both pass every invariant and improve every metric are
interchangeable to the gate even if one is a minimal, low-value patch and the other
is a substantially better-shaped solution. This is a concrete, scoped, and testable
idea — not a vague inspirational parallel — but it is also a real scope expansion:
it would require the Evaluation Gate (or a human reviewer at the Architect/
Implementor boundary) to score *how* a Candidate satisfies the space, not only
*whether* it does, and Recurspec's own evidence-classing table (foundations.md §6)
already flags that "model judgement" evidence is advisory, not gating, for exactly
this kind of qualitative axis. Any such addition should stay non-gating for that
reason.

## 6. Oulipo-style constrained writing — a source that is closer to a disanalogy than an analogy for Recurspec

Oulipo ("Ouvroir de littérature potentielle"), founded in 1960 by Raymond Queneau
and François Le Lionnais, produces literature under deliberately chosen, often
extreme formal constraints: Georges Perec's *La Disparition* (1969) is a
300-page novel written without the letter "e"; Jean Lescure's "N+7" procedure
replaces every noun in a source text with the seventh following noun in a chosen
dictionary; Queneau's *Cent Mille Milliards de Poèmes* (1961) is ten sonnets on
cut strips of paper, combinable into 10^14 distinct poems, all metrically and
grammatically valid by construction. See the overview at
[languageisavirus.com's Oulipo
page](https://www.languageisavirus.com/creative-writing-techniques/oulipo.php) and,
for the movement's own theoretical self-description of "constraint" as
simultaneously arbitrary and generative,
[cursus.edu, "Oulipo: The game of constrained
literature"](https://cursus.edu/en/22498/oulipo-the-game-of-constrained-literature).
Both are secondary descriptions of the movement rather than a single peer-reviewed
primary study; Oulipo's own writings (Queneau, Perec, Roubaud) are the true primary
sources and were not separately fetched here.

**What this supports:** it is possible to construct a rule system so restrictive
that satisfying it *by construction* guarantees a certain kind of surface
well-formedness (N+7 always yields a grammatical sentence; a lipogram always avoids
the forbidden letter), and highly skilled practitioners have produced acclaimed work
under such rules.

**What this does not support, and where the analogy to Recurspec breaks:** in every
Oulipo example, the same person who is doing the creative work chooses (or at least
consents to) their own constraint — it is autotelic. Recurspec's Architect/
Implementor split is the opposite structure: constraints are authored by one party
and satisfied by a different, isolated party who did not choose them and cannot
renegotiate them unilaterally. Oulipo is evidence that self-imposed constraint can
be generative for an individual working alone; it says nothing about whether an
externally imposed, non-negotiable constraint has the same effect on a different
person tasked with satisfying it. This is exactly the kind of parallel the task
brief asked to be honest about rather than force: it sounds supportive at a glance
and is a materially different mechanism on inspection.

**Recurspec design inference:** the one piece that transfers cleanly is narrower
than "constraints breed creativity" — it is that a well-designed constraint can be
*generative* rather than merely *filtering*: N+7 does not just reject bad sentences,
it produces a sentence directly. EARS invariants aspire to the same property (a
"When/If/While ... the ... shall ..." template does not just check a requirement
after the fact, it shapes how the requirement gets written in the first place, per
foundations.md §1's account of the EARS paper). That is a real, already-implemented
structural echo of Oulipo's generative-constraint idea, and foundations.md already
credits Mavin et al. for it correctly. Beyond that specific point, Oulipo should not
be cited as support for the Architect/Implementor split itself; that split's
justification belongs with Section 8 below (independent verification) and with
foundations.md §2 (NASA IV&V), not with constrained-writing theory.

## 7. Design patterns as codified constraint

Gamma, Helm, Johnson, and Vlissides catalog 23 recurring object-oriented design
solutions (creational, structural, behavioral), each documented with the problem it
addresses, when it applies "in view of other design constraints," and its
consequences and trade-offs — explicitly framed as a shared vocabulary that lets
designers name a constrained, pre-vetted solution shape instead of inventing one
from scratch each time. See [Gamma, Helm, Johnson, & Vlissides, *Design Patterns:
Elements of Reusable Object-Oriented Software*, Addison-Wesley,
1994](https://www.google.com/books/edition/Design_Patterns/iyIvGGp2550C) (ISBN
978-0201633610). The book's own preface credits Christopher Alexander's pattern
language for buildings and towns as the origin of "pattern" as a codified,
constraint-bearing, reusable design vocabulary; see [Alexander, Ishikawa, & Silverstein,
*A Pattern Language: Towns, Buildings, Construction*, Oxford University Press,
1977](https://global.oup.com/academic/product/a-pattern-language-9780195019193)
(ISBN 978-0195019193).

**What this supports:** a named, catalogued constraint (this class of problem is
solved this way, here is when it applies and what it costs) reduces the design
search space for a recurring problem shape and gives a team a shared vocabulary for
discussing trade-offs. Both source books argue this from extensive practitioner
experience; neither is a controlled study measuring creativity or defect-rate
outcomes from pattern use.

**What this does not support:** an empirical claim that adopting more patterns, or
enforcing pattern use, improves designs. The GoF book itself repeatedly warns
against applying a pattern where it does not fit and treats overuse (forcing a
recurring pattern where a simpler ad hoc solution would do) as a design smell, not a
virtue.

**Recurspec design inference:** the applicable idea is narrow but real: SYSTEM.md's
existing structure (intent, interface, invariants, evidence maturity, per CONTEXT.md's
Contract Node definition) is already pattern-language-shaped — a recurring,
named format for expressing a constrained design decision, reusable across nodes.
The concretely testable extension this section suggests is a **named catalog of
recurring Contract Node shapes** (e.g., common Evaluation Gate configurations for a
given Decision Class, or common EARS invariant clusters for a given kind of
Procurement Seam) that an Architect can cite by name instead of re-deriving from
scratch — genuinely analogous to citing "Strategy pattern" instead of re-explaining
an interchangeable-algorithm design each time. This is additive tooling, not a
change to the Contract Tree's semantics, and the GoF book's own overuse warning
should travel with it: a Contract Node forced into a catalog shape it does not
actually fit is the Recurspec analogue of a forced design pattern.

## 8. Design by Contract and the formal-methods tension with flexibility

Meyer's Design by Contract formalizes component interaction as explicit
preconditions, postconditions, and class invariants, with the stated goal of
correctness-by-construction and early detection of interface-level errors. See
[Meyer, "Applying 'Design by Contract'," *Computer*, 25(10), 40-51,
1992](https://doi.org/10.1109/2.161279).

Bowen and Hinchey's widely cited "ten commandments" for formal-methods practitioners
is itself partly a caution against over-formalization: among the ten is "thou shalt
not attempt to formalize everything" — explicitly warning that applying formal
methods indiscriminately, rather than to the parts of a system that most need them,
is a documented failure mode of formal-methods adoption, not a hypothetical one. See
[Bowen & Hinchey, "Ten Commandments of Formal Methods," *Computer*, 28(4), 56-63,
1995](https://doi.org/10.1109/2.375178); their ten-years-later follow-up largely
reaffirms the original commandments while noting formal methods had by then become
more mainstream in safety-critical niches specifically, not universally. See [Bowen
& Hinchey, "Ten Commandments of Formal Methods ... Ten Years Later," *Computer*,
39(1), 40-48, 2006](https://doi.org/10.1109/MC.2006.35).

Shipman and Marshall's empirical study of formal-representation tools in
collaborative work found that users routinely resist, work around, or abandon a
required formalism when it demands more explicitness or premature certainty than
they actually have about the content — they term this the central practical tension
of formal representations in real (as opposed to idealized) use. See [Shipman &
Marshall, "Formality Considered Harmful: Experiences, Emerging Themes, and
Directions on the Use of Formal Representations in Interactive Systems," *Computer
Supported Cooperative Work (CSCW)*, 8(4), 333-352,
1999](https://doi.org/10.1023/A:1008716330212).

**What this supports:** the software-engineering literature on formal methods
already contains its own internal caution against over-constraint — this is not an
outside critique being imported, it is a finding from within the formal-methods
community itself, from one of the most-cited papers advocating for formal methods'
broader adoption. Shipman & Marshall's finding is a specific, named mechanism for
*why* over-formalization fails in practice: it forces false precision before the
author actually has that precision, and people evade tools that do this.

**What this does not support:** neither source claims formal methods and creativity
are opposed in general, and Meyer's own DbC framework is presented as compatible
with, not a replacement for, exploratory design.

**Recurspec design inference:** this is the most direct, load-bearing mapping in the
whole document, because Recurspec's own vocabulary already names the two things
these sources are about. EARS invariants and a Contract Node's interface are
Recurspec's version of Meyer's preconditions/postconditions/invariants; **Evidence
Stage** (`Unknown` through `Proved`/`Refuted`, per CONTEXT.md) is Recurspec's
existing, already-implemented answer to Shipman & Marshall's exact failure mode —
it lets an Architect record "I do not yet know enough to write a real invariant
here" instead of being forced to fabricate false precision to satisfy the Contract
Tree's format. **Research Frontier** exists for the same reason. The genuinely
concrete, checkable question this section raises is not "should Recurspec add this
mechanism" (it already has it) but "is `Unknown` actually used honestly and often
enough in practice, or does Contract Tree tooling implicitly pressure an Architect
toward writing a plausible-looking-but-premature invariant rather than declaring
`Unknown`" — e.g., by how `structure_gate.py` or the Contract Tree tooling scores or
flags nodes that are still at `Unknown`. That is an auditable question about
existing telemetry, not a new feature request, and it is exactly Bowen & Hinchey's
"thou shalt not attempt to formalize everything" commandment applied to Recurspec's
own format.

## 9. The failure-mode side: over-constraint, brittleness, and rule bloat

Brooks distinguishes essential complexity (inherent to the problem domain) from
accidental complexity (self-inflicted, arising from process and tooling choices) and
argues no single technique — including, by extension, adding more process — yields
an order-of-magnitude improvement, because most of what remains hard by the 1980s
was already essential rather than accidental. The direct implication for any
constraint-adding practice: it can only ever attack accidental complexity, and past
some point, additional process is itself a source of new accidental complexity
rather than a reduction of it. See [Brooks, "No Silver Bullet — Essence and Accident
in Software Engineering," *Computer*, 20(4), 10-19,
1987](https://www.cs.unc.edu/techreports/86-020.pdf) (also *IEEE Computer*, 1987;
originally presented 1986).

Design fixation (Section 3) is itself a documented cost of a poorly chosen
constraint or example, not only of an absent one: Jansson & Smith's subjects fixated
on a *provided, explicitly flawed* example just as strongly as on an unflagged one —
the existence of guidance, even bad guidance, measurably narrowed subsequent search.
Confirmation bias (Hallihan, Cheong, & Shu, Section 3) compounds this: once a
direction is set — including by an early constraint — designers disproportionately
interpret new information as validating it rather than challenging it.

Shmueli, Pliskin, and Fink's controlled experiment (over 200 participants asked to
specify a "nice-to-have" software feature) found behavioral effects analogous to the
endowment effect and the "IKEA effect" (people overvalue things they helped
construct) driving over-specification: participants who had more involvement in
articulating a feature rated it as more essential than equally-situated participants
who did not, independent of the feature's actual merit. This is a controlled,
peer-reviewed empirical study of *why* specifications accrete unnecessary rules over
time, not just an anecdotal description of "gold-plating." See [Shmueli, Pliskin, &
Fink, "Explaining Over-Requirement in Software Development Projects: An Experimental
Investigation of Behavioral Effects," *International Journal of Project
Management*, 33(2), 380-394,
2015](https://doi.org/10.1016/j.ijproman.2014.06.003).

**What this supports:** over-constraint is not merely a vague worry — it has at
least three distinct, separately documented mechanisms: (1) added process attacks
only accidental complexity and can itself become a new source of it past some point
(Brooks); (2) any provided guidance, including a flawed one, measurably narrows
subsequent search below conscious awareness (Jansson & Smith); (3) the psychological
investment of *writing* a requirement independently inflates perceived necessity of
that requirement, which is a specific, mechanistic account of how a rule set grows
past its actual justification over time (Shmueli, Pliskin, & Fink).

**What this does not support:** none of these sources gives a threshold, ratio, or
test for "how much constraint is too much" in general; each documents a mechanism,
not a stopping rule. Applying a specific numeric guideline from any of them to
Recurspec would be overreach.

**Recurspec design inference:** each mechanism maps onto a specific, existing
Recurspec surface, and each suggests an auditable question rather than a new
subsystem: (1) Brooks's essential/accidental distinction argues that Contract Tree
decomposition depth and EARS invariant count per node should be evaluated against
whether they reduce essential ambiguity (good) or just add checkable-but-arbitrary
process (bad) — this is exactly what CONTEXT.md's `_Avoid_` fields are already
trying to prevent for *vocabulary* sprawl, and the same discipline plausibly needs
to apply to *invariant* sprawl within a single node, which nothing currently
enforces. (2) Jansson & Smith's finding, already discussed in Section 3 for the Best
Known State, applies equally to an Architect's own invariant-authoring: an Architect
who starts from a template or a previous node's invariants (as CONTEXT.md's own
`_Avoid_` guidance encourages, for consistency) is at risk of fixating on that
template's specific shape even where the current node's problem does not call for
it. (3) Shmueli et al.'s finding is the most directly checkable of the three against
Recurspec's actual process: because the Architect is the party who *writes* the
EARS invariants, the same investment effect their experiment measured predicts an
Architect will systematically over-value invariants they personally authored and
under-scrutinize whether each one still earns its place — which is precisely the
justification for keeping invariant *acceptance* (the Evaluation Gate) and invariant
*authorship* (the Architect) as functions that do not collapse into the same
unreviewed step, even when the Architect and the gate's configuration are edited by
the same person. This does not require a new mechanism; it is an argument for
treating "did the Architect re-justify each pre-existing invariant, or only add new
ones" as a real question during Contract Tree revision, not a rhetorical one.

## Actionability summary

The task asked that concrete, testable ideas be distinguished from vague
inspirational parallels rather than treated as equally strong. Ranked from most to
least actionable against Recurspec's actual mechanisms:

| Tier | Concept | Why |
| --- | --- | --- |
| Concrete, checkable now | §8 Design by Contract / formality tension | Recurspec already has `Evidence Stage: Unknown` and Research Frontier as the mitigation; the open question is whether they are used honestly in practice — auditable against existing tooling. |
| Concrete, checkable now | §3 Design fixation via Best Known State | Directly testable ablation (expose vs. hide prior implementation) using the same experimental shape Recurspec already uses for repair-memory (foundations.md §11). |
| Concrete, checkable now | §9 Over-specification via authorship investment | Directly testable against Recurspec's own process: does invariant *authorship* get re-justified at revision time, separately from invariant *acceptance*. |
| Concrete, scoped feature idea | §5 Missing novelty/quality axis in the Evaluation Gate | A real gap (gate tests constraint-satisfaction only), but any fix must stay non-gating per foundations.md's evidence-class table — this is a design proposal, not just an audit. |
| Concrete, scoped feature idea | §7 Named Contract Node pattern catalog | Additive tooling suggestion with a real precedent (GoF/Alexander), but unproven as a benefit versus added catalog-maintenance overhead. |
| Correct as a specific narrow point, weak as a general claim | §6 Oulipo generative constraints | The "generative, not just filtering" property genuinely echoes EARS as already credited in foundations.md; but Oulipo does not support the Architect/Implementor split itself, and should not be cited for that. |
| Directionally supportive, not causally demonstrated | §1 Game design theory / procedural rhetoric, §2 Boden/Wiggins conceptual spaces | Real, structurally apt vocabulary for what a Contract Node is doing, but sourced from design theory and a qualitative case study, not an experiment showing more rules improve outcomes. |
| Actively counsels caution against a tempting citation | §4 Choice overload / jam study | The popular version of this claim does not survive Scheibehenne et al.'s meta-analysis. Do not cite the jam study alone to justify Technology Resolution's fixed taxonomy. |
| Background mechanism, not a lever | §9 Brooks essential/accidental complexity | Correct and important framing for judging whether a given added constraint is worth its cost, but it is a lens for evaluating other proposals, not a proposal itself. |

## Primary-source bibliography

1. Salen, K., & Zimmerman, E. (2004). *Rules of Play: Game Design Fundamentals*. MIT Press. ISBN 978-0262240451.
2. Bogost, I. (2007). *Persuasive Games: The Expressive Power of Videogames*. MIT Press. ISBN 978-0262514880.
3. Lai, G., & Vecchi, I. (2025). [Formal Constraints and Creativity: Connecting Game Jams, Dogma '95, the Demo Scene, OuBaPo, and Renga poets](https://doi.org/10.1177/15554120241233865). *Games and Culture*, 20(8), 963-983.
4. Kultima, A., Alha, K., & Nummenmaa, T. (2016). [Design Constraints in Game Design: Case: Survival Mode Game Jam 2016](https://doi.org/10.1145/2897167.2897174). Proc. Int'l Conf. on Game Jams, Hackathons, and Game Creation Events, ACM, 22-29.
5. Falk, J., Biskjaer, M. M., Halskov, K., & Kultima, A. (2021). [How Organisers Understand and Promote Participants' Creativity in Game Jams](https://doi.org/10.1145/3472688.3472690). Proc. 6th Int'l Conf. on Game Jams, Hackathons and Game Creation Events, ACM, 12-21.
6. Boden, M. A. (2004). *The Creative Mind: Myths and Mechanisms* (2nd ed.). Routledge. ISBN 978-0415314534.
7. Wiggins, G. A. (2006). [A Preliminary Framework for Description, Analysis and Comparison of Creative Systems](https://doi.org/10.1016/j.knosys.2006.04.009). *Knowledge-Based Systems*, 19(7), 449-458.
8. Ritchie, G. D. (2007). [Some Empirical Criteria for Attributing Creativity to a Computer Program](https://doi.org/10.1007/s11023-007-9066-2). *Minds and Machines*, 17(1), 67-99.
9. Duncker, K. (1945). On Problem Solving (trans. L. S. Lees). *Psychological Monographs*, 58(5). Originally *Zur Psychologie des produktiven Denkens*, Springer, 1935.
10. Jansson, D. G., & Smith, S. M. (1991). [Design Fixation](https://doi.org/10.1016/0142-694X(91)90003-F). *Design Studies*, 12(1), 3-11.
11. Hallihan, G. M., Cheong, H., & Shu, L. H. (2012). Confirmation and Cognitive Bias in Design Cognition. Proc. ASME 2012 International Design Engineering Technical Conferences (IDETC-CIE), Vol. 7.
12. Iyengar, S. S., & Lepper, M. R. (2000). [When Choice Is Demotivating: Can One Desire Too Much of a Good Thing?](https://doi.org/10.1037/0022-3514.79.6.995) *Journal of Personality and Social Psychology*, 79(6), 995-1006.
13. Scheibehenne, B., Greifeneder, R., & Todd, P. M. (2010). [Can There Ever Be Too Many Options? A Meta-Analytic Review of Choice Overload](https://doi.org/10.1086/651235). *Journal of Consumer Research*, 37(3), 409-425.
14. Queneau, R. et al. Oulipo primary works (Perec's *La Disparition*, 1969; Queneau's *Cent Mille Milliards de Poèmes*, 1961) as described via [languageisavirus.com](https://www.languageisavirus.com/creative-writing-techniques/oulipo.php) and [cursus.edu](https://cursus.edu/en/22498/oulipo-the-game-of-constrained-literature) — secondary descriptions; the Oulipo works themselves were not directly fetched for this survey.
15. Gamma, E., Helm, R., Johnson, R., & Vlissides, J. (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley. ISBN 978-0201633610.
16. Alexander, C., Ishikawa, S., & Silverstein, M. (1977). *A Pattern Language: Towns, Buildings, Construction*. Oxford University Press. ISBN 978-0195019193.
17. Meyer, B. (1992). [Applying "Design by Contract"](https://doi.org/10.1109/2.161279). *Computer*, 25(10), 40-51.
18. Bowen, J. P., & Hinchey, M. G. (1995). [Ten Commandments of Formal Methods](https://doi.org/10.1109/2.375178). *Computer*, 28(4), 56-63.
19. Bowen, J. P., & Hinchey, M. G. (2006). [Ten Commandments of Formal Methods ... Ten Years Later](https://doi.org/10.1109/MC.2006.35). *Computer*, 39(1), 40-48.
20. Shipman, F. M., & Marshall, C. C. (1999). [Formality Considered Harmful: Experiences, Emerging Themes, and Directions on the Use of Formal Representations in Interactive Systems](https://doi.org/10.1023/A:1008716330212). *Computer Supported Cooperative Work (CSCW)*, 8(4), 333-352.
21. Brooks, F. P. (1987). No Silver Bullet — Essence and Accident in Software Engineering. *Computer*, 20(4), 10-19 (also University of North Carolina Technical Report 86-020, 1986).
22. Shmueli, O., Pliskin, N., & Fink, L. (2015). [Explaining Over-Requirement in Software Development Projects: An Experimental Investigation of Behavioral Effects](https://doi.org/10.1016/j.ijproman.2014.06.003). *International Journal of Project Management*, 33(2), 380-394.
