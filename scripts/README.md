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
| `truetravel.py` | Travel envelope from TRUE vertices. Fusion's own `surfaceX/Y` are bounding boxes and inflate badly on rotated parts - one was 105mm out - so its "Depth (Y) less than the depth of the selected model" warning fires on nests that fit fine. Trust this, not the warning. |
| `offsets.py` | Read-only. Per sheet: part span vs machine travel, and the valid range of stock offsets. Run this **before** building - it is what catches a nest that cannot be cut. |
| `shift.py` | For a sheet that does not fit, names the part at the extreme, the gap next to it, and how far it must move. |
| `breakdown.py` | Per-operation cycle time, plus hole diameters for the boring ops. Finds where the time actually goes. |
| `rename_sheets.py` | Names every sheet body `Sheet N - <thickness>mm` by position, and moves any stray root-level sheet body into the PLYWOOD component. Run after re-nesting so setup names and conversation match. |
| `nestcheck.py` | Read-only. Sheets, parts per sheet, span vs travel, bounding-box overlaps and any part on no sheet. Run after re-nesting. |
| `recentre.py` | Recentres stock offsets where travel is tight and regenerates. |
| `singlepass.py` | Switches contour ops to a single full-depth pass and reports the time change. |
| `totals.py` | Cycle time per sheet and per operation, largest first. |
| `regen.py` | Regenerates any operation that has no toolpath. |
| `toolaudit.py` | Lists the tool library and every operation using each tool, with time. Run it before cutting: it is how you catch a toolpath built around a bit nobody owns. |
| `cylkind.py` | Tells an angled hole from a rounded edge by normal direction. Radius cannot do it - a 3.175mm round and a 6.35mm angled hole are identical by radius. |
| `why3d.py` | For one sheet, every face that pulled a part into the 3D pass, with type, slope and area. Answers "why is it cutting a bevel there?" - which is how the angled-hole bug was found. |
| `reach.py` | Concave radii on sloped faces against the ball radius of the tool, so you know before cutting which corners the tool cannot enter. |
| `real3d.py` | Samples surface normals to separate genuinely sloped faces from vertical extrusion walls. Most NURBS faces in an imported model are walls the profile already cuts - 202 faces looked 3D, 138 actually were. |
| `audit3d.py` | **Run this before cutting.** Every part with any 3D candidate geometry, and where each square millimetre went: machinable, facing down, angled hole, no vertical extent - plus a verdict per part. One table instead of discovering problems one rebuild at a time. |
| `facedown.py` | Sloped area facing up vs down, per part. A part whose bevels all face down is upside down on the sheet - the spindle can never reach them. `flipped.py` only ever checked planar pocket floors and missed this entirely. |
| `verify3d.py` | Posts each 3D pass and buckets every move by part. The only way to know a 3D op cuts what it claims - bucket against the operation's OWN parts, since nested part bounding boxes overlap. |
| `facemax.py` | Largest single sloped face per part. Separates a real surface from a notch facet. |
| `flipped.py` | Reports every pocket floor and which way it faces. A floor facing down means the part is placed upside down and would be machined through from the wrong side. Run after any re-nest. |
| `paramdiff.py` | Diffs every setup parameter between two setups. The tool that found the nanometre stock bug below - when one setup works and another does not, diff them rather than theorise. |
| `cleanup.py` | Deletes leftover `__trial` operations and reports setup health. Run before posting. |

## How `buildall.py` decides things

- **Sheet discovery** - a solid body wider than 2400mm and taller than 1200mm is
  a sheet; anything overlapping its footprint is a part on it. Sheets are
  numbered top-to-bottom, left-to-right. Setups take the sheet body's name, so
  run `rename_sheets.py` first and the two stay in step. Sheet bodies are
  modelled 2450 x 1230; real stock is 2440 x 1220 and that is what the CAM uses.
