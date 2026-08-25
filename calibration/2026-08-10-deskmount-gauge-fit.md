# 2026-08-10 — deskmount shim_gauge v2 fit check

Gauge print (4 mm slice of clamp_shim v2 profile) against the real desk
and clamp. Two deviations found — both user-measurement errors caught
before the full print; no design-rule (clearance) change indicated.

| Dimension | Spec'd | Gauge result | Corrected to |
|---|---|---|---|
| Desk thickness | 20 mm ("measured") | slot did not fit around desk | 23 mm |
| Throat (desk edge → screw center) | 40 mm (crude) | pad landed ~10 mm past the 74 mm plate tip | 79 mm |

Also invalidated: the model's assumption that the clamp foot is centred
over the screw — on this clamp the foot sits toward the front, so pad
coverage (not foot half-span) is the binding plate reach. build()'s
reach check updated accordingly.

Action: clamp_shim v3 + shim_gauge v3 exported (slot 23.5 mm, plate
depth 82 mm, stack 33 mm). Gauge v3 to be re-printed to confirm both
corrections before printing the full shim.

Follow-up (same day): user wants a snugger slot than the 23.5 mm nominal
— gauge v4 sweep plate exported with labeled gaps 22.0 / 22.5 / 23.0 mm.
The gap that slides on snug becomes the shim's slot (as a slot_gap
override or corrected desk thickness). Result: 22.5 mm gap fits snug -> desk is ~22.2 mm actual (both user
estimates, 20 and 23, were off). Baked into clamp_shim v4 as desk 22.0 +
standard 0.25/side sliding clearance = 22.5 slot. No design-rule change:
the sliding-clearance rule produced the expected fit once the desk
dimension was right. Bottom plate also 6 -> 12 mm (user safety margin).
