# Fasteners & inserts — joining that survives disassembly

Read when: any part is screwed, bolted, or threaded to anything.
Numbers: `lib/design_rules.py` `FASTENER_MM` (M3 insert values CALIBRATED,
rest HANDBOOK).

## Decision tree

1. **Assembled more than once?** → M3 (default) **heat-set insert**:
   hole Ø4.0, boss wall ≥ 2.4 around it, depth ≥ insert length + 1 mm.
2. **Assembled once, light load?** → self-tapper into a pilot hole
   (`FASTENER_MM[size]["pilot"]`; servo-kit screws: 1.8 mm pilot, proven).
3. **High load or metal-to-print clamp?** → through-bolt with a trapped
   **nut pocket**: hex across-flats + 0.2, depth = nut + 0.4, slot-loaded
   from the side so the nut can't spin. Nyloc where vibration.
4. **Printed thread?** Only M8+ and coarse (`PRINTED_THREAD_MIN_DIA_MM`),
   via Fusion's Thread feature with a standard profile — never a hand-rolled
   helix. Below M8: insert. Gauge a printed thread before trusting it
   (see calibration/2026-08-14-verge-pole-thread-fit.md).

## Boss recipe (screw or insert)

- OD from `FASTENER_MM[size]["boss_od"]`; blend into a wall or gusset —
  a free-standing boss snaps at its root (add 2 ribs or a fillet ≥ 2 mm).
- Boss height ≥ insert length + 1 mm; counterbore the mating part so the
  screw head sits flush (head Ø + 0.6, depth = head height + 0.4).
- NEVER load a screw in pull-out along the layer direction: orient so the
  boss axis lies within layers, or let a through-bolt carry the tension.

## Tool access — the check everyone forgets

For every screw, verify a straight cylinder above it: driver shaft Ø ≥ 6 mm
(bit holder ≥ 12 mm within 30 mm of the head) from the head to open air, in
the ASSEMBLED state and in assembly ORDER. A screw you can't reach after
step 3 of assembly is a redesign, not an instruction to "angle the driver".
Check it numerically in Fusion: temporary cylinder at each screw axis,
interference-check it against every other occurrence.

## Choosing count and size

- Two screws locate a small bracket; three resist rocking; four is for
  sealing or symmetric load — more screws ≠ stronger print, the plastic
  around the FIRST screw is the limit.
- M2 for servo horns/PCBs, M3 default structure, M4/M5 only where a
  spanner-tight clamp is wanted. Standardize per project — one driver.