- **Stock offsets** are derived, not fixed. Valid offset range is
  `[R, travel - span - R]` for cutter radius `R`. It takes 20mm where there is
  room and the midpoint where there is not, and **refuses to build** a sheet with
  under 10mm of latitude rather than emit a toolpath that cannot be run.
- **Stepdown** comes from stock thickness: `(thickness + 0.508)/2 + 0.15`, which
  lands on 2 even passes with breakthrough. 12mm gives 6.4mm, 18mm gives 9.4mm.
  Fusion rounds pass count up, so a stepdown fractionally under `depth/N` costs a
  whole extra pass.
- **Pocket floors must face up.** A horizontal plane partway through a part is
  not enough - check the true face normal points +Z. A downward-facing floor
  means the part is upside down on the sheet, and machining it from the top cuts
  straight through. Use `f.evaluator.getNormalAtParameter`, not
  `f.geometry.normal`: the latter is the underlying surface's normal and points
  the wrong way whenever the face parameterisation is reversed.
- **A part's underside can be several coplanar faces.** INST PNL UPR has three.
  Taking only the lowest one drops that part's cutouts - it had 2 loops where the
  real underside has 20. Gather from every face at the minimum Z, and use
  `loop.isOuter` to tell a face's own boundary from a cutout rather than guessing
  by perimeter.
- **Feature classification** is by edge type, not bounding box. A face whose
  loops contain any `Line3D` is a pocket corner fillet, not a hole. Bounding
  boxes on rotated occurrences are the transformed AABB and are inflated - never
  classify geometry with them. Measure from vertices instead.
- **Operation order** is pockets, inner cutouts, bores, outer profile, arranged
  so the 1/8" tool is used once in the middle: `#4 #4 #4 #6 #4`, two tool
  changes. There is no API to reorder operations, so the script clears and
  rebuilds a setup rather than patching it.
- **Holes go to whichever bit matches.** Helical-boring is slow - 34s per hole
  on 18mm stock. A hole that matches a drill you own gets plunged instead:
  ~2s. `DRILLABLE` maps diameter to tool number; first match wins. Boring is
  ~3x faster with the 1/4" than the 1/8", so `BIG` is set at 8mm, not 9.
- **Stock is built 0.01mm proud of the model.** Parts laid flat by joints come
  out a few *nanometres* thicker than nominal - 12.00000307mm against 12mm of
  stock. If any part pokes above the stock top, however slightly, Fusion refuses
  to drill: no warning, no error, just no toolpath. Every other strategy works
  fine, which makes it look like a drill problem. This cost ~3 hours of needless
  helical boring before `paramdiff.py` turned it up.
- **A drill that fails to generate falls back to boring.** Fusion silently
  refuses to drill on some setups - no warning, just no toolpath. The drill op
  is generated immediately so the holes can be added to the bore op, which is
  created later and cannot be reordered afterwards.
- **Contours cut in a single full-depth pass.** On a compression bit this is the
  designed use: both the up-cut and down-cut sections engage, giving a clean face
  top and bottom. Multi-pass is what tears out, because only the first pass
  touches the top surface. Halves profile time and keeps the finishing pass.
- **Confirm the operator owns a tool before building around it.** Tool numbers in
  a library are a claim, not an inventory. Two of the entries here were invented
  to make a toolpath work and only questioned later. `toolaudit.py` prints tool
  -> operations -> minutes so the question gets asked early.
- **3D stepdown comes from a cusp height, not a number.** `CUSP_MM` is the
  scallop between passes; stepdown is derived from it and the tool's ball radius.
  Copying a stepdown that suited a different tool wastes the bigger tool: the
  0.04in that suits a 1.587mm ball is 1.442mm on a 3.175mm ball for identical
  finish, and that alone took sheet 4's 3D pass from 37.4 to 24.9 min.
- **A pointed drill needs deeper breakthrough than a flat endmill.** Full diameter
  does not clear the underside until the point is one tip-length past it: 0.95mm
  for a 118-degree 1/8in, 1.67mm for a 7/32in. The -0.02in that suits an endmill
  leaves a cone of uncut material. Derived from `tool_tipAngle`.
