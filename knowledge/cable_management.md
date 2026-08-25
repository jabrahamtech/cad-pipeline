# Cable management — wires are a mechanical part

Read when: the part hosts, passes, or moves anything electronic. A spec for
a powered project is INCOMPLETE without a "Cables & service" section —
where wires enter, exit, live, and how they're serviced.
Numbers: `lib/design_rules.py` (CABLE_*, ZIP_TIE_SLOT_MM — HANDBOOK).

## Routing rules

- Channel/conduit Ø ≥ 1.5 × bundle Ø (bundle Ø ≈ 1.2 × √n × wire Ø for n
  same-size wires). Open U-channels with retaining fingers beat closed
  tunnels — you can't fish a connector through a tight printed tube.
- Bend radius ≥ 4 × cable Ø; no bends at an entry hole (straight for the
  first 5 mm).
- Route AROUND pinch points; through a rotating joint, route ALONG the
  rotation axis with a service loop that tolerates the full swing — check
  the swept extremes, not just the neutral pose.
- Deburr in design: every wire pass-through gets a 1 mm chamfer or radius
  both sides (printed edges are sharp enough to abrade insulation under
  vibration).

## Strain relief — every entry, no exceptions

- Zip-tie anchor beside every cable entry: slot from `ZIP_TIE_SLOT_MM`
  (4 × 2), bar ≥ 3 mm wide, positioned so the tie clamps the jacket, not
  the conductors.
- Alternatives where a tie won't fit: printed cleat (two posts, wire
  S-wrapped), TPU grommet pocket, or a clamped lid rib with a wave path.
- Servo leads: the proven repo pattern is a side notch in the wall
  (~9 × 3 mm, room for the lead + slack) placed above the cradle floor —
  see wrist_yoke. Lead exits toward the service loop, not the joint.

## Connectors — measure them, pocket them

- A connector is an interface: its dimensions go in the spec table with a
  source tag like any other (JST-XH/PH, Dupont, XT30/60 vary by vendor —
  MEASURE the one in hand).
- Pockets: connector body + locational fit (0.20) per side; latch side
  gets finger access (10 × 15 mm minimum for a fingertip).
- Never bury a connector that will ever be unplugged: it must be reachable
  in the ASSEMBLED state or sit in a hatch/removable tray.

## Service checklist (folds into the design review)

- Can each board come out without desoldering? (Connectorize or hatch.)
- Slack: ≥ 10 mm service loop at every board so it lifts for inspection.
- Airflow: cable bundles not blocking vents; high-current wires (≥ 3 A)
  get their own channel, not zip-tied to signal lines.
- Label/color notes belong in docs/<project>/README.md assembly section.
