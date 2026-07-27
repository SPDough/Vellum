# Vellum: Offering, Value, and MOAT

**Status:** Product reference — consolidates offering, value proposition, and defensibility.
**Related:** [Product Positioning](product-positioning.md) · [Authority Order](vellum-authority-order.md) · [Rule Definition contract](../contracts/RULE_DEFINITION_CONTRACT.md) · [RAG architecture](../rag/RAG_MVP_ARCHITECTURE.md)

## The one sentence

Vellum is a **deterministic, AI-enhanced control layer** for buy-side middle- and back-office
operations: it normalizes fragmented OMS/IBOR/ABOR/CBOR data into a canonical domain model,
applies proprietary versioned rules to catch real breaks, orchestrates the exceptions into
governed workflows, and uses retrieval + agents to help operators resolve them faster — **without
ever letting a probabilistic model make a control decision.**

## The offering (what Vellum actually does)

Five capabilities, layered so that trust flows from the bottom up:

1. **Canonical data contracts** — integrate OMS/IBOR/ABOR/CBOR and custodian feeds and normalize
   them into a shared domain model (positions, cash, trade-status, exceptions, breaks, cases,
   approvals). Provider quirks stop here; everything above evaluates the canonical form.
2. **Deterministic rule engine** — proprietary rules expressed as **versioned JSON data
   artifacts** (not hidden code, not a black-box model) that decide *"is something wrong?"* —
   inspectable, testable, replayable. See the [rule contract](../contracts/RULE_DEFINITION_CONTRACT.md).
3. **Workflow orchestration & control objects** — turn true exceptions into cases with ownership,
   SLAs, evidence capture, sign-off, and approvals. Decides *"what do we do now?"*.
4. **Knowledge repository & knowledge assistant** — a curated, governed corpus of securities
   mechanics, accounting treatments, market conventions, and internal playbooks, retrieved with
   hybrid search + reranking and served through a cited, multi-turn agent that **explains and
   assists** but never decides. (Built across the RAG ingestion → retrieval → agent phases.)
5. **Proprietary ontology** — the domain model the whole stack shares, with **selective FIBO
   intersections** where an industry standard adds value and Vellum-native definitions where it
   does not.

## The value proposition (why a buyer pays)

The buyer is trying to double-check custodians, find errors, manage exceptions, and reduce
reimbursement and regulatory exposure. Vellum delivers:

- **Fewer, truer exceptions** — deterministic rules over canonical data mean breaks are real,
  not feed noise; operators stop drowning in false positives.
- **Faster resolution with evidence** — every break carries its evidence snapshot, a plain-language
  explanation, and cited domain knowledge, so investigation starts with context instead of a blank page.
- **Operational trust: explainable, repeatable, auditable** — the same inputs always produce the
  same official outcome, every fired rule leaves a replayable record, and AI output is clearly
  labeled as commentary. This is a *product* decision, not just an architecture one.
- **Lower reimbursement / regulatory exposure** — catching custodian and processing errors before
  they compound is the ROI story.
- **A path off brittle, IBOR-heavy legacy** — an adaptive control layer instead of batch books and
  manual reconciliation.

## The MOAT (why it's hard to copy)

Vellum's defensibility is **not the LLM** — anyone can call one. It is the deterministic domain
scaffolding around it, which compounds and is expensive to reproduce:

1. **The proprietary ontology + canonical contracts.** A curated, versioned domain model of
   custody/fund-accounting — the shared meaning everything evaluates against — with selective FIBO
   alignment. This is deep domain capital; a competitor can't shortcut it with a bigger model.
2. **The accumulating rule library.** Because rules are versioned, tested, inspectable data
   artifacts bound to the ontology, every encoded piece of custodian/accounting expertise adds to a
   compounding, portable asset — not scattered code. The library *is* the product's institutional knowledge.
3. **The curated knowledge repository.** A governed corpus with trust levels, provenance, and
   citations, tuned for domain retrieval quality — proprietary curation that improves with use, far
   beyond pointing a chatbot at public PDFs.
4. **The authority-order architecture (neuro-symbolic by design).** Deterministic control governs;
   AI assists and cites; probabilistic output can never overrule a rule. This trust posture is the
   thing regulated buyers require and the thing a generic "AI copilot" cannot bolt on after the
   fact — it has to be built in from the substrate up, which Vellum has.
5. **The integration + normalization breadth.** Mapping fragmented OMS/IBOR/ABOR/CBOR reality into
   one canonical model is unglamorous, high-switching-cost work that sits under everything else.

Individually each is a moat; together they reinforce — better contracts make better rules, better
rules generate better evidence needs, better evidence sharpens the knowledge corpus, and all of it
is governed by an authority model competitors would have to re-architect to match.

## Where AI sits (the guardrail, stated plainly)

Modern agents are powerful *and* probabilistic — capable of fluent, confident, wrong output, and
of loops, drift, and runaway cost. Vellum's stance: use AI to make humans faster and better
informed, and put deterministic gates around it. Retrieval and LLM reasoning enrich and explain;
the **canonical contracts, deterministic rules, and control objects decide.** That boundary is the
product's core trust guarantee — impressive-but-dangerous demos are exactly what Vellum is designed
*not* to ship.

## What Vellum is not

- Not another reconciliation dashboard.
- Not a generic AI copilot with no control logic.
- Not a passive data warehouse.
- Not a rip-and-replace accounting platform.
- Not a system that lets probabilistic models override deterministic operational controls.
