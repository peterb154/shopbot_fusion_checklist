import adsk.core, adsk.fusion, adsk.cam, collections, time, math

TX, TY, R = 2438.4, 1219.2, 3.175
SHEET_W, SHEET_H = 2440.0, 1220.0     # standard baltic birch
MIN_LATITUDE = 10.0                   # refuse to build a sheet tighter than this
BIG = 8.0          # >= this bores with the 1/4in - 3x faster than the 1/8in
VENT_DIA, VENT_TOL = 6.35, 0.05    # cosmetic vent holes - diameter not critical
SMALL_DIA = 3.175                  # the 1/8in tools
# Holes that match a drill you own get plunged instead of helical-bored.
# (diameter mm, tool number, tolerance) - first match wins, so order matters.
DRILLABLE = ((6.350, 7, 0.05),     # cosmetic vent holes - deliberately drilled undersize
             (5.556, 8, 0.15),     # M4 furniture inserts, 7/32in
             (3.175, 7, 0.40))     # at-size 1/8in
DRILL_FEED = {7: "40 in/min", 8: "20 in/min"}
DRILL_PECK = {7: "6mm", 8: "5mm"}
BORE_MIN  = SMALL_DIA * 1.15       # below this there is no room to helix - must drill
DRILL_TOL = 0.40                   # hole within this of 3.175mm -> plunge it
TOOL_BIG, TOOL_SMALL, TOOL_VENT, TOOL_3D = 4, 6, 7, 3
SLOPE_MIN, SLOPE_MAX = 5.0, 85.0   # degrees from horizontal that count as 3D
FORCE = []                      # sheet indices to rebuild even if already done

def classify(f):
    k = collections.Counter()
    for L in f.loops:
        for e in L.edges:
            k[e.geometry.objectType.split("::")[-1]] += 1
    if k.get("Line3D", 0) > 0: return "fillet"
    if k.get("Circle3D", 0) >= 1 and k.get("Arc3D", 0) == 0: return "hole"
    return "other"

def shopbot_machine():
    """Load the machine from the library. Do not copy it off setup 0 - that
    breaks the moment setup 0 does not exist, e.g. after clearing all setups."""
    ml = adsk.cam.CAMManager.get().libraryManager.machineLibrary
    for loc in (adsk.cam.LibraryLocations.LocalLibraryLocation,
                adsk.cam.LibraryLocations.Fusion360LibraryLocation):
        try:
            for u in ml.childAssetURLs(ml.urlByLocation(loc)):
                if "ShopBot PRSalpha" in u.leafName:
                    return ml.machineAtURL(u)
        except Exception:
            pass
    return None

def tool_by_number(n):
    lm = adsk.cam.CAMManager.get().libraryManager.toolLibraries
    local = lm.urlByLocation(adsk.cam.LibraryLocations.LocalLibraryLocation)
    for u in lm.childAssetURLs(local):
        if "MCC ShopBot" not in u.leafName: continue
        for t in lm.toolLibraryAtURL(u):
            if {x.name: x for x in t.parameters}['tool_number'].value.value == n: return t
    return None

def setp(holder, pairs):
    idx = {x.name: x for x in holder.parameters}
    for k, v in pairs:
        p = idx.get(k)
        if not p: continue
        try: p.expression = v
        except Exception as e: print(f"      ! {k}: {str(e)[:55]}")

def face_slopes(f, n=3):
    """Angles from horizontal over the face. 0 = flat, 90 = vertical wall.
    A NURBS face is usually just a vertical extrusion wall, which the outer
    profile already cuts - sampling is the only way to tell those from real 3D."""
    t = f.geometry.objectType.split("::")[-1]
    if t == "Plane":
        a = math.degrees(math.acos(min(1.0, abs(f.geometry.normal.z))))
        return [a, a]
    if t == "Cylinder" and abs(abs(f.geometry.axis.z) - 1.0) < 1e-6:
        return [90.0, 90.0]
    ev = f.evaluator
    rng = ev.parametricRange()
    if rng is None: return []
    out = []
    for i in range(n):
        for j in range(n):
            u = rng.minPoint.x + (rng.maxPoint.x - rng.minPoint.x)*(i+0.5)/n
            v = rng.minPoint.y + (rng.maxPoint.y - rng.minPoint.y)*(j+0.5)/n
            ok, nv = ev.getNormalAtParameter(adsk.core.Point2D.create(u, v))
            if ok: out.append(math.degrees(math.acos(min(1.0, abs(nv.z)))))
    return out

