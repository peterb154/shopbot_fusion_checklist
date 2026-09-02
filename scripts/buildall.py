import adsk.core, adsk.fusion, adsk.cam, collections, time

TX, TY, R = 2438.4, 1219.2, 3.175
SHEET_W, SHEET_H = 2440.0, 1220.0     # standard baltic birch
MIN_LATITUDE = 10.0                   # refuse to build a sheet tighter than this
BIG = 9.0
TOOL_BIG, TOOL_SMALL = 4, 6

def classify(f):
    k = collections.Counter()
    for L in f.loops:
        for e in L.edges:
            k[e.geometry.objectType.split("::")[-1]] += 1
    if k.get("Line3D", 0) > 0: return "fillet"
    if k.get("Circle3D", 0) >= 1 and k.get("Arc3D", 0) == 0: return "hole"
    return "other"

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
                        name=f"Sheet {i} - {th:.0f}mm ({s['n']} X{s['x0']:.0f} Y{s['y0']:.0f})"))
    return out

def offsets(spanx, spany):
    hx, hy = TX - spanx - R, TY - spany - R
    if hx < R or hy < R: return None, None, min(hx-R, hy-R)
    ox = min(20.0, max(R, hx*0.5)); oy = min(20.0, max(R, hy*0.5))
    return round(ox,2), round(oy,2), min(hx-R, hy-R)

def run(_context: str):
    app = adsk.core.Application.get()
    doc = app.activeDocument
    des = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(doc.products.itemByProductType("CAMProductType"))
    plan = discover(des)
    have = {cam.setups.item(i).name: cam.setups.item(i) for i in range(cam.setups.count)}

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
        if state == "TO BUILD" and target is None: target = (s, ox, oy, exist)
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
        setup.machine = cam.setups.item(0).machine
        print(f"    created setup, {len(si.models)} models, machine "
              f"{setup.machine.vendor} {setup.machine.model}")
    while setup.operations.count: setup.operations.item(0).deleteMe()

    setp(setup, [("job_stockMode","'fixedbox'"),
                 ("job_stockFixedX", f"{SHEET_W}mm"), ("job_stockFixedXMode","'left'"),
                 ("job_stockFixedXOffset", f"{ox}mm"),
                 ("job_stockFixedY", f"{SHEET_H}mm"), ("job_stockFixedYMode","'front'"),
                 ("job_stockFixedYOffset", f"{oy}mm"),
                 ("job_stockFixedZ", f"{s['th']}mm"), ("job_stockFixedZMode","'bottom'"),
                 ("job_stockFixedZOffset","0mm"),
                 ("wcs_origin_mode","'stockPoint'"), ("wcs_origin_boxPoint","'top 1'"),
                 ("job_programName", f"'{1000+s['idx']}'")])

    stepdown = round((s['th'] + 0.508) / 2 + 0.15, 2)
    print(f"    stock {s['th']:.0f}mm -> stepdown {stepdown}mm for 2 passes")

    names = {m.name for m in setup.models}
    bodies, cutouts, big_c, small_c, floors = [], [], [], [], []
    for occ in des.rootComponent.allOccurrences:
        if occ.name not in names: continue
        for b in occ.bRepBodies:
            if not b.isSolid: continue
            bodies.append(b)
            _,_,_,_, zb, zt = extents(b)
            pl = [f for f in b.faces if f.geometry.objectType == adsk.core.Plane.classType()
                  and abs(abs(f.geometry.normal.z)-1.0) < 1e-6]
            for f in pl:
                fz = f.boundingBox.minPoint.z*10
                if zb + 0.1 < fz < zt - 0.1: floors.append(f)
            if pl:
                bot = min(pl, key=lambda f: f.boundingBox.minPoint.z)
                ls = list(bot.loops)
                outer = max(ls, key=lambda L: sum(e.length for e in L.edges))
                for L in ls:
                    if L is outer: continue
                    edges = list(L.edges)
                    ks = {e.geometry.objectType.split('::')[-1] for e in edges}
                    if len(edges) <= 2 and ks <= {"Circle3D","Arc3D"}: continue
                    cutouts.append(edges)
            for f in b.faces:
                g = f.geometry
                if g.objectType != adsk.core.Cylinder.classType(): continue
                if abs(abs(g.axis.z)-1.0) > 1e-6: continue
                if classify(f) != "hole": continue
                (big_c if g.radius*20 >= BIG else small_c).append(f)
    print(f"    bodies {len(bodies)} | cutouts {len(cutouts)} | big {len(big_c)} | "
          f"small {len(small_c)} | floors {len(floors)}")

    t_big, t_small = tool_by_number(TOOL_BIG), tool_by_number(TOOL_SMALL)
    common = [("tool_spindleSpeed","14000"), ("tool_coolant","'disabled'"),
              ("bottomHeight_mode","'from stock bottom'"), ("bottomHeight_offset","-0.02in")]
    mill = common + [("tool_feedCutting","180 in/min"), ("tool_feedPlunge","60 in/min"),
                     ("tolerance","0.1mm"), ("doMultipleDepths","true"),
                     ("maximumStepdown", f"{stepdown}mm"), ("doRoughingPasses","true"),
                     ("maximumStepover","0.1in"), ("useStockToLeave","true"),
                     ("stockToLeave","0.02in"), ("compensation","'left'")]

    def contour(nm, build):
        i = setup.operations.createInput("contour2d"); i.tool = t_big; i.displayName = nm
        o = setup.operations.add(i); setp(o, mill)
        cv = o.parameters.itemByName("contours").value
        sel = cv.getCurveSelections(); sel.clear(); build(sel); cv.applyCurveSelections(sel)
        return o

    if floors:
        i = setup.operations.createInput("pocket2d"); i.tool = t_big
        i.displayName = "0 Pockets 1/4in"
        o = setup.operations.add(i)
        setp(o, common[:2] + [("tool_feedCutting","180 in/min"),("tool_feedPlunge","60 in/min"),
                              ("tolerance","0.1mm"),("doMultipleDepths","true"),
                              ("maximumStepdown","3mm"),("useStockToLeave","true"),
                              ("stockToLeave","0.02in")])
        cv = o.parameters.itemByName("pockets").value
        sel = cv.getCurveSelections(); sel.clear()
        for f in floors:
            ps = sel.createNewPocketSelection(); ps.inputGeometry = [f]
        cv.applyCurveSelections(sel)
    if cutouts:
        def b1(sel):
            for edges in cutouts:
                c = sel.createNewChainSelection(); c.inputGeometry = edges
                c.sideType = adsk.cam.SideTypes.AlwaysInsideSideType
        contour("1 Inner cutouts 1/4in", b1)
    for label, faces, tool, feed in (("2 Bore large 1/4in", big_c, t_big, "180 in/min"),
                                     ("3 Bore small 1/8in", small_c, t_small, "125 in/min")):
        if not faces: continue
        i = setup.operations.createInput("bore"); i.tool = tool; i.displayName = label
        o = setup.operations.add(i)
        setp(o, common + [("tool_feedCutting", feed), ("tool_feedPlunge","50 in/min")])
        o.parameters.itemByName("circularFaces").value.value = faces
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
