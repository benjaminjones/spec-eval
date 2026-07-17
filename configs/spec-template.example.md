<!--
Example custom authoring template for `spec-eval generate --template configs/spec-template.example.md`
(or `authoring.template` in a config).

This REPLACES spec-eval's built-in section structure. spec-eval always APPENDS its
built-in authoring discipline (assert an invariant only when the code enforces it;
drop code trivia; label reconstructed intent), so a spec authored from this template
is still gradeable by `audit` and `sufficiency`.

Edit the sections below to your house style; the text is an instruction to the model,
not a fixed skeleton. Author the spec for ONE module.
-->

Author an intent-led specification for the module using EXACTLY these sections:

## Summary
Open with `**In one line:** <the capability in ≤20 words>`, then one short paragraph — what capability this
module gives the system, and why it exists. Lead with intent, before any signature or type.

## Behavior
The rules, modes, and flows the module implements — with **Why:** notes inline.
Not a per-function walkthrough.

## Interface & guarantees
The inputs/outputs (semantic shapes, with bounds) and the invariants the code
actually enforces (an assert / clamp / validation / raised error).
