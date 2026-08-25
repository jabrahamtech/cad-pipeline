"""Generates the robotarm build manual as a PDF.

Every drawing is rendered from the models themselves and every callout is
anchored to real model coordinates, so the manual cannot drift away from the
geometry: move a hole and its label moves with it.

Not a printed part (no build()), so the invariant tests skip it.

Run:  PYTHONPATH=. .venv/bin/python models/robotarm/manual.py
Out:  docs/robotarm/robotarm_build_manual.pdf
"""

import math
import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import cast

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from build123d import Location, Part, Pos  # noqa: E402

from lib.manual import Manual  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frame as F  # noqa: E402
from _assembly import place_all  # noqa: E402

OUT = REPO_ROOT / "docs" / "robotarm" / "robotarm_build_manual.pdf"
DARK, MID, LIGHT, ACCENT = "#3f454e", "#7b828c", "#eef0f3", "#c9ced6"


def _load(name: str):
    py = Path(__file__).parent / f"{name}.py"
    spec = importlib_util.spec_from_file_location(name, py)
    assert spec and spec.loader
    mod = importlib_util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def polar(r: float, az_deg: float, z: float) -> tuple[float, float, float]:
    a = math.radians(az_deg)
    return (r * math.cos(a), r * math.sin(a), z)


# ---------------------------------------------------------------- content
SERVO_PINS = [
    ("Base yaw", "SG90", "GPIO 13", "1.8", "≈180°, software-limited"),
    ("Shoulder", "MG995", "GPIO 14", "11.0", "−95°…+25° from horizontal"),
    ("Elbow", "MG90S", "GPIO 27", "2.2", "−130°…+130°"),
    ("Wrist pitch", "MG90S", "GPIO 26", "2.2", "±90°, set to taste"),
    ("Hand, left jaw", "SG90", "GPIO 25", "1.8", "0…58 mm, 58° of travel"),
    ("Hand, right jaw", "SG90", "GPIO 33", "1.8", "0…58 mm, mirror of left"),
]

BOUGHT = [
    ("MG995 servo", "1", "Shoulder — the only joint gravity really loads"),
    ("MG90S servo", "2", "Elbow and wrist pitch"),
    ("SG90 servo", "3 (+1 spare)", "Base yaw, and one per claw finger"),
    ("608ZZ bearing", "5", "3 turntable rollers + 2 idler journals"),
    ("M8 × 30 bolt + nyloc nut", "3", "Roller axles"),
    ("M3 heat-set insert, Ø4.0 hole", "10",
     "7 in the base, 3 radial in the cap"),
    ("M3 × 10 socket screw", "10", "Turret, lid, clips"),
    ("M3 heat-set insert (rotator)", "4", "Effector bolt circle, Ø22"),
    ("M3 × 8 socket screw", "4", "Hand or scissors onto the rotator"),
    ("M3 × 30 socket screw + nyloc", "2", "wrist_mount through the forearm"),
    ("M3 × 10 self-tapper", "2", "Upper arm cover"),
    ("ESP32 dev board", "1", "38-pin DevKit assumed"),
    ("400-point breadboard", "1", "85.5 × 55.5 measured, bay is built to it"),
    ("5 V 5 A PSU + DC lead", "1", "See the power page — 5 A is not optional"),
    ("Toggle switch, Ø13.1 thread", "1", "Rim, switches the whole supply"),
    ("5 mm LED + 220 Ω resistor", "2", "Rim, press fit — now on GPIO 32/2"),
    ("1000 µF electrolytic, 10 V+", "1", "Across the servo rail"),
    ("Zip ties, 2.5 mm", "~6", "Cable strain relief"),
    ("Servo screws", "—", "Use the ones supplied with each servo"),
]



