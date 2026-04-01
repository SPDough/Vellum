# Playbook: Investigate Position Break

## Purpose
This playbook defines a first-pass operator workflow for investigating a position break.

## Trigger
A position break case is opened when a deterministic comparison indicates that OMS, IBOR, and/or ABOR/CBOR position state differ beyond allowed tolerance.

## Inputs
Typical inputs include:
- OMS position or allocation expectation
- IBOR position snapshot
- ABOR and/or CBOR position snapshot
- security identifiers
- account identifiers
- effective date / as-of date
- quantity difference
- market value difference
- prior known exceptions

## Core questions
The operator should answer, in order:
1. where in the OMS → IBOR → ABOR/CBOR chain does the divergence first appear?
2. is this a real break or a timing artifact?
3. is the identity match correct?
4. is the quantity difference real and material?
5. does the break trace back to trade activity, corporate action activity, pricing, or reference data?
6. what action is required next, and who owns it?

## Step-by-step workflow

### Step 1: confirm the match keys
Check whether the comparison matched the right:
- account
- security identifier
- currency
- as-of date
- book / sleeve / strategy context if applicable

If the match keys are wrong, this may be a false break caused by identity mapping.

### Step 2: assess timing
Determine whether one side is simply ahead of the other due to:
- cutoffs
- market timing
- settlement timing
- file delivery lag
- batch processing windows

Many early breaks are timing-related and should be classified accordingly.

### Step 3: quantify the break
Measure:
- absolute quantity difference
- relative difference
- affected market value
- number of impacted accounts or sleeves

This helps determine urgency and escalation path.

### Step 4: look for likely operational causes
Common drivers include:
- unsettled trades
- failed trades
- corporate actions not reflected consistently
- manual adjustment on one side only
- stale or inconsistent reference data
- incorrect lot handling or booking logic

### Step 5: gather evidence
Attach or reference:
- source records
- timestamps
- provider data lineage
- rule result
- related workflow case notes

### Step 6: decide next action
Possible actions:
- monitor until next cycle
- request clarification from provider
- correct internal mapping or reference data
- escalate to operations lead
- classify as known issue / recurring pattern

## Expected output
A good position-break investigation should leave behind:
- a clear classification
- an owner
- a timestamped trail
- supporting evidence
- a defined next step

## Role of Vellum
Vellum should reduce operator effort by:
- normalizing the compared records
- applying deterministic tolerances
- pre-classifying likely break types
- retrieving relevant guidance
- helping draft investigation notes

But the system should still preserve human accountability for final operational resolution.