- **Fusion's own extents are bounding boxes too.** `surfaceXHigh` and friends
  inflate on rotated occurrences - after flipping four parts, one box was 105mm
  larger than the part in Y, and every operation on that sheet raised "Depth (Y)
  less than the depth of the selected model". The real geometry had 12.8mm of
  travel to spare. Check with `truetravel.py` before believing it.
- **Never take `abs()` of a face normal's Z.** A 59-degree bevel facing DOWN
  scores identically to one facing up, so an upside-down part gets a toolpath for
  geometry the spindle cannot reach, with no warning. Keep the sign and require
  it positive. Checking pocket floors alone is not enough - `flipped.py` passed
  every one of these parts.
- **A face with no vertical extent is not a bevel.** One face sat entirely at
  Z 18.00 on an 18mm part and still sampled at 20-60 degrees.
- **A part earns a 3D pass on one substantial face (500mm2) or a genuine cluster
  (8+ faces, 800mm2).** A total-area floor alone lets a 192mm2 notch facet drag a
  89x707mm part into a finishing pass.
- **A silhouette is silently ignored as a 3D machining boundary.**
  `machiningBoundarySel` accepts a SilhouetteSelection, reports no warning, and
  then scans the entire model anyway: 724,507 feed moves and 64m of cutting where
  the answer is 3,287 and 7.5m. Use chain selections from the top face's outer
  loop. This is invisible in the time estimate - it just looks like 3D is
  expensive.
- **Containment must be 'outside' when the bevels are the outer edge.** With
  'inside' the region shrinks by a tool radius and edge rounds get no toolpath at
  all, silently: two parts on sheet 1 had zero moves. Verify by posting and
  bucketing the moves by part, not by trusting `hasToolpath`.
- **Tell an angled hole from a rounded edge by NORMAL DIRECTION, not radius.**
  If the face normal points toward the cylinder axis, material is outside it and
  it is a hole. Pointing away means material is inside: a convex round, which is
  exactly what a ball nose is for. Radius cannot distinguish them - a 3.175mm
  round and a 6.35mm angled hole look the same. Getting this wrong wrote off
  8,040mm2 of machinable edge on one part as "needs hand finishing".
- **An angled hole is not a bevel.** Any cylinder whose axis is not vertical
  looks like 3D geometry, so a 6.35mm hole drilled at an angle counted the same
  as a 488mm-radius curved surface. On ECS VENT PLATE 1 that was 20 of 38 faces
  and 7,900 of 10,764 mm2, and it pulled a 1838x703mm panel into a 3D pass for
  one 42mm2 face. Non-vertical cylinders under `HOLE_R_MM` are holes - 3-axis
  cannot make them anyway - and a part needs `MIN_3D_AREA` of real slope to earn
  a pass.
- **A 3D contour's cost is Z moves, not feed rate.** Raising the cutting feed
  from 90 to 150 ipm saved 3.7 min; raising the PLUNGE feed from 45 to 90 took
  the same pass from 30.6 to 16.9. The 45 ipm was inherited from a recipe written
  for a different operation.
- **3D bevels are confined by slope angle.** A 3D contour with no
  `slopeConfinement` re-machines every flat top and vertical wall the 2D
  operations already cut: 16 min against 1.1 for the same two parts. Confine it
  to 5-85 degrees from horizontal and it touches only what the 2D passes cannot.
- **Only include a body whose slope range overlaps what the op will cut.** A face
  at 86-89 degrees is a near-vertical wall; inside a 5-85 confinement it yields
  nothing, and one empty body takes the whole batch operation down with it. That
  is what stopped sheet 4's 3D pass generating at all.
- **Outer profiles** use a silhouette selection with `OnlyOutsideLoops`. The
  bottom face is the wrong outline on any bevelled part - on some of these it is
  only ~30% of the footprint. `AllLoops` instead warns about lead-in collisions.
