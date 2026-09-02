# Fusion CAM scripts

Scripts that drive Fusion's CAM API through the [Fusion MCP add-in][mcp]
(`http://127.0.0.1:27182/mcp`). They exist because laying out 6 sheets of
identical operations by hand is where the mistakes come from - every sheet gets
the same speeds, feeds, stepdowns and heights, derived rather than typed.

[mcp]: https://github.com/user/fusion-mcp

## Running

```bash
python3 run.py buildall.py      # executes buildall.py inside Fusion
```

`run.py` is a two-line harness over `mcp.py`; Fusion must be open with the
design active. Output comes back as the script's stdout.

Long generations can exceed the HTTP timeout. **The call failing does not mean
the build failed** - Fusion carries on. Re-run `status.py` to see the real
state before rebuilding anything.

## What each does

| script | purpose |
|---|---|
| `buildall.py` | The main event. Discovers sheets, works out stock offsets, creates one setup per sheet and builds its operations. Builds **one sheet per invocation**, so run it repeatedly until it says `nothing left to build`. |
| `status.py` | Read-only. Every setup, its offsets, operations, tool numbers, and whether the cutter stays inside machine travel. |
| `offsets.py` | Read-only. Per sheet: part span vs machine travel, and the valid range of stock offsets. Run this **before** building - it is what catches a nest that cannot be cut. |
| `shift.py` | For a sheet that does not fit, names the part at the extreme, the gap next to it, and how far it must move. |
| `breakdown.py` | Per-operation cycle time, plus hole diameters for the boring ops. Finds where the time actually goes. |
| `cleanup.py` | Deletes leftover `__trial` operations and reports setup health. Run before posting. |

## How `buildall.py` decides things

- **Sheet discovery** - a solid body wider than 2400mm and taller than 1200mm is
  a sheet; anything overlapping its footprint is a part on it. Sheets are
  numbered top-to-bottom, left-to-right, and the sheet body may be a root-level
  body rather than an occurrence.
- **Stock offsets** are derived, not fixed. Valid offset range is
  `[R, travel - span - R]` for cutter radius `R`. It takes 20mm where there is
  room and the midpoint where there is not, and **refuses to build** a sheet with
  under 10mm of latitude rather than emit a toolpath that cannot be run.
- **Stepdown** comes from stock thickness: `(thickness + 0.508)/2 + 0.15`, which
  lands on 2 even passes with breakthrough. 12mm gives 6.4mm, 18mm gives 9.4mm.
  Fusion rounds pass count up, so a stepdown fractionally under `depth/N` costs a
  whole extra pass.
- **Feature classification** is by edge type, not bounding box. A face whose
  loops contain any `Line3D` is a pocket corner fillet, not a hole. Bounding
  boxes on rotated occurrences are the transformed AABB and are inflated - never
  classify geometry with them. Measure from vertices instead.
- **Operation order** is pockets, inner cutouts, bores, outer profile, arranged
  so the 1/8" tool is used once in the middle: `#4 #4 #4 #6 #4`, two tool
  changes. There is no API to reorder operations, so the script clears and
  rebuilds a setup rather than patching it.
- **Outer profiles** use a silhouette selection with `OnlyOutsideLoops`. The
  bottom face is the wrong outline on any bevelled part - on some of these it is
  only ~30% of the footprint. `AllLoops` instead warns about lead-in collisions.
