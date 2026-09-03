import adsk.core, adsk.fusion, adsk.cam, math

def true_normal_at(f):
    ev = f.evaluator
    ok, prm = ev.getParameterAtPoint(f.pointOnFace)
    if not ok: return None
    ok2, n = ev.getNormalAtParameter(prm)
    return n if ok2 else None

def sampled(f, n=3):
    """[(slope_deg, normal_z)] over the face, using the TRUE face normal."""
    ev = f.evaluator; rng = ev.parametricRange()
    if rng is None:
        nv = true_normal_at(f)
        if nv is None: return []
        return [(math.degrees(math.acos(min(1.0, abs(nv.z)))), nv.z)]
    out = []
    for i in range(n):
        for j in range(n):
            u = rng.minPoint.x + (rng.maxPoint.x-rng.minPoint.x)*(i+0.5)/n
            v = rng.minPoint.y + (rng.maxPoint.y-rng.minPoint.y)*(j+0.5)/n
            ok, nv = ev.getNormalAtParameter(adsk.core.Point2D.create(u, v))
            if ok: out.append((math.degrees(math.acos(min(1.0, abs(nv.z)))), nv.z))
    return out

def run(_context: str):
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeDocument.products.itemByProductType("DesignProductType"))
    cam = adsk.cam.CAM.cast(app.activeDocument.products.itemByProductType("CAMProductType"))
    print("sloped faces by which way they FACE (up = reachable from the top):\n")
    flipped = []
    for i in range(cam.setups.count):
        s = cam.setups.item(i)
        names = {m.name for m in s.models}
        rows = []
        for occ in des.rootComponent.allOccurrences:
            if occ.name not in names: continue
            for b in occ.bRepBodies:
                if not b.isSolid: continue
                up = dn = 0.0; nup = ndn = 0
                for f in b.faces:
                    sm = sampled(f)
                    if not sm: continue
                    sl = [a for a, _ in sm]
                    if max(sl) < 5.0 or min(sl) > 85.0: continue
                    mz = sum(z for _, z in sm)/len(sm)
                    if mz >= 0: up += f.area*100; nup += 1
                    else:       dn += f.area*100; ndn += 1
                if nup or ndn:
                    rows.append((occ.name.split(':')[0].strip(), nup, up, ndn, dn))
        rows = [r for r in rows if r[3]]
        if rows:
            print(f"  {s.name}")
            for nm, nup, up, ndn, dn in sorted(rows, key=lambda r: -r[4]):
                tag = "  *** ALL BEVELS FACE DOWN - PART IS UPSIDE DOWN" if nup == 0 else "  (mixed)"
                print(f"      {nm:<22} up {nup:2} / {up:8.1f} mm2   "
                      f"DOWN {ndn:2} / {dn:8.1f} mm2{tag}")
                flipped.append((s.name, nm, nup, ndn))
    if not flipped:
        print("  none - every sloped face is reachable from the top")
    else:
        print(f"\n  {len(flipped)} part(s) with downward-facing sloped faces")