def is_sloped(b):
    """True only if some face overlaps the range the operation will actually cut.
    A face at 86-89deg is a near-vertical wall: inside the op's slope confinement
    it yields nothing, and an empty body in the batch can take the whole
    operation down with it."""
    for f in b.faces:
        sl = face_slopes(f)
        if sl and max(sl) >= SLOPE_MIN and min(sl) <= SLOPE_MAX: return True
    return False

def true_normal(f):
    """Outward normal of the FACE. f.geometry.normal is the underlying surface's
    normal and points the wrong way when the face parameterisation is reversed."""
    ev = f.evaluator
    ok, prm = ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return None
    ok2, n = ev.getNormalAtParameter(prm)
    return n if ok2 else None

def face_z(f):
    """Mean Z of the face's vertices. NEVER use f.boundingBox for this - on a
    rotated occurrence it is the transformed AABB and can land outside the body."""
    zs = [v.geometry.z*10 for v in f.vertices]
    return sum(zs)/len(zs) if zs else None

def extents(b):
    xs=[v.geometry.x*10 for v in b.vertices]; ys=[v.geometry.y*10 for v in b.vertices]
    zs=[v.geometry.z*10 for v in b.vertices]
    return min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)

def discover(des):
    root = des.rootComponent
    sheets, parts = [], []
    for occ in root.allOccurrences:
        for b in occ.bRepBodies:
            if not b.isSolid: continue
            x0,x1,y0,y1,z0,z1 = extents(b)
            rec = dict(occ=occ, n=occ.name.split(':')[0], x0=x0,x1=x1,y0=y0,y1=y1,
                       th=round(z1-z0,1))
            (sheets if (x1-x0>2400 and y1-y0>1200) else parts).append(rec)
    for b in root.bRepBodies:
        if not b.isSolid: continue
        x0,x1,y0,y1,z0,z1 = extents(b)
        rec = dict(occ=None, n=f"<root>/{b.name}", x0=x0,x1=x1,y0=y0,y1=y1, th=round(z1-z0,1))
        (sheets if (x1-x0>2400 and y1-y0>1200) else parts).append(rec)
    sheets.sort(key=lambda s: (-s['y0'], s['x0']))
    out = []
    for i, s in enumerate(sheets, 1):
        on = [p for p in parts if p['x0']<s['x1'] and p['x1']>s['x0']
              and p['y0']<s['y1'] and p['y1']>s['y0']]
        if not on: continue
        lo, hi = min(p['x0'] for p in on), max(p['x1'] for p in on)
        ylo, yhi = min(p['y0'] for p in on), max(p['y1'] for p in on)
        th = collections.Counter(p['th'] for p in on).most_common(1)[0][0]
        out.append(dict(idx=i, sheet=s, parts=on, spanx=hi-lo, spany=yhi-ylo, th=th,
                        name=f"Sheet {i} - {th:.0f}mm"))
    return out

def offsets(spanx, spany):
    hx, hy = TX - spanx - R, TY - spany - R
    if hx < R or hy < R: return None, None, min(hx-R, hy-R)
    # 20mm of edge trim only if that still leaves 20mm of placement tolerance on
    # the far side; otherwise centre the offset so the tolerance is shared.
    ox = 20.0 if hx >= 40.0 else max(R, hx*0.5)
    oy = 20.0 if hy >= 40.0 else max(R, hy*0.5)
    return round(ox,2), round(oy,2), min(hx-R, hy-R)

