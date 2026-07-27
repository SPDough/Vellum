# Product.md — Vellum differentiated value

## Purpose
This document states what Vellum sells and what we refuse to become.
It also records how our approach relates to—but is distinct from—the neurosymbolic
“ontology as guardrail for agents” recommendation popularized by Frank Coyle
(UC Berkeley / AI Engineer World’s Fair).

## One-line product
Vellum is a **backend-owned industry control layer** for custodian / buy-side
portfolio oversight: canonical contracts, ontology-aligned meaning, and
deterministic rules—made usable for every expertise level through the client
portal UX.

## The moat
Our moat is not a generic AI agent platform and not a reconciliation dashboard.

It is the combination of:
1. **Industry data understanding** — how OMS, IBOR, ABOR/CBOR, and custodian
   books relate in real operating practice
2. **Rules** — versioned, inspectable, deterministic detection of true breaks
3. **Ontology / dictionary** — shared meaning of positions, cash, trades,
   exceptions, and evidence (with optional FIBO alignment where useful)
4. **Accessibility** — that meaning and those decisions are consumable by ops,
   control, fund accounting, and leadership without requiring ontology or
   rules expertise

**Architectural consequence:** moat differentiators are managed in the
**Vellum backend**. Clients access capabilities through **otomeshon-portal**
(and similar front ends). The UI is an access layer, not where industry meaning
is redefined.

## Parallel to Coyle (where we agree)
Coyle’s core thesis: *probabilistic reasoning inside, logical guardrails outside.*

We agree that:
- LLMs and agents are unreliable as the sole authority in high-stakes operations
- Prompting cannot replace a formal shared conceptualization of the domain
- Type/schema checks (“at the door”) plus semantic/business constraints
  (“at the ledger”) are required before consequential action
- A prose SOP is a hope; a machine-enforced constraint is a control

This aligns with Vellum’s authority order:
contracts / dictionary → deterministic rules → workflows → RAG → LLM explanation.

## Distinct from Coyle (where we diverge)
Coyle’s recommended artifact is largely a **general neurosymbolic pattern**:
reuse public ontologies (schema.org, FOAF, etc.), express constraints in
RDFS/OWL, and intercept agent tool calls with Pydantic + ontology checks.

Vellum’s differentiated artifact is **industry control product IP**:

| Dimension | Coyle-style recommendation | Vellum product |
|-----------|----------------------------|----------------|
| Primary problem | Make agents safer in general domains | Detect and govern custodian / book-of-record breaks |
| Symbolic core | OWL/RDFS axioms + graph reasoner | Versioned JSON contracts + JSON-first rules (+ FIBO hints) |
| Who authors meaning | Often developers / knowledge engineers | Product encodes industry meaning; clients consume it |
| Where value lives | Guardrail pattern around an agent loop | Backend control plane; portal accessibility UX |
| LLM role | Proposes tools inside a constrained loop | Explains and assists; never overrides rule outcomes |
| Success metric | Fewer invalid agent actions | Faster, auditable exception resolution with evidence |

We may later map selected constraints into richer ontology formalisms where a
reasoner earns its keep. That is an implementation option, not the product
definition. **We do not sell “OWL for agents.” We sell industry meaning,
rules, and accessible control.**

## What clients experience
- Operators see *what broke*, *why*, and *evidence*—not JSONLogic or OWL
- Control / risk see *which rule version* fired on *which contract version*
- Leadership see aging, severity, and exposure—not platform plumbing
- Power users can progressively disclose contract and rule detail when needed

Expertise leveling is a product requirement. Hiding the moat behind an expert
tooling UI would destroy the accessibility half of the moat.

## What we will not do
- Let probabilistic models decide official break / exception state
- Rebuild Drools / generic BRE surface as the product rules path
- Treat full FIBO / Neo4j / OWL runtime as the P1 control plane
- Put ontology or rules authoring in the portal as the default client experience
- Expand the in-repo marketing frontend as the product home (portal is the client surface)

## Product implications for roadmap
- **Backend first:** deepen contracts, dictionaries, rules, ingest normalization,
  persistence of RuleResult / ReconciliationBreak, and explainability APIs
- **Portal second:** consume those APIs; improve triage and progressive disclosure
- **Filter:** if a change encodes industry meaning, it belongs in Vellum; if it
  only helps a human see or act on that meaning, it belongs in the portal

### P1 execution (moat filter)
- **P1a:** durable oversight control objects in Postgres
  (`oversight_runs` / positions / comparisons / rule_results / breaks),
  `GET /oversight/runs`, `GET /oversight/breaks/{id}/explain`
- **P1b:** JSON rule catalog expanded (quantity, missing-leg, valuation, cash
  value-date, unsettled trade); portal progressive disclosure (Operator /
  Control / Power user) via explain API
- **P1c:** CSV position ingest (`POST /oversight/ingest/csv`, sample CSV path);
  fixtures remain regression goldens
- **Out of P1:** Drools investment, OWL runtime, portal rules editors, multi-custodian live APIs

## Related docs
- `docs/product/vellum-authority-order.md` — who is allowed to decide
- `docs/product/custodian-oversight-wedge.md` — first commercial wedge
- `docs/product/product-positioning.md` — external messaging
- `contracts/README.md` — pragmatic contract registry (ontology substitute for runtime)
- `ARCHITECTURE.md` — backend vs portal ownership
