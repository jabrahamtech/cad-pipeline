# legacy — frozen build123d pipeline (pre-2026-08-25)

The original CAD-as-code pipeline, authored in
[build123d](https://build123d.readthedocs.io/) before the repo went
Fusion-only. **Frozen: reference only.** Never extend it, never import from
it in new code — `tests/test_fusion_scripts.py` enforces this.

What lives here:

```
lib/     build123d generators (limb, servo, plate_export, preview, manual,
         cots, ref_layout, stand_socket) + a snapshot of design_rules.py
models/  every build123d part script, one folder per project
specs/   specs superseded by later Fusion parts (hand_body, hand_jaw)
tests/   the invariant suite + part-specific tests for the models above
```

Why it's kept: these parts were printed and many are ACCEPTED — their
scripts are the record of what was actually manufactured, and their
measured results in `../calibration/` still feed `../lib/design_rules.py`.
The exports they generated remain valid in `../exports/`.

`lib/design_rules.py` here is a snapshot; the live, calibrated copy is
`../lib/design_rules.py`.

To rebuild an old part (needs the old deps):

```bash
python -m venv .venv-legacy && source .venv-legacy/bin/activate
pip install -r requirements.txt
pytest tests/ -q          # run from inside legacy/
```
