# <project> — assembly spec

Status: DRAFT <!-- DRAFT → CONTRACTED → FIT-CHECKED → ASSEMBLED -->
Written BEFORE any piece is modelled (knowledge/assembly_decomposition.md).

## Function & envelope
What the whole assembly does; overall size; which pieces move relative to
which. Why it's split the way it is (envelope / orientation / support /
material / service / iteration — name the reason per split).

## Piece tree

| Piece (component name) | Role | Print mode | Material | Orientation | Spec |
|---|---|---|---|---|---|
| `<project>_<piece>` | | single/dual | | | specs/<project>/<piece>.md |

## Joint contracts — every piece-to-piece interface
Shared dims are SHARED user parameters (one prefix, defined identically in
both scripts), not copied numbers. Clearances from JOINT_FIT_MM.

| Joint | Pieces | Type (clearance) | Shared params | Fastening |
|---|---|---|---|---|
| e.g. lid seat | base ↔ lid | locational (0.20) | `asm_seat_w`, `asm_seat_l` | 4× M3 into inserts |

## Assembly order — walked, not assumed
Numbered. At each step confirm: insertion path clear; every fastener's
driver axis reachable IN THIS STATE; cables connected before their channel
closes.

1.
2.

## Fit-check plan
`models/<project>/_check_fit.py` must print, before any piece exports:
- interference across every mating pair (expected contact only)
- each contracted clearance measured present (and at motion extremes for
  moving joints)
- per-piece bbox vs its envelope/mode

## Gauges
The riskiest inter-piece joint, printed as a small sample FIRST:

- [ ] <joint> gauge — result → calibration/

## Proven-together versions
| Date | Piece versions | Result |
|---|---|---|