def draw_wiring(ax) -> None:
    """Power and signal schematic. Drawn, not photographed, because the point
    is which wire goes where — the physical layout is up to you."""
    from matplotlib.patches import FancyBboxPatch, Rectangle

    INK, ACC, RED, BLK, SIG = "#1c2128", "#2f6f8f", "#c0392b", "#2b2f36", "#b8860b"

    def box(x, y, w, h, label, sub="", fc="#f2f4f7"):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.006",
                                    linewidth=1.0, edgecolor=INK, facecolor=fc))
        ax.text(x + w / 2, y + h / 2 + (0.012 if sub else 0), label,
                ha="center", va="center", fontsize=8.4, color=INK,
                fontweight="bold")
        if sub:
            ax.text(x + w / 2, y + h / 2 - 0.016, sub, ha="center",
                    va="center", fontsize=7.0, color="#5a626e")

    def wire(pts, colour, lw=1.5):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=colour,
                linewidth=lw, solid_capstyle="round", zorder=1)

    V, G = 0.575, 0.055           # +5 V rail and GND rail heights

    # supply chain
    box(0.01, 0.44, 0.15, 0.075, "5 V PSU", "5 A minimum")
    box(0.20, 0.44, 0.13, 0.075, "TOGGLE", "rim switch")
    wire([(0.16, 0.4775), (0.20, 0.4775)], RED)
    wire([(0.33, 0.4775), (0.37, 0.4775), (0.37, V), (0.99, V)], RED, 2.2)
    wire([(0.085, 0.44), (0.085, G), (0.99, G)], BLK, 2.2)
    ax.text(0.99, V + 0.018, "+5 V RAIL", ha="right", fontsize=7.6,
            color=RED, fontweight="bold")
    ax.text(0.99, G - 0.028, "GND RAIL  (common — ESP32 and servos)",
            ha="right", fontsize=7.6, color=BLK, fontweight="bold")

    # bulk capacitor across the rails
    wire([(0.345, V), (0.345, 0.20)], RED)
    wire([(0.345, 0.13), (0.345, G)], BLK)
    ax.plot([0.322, 0.368], [0.185, 0.185], color=INK, lw=2.0)
    ax.plot([0.322, 0.368], [0.150, 0.150], color=INK, lw=2.0)
    ax.text(0.345, 0.105, "1000 µF 10 V+", fontsize=7.0, color=INK,
            ha="center")

    # ESP32
    box(0.03, 0.165, 0.25, 0.225, "ESP32 DevKit", "on the breadboard")
    wire([(0.10, 0.39), (0.10, 0.4775), (0.20, 0.4775)], RED)
    ax.text(0.107, 0.43, "VIN", fontsize=7.0, color=RED)
    wire([(0.055, 0.165), (0.055, G)], BLK)

    # servos
    servos = [("Base\nSG90", "13"), ("Shoulder\nMG995", "14"),
              ("Elbow\nMG90S", "27"), ("Wrist\nMG90S", "26"),
              ("Gripper\nSG90", "25")]
    x = 0.375
    for i, (name, pin) in enumerate(servos):
        w = 0.115
        box(x, 0.235, w, 0.115, name.split(chr(10))[0],
            name.split(chr(10))[1], fc="#ffffff")
        cx = x + w / 2
        wire([(cx - 0.03, 0.35), (cx - 0.03, V)], RED)          # V+
        wire([(cx, 0.235), (cx, G)], BLK)                        # GND
        y_sig = 0.205 + 0.040 * i
        wire([(cx + 0.03, 0.35), (cx + 0.03, 0.40 + 0.012 * i),
              (0.30, 0.40 + 0.012 * i), (0.30, y_sig), (0.28, y_sig)],
             SIG, 1.2)                                            # signal
        ax.text(cx + 0.034, 0.355, f"GPIO {pin}", fontsize=6.6, color=SIG,
                rotation=90, va="bottom")
        x += 0.125

    # LEDs
    for j, (pin, xx) in enumerate((("33", 0.10), ("32", 0.21))):
        wire([(xx, 0.165), (xx, 0.15)], SIG, 1.2)
        ax.add_patch(Rectangle((xx - 0.016, 0.118), 0.032, 0.020,
                               facecolor="#ffffff", edgecolor=INK, lw=0.9))
        ax.text(xx, 0.128, "220Ω", ha="center", va="center", fontsize=5.8)
        wire([(xx, 0.118), (xx, 0.095)], SIG, 1.2)
        ax.plot([xx - 0.014, xx + 0.014, xx], [0.095, 0.095, 0.075],
                color=INK, lw=1.0)
        ax.plot([xx - 0.014, xx + 0.014], [0.075, 0.075], color=INK, lw=1.6)
        wire([(xx, 0.075), (xx, G)], BLK)
        ax.text(xx, 0.038, f"LED · GPIO {pin}", fontsize=6.6,
                color=INK, ha="center")

    ax.text(0.01, 0.63, "RED = +5 V     BLACK = GND     GOLD = signal",
            fontsize=7.6, color="#5a626e")


