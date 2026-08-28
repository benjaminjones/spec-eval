# `compare` — replicate and vendor comparison

**In one line:** given two `--reps` runs, report how much of the sufficiency variance is the instrument talking to itself and whether a vendor difference survives its own standard error — arithmetic over retained output, no API key and no model call.

## 1. Purpose

A single sufficiency score is **one draw**. This module answers the two questions that draw cannot:
**how noisy is the instrument**, and **is there a vendor effect large enough to act on**.

## 2. Scope

`sufficiency --reps N` repeats scoring N times per pair and writes every rep. `compare` reads two such
files and fits a paired contrast. **It makes no model calls** — it is arithmetic over retained output.

## 3. Call order

**`compare` is independent and runs after scoring — never inside it, and never on `audit` output.**

```
spec-eval sufficiency <repo> --reps 3 --model <A> --out runA
spec-eval sufficiency <repo> --reps 3 --model <B> --out runB
spec-eval compare runA/sufficiency-reps.json runB/sufficiency-reps.json
```

It accepts **either** shape: `sufficiency-reps.json` (written when `--reps > 1`) or a plain
`sufficiency.json`, which is read as a **single rep**. `--reps 1` is the default, so the plain file is the
likeliest thing a first caller points here and must not be a stack trace. **With one rep the paired delta
is still computable and `noise_share` is not** — it is reported as `null` with a reason, because zero noise
is a claim one observation cannot support.

## 4. The design

| | |
|---|---|
| **Pair** | a block. Each contributes one difference of per-vendor means |
| **Vendor** | the fixed effect under test |
| **Rep** | replication within (pair, vendor) |
| **n** | the number of **pairs**, never the number of calls |

**11 pairs × 3 reps × 2 vendors is 66 calls and `n = 11`.** A pair that is hard for both vendors cancels
in the difference instead of inflating the effect.

## 5. What is reported

| Field | Meaning |
|---|---|
| `mde_80pct_power` | Smallest detectable effect. **Reported first, whatever the result** |
| `delta`, `se_delta` | The vendor effect **against its standard error**, never bare |
| `ci95`, `ci90_used_for_tost` | TOST uses the 90% interval — a 5% one-sided pair |
| `tost_equivalent` | True only when the **whole** 90% interval lies inside the margin |
| `noise.<vendor>.noise_share` | Within-vendor variance ÷ total |
| `per_pair_delta` | Exploratory, ordered by magnitude |
| `dropped_pairs` | Pairs scored by only one vendor, listed rather than silently dropped |

## 6. Invariants

- **INV-1** `n` is the count of **shared** pairs. A pair either vendor failed to score is excluded and listed.
- **INV-2** A `sufficiency: null` record is **dropped, never coerced to 0.0**. Missing data is not a bad spec.
- **INV-3** `mde_80pct_power` is emitted on every run, including when the result is null.
- **INV-4** `tost_equivalent` is true **only** if `-margin < ci90.low` and `ci90.high < margin`.
- **INV-5** A `--reps 1` input yields `noise_share: null` with an `unavailable_because` reason, never `0`.
- **INV-6** `noise_share` **rises with noise** — it is the complement of a classic ICC, and carries a
  `definition` field saying so on every emission.

## 7. What it does not do

- **It does not test `delta ≠ 0`.** *"p > 0.05"* is not evidence of no difference; that is what TOST is for.
- **It does not correct `per_pair_delta`.** The caller applies `benjamini_hochberg` before reading any
  single pair as a finding. With `n` pairs examined, the largest `|delta|` is expected to be large by chance.
- **It does not decide which vendor is better.** Sufficiency is an indicator; a higher score is not a
  demonstrated better spec.

## 8. Acceptance

| | Given | Then |
|---|---|---|
| **AC-1** | two reps files sharing 0 or 1 pairs | an `error` field, no `delta` |
| **AC-2** | a pair with `sufficiency: null` in every rep | that pair appears in `dropped_pairs` |
| **AC-3** | identical scores from both vendors | `delta` = 0 and `tost_equivalent` is true |
| **AC-4** | any successful comparison | `mde_80pct_power` is present |
| **AC-5** | a 90% interval straddling the margin | `tost_equivalent` is false |
| **AC-6** | a plain `sufficiency.json` (a bare list) | it loads as one rep; no exception |
| **AC-7** | a file that is neither shape | a `ValueError` naming both accepted shapes, not an `AttributeError` |
| **AC-8** | one rep per pair | `noise_share` is `null` with `unavailable_because` set |
