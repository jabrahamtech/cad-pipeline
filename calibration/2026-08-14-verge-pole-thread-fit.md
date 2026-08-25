# Printed internal fine thread — amaran Verge pole (M28-class × 1.0)

Part: `models/vergemax/thread_gauge.py` v2 ring sweep, PLA, 0.1 mm layers,
engraved face up, entry chamfers 0.8 both mouths.

Male thread: amaran Verge desk-clamp pole, caliper crest Ø27.5 (reads low
on fine crests — nominal likely M28), pitch 1.0 single start (confirmed by
photo pixel analysis after a pitch-sweep round all jammed at bore 27.9).

| Ring bore major | Result |
|---|---|
| 27.9 (round 1, pitch also unconfirmed) | jammed |
| 28.3 | not reported |
| 28.7 | **great fit** — runs the full 12 mm smoothly |
| 29.1 | not reported |

Takeaways:
- Printed internal thread against a machined fine-pitch male: winning bore
  major = caliper crest + 1.2 mm diametral (≈ nominal + 0.7 if male is
  truly M28). Larger than the coarse-thread habit (+0.4).
- Caliper crest readings on sub-1.5 mm-pitch males underestimate: trust
  photo/pixel measurement or a nut test over the caliper number.
- 0.1 mm layers + entry chamfer are mandatory at pitch 1.0; round 1
  failed partly on mouth squish.
- PETG may run slightly tighter than PLA; if the PETG part binds, bump
  another +0.4 before assuming anything else.