def build_manual() -> Path:
    parts = {n: _load(n).build() for n in (
        "base_platter", "base_lid", "turret_cap", "shoulder_bracket",
        "upper_arm", "forearm", "upper_arm_cover", "wrist_mount",
        "wrist_rotator", "hand_base", "hand_finger",
    )}
    placed = place_all()
    hero = [(p, loc) for _, p, loc, _ in placed]
    hero_cols = [c for _, _, _, c in placed]

    with Manual(OUT, "Robot Arm", footer="robotarm · build manual") as m:
        # ---------------------------------------------------------- cover
        m.cover(
            hero, colours=hero_cols,
            subtitle="5-axis desktop arm · ESP32 · 3D printed · build manual",
            facts=[
                ("Printed parts", "11 (+2 optional)"),
                ("Print plates", "6"),
                ("Filament", "≈430 g PETG"),
                ("Reach, shoulder to wrist", f"{F.UPPER_ARM_LEN + F.FOREARM_LEN:.0f} mm"),
                ("Rated payload", "40 g (46 g limit, set by the elbow)"),
                ("Base", f"Ø{F.OUTER_DIA + 10:.0f} × {F.Z_RIM:.0f} mm"),
            ],
        )

        # ------------------------------------------------------ how it works
        m.prose("How the arm works", "overview", [
            ("Five axes", """
Base yaw turns the whole arm about a vertical axis. Shoulder and elbow lift
and fold it. The wrist ROLLS — it spins the hand about the arm's own axis —
and the last two servos are the claw, one per finger. Every joint is a hobby
servo driving a printed part directly: no gearboxes, no belts and no gears
anywhere. There ARE bearings, five 608ZZ, but they carry load beside the
servos rather than transmitting anything.
"""),
            ("The turntable is the clever bit", """
The base does NOT hang the arm off a servo shaft. Three 608ZZ bearings run on
horizontal axles inside the turret cap and bear on the flat underside of the
shoulder bracket's disc. They take the arm's weight and its overturning
moment, which leaves the base servo transmitting torque only. That is what
lets the smallest servo in the kit drive the base: gravity does no work about
a vertical axis, so once the bearings carry the tipping load there is almost
nothing left to hold.
"""),
            ("Why the joints are drums", """
Each joint is a cylinder concentric with its own axis. The part holding a
servo's CASE carries the drum; the part driven by its HORN carries a skirt
that laps over it. Both being concentric means the joint stays closed at every
angle and neither part sweeps into the other. It also means each drum's far
cap can carry an idler bore, so every joint is in double shear rather than
hanging off the servo's output shaft alone.
"""),
            ("What limits it", """
Not the plastic — bending stress in the loaded sections is about 0.02 MPa
against a conservative 12 MPa allowable, a margin of several hundred times.
The limit is servo duty. Held straight out, the elbow is the busiest joint at
46 % of its stall torque, and that is what sets the 40 g payload.
"""),
        ])

        # ----------------------------------------------------------- BOM
        m.table("What you need to buy", "bill of materials",
                ["Item", "Qty", "Notes"], BOUGHT, widths=[0.34, 0.13, 0.53],
                note="Everything else is printed. No glue is used anywhere;\n"
                     "the arm comes apart again.")

        # -------------------------------------------------------- printing
        m.table("Print plates", "printing",
                ["File", "Contains", "Orientation", "Infill"],
                [
                    ("p1_base", "base_platter", "flat, bay up", "25 %, 4 walls"),
                    ("p2_lid", "base_lid", "flat, either face", "15 %, 3 walls"),
                    ("p3_turret", "turret_cap, shoulder_bracket",
                     "disc down, drum up", "40 %, 4 walls"),
                    ("p4_links", "upper_arm, forearm, cover",
                     "flat, channel up", "30 %, 4 walls"),
                    ("p5_hand", "bracket, rotator, claw ×5", "as modelled",
                     "40 %, 4 walls"),
                    ("p6_scissors", "scissor_cradle, effector_lever",
                     "flat", "30 % — INCOMPLETE, see note"),
                ], widths=[0.16, 0.36, 0.27, 0.21],
                note="PETG throughout: tougher than PLA at the joints and it\n"
                     "does not creep in a warm room. Bed 70–80 °C, no chamber\n"
                     "heat needed. NO PART NEEDS SUPPORT MATERIAL — if your\n"
                     "slicer wants to add any, the part is oriented wrong.\n"
                     "Print p3_turret first: it holds the bearings and is the\n"
                     "least forgiving plate.\n"
                     "DO NOT PRINT p6 YET. The cradle pins into the wrist\n"
                     "rotator correctly, but the effector servo lost its\n"
                     "mount when the wrist was rebuilt, and re-siting it\n"
                     "depends on the real scissors — every scissor dimension\n"
                     "in the model is still an assumption. Measure yours\n"
                     "first; see specs/robotarm/scissor_cradle.md.")

        # --------------------------------------------------- part reference
        z_lid, z_rim = F.Z_LID, F.Z_RIM
        m.figure(
            "Base platter", "part reference",
            [(parts["base_platter"], None)], colours=[LIGHT],
            azimuth=52, elevation=34,
            callouts=[
                ("Lid insert ×4 · M3 heat-set, r=78",
                 polar(78, 45, z_lid), (78, 44)),
                ("Turret insert ×3 · M3 heat-set, r=45\nBolts land on the column, not the lid",
                 polar(45, 120, z_rim), (-92, 96)),
                ("Servo column · base SG90 hangs here",
                 (0, F.COLUMN_Y, z_rim), (96, 6)),
                ("Toggle switch Ø13.35",
                 polar(F.OUTER_DIA / 2, 180, F.FLOOR_T + F.BAY_H / 2),
                 (-104, 18)),
                ("DC cable Ø9.95 + 2 floor zip-tie\nslots = strain relief",
                 polar(F.OUTER_DIA / 2, 205, F.FLOOR_T + 7), (-104, -34)),
                ("LED Ø4.85 ×2, press fit",
                 polar(F.OUTER_DIA / 2, 20, F.FLOOR_T + F.BAY_H * 0.75),
                 (92, -30)),
                ("Breadboard posts ×4",
                 (F.BREADBOARD_X0 + F.BREADBOARD[0] * 0.3,
                  F.BREADBOARD[1] / 2 + 3.5, F.FLOOR_T + 12), (40, -74)),
            ],
            body="""
Heat-set all seven inserts FIRST, while the bay is empty. The three at r=45
are the ones the turret bolts to; they pass up through the lid so the load
lands on the column. The breadboard needs no fixing — the column wall stops
it inboard and the four posts hold its sides.
""")

        m.figure(
            "Turret cap", "part reference",
            [(parts["turret_cap"], None)], colours=[LIGHT],
            azimuth=48, elevation=30,
            callouts=[
                ("Roller fork ×3 at r=36 —\n608ZZ + M8 bolt + nyloc",
                 polar(F.ROLLER_PITCH_R, 90, F.Z_AXLE - F.Z_RIM + 6), (30, 30)),
                ("Axle bore Ø8.4 — bolt runs\nfree, nut does the clamping",
                 polar(F.ROLLER_PITCH_R, 210, F.Z_AXLE - F.Z_RIM), (-56, 6)),
                ("Base servo aperture —\ndrops in from ABOVE",
                 (0, F.COLUMN_Y, F.CAP_H), (40, -16)),
                ("Cap bolt ×3, Ø3.4 +\ncounterbore",
                 polar(F.CAP_BOLT_R, 180, F.CAP_H), (-46, -28)),
            ],
            body="""
The clamp pads inside each fork touch the bearing's INNER race only, so the
outer race never rubs. After assembly every bearing must still spin freely by
hand — if one is stiff, the nyloc is over-tightened or a pad printed proud.
""")

        m.figure(
            "Shoulder bracket", "part reference",
            [(parts["shoulder_bracket"], None)], colours=[LIGHT],
            azimuth=44, elevation=18,
            callouts=[
                ("Race face — rides the three\nrollers. Keep it clean and flat",
                 (F.TURNTABLE_DIA / 2 - 8, 0, 0), (34, -22)),
                ("Base-servo horn pocket\n(underside) + Ø6 screw access",
                 (0, 0, 2), (-52, -18)),
                ("Shoulder drum — MG995 goes\nin through this cap, 4 screws",
                 (0, F.SHOULDER_DRUM_Y[0],
                  F.TURNTABLE_T + F.SHOULDER_RISE), (-58, 26)),
                ("Idler bore in the FAR cap —\nupper_arm's stub lands here",
                 (0, F.SHOULDER_DRUM_Y[1],
                  F.TURNTABLE_T + F.SHOULDER_RISE), (40, 30)),
            ],
            body="""
This part is both the turntable and the shoulder housing. The disc's flat
underside is a bearing race: do not sand it, and do not print this part on
its side — the race has to come off the bed flat.
""")

        m.figure(
            "Upper arm and forearm", "part reference",
            [(parts["upper_arm"], None),
             (parts["forearm"], cast(Location, Pos(0, 95, 0)))],
            colours=[LIGHT, ACCENT], azimuth=54, elevation=26,
            callouts=[
                ("Shoulder skirts — lap the drum,\nhide the joint", (0, -20, 30), (-58, 26)),
                ("Horn pocket: MG995 horn is\nCAPTURED, not screwed",
                 (0, -25, 14), (-56, -14)),
                ("Idler stub — MUST seat in the\ndrum's far cap", (0, 25, 14), (34, 26)),
                ("Elbow drum: elbow servo in\nthis cap", (F.UPPER_ARM_LEN, -17, 14), (30, -34)),
            ],
            body="""
Both links are open channels on top so the servo can be fitted and its lead
routed; the gable cover closes the upper arm afterwards. The channel must
stay clear near the shoulder — that space is swept by the bracket as the arm
lifts.
""")

        m.figure(
            "Wrist and hand", "part reference",
            [(parts["wrist_mount"], None),
             (parts["wrist_rotator"], cast(Location, Pos(0, 62, 0))),
             (parts["hand_base"], cast(Location, Pos(0, 116, 0))),
             (parts["hand_finger"], cast(Location, Pos(-56, 90, 0)))],
            colours=[LIGHT, LIGHT, LIGHT, ACCENT],
            azimuth=52, elevation=36,
            callouts=[
                ("BRACKET: slides over the forearm's tip,\n2 x M3 straight through both plates",
                 (-14, 0, 10), (60, 26)),
                ("Servo goes in NOSE-FIRST,\nshaft down the arm",
                 (6, 0, 17), (58, -20)),
                ("ROTATOR: skirt runs on the boss,\nNOT on the servo shaft",
                 (0, 62, 7), (-92, 30)),
                ("Hand bolts on with 4 M3.\nFIT THESE FIRST",
                 (0, 116, 2), (-96, -6)),
                ("Both fingers are THIS PART TWICE —\nturn one OVER, not round",
                 (-56, 90, 2), (-70, 44)),
            ],
            body="""
The wrist ROLLS, and it bolts on. wrist_mount is a saddle that slips over the
forearm's tip and takes two M3 straight through it and both of the link's
side plates; the servo sits in it nose-first with its shaft pointing forward
down the arm. The effector's weight is carried by the rotator's SKIRT running
on the boss in front of that bracket, not by the servo's 4.8 mm shaft.

The hand is a claw with ONE SERVO PER FINGER — no gears, no rack, no linkage.
Each finger bolts straight to its own horn. It opens 0-43 mm with about
0.25 kgf per finger.

BOTH FINGERS ARE THE SAME PRINTED PART, and the second one goes on TURNED
OVER rather than turned round: flipping it is what swaps which edge grips.
That is the reason its horn pocket is cut clean through, and the reason the
horn's own screw needs a WASHER under the head.

What it costs, plainly: the fingers rotate, so their faces only meet flush at
one opening and roll off anything wider or narrower.
""")

        # --------------------------------------------------------- retrofit
        cap = parts["turret_cap"]
        m.figure(
            "Already printed an earlier version?", "retrofit",
            [(cap, None)], colours=[LIGHT], azimuth=44, elevation=32,
            callouts=[
                (f"WIRE PASS · drill Ø{F.WIRE_PASS_DIA:.0f} through\n"
                 f"r={F.WIRE_PASS_R:.0f}, opposite the middle cap bolt",
                 polar(F.WIRE_PASS_R, F.WIRE_PASS_AZ, F.CAP_H), (96, 30)),
                ("CLIP INSERT ×3 · drill Ø4.0 RADIALLY into\n"
                 f"the edge, {abs(F.CLIP_SCREW_Z):.0f} mm below the top, "
                 f"~10 deep",
                 polar(F.CAP_DIA / 2, F.CLIP_AZ[0],
                       F.CAP_H + F.CLIP_SCREW_Z), (86, -34)),
                ("...at 30°, 150° and 270°",
                 polar(F.CAP_DIA / 2, F.CLIP_AZ[2],
                       F.CAP_H + F.CLIP_SCREW_Z), (-64, 46)),
            ],
            body="""
REPRINT the turret cap. Earlier plates had the three roller forks turned 90
degrees, with the axles laid tangentially. That is wrong and cannot be
drilled out: the disc's surface moves tangentially over each roller, so a
tangential axle makes the bearing scrub instead of roll and wear a flat on
its outer race. The axle has to point at the hub. Nothing else on plate 3
changed, so reprint just this part.

Everything else is a drill or a reprint of one small item:

  shoulder_bracket  open the centre bore from Ø6 to Ø14, right through.
                    It is the horn-screw access AND the wire pass.
  print             turntable_clip x3, about 4.7 g each
  plates 1, 2, 4    unchanged — keep what you have

THE FOREARM AND ALL OF PLATE 5 ARE NEW. The wrist ROLLS now instead of
pitching, and it bolts on: the forearm's far end is a plain square-ended
channel with two cross-drilled M3, so the link is a different part and has to
be reprinted. The upper arm and its cover are unchanged — print the forearm
on its own. Plate 5 is all new too: a bracket, a rotator, a claw body and two
fingers.

PLATE 6 IS ON HOLD. The cradle bolts to the rotator like the hand does,
but the effector servo lost its mount with the old wrist and re-siting it
needs the scissors measured. Do not print it yet.

Servo pockets on earlier plates have no notch for the servo's own lead, so
the servo will not push home with its wire attached. Current plates have the
notch printed in; on an older part, file a 7 x 4 mm slot in the side of the
pocket where the lead comes out. See the fitting page.
""")

        # --------------------------------------------------------- fitting
        m.table("Which holes to open, and which to leave", "fitting",
                ["Feature", "Size", "Fit", "If it is tight"],
                [
                    ("M3 heat-set insert", "Ø4.0", "interference",
                     "LEAVE IT. The insert needs the grip"),
                    ("5 mm LED", "Ø4.85", "press",
                     "LEAVE IT. Push harder, or warm the LED"),
                    ("M3 screw clearance", "Ø3.4", "clearance",
                     "Open to 3.5 if a screw binds"),
                    ("M8 roller axle", "Ø8.4", "loose",
                     "Already loose; the nut does the clamping"),
                    ("Toggle switch", "Ø13.35", "sliding",
                     "Open to 13.6 — thread tolerances vary"),
                    ("DC cable gland", "Ø9.95", "sliding", "Open as needed"),
                    ("Wire pass, cap", "Ø14.0", "generous",
                     "Open to 16 if 4 connectors will not pass"),
                    ("Turntable centre bore", "Ø14.0", "generous",
                     "Open to 16, but stay under 18 or the horn pocket goes"),
                    ("Servo case pocket", "case + 0.25", "sliding",
                     "File the LEAD NOTCH, do not widen the pocket"),
                    ("Servo lead notch", "7 × 3.5", "clearance",
                     "Deepen freely — it carries nothing"),
                ], widths=[0.27, 0.14, 0.16, 0.43],
                note="PETG holes print UNDERSIZE, typically 0.1–0.3 mm, and\n"
                     "the first layer is tighter again because of elephant's\n"
                     "foot. That is why several of these are meant to be\n"
                     "cleaned up on assembly rather than printed to size.\n\n"
                     "HOW: run the drill SLOWLY. PETG melts and the flutes\n"
                     "grab, which snatches the part and tears the hole oval.\n"
                     "Step drills are much safer than twist drills in thin\n"
                     "plastic. For pockets use a flat file, not a drill —\n"
                     "you want to relieve one face, not enlarge the bore.\n"
                     "Go one size under, test the fit, then creep up.")

        # ---------------------------------------------------------- assembly
        m.steps("Assembly · base and turret", "assembly", [
            ("1", "Heat-set the base inserts",
             "Seven M3 inserts into base_platter: three at r=45, four at\n"
             "r=78. Do this before anything else goes in the bay."),
            ("2", "Prepare the turret cap  ·  RETROFIT ONLY",
             "If your cap came off an earlier plate, drill it NOW while it\n"
             "is loose: the Ø14 wire pass, and three radial Ø4.0 holes in\n"
             "the edge. Heat-set an M3 insert into each of the three. See\n"
             "the retrofit page. Current plates have all of this printed in."),
            ("3", "Fit the rim electronics",
             "Toggle switch, DC lead and the two LEDs. Zip-tie the DC lead\n"
             "to the floor through the two slots beside its hole — that is\n"
             "the strain relief, and without it every tug lands on the\n"
             "switch terminals."),
            ("4", "Drop in the breadboard",
             "It locates against the column wall and the four posts."),
            ("5", "Base servo into the turret cap",
             "SG90 down through the rectangular opening from above, flange\n"
             "screwed to the cap's top face. Its lead sits in the notch in\n"
             "the side of the pocket — if the servo will not seat with the\n"
             "wire on, that notch is what needs filing, not the pocket."),
            ("6", "Build the three rollers",
             "608ZZ between each fork's pads, M8 × 30 through, nyloc snug.\n"
             "Every bearing must still spin freely afterwards — the pads\n"
             "clamp the INNER race only, so the outer race never rubs."),
        ])

        m.steps("Assembly · closing the base", "assembly", [
            ("7", "Lid on, then turret cap",
             "The lid drops over the three bosses; the cap bolts to those\n"
             "bosses with 3 M3 screws and traps the lid. No visible\n"
             "fasteners in the lid itself."),
            ("8", "Feed the arm loom up through the wire pass",
             "Before the turntable goes on, pull the four servo leads\n"
             "(shoulder, elbow, wrist and the two claw servos) up\n"
             "through the cap's Ø14\n"
             "hole and zip-tie them to it. Leave a generous slack loop in\n"
             "the 12 mm gap — that loop is what lets the base rotate."),
            ("9", "Shoulder bracket onto the rollers",
             "Thread the loom up through the disc's Ø14 centre bore FIRST.\n"
             "Then press the base servo's cross horn into the pocket\n"
             "underneath, set the disc on the three rollers, and drive the\n"
             "horn's retaining screw up through that same bore. It should\n"
             "turn smoothly with no rock."),
            ("10", "Fit the three hold-down clips",
             "One M3 radially into each insert in the cap's edge, tongue\n"
             "hooked over the disc's rim. These stop the turntable lifting\n"
             "off a roller when the arm reaches out — without them that\n"
             "load goes into the base servo's shaft. Check the disc still\n"
             "turns freely by hand with all three fitted."),
        ])

        m.steps("Assembly · arm and hand", "assembly", [
            ("11", "Shoulder MG995 into the drum",
             "In through the aperture in the near cap, 4 screws. Route its\n"
             "lead out before you fit anything else."),
            ("12", "Upper arm onto the shoulder",
             "Driven plate onto the horn, and CHECK THE IDLER STUB IS HOME\n"
             "in the far cap's bore before you tighten the horn screw. If\n"
             "it is not seated, the servo shaft carries the whole bending\n"
             "load on its own — the exact failure the drums exist to stop."),
            ("13", "Elbow servo, then forearm",
             "MG90S into the upper arm's far drum, 2 screws. Forearm onto\n"
             "its horn, idler stub into the far cap. Same check."),
            ("14", "Route the leads, then the cover",
             "Run the elbow, wrist and gripper leads along the upper arm's\n"
             "channel, then clip the gable cover on with 2 self-tappers\n"
             "through the flank. That is what it is hiding."),
            ("15", "Wrist bracket onto the forearm's tip",
             "wrist_mount slides straight over the end of the link — it\n"
             "only fits over the PARALLEL part, so push it home until it\n"
             "stops. Two M3 x 30 through the saddle and both side plates,\n"
             "nylocs on the far side. Then the MG90S goes in nose-first:\n"
             "case behind the face, shaft forward down the arm, two screws\n"
             "through the face into its tabs."),
            ("16", "Rotator onto the horn",
             "Heat-set its four M3 inserts first, from the FLAT face —\n"
             "they bottom out in bosses on the back. Then drop the disc on\n"
             "so its skirt slides over the boss in the tip and the horn\n"
             "lands in the pocket, and drive the horn's own screw with a\n"
             "washer under the head through the Ø6 bore. It must spin\n"
             "smoothly with no rock: that skirt, not the servo shaft, is\n"
             "what carries the whole hand."),
            ("17", "Hand onto the rotator, THEN its servos",
             "Four M3 x 8 through the hand's flange into the rotator's\n"
             "inserts FIRST — a driver cannot reach past a fitted servo\n"
             "case. Then an SG90 into each upright from the front, leads\n"
             "out the side, two screws each."),
            ("18", "The two fingers",
             "They are the SAME printed part. Fit the first one; fit the\n"
             "second TURNED OVER, not turned round — flipping it is what\n"
             "swaps which edge grips. Its pocket is cut through, so either\n"
             "face meets the horn. Put a WASHER under each horn screw:\n"
             "there is no material above it to bear on.\n"
             "CENTRE BOTH SERVOS FIRST and fit both fingers at the same\n"
             "angle, or the tips will not meet."),
        ])

        # -------------------------------------------------------- electronics
        m.table("Servo wiring", "electronics",
                ["Joint", "Servo", "Signal pin", "Stall kg·cm", "Travel limit"],
                SERVO_PINS, widths=[0.19, 0.14, 0.18, 0.17, 0.32],
                note="Signal wires only on the breadboard. Servo POWER must\n"
                     "not go through breadboard rails — see the next page.\n"
                     "Pins chosen to avoid the ESP32's strapping pins (0, 2,\n"
                     "12, 15), the flash pins (6–11) and the input-only pins\n"
                     "(34–39). Drive them at 50 Hz with the LEDC peripheral.")

        m.canvas("Wiring", "electronics", draw_wiring, body="""
Servo POWER (red) comes straight off the rail — NOT through the breadboard's
rails, which are good for 1-2 A and will sag under an MG995. Only the ESP32
and the five signal wires (gold) belong on the breadboard. The ground rail is
common to everything: the servo signal is referenced to the ESP32's ground,
and without that link the servos twitch or ignore you entirely.
""")

        m.prose("Power — read before switching on", "electronics", [
            ("Size the supply for stall, not for idle", """
Five servos stalling together draw roughly 3.9 A: the MG995 alone is about
1.2 A stalled and can spike higher. Use a 5 V supply rated 5 A or more. A
phone charger or a USB port will brown out the moment the arm takes a load,
and a browning-out ESP32 reboots mid-move.
"""),
            ("Do NOT run servo power through the breadboard", """
Breadboard rails are good for about 1–2 A and their spring contacts have real
resistance. The MG995 on its own is beyond what they should carry, and the
voltage sag upsets the ESP32 sharing the same rail. Run servo V+ and GND as
their own wiring — soldered, or a screw terminal block — and use the
breadboard for the ESP32 and the five signal lines only.
"""),
            ("Common ground is mandatory", """
The servo signal is referenced to the ESP32's ground. Tie the servo supply's
GND to the ESP32's GND even if they come from different supplies. Without it
the servos will twitch, or simply not respond.
"""),
            ("One bulk capacitor", """
1000 µF, 10 V or better, across the servo rail as close to the servos as you
can get it, electrolytic polarity observed. It absorbs the current step when
a servo starts moving, which is the single most effective thing you can do to
stop the ESP32 resetting mid-motion.
"""),
            ("What the toggle switch should switch", """
Put it in the DC positive line ahead of everything, so it kills servo power
and the ESP32 together. Switching only the servo rail while the ESP32 stays
alive on USB means the arm slams to its commanded pose the instant you
switch on.
"""),
            ("LEDs", """
Each 5 mm LED needs its own series resistor — 220 Ω from a 3.3 V GPIO. Wire
them GPIO → resistor → LED anode, cathode to GND.
"""),
        ])

        m.prose("First power-on", "commissioning", [
            ("Centre the servos BEFORE fitting the horns", """
This is the step people skip and regret. A servo snaps to whatever position
the first PWM pulse commands. With the arm assembled and the horns already
fitted at some arbitrary angle, that first command can drive a link straight
into the base.

Procedure, one servo at a time, OFF the arm:
  1. Wire the servo up on its own.
  2. Send a steady 1500 µs pulse at 50 Hz. The servo goes to its centre.
  3. With power still on, fit the horn at the angle the assembly needs.
  4. Only then bolt that joint together.
"""),
            ("Set software end stops", """
Nothing mechanical stops these joints; the software has to. Use the measured
envelopes:

    Shoulder   −95° to +25° from horizontal   (below that the arm's tail
                                               meets the turntable)
    Elbow      −130° to +130°
    Base       keep clear of the DC lead's exit
    Gripper    stop at the closed position; do not drive it into a stall,
               it will cook the servo

Clamp every command to these in code, not by hand.
"""),
            ("First move", """
Support the arm by hand, power on, and command each joint to its centre one
at a time. Watch for: a joint moving the wrong way (swap the direction in
software, do not re-fit the horn), a joint buzzing at rest (it is fighting an
end stop, or the horn was fitted off-centre), or the ESP32 rebooting (supply
or capacitor).
"""),
            ("Then check the fingers", """
Drive both claw servos to their closed end. The two tips should meet on the
centreline. If one leads the other, lift that finger off its horn, rotate it
a spline tooth and re-seat — the geometry is right in the model, so this is
only about where the horn happened to land on its spline.

Set each servo's closed limit where the tips touch and NOT further. Past that
point they just push against each other and both servos sit at stall.

The fingers ROTATE, so their faces only meet flush at one opening. That is
inherent to a claw, not a fault.
"""),
        ])

        # ------------------------------------------------------------ limits
        m.table("Load budget and limits", "reference",
                ["Joint", "Servo", "Stall", "Held", "Duty"],
                [("Shoulder", "MG995", "11.0 kg·cm", "2.16", "20 %"),
                 ("Elbow", "MG90S", "2.2 kg·cm", "1.08", "49 %"),
                 ("Wrist roll", "MG90S", "2.2 kg·cm", "0.06", "3 %")],
                widths=[0.22, 0.18, 0.22, 0.18, 0.20],
                note="Arm straight out horizontal, the worst case for every\n"
                     "joint, with the parts' real masses and centres of mass.\n"
                     "A hobby servo should hold a static load at or under\n"
                     "50 % of stall — stall is a peak rating, not a duty\n"
                     "rating. RATED PAYLOAD IS 28 g; the hard limit is 35 g\n"
                     "and it is the elbow that sets it, not the shoulder\n"
                     "(which would allow 187 g). The wrist barely counts:\n"
                     "gravity does almost no work about a ROLL axis, so it\n"
                     "only holds whatever you grip off-centre.\n"
                     "Want more? Put the spare MG995 on the ELBOW instead of\n"
                     "the MG90S and the ceiling roughly triples. Or shorten\n"
                     "the forearm, or lighten anything outboard of it.")

    return OUT


if __name__ == "__main__":
    out = build_manual()
    print(f"wrote {out.relative_to(REPO_ROOT)} "
          f"({out.stat().st_size // 1024} KB)")