def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(doc.products.itemByProductType("CAMProductType"))
    plan = discover(des)
    have = {cam.setups.item(i).name: cam.setups.item(i) for i in range(cam.setups.count)}

    m = shopbot_machine()
    for i in range(cam.setups.count):
        st = cam.setups.item(i)
        try: has = st.machine is not None and st.machine.model
        except Exception: has = False
        if not has and m is not None:
            st.machine = m
            print(f"backfilled machine on {st.name}")

    target = None
    print("plan:")
    for s in plan:
        ox, oy, lat = offsets(s['spanx'], s['spany'])
        exist = next((v for k,v in have.items() if k.startswith(f"Sheet {s['idx']} ")), None)
        n_ops = exist.operations.count if exist else 0
        cooked = n_ops and all(exist.operations.item(j).hasToolpath for j in range(n_ops))
        if lat < MIN_LATITUDE:      state = f"BLOCKED latitude {lat:.2f}mm"
        elif cooked:                state = f"done ({n_ops} ops)"
        else:                       state = "TO BUILD"
        if s['idx'] in FORCE and lat >= MIN_LATITUDE:
            state = "FORCED REBUILD"
        if state in ("TO BUILD", "FORCED REBUILD") and target is None:
            target = (s, ox, oy, exist)
        print(f"  {s['idx']}  {s['name'][:44]:<44} {len(s['parts']):>3}p  "
              f"span {s['spanx']:7.1f} x {s['spany']:6.1f}  lat {lat:6.2f}  {state}")
    if not target:
        print("\nnothing left to build"); return
    s, ox, oy, setup = target
    print(f"\n=== building {s['name']}   offsets X {ox} Y {oy}")

    if setup is None:
        si = cam.setups.createInput(adsk.cam.OperationTypes.MillingOperation)
        si.models = [p['occ'] for p in s['parts'] if p['occ']]
        setup = cam.setups.add(si)
        setup.name = s['name']
        m = shopbot_machine()
        if m is None: raise RuntimeError("ShopBot machine not found in library")
        setup.machine = m
        print(f"    created setup, {len(si.models)} models, machine "
              f"{setup.machine.vendor} {setup.machine.model}")
    while setup.operations.count: setup.operations.item(0).deleteMe()

    setp(setup, [("job_stockMode","'fixedbox'"),
                 ("job_stockFixedX", f"{SHEET_W}mm"), ("job_stockFixedXMode","'left'"),
                 ("job_stockFixedXOffset", f"{ox}mm"),
                 ("job_stockFixedY", f"{SHEET_H}mm"), ("job_stockFixedYMode","'front'"),
                 ("job_stockFixedYOffset", f"{oy}mm"),
                 # 0.01mm proud of the model. Parts laid flat by joints end up a
                 # few NANOMETRES thicker than nominal, and if any part pokes above
                 # the stock top Fusion silently refuses to drill - no warning, no
                 # toolpath. Cost ~3h of helical boring before it was found.
                 ("job_stockFixedZ", f"{round(s['th'] + 0.01, 3)}mm"),
                 ("job_stockFixedZMode","'bottom'"),
                 ("job_stockFixedZOffset","0mm"),
                 ("wcs_origin_mode","'stockPoint'"), ("wcs_origin_boxPoint","'top 1'"),
                 ("job_programName", f"'{1000+s['idx']}'")])

    # Single full-depth pass. On a compression bit this is the designed use -
    # up-cut and down-cut sections both engage, clean face top and bottom. Multi-
    # pass is what tears out, because only the first pass touches the top surface.
    stepdown = round(s['th'] + 1.0, 2)
    print(f"    stock {s['th']:.0f}mm -> stepdown {stepdown}mm, single pass")

    names = {m.name for m in setup.models}
    bodies, cutouts, big_c, small_c, tiny_c, floors, sloped = [], [], [], [], [], [], []
    drill_c = collections.defaultdict(list)
    for occ in des.rootComponent.allOccurrences:
        if occ.name not in names: continue
        for b in occ.bRepBodies:
            if not b.isSolid: continue
            bodies.append(b)
            if is_sloped(b): sloped.append((b, occ.name.split(':')[0].strip()))
            _,_,_,_, zb, zt = extents(b)
            pl = [f for f in b.faces if f.geometry.objectType == adsk.core.Plane.classType()
                  and abs(abs(f.geometry.normal.z)-1.0) < 1e-6]
            planar = [(f, face_z(f), true_normal(f)) for f in pl]
            planar = [t for t in planar if t[1] is not None and t[2] is not None]
            for f, fz, n in planar:
                # a pocket must open upward, or it is on the underside and the
                # part is placed upside down
                if n.z > 0 and zb + 0.1 < fz < zt - 0.1: floors.append(f)
            if planar:
                # The underside can be several coplanar faces - INST PNL UPR has
                # three. Taking only one of them silently drops that part's
                # cutouts, so gather from all of them. Fusion's isOuter marks each
                # face's own boundary; guessing by perimeter gets it wrong when a
                # face is a fragment rather than the whole underside.
                zmin = min(t[1] for t in planar)
                bots = [f for f, fz, n in planar if abs(fz - zmin) < 0.05 and n.z < 0]
                for bot in bots:
                    for L in bot.loops:
                        if L.isOuter: continue
                        edges = list(L.edges)
                        ks = {e.geometry.objectType.split('::')[-1] for e in edges}
                        if len(edges) <= 2 and ks <= {"Circle3D","Arc3D"}: continue
                        cutouts.append(edges)
            for f in b.faces:
                g = f.geometry
                if g.objectType != adsk.core.Cylinder.classType(): continue
                if abs(abs(g.axis.z)-1.0) > 1e-6: continue
                if classify(f) != "hole": continue
                d = g.radius*20
                nm = occ.name.split(':')[0]
                hit = next((t for dia, t, tol in DRILLABLE if abs(d - dia) <= tol), None)
                if hit:                 drill_c[hit].append((f, nm))
                elif d >= BIG:          big_c.append(f)           # 1/4in bore
                elif d >= BORE_MIN:     small_c.append((f, nm))   # 1/8in bore
                else:                   tiny_c.append((f, nm, round(d, 2)))
    import collections as _c
    print(f"    bodies {len(bodies)} | cutouts {len(cutouts)} | big {len(big_c)} | "
          f"drill {sum(len(v) for v in drill_c.values())} | small {len(small_c)} | "
          f"floors {len(floors)}")
    groups = [(f"-> #{t} drill", g) for t, g in sorted(drill_c.items())] + \
             [("-> #6 bore", small_c)]
    for lbl, grp in groups:
        if grp:
            byp = _c.Counter(nm for _, nm in grp)
            byd = _c.Counter(round(f.geometry.radius*20, 2) for f, _ in grp)
            print(f"      {lbl}: {dict(byd)}  on {dict(byp)}")
    if tiny_c:
        byd = _c.Counter((d, nm) for _, nm, d in tiny_c)
        print(f"      *** {len(tiny_c)} holes too small for any tool you have "
              f"(under {SMALL_DIA - DRILL_TOL:.2f}mm) - NOT MACHINED:")
        for (d, nm), n in byd.most_common():
            print(f"          {d:5.2f}mm x{n:3}  on {nm}")


    t_big, t_small = tool_by_number(TOOL_BIG), tool_by_number(TOOL_SMALL)
    common = [("tool_spindleSpeed","14000"), ("tool_coolant","'disabled'"),
              ("bottomHeight_mode","'from stock bottom'"), ("bottomHeight_offset","-0.02in")]
    mill = common + [("tool_feedCutting","180 in/min"), ("tool_feedPlunge","60 in/min"),
                     ("tolerance","0.1mm"), ("doMultipleDepths","true"),
                     ("maximumStepdown", f"{stepdown}mm"), ("doRoughingPasses","true"),
                     ("maximumStepover","0.1in"), ("useStockToLeave","true"),
                     ("stockToLeave","0.02in"), ("compensation","'left'")]

    small_f = [f for f, _ in small_c]

    def contour(nm, build):
        i = setup.operations.createInput("contour2d"); i.tool = t_big; i.displayName = nm
        o = setup.operations.add(i); setp(o, mill)
        cv = o.parameters.itemByName("contours").value
        sel = cv.getCurveSelections(); sel.clear(); build(sel); cv.applyCurveSelections(sel)
        return o

    if floors:
        def make_pocket(faces, name):
            i = setup.operations.createInput("pocket2d"); i.tool = t_big
            i.displayName = name
            o = setup.operations.add(i)
            setp(o, common[:2] + [("tool_feedCutting","180 in/min"),("tool_feedPlunge","60 in/min"),
                                  ("tolerance","0.1mm"),("doMultipleDepths","true"),
                                  ("maximumStepdown","3mm"),("useStockToLeave","true"),
                                  ("stockToLeave","0.02in")])
            cv = o.parameters.itemByName("pockets").value
            sel = cv.getCurveSelections(); sel.clear()
            for f in faces:
                ps = sel.createNewPocketSelection(); ps.inputGeometry = [f]
            cv.applyCurveSelections(sel)
            fut2 = cam.generateToolpath(o)
            for _ in range(400):
                if fut2.isGenerationCompleted: break
                time.sleep(1)
            return o
        # One floor Fusion refuses takes the whole operation down with it, and the
        # other pockets go unmachined without a word. Test the batch, and on
        # failure keep whatever generates. Done before the later ops exist, so the
        # replacement still lands first in the order.
        o = make_pocket(floors, "0 Pockets 1/4in")
        if not o.hasToolpath:
            o.deleteMe()
            good, bad = [], []
            for f in floors:
                probe = make_pocket([f], "__probe pocket")
                (good if probe.hasToolpath else bad).append(f)
                probe.deleteMe()
            print(f"      ! pocket batch failed - {len(good)} of {len(floors)} floors "
                  f"generate individually")
            for f in bad:
                print(f"          NOT MACHINED: floor of {f.area*100:.1f} mm2")
            if good:
                make_pocket(good, "0 Pockets 1/4in")
    if cutouts:
        def b1(sel):
            for edges in cutouts:
                c = sel.createNewChainSelection(); c.inputGeometry = edges
                c.sideType = adsk.cam.SideTypes.AlwaysInsideSideType
        contour("1 Inner cutouts 1/4in", b1)
    if big_c:
        i = setup.operations.createInput("bore"); i.tool = t_big
        i.displayName = "2 Bore large 1/4in"
        o = setup.operations.add(i)
        setp(o, common + [("tool_feedCutting","180 in/min"), ("tool_feedPlunge","50 in/min")])
        o.parameters.itemByName("circularFaces").value.value = big_c
    for tno in sorted(drill_c):
        faces = [f for f, _ in drill_c[tno]]
        t = tool_by_number(tno)
        if t is None:
            print(f"      ! tool #{tno} not in library - {len(faces)} holes skipped"); continue
        dia = {x.name: x for x in t.parameters}['tool_diameter'].value.value*10
        i = setup.operations.createInput("drill"); i.tool = t
        i.displayName = f"3 Drill {dia:.2f}mm #{tno}"
        o = setup.operations.add(i)
        setp(o, common + [("tool_feedPlunge", DRILL_FEED.get(tno, "20 in/min")),
                          ("cycleType","'chip-breaking'"),
                          ("peckingDepth", DRILL_PECK.get(tno, "5mm"))])
        o.parameters.itemByName("holeFaces").value.value = faces
        # Generate now: if the drill will not produce a toolpath, these holes have
        # to fall back to boring, and the bore op is created further down - after
        # this point there is no way to reorder.
        f2 = cam.generateToolpath(o)
        for _ in range(400):
            if f2.isGenerationCompleted: break
            time.sleep(1)
        if not o.hasToolpath:
            borable = [f for f in faces if f.geometry.radius*20 >= BORE_MIN]
            print(f"      ! drill #{tno} produced no toolpath - falling back to bore "
                  f"for {len(borable)} of {len(faces)} holes"
                  + (f", {len(faces)-len(borable)} too small to bore" if len(borable) < len(faces) else ""))
            o.deleteMe()
            small_f.extend(borable)
    if small_f:
        i = setup.operations.createInput("bore"); i.tool = t_small
        i.displayName = "3b Bore small 1/8in"
        o = setup.operations.add(i)
        setp(o, common + [("tool_feedCutting","125 in/min"), ("tool_feedPlunge","50 in/min")])
        o.parameters.itemByName("circularFaces").value.value = small_f
    if sloped:
        t3 = tool_by_number(TOOL_3D)
        if t3 is None:
            print(f"      ! tool #{TOOL_3D} missing - {len(sloped)} sloped parts not finished")
        else:
            def make_3d(bs, name):
                i = setup.operations.createInput("contour3d"); i.tool = t3
                i.displayName = name
                o = setup.operations.add(i)
                setp(o, common + [("tool_feedCutting","90 in/min"),
                                  ("tool_feedPlunge","45 in/min"),
                                  ("maximumStepdown","0.04in"), ("tolerance","0.05mm"),
                                  ("boundaryMode","'selection'"),
                                  ("boundaryContainment","'inside'"),
                                  # Without this it re-machines every flat top and
                                  # vertical wall the 2D ops already cut: 16min vs 1.1
                                  ("slopeConfinement","true"),
                                  ("slopeAngleFrom", f"{SLOPE_MIN}deg"),
                                  ("slopeAngleTo", f"{SLOPE_MAX}deg")])
                cv = o.parameters.itemByName("machiningBoundarySel").value
                sel = cv.getCurveSelections(); sel.clear()
                for b in bs:
                    sil = sel.createNewSilhouetteSelection(); sil.inputGeometry = [b]
                    sil.loopType = adsk.cam.LoopTypes.OnlyOutsideLoops
                cv.applyCurveSelections(sel)
                f3 = cam.generateToolpath(o)
                for _ in range(600):
                    if f3.isGenerationCompleted: break
                    time.sleep(1)
                return o
            print(f"      3D bevels on {len(sloped)}: "
                  f"{', '.join(sorted({n for _, n in sloped}))}")
            o = make_3d([b for b, _ in sloped], "3c Bevels 3D tapered ball")
            if not o.hasToolpath:
                o.deleteMe()
                good, bad = [], []
                for b, nm in sloped:
                    probe = make_3d([b], "__probe 3d")
                    (good if probe.hasToolpath else bad).append((b, nm))
                    probe.deleteMe()
                print(f"      ! 3D batch failed - {len(good)} of {len(sloped)} "
                      f"bodies generate individually")
                for _, nm in bad:
                    print(f"          NOT FINISHED: {nm}")
                if good:
                    o2 = make_3d([b for b, _ in good], "3c Bevels 3D tapered ball")
                    if not o2.hasToolpath:
                        o2.deleteMe()
                        for b, nm in good:
                            make_3d([b], f"3c Bevel {nm[:18]}")

    def b2(sel):
        for b in bodies:
            sil = sel.createNewSilhouetteSelection(); sil.inputGeometry = [b]
            sil.loopType = adsk.cam.LoopTypes.OnlyOutsideLoops
            sil.sideType = adsk.cam.SideTypes.AlwaysOutsideSideType
    contour("4 Outer profile 1/4in", b2)

    fut = cam.generateToolpath(setup)
    for _ in range(900):
        if fut.isGenerationCompleted: break
        time.sleep(1)
    # An operation with no toolpath blocks posting for the whole document, and
    # the error names no culprit. Drop it here and say so.
    for j in range(setup.operations.count - 1, -1, -1):
        op = setup.operations.item(j)
        if not op.hasToolpath:
            n = op.parameters.itemByName("holeFaces")
            cnt = len(n.value.value) if n and n.value.value else 0
            print(f"    *** '{op.name}' produced no toolpath ({cnt} holes) - REMOVED."
                  f" Those holes are not machined.")
            op.deleteMe()

    print("\n    result:")
    for i in range(setup.operations.count):
        o = setup.operations.item(i)
        p = {x.name: x for x in o.parameters}
        w = o.warning.strip().replace("\n"," ")[:55] if o.hasWarning else ""
        print(f"      {o.name:24} #{p['tool_number'].value.value}  path {o.hasToolpath}"
              f"  warn {o.hasWarning}  {w}")
    q = {x.name: x for x in setup.parameters}
    cx0 = q['surfaceXLow'].value.value*10 - R; cx1 = q['surfaceXHigh'].value.value*10 + R
    cy0 = q['surfaceYLow'].value.value*10 - R; cy1 = q['surfaceYHigh'].value.value*10 + R
    print(f"    cutter X {cx0:7.2f}..{cx1:7.2f} / {TX}   "
          f"Y {cy0:6.2f}..{cy1:7.2f} / {TY}   "
          f"{'OK' if cx0>=0 and cx1<=TX and cy0>=0 and cy1<=TY else '*** OVER TRAVEL ***'}")
